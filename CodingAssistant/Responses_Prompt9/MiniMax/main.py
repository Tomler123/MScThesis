"""In-memory inverted index for full-text search."""
import re
from collections import defaultdict
from typing import Dict, List


class SearchIndex:
    """An in-memory inverted index for full-text search over documents."""

    def __init__(self) -> None:
        """Initialize the search index with empty data structures."""
        # Inverted index: token -> {doc_id: frequency_in_that_doc}
        self._index: Dict[str, Dict[str, int]] = defaultdict(dict)
        # Document store: doc_id -> {token: frequency_in_that_doc}
        self._doc_store: Dict[str, Dict[str, int]] = {}

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text by splitting on non-alphanumeric characters, lowercase."""
        tokens = re.split(r'[^a-zA-Z0-9]+', text)
        return [t.lower() for t in tokens if t]

    def add(self, doc_id: str, text: str) -> None:
        """Index a document. If the same doc_id is added again, replace the previous content."""
        tokens = self._tokenize(text)

        # Count token frequencies in this document
        token_counts: Dict[str, int] = defaultdict(int)
        for token in tokens:
            token_counts[token] += 1

        # Remove existing document if present (for replacement)
        if doc_id in self._doc_store:
            self.remove(doc_id)

        # Store the document's token counts
        self._doc_store[doc_id] = dict(token_counts)

        # Update inverted index with token -> doc_id mappings
        for token, count in token_counts.items():
            self._index[token][doc_id] = count

    def search(self, query: str) -> List[str]:
        """Return doc_ids containing all query terms (AND logic), sorted by relevance."""
        query_tokens = self._tokenize(query)

        # Empty query returns empty list
        if not query_tokens:
            return []

        # Find docs containing first token
        first_token = query_tokens[0]
        if first_token not in self._index:
            return []

        # Start with docs containing first token, intersect with others (AND logic)
        result_docs = set(self._index[first_token].keys())
        for token in query_tokens[1:]:
            if token in self._index:
                result_docs &= self._index[token].keys()
            else:
                return []  # No doc contains this term

        # Calculate relevance score (sum of query term frequencies) for each doc
        relevance_scores = []
        for doc_id in result_docs:
            total_occurrences = sum(
                self._doc_store[doc_id].get(token, 0) for token in query_tokens
            )
            relevance_scores.append((doc_id, total_occurrences))

        # Sort by relevance descending, then by doc_id ascending (for ties)
        relevance_scores.sort(key=lambda x: (-x[1], x[0]))

        return [doc_id for doc_id, _ in relevance_scores]

    def remove(self, doc_id: str) -> None:
        """Remove a document from the index. If not found, do nothing."""
        if doc_id not in self._doc_store:
            return

        # Remove this doc from inverted index entries
        for token in self._doc_store[doc_id]:
            del self._index[token][doc_id]
            # Clean up empty token entries
            if not self._index[token]:
                del self._index[token]

        # Remove from document store
        del self._doc_store[doc_id]
