import os
import time
import hashlib
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from jcapy.config import get_active_library_path

class MemoryBank:
    """
    The Long-Term Memory of JCapy.
    Uses ChromaDB to store and retrieve skills based on semantic meaning.
    """
    def __init__(self, persistence_path=None):
        if not persistence_path:
            # Default to ~/.jcapy/memory
            home = os.path.expanduser("~/.jcapy")
            persistence_path = os.path.join(home, "memory_db")

        if not os.path.exists(persistence_path):
            os.makedirs(persistence_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persistence_path)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="jcapy_skills",
            metadata={"hnsw:space": "cosine"}
        )

    def add_skill(self, name: str, content: str, source_path: str):
        """Adds or updates a skill in the memory bank."""
        # Create a unique ID based on the file path
        doc_id = hashlib.md5(source_path.encode()).hexdigest()

        # Upsert (Update or Insert)
        self.collection.upsert(
            documents=[content],
            metadatas=[{"name": name, "source": source_path, "type": "skill"}],
            ids=[doc_id]
        )

    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Semantically searches for skills.
        Returns a list of dicts with 'name', 'source', 'distance', and 'content'.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Simplify result structure
        hits = []
        if not results['ids']: return hits

        for i in range(len(results['ids'][0])):
            hits.append({
                "id": results['ids'][0][i],
                "distance": results['distances'][0][i],
                "metadata": results['metadatas'][0][i],
                "content": results['documents'][0][i]
            })

        return hits

    def sync_library(self, library_path: str):
        """
        Scans all .md files in the library and indexes them.
        This allows 'jcapy recall' to work on the current knowledge base.
        """
        print(f"🧠 Syncing Memory Bank from {library_path}...")
        count = 0
        for root, dirs, files in os.walk(library_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        self.add_skill(
                            name=file,
                            content=content,
                            source_path=full_path
                        )
                        count += 1
                        # print(f"  • Memorized: {file}")
                    except Exception as e:
                        print(f"  ⚠️ Error reading {file}: {e}")

        print(f"✨ Memory Sync Complete. {count} skills indexed.")

def get_memory_bank():
    """Singleton-like accessor"""
    return MemoryBank()
