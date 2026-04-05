import re
from collections import defaultdict


class SearchIndex:
    """An in-memory inverted index for full-text search over documents."""
    
    def __init__(self) -> None:
        """Initialize an empty search index."""
        # Inverted index: term -> {doc_id: frequency}
        self._index: dict[str, dict[str, int]] = defaultdict(dict)
        # Document store: doc_id -> original text
        self._docs: dict[str, str] = {}
    
    def _tokenize(self, text: str) -> list[str]:
        """Split text on non-alphanumeric characters and convert to lowercase.
        
        Args:
            text: The input text to tokenize.
            
        Returns:
            A list of lowercase alphanumeric tokens.
        """
        return [token.lower() for token in re.split(r'[^a-zA-Z0-9]+', text) if token]
    
    def add(self, doc_id: str, text: str) -> None:
        """Index a document. If the same doc_id is added again, replace the previous content.
        
        Args:
            doc_id: Unique identifier for the document.
            text: The document content to index.
        """
        # Remove old content if doc_id already exists
        if doc_id in self._docs:
            self.remove(doc_id)
        
        # Store the document
        self._docs[doc_id] = text
        
        # Tokenize and count term frequencies
        tokens = self._tokenize(text)
        term_counts: dict[str, int] = {}
        for token in tokens:
            term_counts[token] = term_counts.get(token, 0) + 1
        
        # Update inverted index
        for term, count in term_counts.items():
            self._index[term][doc_id] = count
    
    def search(self, query: str) -> list[str]:
        """Return doc_ids of documents containing all query terms (AND logic).
        
        Results are sorted by relevance (total query term occurrences, descending),
        with ties broken by doc_id ascending (lexicographic).
        
        Args:
            query: The search query string.
            
        Returns:
            A list of matching doc_ids, sorted by relevance.
        """
        terms = self._tokenize(query)
        
        if not terms:
            return []
        
        # Find documents containing all terms (AND logic)
        doc_sets: list[set[str]] = []
        for term in terms:
            if term in self._index:
                doc_sets.append(set(self._index[term].keys()))
            else:
                # Term not found anywhere, no docs can match
                return []
        
        # Intersect all doc sets
        if not doc_sets:
            return []
        
        common_docs = doc_sets[0]
        for doc_set in doc_sets[1:]:
            common_docs = common_docs & doc_set
        
        if not common_docs:
            return []
        
        # Calculate relevance score for each matching doc
        # Score = total occurrences of all query terms in the document
        scored_docs: list[tuple[str, int]] = []
        for doc_id in common_docs:
            score = sum(self._index[term].get(doc_id, 0) for term in terms)
            scored_docs.append((doc_id, score))
        
        # Sort by score descending, then doc_id ascending
        scored_docs.sort(key=lambda x: (-x[1], x[0]))
        
        return [doc_id for doc_id, _ in scored_docs]
    
    def remove(self, doc_id: str) -> None:
        """Remove a document from the index. If not found, do nothing.
        
        Args:
            doc_id: The identifier of the document to remove.
        """
        if doc_id not in self._docs:
            return
        
        text = self._docs[doc_id]
        tokens = self._tokenize(text)
        
        # Remove doc_id from index for each unique term
        for token in set(tokens):
            if token in self._index and doc_id in self._index[token]:
                del self._index[token][doc_id]
                # Clean up empty index entries
                if not self._index[token]:
                    del self._index[token]
        
        # Remove from document store
        del self._docs[doc_id]