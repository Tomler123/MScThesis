import re
from collections import defaultdict


class SearchIndex:
    """An in-memory inverted index for full-text search over documents."""

    def __init__(self) -> None:
        # Maps token -> {doc_id -> frequency}
        self._index: dict[str, dict[str, int]] = defaultdict(dict)
        # Maps doc_id -> list of tokens (with repetition, for re-indexing on replace)
        self._docs: dict[str, list[str]] = {}

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Split text on non-alphanumeric characters and lowercase all tokens.

        Empty strings produced by the split are discarded.
        """
        return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]

    def add(self, doc_id: str, text: str) -> None:
        """Index a document.

        If a document with the same doc_id already exists, its previous
        content is removed before the new content is indexed.

        Args:
            doc_id: Unique identifier for the document.
            text:   Raw text content of the document.
        """
        if doc_id in self._docs:
            self.remove(doc_id)

        tokens = self._tokenize(text)
        self._docs[doc_id] = tokens

        freq: dict[str, int] = defaultdict(int)
        for token in tokens:
            freq[token] += 1

        for token, count in freq.items():
            self._index[token][doc_id] = count

    def search(self, query: str) -> list[str]:
        """Return doc_ids of documents containing all query terms (AND logic).

        Results are sorted by the total number of query-term occurrences in
        the document (descending). Ties are broken by doc_id lexicographically
        (ascending).

        Args:
            query: Raw query string; tokenized the same way as documents.

        Returns:
            Ordered list of matching doc_ids, or an empty list if no query
            terms are found or no document matches all terms.
        """
        terms = self._tokenize(query)
        if not terms:
            return []

        candidate_sets = [set(self._index.get(t, {}).keys()) for t in terms]
        matching_ids = candidate_sets[0]
        for s in candidate_sets[1:]:
            matching_ids = matching_ids & s

        if not matching_ids:
            return []

        def score(doc_id: str) -> tuple[int, str]:
            total = sum(self._index[t].get(doc_id, 0) for t in terms)
            return (-total, doc_id)  # negate so higher scores sort first

        return sorted(matching_ids, key=score)

    def remove(self, doc_id: str) -> None:
        """Remove a document from the index.

        Does nothing if doc_id is not present.

        Args:
            doc_id: Identifier of the document to remove.
        """
        if doc_id not in self._docs:
            return

        tokens = self._docs.pop(doc_id)
        seen = set(tokens)
        for token in seen:
            self._index[token].pop(doc_id, None)
            if not self._index[token]:
                del self._index[token]