import os
from pathlib import Path
from rank_bm25 import BM25Okapi
import re
from typing import List, Literal

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk


BASE_PATH = Path(__file__).resolve().parent

def get_file_map() -> dict:
    """Cache file mappings to avoid repeated directory scans"""
    files = os.listdir(BASE_PATH)
    file_map = {}
    
    for file in files:
        if file.endswith('.md'):
            # Extract number and name: "6_chunking_strategies.md" -> ("chunking_strategies", "6")
            match = re.match(r'(\d+)_(.+?)(?:\.(?:ex|xs|sm|q)?\.md)?$', file)
            if match:
                num, name = match.groups()
                if name not in file_map:
                    file_map[name] = num
    return file_map

def concatenate_docs(file_names: List[str], mode: Literal["extended", "condensed"]) -> str:
    """Concatenate documentation files based on names and mode."""
    file_map = get_file_map()
    result = []
    suffix_map = {
        "extended": ".ex.md",
        "condensed": [".xs.md", ".sm.md"]
    }
    
    for name in file_names:
        if name not in file_map:
            continue
            
        num = file_map[name]
        base_path = BASE_PATH
        
        if mode == "extended":
            file_path = base_path / f"{num}_{name}{suffix_map[mode]}"
            if not file_path.exists():
                file_path = base_path / f"{num}_{name}.md"
        else:
            file_path = None
            for suffix in suffix_map["condensed"]:
                temp_path = base_path / f"{num}_{name}{suffix}"
                if temp_path.exists():
                    file_path = temp_path
                    break
            if not file_path:
                file_path = base_path / f"{num}_{name}.md"
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                result.append(f.read())
    
    return "\n\n---\n\n".join(result)

def extract_questions(content: str) -> List[tuple[str, str, str]]:
    """
    Extract questions from Q files, returning list of (category, question, full_section).
    """
    # Split into main sections (### Questions or ### Hypothetical Questions)
    sections = re.split(r'^###\s+.*Questions\s*$', content, flags=re.MULTILINE)[1:]
    
    results = []
    for section in sections:
        # Find all numbered categories (1. **Category Name**)
        categories = re.split(r'^\d+\.\s+\*\*([^*]+)\*\*\s*$', section.strip(), flags=re.MULTILINE)
        
        # Process each category
        for i in range(1, len(categories), 2):
            category = categories[i].strip()
            category_content = categories[i+1].strip()
            
            # Extract questions (lines starting with dash and wrapped in italics)
            questions = re.findall(r'^\s*-\s*\*"([^"]+)"\*\s*$', category_content, flags=re.MULTILINE)
            
            # Add each question with its category and full context
            for q in questions:
                results.append((category, q, f"Category: {category}\nQuestion: {q}"))
    
    return results

def preprocess_text(text: str) -> List[str]:
    """Preprocess text for better semantic matching"""
    # Lowercase and tokenize
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords but keep question words
    stop_words = set(stopwords.words('english')) - {'how', 'what', 'when', 'where', 'why', 'which'}
    lemmatizer = WordNetLemmatizer()
    
    # Lemmatize but preserve original form for technical terms
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    
    return tokens

def search_questions(query: str, top_k: int = 5) -> str:
    """Search through Q files using BM25 ranking and return top K matches."""
    q_files = [f for f in os.listdir(BASE_PATH) if f.endswith(".q.md")]
    # Prepare base path for file reading
    q_files = [BASE_PATH / f for f in q_files] # Convert to full path
    
    documents = []
    file_contents = {}
    
    for file in q_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            questions = extract_questions(content)
            for category, question, full_section in questions:
                documents.append(question)
                file_contents[question] = (file, category, full_section)

    if not documents:
        return "No questions found in documentation."

    tokenized_docs = [preprocess_text(doc) for doc in documents]
    tokenized_query = preprocess_text(query)
    
    bm25 = BM25Okapi(tokenized_docs)
    doc_scores = bm25.get_scores(tokenized_query)
    
    score_threshold = max(doc_scores) * 0.4
    
    # Aggregate scores by file
    file_data = {}
    for idx, score in enumerate(doc_scores):
        if score > score_threshold:
            question = documents[idx]
            file, category, _ = file_contents[question]
            
            if file not in file_data:
                file_data[file] = {
                    'total_score': 0,
                    'match_count': 0,
                    'questions': []
                }
            
            file_data[file]['total_score'] += score
            file_data[file]['match_count'] += 1
            file_data[file]['questions'].append({
                'category': category,
                'question': question,
                'score': score
            })
    
    # Sort files by match count and total score
    ranked_files = sorted(
        file_data.items(),
        key=lambda x: (x[1]['match_count'], x[1]['total_score']),
        reverse=True
    )[:top_k]
    
    # Format results by file
    results = []
    for file, data in ranked_files:
        questions_summary = "\n".join(
            f"- [{q['category']}] {q['question']} (score: {q['score']:.2f})"
            for q in sorted(data['questions'], key=lambda x: x['score'], reverse=True)
        )
        
        results.append(
            f"File: {file}\n"
            f"Match Count: {data['match_count']}\n"
            f"Total Score: {data['total_score']:.2f}\n\n"
            f"Matching Questions:\n{questions_summary}"
        )
    
    return "\n\n---\n\n".join(results) if results else "No relevant matches found."

if __name__ == "__main__":
    # Example 1: Concatenate docs
    docs = concatenate_docs(["chunking_strategies", "content_selection"], "extended")
    print("Concatenated docs:", docs[:200], "...\n")
    
    # Example 2: Search questions
    results = search_questions("How do I execute JS script on the page?", 3)
    print("Search results:", results[:200], "...")