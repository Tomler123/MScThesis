import re
from collections import Counter, defaultdict

class SearchIndex:
    """An in-memory inverted index for full-text search over documents."""

    def __init__(self) -> None:
        # Inverted index: maps a term to a dictionary of {doc_id: frequency}
        self.inverted_index: defaultdict[str, dict[str, int]] = defaultdict(dict)
        
        # Document store: maps a doc_id to its term frequencies
        # Used primarily to enable efficient document replacement and removal
        self.doc_store: dict[str, Counter[str]] = {}

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text by splitting on non-alphanumeric characters 
        and lowercasing all tokens.
        """
        return re.findall(r'[a-z0-9]+', text.lower())

    def add(self, doc_id: str, text: str) -> None:
        """
        Index a document. If the same doc_id is added again, 
        replace the previous content.
        
        Args:
            doc_id: A unique identifier for the document.
            text: The full-text content of the document.
        """
        # If the document already exists, remove it first to handle replacements cleanly
        if doc_id in self.doc_store:
            self.remove(doc_id)
            
        tokens = self._tokenize(text)
        term_freqs = Counter(tokens)
        
        # Save the document's term frequencies for future removal/updates
        self.doc_store[doc_id] = term_freqs
        
        # Populate the inverted index
        for term, freq in term_freqs.items():
            self.inverted_index[term][doc_id] = freq

    def search(self, query: str) -> list[str]:
        """
        Search for documents containing all query terms (AND logic).
        
        Args:
            query: The search string.
            
        Returns:
            A list of doc_ids sorted by relevance (descending) and then 
            lexicographically by doc_id (ascending).
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
            
        unique_query_terms = set(query_tokens)
        
        # Optimization: start with the term that exists in the index to fail fast
        first_term = query_tokens[0]
        if first_term not in self.inverted_index:
            return []
            
        # Get the initial set of documents matching the first term
        matching_docs = set(self.inverted_index[first_term].keys())
        
        # Intersect with doc sets of all other query terms (AND logic)
        for term in unique_query_terms:
            if term not in self.inverted_index:
                return []
            matching_docs.intersection_update(self.inverted_index[term].keys())
            
            # If at any point the intersection is empty, no docs contain all terms
            if not matching_docs:
                break
                
        # Calculate relevance scores
        doc_scores: list[tuple[int, str]] = []
        for doc_id in matching_docs:
            # Relevance = total occurrences of the unique query terms in the doc
            score = sum(self.inverted_index[term][doc_id] for term in unique_query_terms)
            doc_scores.append((score, doc_id))
            
        # Sort: Primary key is score descending (-score), secondary is doc_id ascending
        doc_scores.sort(key=lambda x: (-x[0], x[1]))
        
        return [doc_id for score, doc_id in doc_scores]

    def remove(self, doc_id: str) -> None:
        """
        Remove a document from the index. If not found, do nothing.
        
        Args:
            doc_id: The unique identifier of the document to remove.
        """
        if doc_id not in self.doc_store:
            return
            
        term_freqs = self.doc_store[doc_id]
        
        # Remove the document references from the inverted index
        for term in term_freqs:
            del self.inverted_index[term][doc_id]
            # Clean up the term entirely if no documents contain it anymore
            if not self.inverted_index[term]:
                del self.inverted_index[term]
                
        # Finally, remove it from the document store
        del self.doc_store[doc_id]

# ==========================================
# Test Cases 
# ==========================================
if __name__ == "__main__":
    idx = SearchIndex()
    idx.add("d1", "The quick brown fox jumps over the lazy dog")
    idx.add("d2", "The quick brown cat")
    idx.add("d3", "Fox fox fox")

    assert idx.search("fox") == ["d3", "d1"]
    assert idx.search("quick brown") == ["d1", "d2"]
    assert idx.search("elephant") == []
    assert idx.search("fox cat") == []
    assert idx.search("") == []
    assert idx.search("   ") == []
    assert idx.search("THE QUICK") == ["d1", "d2"]

    idx.add("d1", "New content entirely")
    assert idx.search("fox") == ["d3"]
    assert idx.search("entirely") == ["d1"]

    idx.remove("d3")
    assert idx.search("fox") == []
    idx.remove("d99")  

    idx2 = SearchIndex()
    idx2.add("a", "python python python java")
    idx2.add("b", "python java java java")
    assert idx2.search("python java") == ["a", "b"]

    idx2.add("c", "python python java java java")
    assert idx2.search("python java") == ["c", "a", "b"]

    idx3 = SearchIndex()
    idx3.add("x", "hello-world! foo_bar123 baz")
    assert idx3.search("hello") == ["x"]
    assert idx3.search("world") == ["x"]
    assert idx3.search("bar123") == ["x"]
    
    print("All tests passed!")