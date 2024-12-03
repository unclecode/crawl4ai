from abc import ABC, abstractmethod
from .models import CrawlResult
import json
import re
from datasets import Dataset
from huggingface_hub import DatasetCard
from typing import Any


class DataPersistenceStrategy(ABC):
    """
    Abstract base class for implementing data persistence strategies.
    """

    @abstractmethod
    def save(self, result: CrawlResult) -> dict[str, Any]:
        """
        Save the given crawl result using a specific persistence strategy.

        Args:
            result (CrawlResult): The crawl result containing data to persist.

        Returns:
            dict[str, Any]: A dictionary representing the outcome details of the persistence operation.
        """
        pass


class SkipDataPersistenceStrategy(DataPersistenceStrategy):
    def save(self, result: CrawlResult) -> dict[str, Any]:
        return None


DATASET_CARD_TEMPLATE = """
---
tags:
- crawl4ai
- crawl
---

**Source of the data:**

The dataset was generated using [Crawl4ai](https://crawl4ai.com/mkdocs/) library from {url}.

"""


class HFDataPersistenceStrategy(DataPersistenceStrategy):
    """
    A persistence strategy for uploading extracted content or markdown from crawl results to the Hugging Face Hub.

    This strategy converts the extracted content or markdown into a Hugging Face Dataset
    and uploads it to a specified repository on the Hub.

    Args:
        repo_id (str): The repository ID on the Hugging Face Hub.
        private (bool): Whether the repository should be private.
        card (str, optional): The card information for the dataset. Defaults to None.
        token (str, optional): The authentication token for the Hugging Face Hub. Defaults to None.
        logger (Logger, optional): Logger instance for logging messages. Defaults to None.
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self, repo_id: str, private: bool, card: str = None, token=None, **kwargs
    ):
        self.repo_id = repo_id
        self.private = private
        self.card = card
        self.verbose = kwargs.get("verbose", False)
        self.token = token

    def save(self, result: CrawlResult) -> dict[str, Any]:
        """
        Uploads extracted content or markdown from the given crawl result to the Hugging Face Hub.

        Args:
            result (CrawlResult): The crawl result containing extracted content or markdown to upload.

        Returns:
            dict[str, Any]: A dictionary with the repository ID and dataset split name.

        Raises:
            ValueError: If neither extracted content nor markdown is present in the result.
            TypeError: If extracted content or markdown is not a string.

        Notes:
            - Extracted content should be a JSON string containing a list of dictionaries.
            - If extracted content is invalid, raw markdown will be used as a fallback.
            - The repository ID and dataset split name are returned upon successful upload.
        """
        if not (result.extracted_content or result.markdown):
            raise ValueError("No extracted content or markdown present.")

        if result.extracted_content and not isinstance(result.extracted_content, str):
            raise TypeError("Extracted content must be a string.")

        if result.markdown and not isinstance(result.markdown, str):
            raise TypeError("Markdown must be a string.")

        records = self._prepare_records(result)

        if self.verbose:
            print(
                f"[LOG] 🔄 Successfully converted extracted content to JSON records: {len(records)} records found"
            )

        ds = Dataset.from_list(records)
        sanitized_split_name = re.sub(r"[^a-zA-Z0-9_]", "_", result.url)
        commit_info = ds.push_to_hub(
            repo_id=self.repo_id,
            private=self.private,
            token=self.token,
            split=sanitized_split_name,
        )

        repo_id = commit_info.repo_url.repo_id
        self._push_dataset_card(repo_id, result.url)

        if self.verbose:
            print(
                f"[LOG] ✅ Data has been successfully pushed to the Hugging Face Hub. Repository ID: {repo_id}"
            )

        return {"repo_id": repo_id, "split": sanitized_split_name}

    def _prepare_records(self, result: CrawlResult) -> list[dict[str, Any]]:
        if result.extracted_content:
            try:
                records = json.loads(result.extracted_content)
                if not isinstance(records, list) or not all(
                    isinstance(rec, dict) for rec in records
                ):
                    raise ValueError(
                        "Extracted content must be a JSON list of dictionaries."
                    )
            except json.JSONDecodeError as e:
                if self.verbose:
                    print(f"[LOG] ⚠️ Failed to parse extracted content as JSON: {e}")
                records = [{"extracted_content": result.extracted_content}]
        else:
            records = [{"markdown": result.markdown}]

        return records

    def _push_dataset_card(self, repo_id: str, url: str) -> None:
        card_content = self.card or DATASET_CARD_TEMPLATE.format(url=url)
        DatasetCard(content=card_content).push_to_hub(
            repo_id=repo_id, repo_type="dataset", token=self.token
        )
        if self.verbose:
            print(f"[LOG] 🔄 Dataset card successfully pushed to repository: {repo_id}")
