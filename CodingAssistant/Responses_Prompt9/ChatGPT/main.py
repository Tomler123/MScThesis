from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import DefaultDict


class SearchIndex:
    """An in-memory inverted index for full-text search over documents.

    Documents are tokenized by splitting on non-alphanumeric characters and
    lowercasing all tokens. Search uses AND semantics: a document matches only
    if it contains every query term.
    """

    def __init__(self) -> None:
        """Initialize an empty search index."""
        self._docs: dict[str, Counter[str]] = {}
        self._index: DefaultDict[str, dict[str, int]] = defaultdict(dict)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Split text into lowercase alphanumeric tokens."""
        return re.findall(r"[A-Za-z0-9]+", text.lower())

    def add(self, doc_id: str, text: str) -> None:
        """Index a document, replacing any previously indexed content.

        Args:
            doc_id: Unique document identifier.
            text: Document text to index.
        """
        self.remove(doc_id)

        term_counts = Counter(self._tokenize(text))
        self._docs[doc_id] = term_counts

        for term, count in term_counts.items():
            self._index[term][doc_id] = count

    def search(self, query: str) -> list[str]:
        """Return matching document IDs ranked by relevance.

        A document matches only if it contains all query terms. Results are
        sorted by:
        1. total occurrences of all query terms in the document, descending
        2. doc_id ascending for ties

        Args:
            query: Search query string.

        Returns:
            A list of matching document IDs in ranked order.
        """
        query_terms = set(self._tokenize(query))
        if not query_terms:
            return []

        postings_lists: list[dict[str, int]] = []
        for term in query_terms:
            postings = self._index.get(term)
            if not postings:
                return []
            postings_lists.append(postings)

        matching_docs = set(postings_lists[0].keys())
        for postings in postings_lists[1:]:
            matching_docs &= postings.keys()

        ranked = sorted(
            matching_docs,
            key=lambda doc_id: (
                -sum(self._docs[doc_id][term] for term in query_terms),
                doc_id,
            ),
        )
        return ranked

    def remove(self, doc_id: str) -> None:
        """Remove a document from the index.

        If the document is not present, this method does nothing.

        Args:
            doc_id: Document identifier to remove.
        """
        term_counts = self._docs.pop(doc_id, None)
        if term_counts is None:
            return

        for term in term_counts:
            postings = self._index[term]
            postings.pop(doc_id, None)
            if not postings:
                del self._index[term]