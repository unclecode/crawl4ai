# Optional source receipts

Pass `CrawlerRunConfig(source_receipt=True)` and inspect `result.source_receipt`.
The JSON-safe receipt hashes each available raw/fit Markdown output as exact UTF-8
bytes, without whitespace normalization. It records served time separately from
fetch completion time and reports cache status. Minimal fetch provenance persists
in the reserved `_crawl4ai_source_receipt_v1` metadata key without a database migration.

On cache hits, original recorded fetch time and processing fingerprint are reused.
Legacy cache entries have unknown fetch time/version/options (`null`), rather than
inventing a fresh fetch time from the cache write or current request. Provided raw
HTML and local files likewise do not claim a network fetch time. Failed crawls do
not get receipts. Cached Markdown may expose fewer output kinds than a live result;
the receipt hashes only the exact outputs actually returned.

Credentials, query strings and fragments are omitted from receipt URLs, and raw
HTML/file URLs are not included. URL paths can still contain private data; receipts
are provenance for your application, not automatically safe publication records.
Only `word_count_threshold`, `only_text`, `remove_forms`, and `parser_type` enter the
processing fingerprint. It is explicitly not a complete cache key: selectors, custom
strategies, model/provider parameters and secrets are not serialized or fingerprinted.
The text digest itself identifies the returned bytes; it does not prove truth,
source rights, or equivalence of different processing configurations.
