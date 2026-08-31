import os
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional, Any
import json
from tqdm import tqdm
import time
import psutil
import numpy as np
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from litellm import batch_completion
from .async_logger import AsyncLogger
import litellm
import pickle
import hashlib  # <--- ADDED for file-hash
import glob

litellm.set_verbose = False


def _compute_file_hash(file_path: Path) -> str:
    """Compute MD5 hash for the file's entire content."""
    hash_md5 = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class AsyncLLMTextManager:
    def __init__(
        self,
        docs_dir: Path,
        logger: Optional[AsyncLogger] = None,
        max_concurrent_calls: int = 5,
        batch_size: int = 3,
    ) -> None:
        self.docs_dir = docs_dir
        self.logger = logger
        self.max_concurrent_calls = max_concurrent_calls
        self.batch_size = batch_size
        self.bm25_index = None
        self.document_map: Dict[str, Any] = {}
        self.tokenized_facts: List[str] = []
        self.bm25_index_file = self.docs_dir / "bm25_index.pkl"

    async def _process_document_batch(self, doc_batch: List[Path]) -> None:
        """Process a batch of documents in parallel"""
        contents = []
        for file_path in doc_batch:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    contents.append(f.read())
            except Exception as e:
                self.logger.error(f"Error reading {file_path}: {str(e)}")
                contents.append("")  # Add empty content to maintain batch alignment

        prompt = """Given a documentation file, generate a list of atomic facts where each fact:
1. Represents a single piece of knowledge
2. Contains variations in terminology for the same concept
3. References relevant code patterns if they exist
4. Is written in a way that would match natural language queries

Each fact should follow this format:
<main_concept>: <fact_statement> | <related_terms> | <code_reference>

Example Facts:
browser_config: Configure headless mode and browser type for AsyncWebCrawler | headless, browser_type, chromium, firefox | BrowserConfig(browser_type="chromium", headless=True)
redis_connection: Redis client connection requires host and port configuration | redis setup, redis client, connection params | Redis(host='localhost', port=6379, db=0)
pandas_filtering: Filter DataFrame rows using boolean conditions | dataframe filter, query, boolean indexing | df[df['column'] > 5]

Wrap your response in <index>...</index> tags.
"""

        # Prepare messages for batch processing
        messages_list = [
            [
                {
                    "role": "user",
                    "content": f"{prompt}\n\nGenerate index for this documentation:\n\n{content}",
                }
            ]
            for content in contents
            if content
        ]

        try:
            responses = batch_completion(
                model="anthropic/claude-3-5-sonnet-latest",
                messages=messages_list,
                logger_fn=None,
            )

            # Process responses and save index files
            for response, file_path in zip(responses, doc_batch):
                try:
                    index_content_match = re.search(
                        r"<index>(.*?)</index>",
                        response.choices[0].message.content,
                        re.DOTALL,
                    )
                    if not index_content_match:
                        self.logger.warning(
                            f"No <index>...</index> content found for {file_path}"
                        )
                        continue

                    index_content = re.sub(
                        r"\n\s*\n", "\n", index_content_match.group(1)
                    ).strip()
                    if index_content:
                        index_file = file_path.with_suffix(".q.md")
                        with open(index_file, "w", encoding="utf-8") as f:
                            f.write(index_content)
                        self.logger.info(f"Created index file: {index_file}")
                    else:
                        self.logger.warning(
                            f"No index content found in response for {file_path}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error processing response for {file_path}: {str(e)}"
                    )

        except Exception as e:
            self.logger.error(f"Error in batch completion: {str(e)}")

    def _validate_fact_line(self, line: str) -> Tuple[bool, Optional[str]]:
        if "|" not in line:
            return False, "Missing separator '|'"

        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            return False, f"Expected 3 parts, got {len(parts)}"

        concept_part = parts[0]
        if ":" not in concept_part:
            return False, "Missing ':' in concept definition"

        return True, None

    def _load_or_create_token_cache(self, fact_file: Path) -> Dict:
        """
        Load token cache from .q.tokens if present and matching file hash.
        Otherwise return a new structure with updated file-hash.
        """
        cache_file = fact_file.with_suffix(".q.tokens")
        current_hash = _compute_file_hash(fact_file)

        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cache = json.load(f)
                # If the hash matches, return it directly
                if cache.get("content_hash") == current_hash:
                    return cache
                # Otherwise, we signal that it's changed
                self.logger.info(f"Hash changed for {fact_file}, reindex needed.")
            except json.JSONDecodeError:
                self.logger.warning(f"Corrupt token cache for {fact_file}, rebuilding.")
            except Exception as e:
                self.logger.warning(f"Error reading cache for {fact_file}: {str(e)}")

        # Return a fresh cache
        return {"facts": {}, "content_hash": current_hash}

    def _save_token_cache(self, fact_file: Path, cache: Dict) -> None:
        cache_file = fact_file.with_suffix(".q.tokens")
        # Always ensure we're saving the correct file-hash
        cache["content_hash"] = _compute_file_hash(fact_file)
        with open(cache_file, "w") as f:
            json.dump(cache, f)

    def preprocess_text(self, text: str) -> List[str]:
        parts = [x.strip() for x in text.split("|")] if "|" in text else [text]
        # Remove : after the first word of parts[0]
        parts[0] = re.sub(r"^(.*?):", r"\1", parts[0])

        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words("english")) - {
            "how",
            "what",
            "when",
            "where",
            "why",
            "which",
        }

        tokens = []
        for part in parts:
            if "(" in part and ")" in part:
                code_tokens = re.findall(
                    r'[\w_]+(?=\()|[\w_]+(?==[\'"]{1}[\w_]+[\'"]{1})', part
                )
                tokens.extend(code_tokens)

            words = word_tokenize(part.lower())
            tokens.extend(
                [
                    lemmatizer.lemmatize(token)
                    for token in words
                    if token not in stop_words
                ]
            )

        return tokens

    def maybe_load_bm25_index(self, clear_cache=False) -> bool:
        """
        Load existing BM25 index from disk, if present and clear_cache=False.
        """
        if not clear_cache and os.path.exists(self.bm25_index_file):
            self.logger.info("Loading existing BM25 index from disk.")
            with open(self.bm25_index_file, "rb") as f:
                data = pickle.load(f)
            self.tokenized_facts = data["tokenized_facts"]
            self.bm25_index = data["bm25_index"]
            return True
        return False

    def build_search_index(self, clear_cache=False) -> None:
        """
        Checks for new or modified .q.md files by comparing file-hash.
        If none need reindexing and clear_cache is False, loads existing index if available.
        Otherwise, reindexes only changed/new files and merges or creates a new index.
        """
        # If clear_cache is True, we skip partial logic: rebuild everything from scratch
        if clear_cache:
            self.logger.info("Clearing cache and rebuilding full search index.")
            if self.bm25_index_file.exists():
                self.bm25_index_file.unlink()

        process = psutil.Process()
        self.logger.info("Checking which .q.md files need (re)indexing...")

        # Gather all .q.md files
        q_files = [
            self.docs_dir / f for f in os.listdir(self.docs_dir) if f.endswith(".q.md")
        ]

        # We'll store known (unchanged) facts in these lists
        existing_facts: List[str] = []
        existing_tokens: List[List[str]] = []

        # Keep track of invalid lines for logging
        invalid_lines = []
        needSet = []  # files that must be (re)indexed

        for qf in q_files:
            token_cache_file = qf.with_suffix(".q.tokens")

            # If no .q.tokens or clear_cache is True → definitely reindex
            if clear_cache or not token_cache_file.exists():
                needSet.append(qf)
                continue

            # Otherwise, load the existing cache and compare hash
            cache = self._load_or_create_token_cache(qf)
            # If the .q.tokens was out of date (i.e. changed hash), we reindex
            if len(cache["facts"]) == 0 or cache.get(
                "content_hash"
            ) != _compute_file_hash(qf):
                needSet.append(qf)
            else:
                # File is unchanged → retrieve cached token data
                for line, cache_data in cache["facts"].items():
                    existing_facts.append(line)
                    existing_tokens.append(cache_data["tokens"])
                    self.document_map[line] = qf  # track the doc for that fact

        if not needSet and not clear_cache:
            # If no file needs reindexing, try loading existing index
            if self.maybe_load_bm25_index(clear_cache=False):
                self.logger.info(
                    "No new/changed .q.md files found. Using existing BM25 index."
                )
                return
            else:
                # If there's no existing index, we must build a fresh index from the old caches
                self.logger.info(
                    "No existing BM25 index found. Building from cached facts."
                )
                if existing_facts:
                    self.logger.info(
                        f"Building BM25 index with {len(existing_facts)} cached facts."
                    )
                    self.bm25_index = BM25Okapi(existing_tokens)
                    self.tokenized_facts = existing_facts
                    with open(self.bm25_index_file, "wb") as f:
                        pickle.dump(
                            {
                                "bm25_index": self.bm25_index,
                                "tokenized_facts": self.tokenized_facts,
                            },
                            f,
                        )
                else:
                    self.logger.warning("No facts found at all. Index remains empty.")
                return

        # ----------------------------------------------------- /Users/unclecode/.crawl4ai/docs/14_proxy_security.q.q.tokens '/Users/unclecode/.crawl4ai/docs/14_proxy_security.q.md'
        # If we reach here, we have new or changed .q.md files
        # We'll parse them, reindex them, and then combine with existing_facts
        # -----------------------------------------------------

        self.logger.info(f"{len(needSet)} file(s) need reindexing. Parsing now...")

        # 1) Parse the new or changed .q.md files
        new_facts = []
        new_tokens = []
        with tqdm(total=len(needSet), desc="Indexing changed files") as file_pbar:
            for file in needSet:
                # We'll build up a fresh cache
                fresh_cache = {"facts": {}, "content_hash": _compute_file_hash(file)}
                try:
                    with open(file, "r", encoding="utf-8") as f_obj:
                        content = f_obj.read().strip()
                        lines = [l.strip() for l in content.split("\n") if l.strip()]

                    for line in lines:
                        is_valid, error = self._validate_fact_line(line)
                        if not is_valid:
                            invalid_lines.append((file, line, error))
                            continue

                        tokens = self.preprocess_text(line)
                        fresh_cache["facts"][line] = {
                            "tokens": tokens,
                            "added": time.time(),
                        }
                        new_facts.append(line)
                        new_tokens.append(tokens)
                        self.document_map[line] = file

                    # Save the new .q.tokens with updated hash
                    self._save_token_cache(file, fresh_cache)

                    mem_usage = process.memory_info().rss / 1024 / 1024
                    self.logger.debug(
                        f"Memory usage after {file.name}: {mem_usage:.2f}MB"
                    )

                except Exception as e:
                    self.logger.error(f"Error processing {file}: {str(e)}")

                file_pbar.update(1)

        if invalid_lines:
            self.logger.warning(f"Found {len(invalid_lines)} invalid fact lines:")
            for file, line, error in invalid_lines:
                self.logger.warning(f"{file}: {error} in line: {line[:50]}...")

        # 2) Merge newly tokenized facts with the existing ones
        all_facts = existing_facts + new_facts
        all_tokens = existing_tokens + new_tokens

        # 3) Build BM25 index from combined facts
        self.logger.info(
            f"Building BM25 index with {len(all_facts)} total facts (old + new)."
        )
        self.bm25_index = BM25Okapi(all_tokens)
        self.tokenized_facts = all_facts

        # 4) Save the updated BM25 index to disk
        with open(self.bm25_index_file, "wb") as f:
            pickle.dump(
                {
                    "bm25_index": self.bm25_index,
                    "tokenized_facts": self.tokenized_facts,
                },
                f,
            )

        final_mem = process.memory_info().rss / 1024 / 1024
        self.logger.info(f"Search index updated. Final memory usage: {final_mem:.2f}MB")

    async def generate_index_files(
        self, force_generate_facts: bool = False, clear_bm25_cache: bool = False
    ) -> None:
        """
        Generate index files for all documents in parallel batches

        Args:
            force_generate_facts (bool): If True, regenerate indexes even if they exist
            clear_bm25_cache (bool): If True, clear existing BM25 index cache
        """
        self.logger.info("Starting index generation for documentation files.")

        md_files = [
            self.docs_dir / f
            for f in os.listdir(self.docs_dir)
            if f.endswith(".md") and not any(f.endswith(x) for x in [".q.md", ".xs.md"])
        ]

        # Filter out files that already have .q files unless force=True
        if not force_generate_facts:
            md_files = [
                f
                for f in md_files
                if not (self.docs_dir / f.name.replace(".md", ".q.md")).exists()
            ]

        if not md_files:
            self.logger.info("All index files exist. Use force=True to regenerate.")
        else:
            # Process documents in batches
            for i in range(0, len(md_files), self.batch_size):
                batch = md_files[i : i + self.batch_size]
                self.logger.info(
                    f"Processing batch {i//self.batch_size + 1}/{(len(md_files)//self.batch_size) + 1}"
                )
                await self._process_document_batch(batch)

        self.logger.info("Index generation complete, building/updating search index.")
        self.build_search_index(clear_cache=clear_bm25_cache)

    def generate(self, sections: List[str], mode: str = "extended") -> str:
        # Get all markdown files
        all_files = glob.glob(str(self.docs_dir / "[0-9]*.md")) + glob.glob(
            str(self.docs_dir / "[0-9]*.xs.md")
        )

        # Extract base names without extensions
        base_docs = {
            Path(f).name.split(".")[0]
            for f in all_files
            if not Path(f).name.endswith(".q.md")
        }

        # Filter by sections if provided
        if sections:
            base_docs = {
                doc
                for doc in base_docs
                if any(section.lower() in doc.lower() for section in sections)
            }

        # Get file paths based on mode
        files = []
        for doc in sorted(
            base_docs,
            key=lambda x: int(x.split("_")[0]) if x.split("_")[0].isdigit() else 999999,
        ):
            if mode == "condensed":
                xs_file = self.docs_dir / f"{doc}.xs.md"
                regular_file = self.docs_dir / f"{doc}.md"
                files.append(str(xs_file if xs_file.exists() else regular_file))
            else:
                files.append(str(self.docs_dir / f"{doc}.md"))

        # Read and format content
        content = []
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    fname = Path(file).name
                    content.append(f"{'#'*20}\n# {fname}\n{'#'*20}\n\n{f.read()}")
            except Exception as e:
                self.logger.error(f"Error reading {file}: {str(e)}")

        return "\n\n---\n\n".join(content) if content else ""

    def search(self, query: str, top_k: int = 5) -> str:
        if not self.bm25_index:
            return "No search index available. Call build_search_index() first."

        query_tokens = self.preprocess_text(query)
        doc_scores = self.bm25_index.get_scores(query_tokens)

        mean_score = np.mean(doc_scores)
        std_score = np.std(doc_scores)
        score_threshold = mean_score + (0.25 * std_score)

        file_data = self._aggregate_search_scores(
            doc_scores=doc_scores,
            score_threshold=score_threshold,
            query_tokens=query_tokens,
        )

        ranked_files = sorted(
            file_data.items(),
            key=lambda x: (
                x[1]["code_match_score"] * 2.0
                + x[1]["match_count"] * 1.5
                + x[1]["total_score"]
            ),
            reverse=True,
        )[:top_k]

        results = []
        for file, _ in ranked_files:
            main_doc = str(file).replace(".q.md", ".md")
            if os.path.exists(self.docs_dir / main_doc):
                with open(self.docs_dir / main_doc, "r", encoding="utf-8") as f:
                    only_file_name = main_doc.split("/")[-1]
                    content = ["#" * 20, f"# {only_file_name}", "#" * 20, "", f.read()]
                    results.append("\n".join(content))

        return "\n\n---\n\n".join(results)

    def _aggregate_search_scores(
        self, doc_scores: List[float], score_threshold: float, query_tokens: List[str]
    ) -> Dict:
        file_data = {}

        for idx, score in enumerate(doc_scores):
            if score <= score_threshold:
                continue

            fact = self.tokenized_facts[idx]
            file_path = self.document_map[fact]

            if file_path not in file_data:
                file_data[file_path] = {
                    "total_score": 0,
                    "match_count": 0,
                    "code_match_score": 0,
                    "matched_facts": [],
                }

            components = fact.split("|") if "|" in fact else [fact]

            code_match_score = 0
            if len(components) == 3:
                code_ref = components[2].strip()
                code_tokens = self.preprocess_text(code_ref)
                code_match_score = len(set(query_tokens) & set(code_tokens)) / len(
                    query_tokens
                )

            file_data[file_path]["total_score"] += score
            file_data[file_path]["match_count"] += 1
            file_data[file_path]["code_match_score"] = max(
                file_data[file_path]["code_match_score"], code_match_score
            )
            file_data[file_path]["matched_facts"].append(fact)

        return file_data

    def refresh_index(self) -> None:
        """Convenience method for a full rebuild."""
        self.build_search_index(clear_cache=True)
