import os
import time
import hashlib
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from jcapy.config import get_active_library_path

class MemoryBank:
    """
    The Long-Term Memory of JCapy.
    Uses ChromaDB to store and retrieve skills/docs based on semantic meaning.
    """
    def __init__(self, persistence_path=None):
        if not persistence_path:
            # Default to ~/.jcapy/memory_db
            home = os.path.expanduser("~/.jcapy")
            persistence_path = os.path.join(home, "memory_db")

        if not os.path.exists(persistence_path):
            os.makedirs(persistence_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persistence_path)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="jcapy_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

    def add_document(self, content: str, source_path: str, metadata: Dict[str, Any] = None):
        """Adds or updates a document in the memory bank."""
        # Create a unique ID based on the file path
        doc_id = hashlib.md5(source_path.encode()).hexdigest()

        if metadata is None:
            metadata = {}

        # Ensure source is always in metadata
        metadata["source"] = source_path

        # Upsert (Update or Insert)
        self.collection.upsert(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Semantically searches for knowledge.
        Returns a list of dicts with 'metadata', 'distance', 'content'.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
        except Exception:
             # Likely empty collection or index error
             return []

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

    def clear(self):
        """Wipes the entire memory bank."""
        try:
            self.client.delete_collection("jcapy_knowledge")
            self.collection = self.client.get_or_create_collection(
                name="jcapy_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False

    def memorize(self, paths: List[str], clear_first: bool = False) -> Dict[str, int]:
        """
        Ingests content from list of paths (files or directories).
        """
        stats = {"added": 0, "errors": 0, "skipped": 0}

        if clear_first:
            print("🧹 Clearing existing memory...")
            self.clear()

        for path in paths:
            if os.path.isfile(path):
                self._ingest_file(path, stats)
            elif os.path.isdir(path):
                self._scan_directory(path, stats)
            else:
                print(f"⚠️ Path not found: {path}")
                stats["skipped"] += 1

        return stats

    def _scan_directory(self, directory: str, stats: Dict[str, int]):
        """Recursively scans a directory for valid files."""
        # Ignore list
        IGNORE_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', '.idea', '.vscode'}
        VALID_EXTS = {'.md', '.txt', '.py', '.sh', '.json', '.yaml', '.yml'}

        for root, dirs, files in os.walk(directory):
            # Prune ignored dirs
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in VALID_EXTS:
                    full_path = os.path.join(root, file)
                    self._ingest_file(full_path, stats)

    def _ingest_file(self, file_path: str, stats: Dict[str, int]):
        """Reads, extracts metadata, and stores a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                stats["skipped"] += 1
                return

            # Extract basic metadata
            meta = self._extract_metadata(file_path, content)

            self.add_document(content, file_path, meta)
            stats["added"] += 1
            # Optional: Print verbose?
            # print(f"  • Memorized: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"  ❌ Error reading {file_path}: {e}")
            stats["errors"] += 1

    def _extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extracts useful metadata from file content/stats."""
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        meta = {
            "name": filename,
            "type": ext.replace(".", ""),
            "path": file_path,
            "size": len(content)
        }

        # Heuristic: Try to find title in Markdown
        if ext == ".md":
            for line in content.split('\n')[:5]:
                if line.strip().startswith('# '):
                    meta["title"] = line.strip().replace('# ', '').strip()
                    break

        # Fallback title
        if "title" not in meta:
             meta["title"] = filename

        return meta

    # Legacy alias for backward compatibility until refactor complete
    def sync_library(self, library_path: str):
        print(f"🧠 Syncing Memory Bank from {library_path}...")
        results = self.memorize([library_path], clear_first=False)
        print(f"✨ Memory Sync Complete. {results['added']} items indexed.")

def get_memory_bank():
    """Singleton-like accessor"""
    return MemoryBank()

