# SPDX-License-Identifier: Apache-2.0
import os
import logging
import hashlib
from typing import List, Dict, Any, Optional

from rich.console import Console
from jcapy.memory_interfaces import MemoryInterface
from jcapy.core.vault import resolve_secret

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

console = Console()
logger = logging.getLogger('jcapy.memory.chroma_cloud')

class ChromaCloudMemoryBank(MemoryInterface):
    """
    Managed Memory Tier: Remote implementation using ChromaDB Cloud.
    """
    def __init__(self):
        if not chromadb:
            console.print("[red]Error: 'chromadb' package not installed.[/red]")
            self.active = False
            return

        self.api_key = resolve_secret("CHROMA_CLOUD_API_KEY")
        self.tenant = resolve_secret("CHROMA_CLOUD_TENANT")
        self.database = resolve_secret("CHROMA_CLOUD_DATABASE", "jcapy")

        if not self.api_key or not self.tenant:
            console.print("[yellow]Warning: ChromaDB Cloud credentials not set. Cloud memory disabled.[/yellow]")
            self.active = False
            return

        try:
            # Note: chromadb.CloudClient is the specialized client for Chroma Cloud
            self.client = chromadb.CloudClient(
                api_key=self.api_key,
                tenant=self.tenant,
                database=self.database
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="jcapy_knowledge",
                metadata={"hnsw:space": "cosine"}
            )

            self.active = True
            console.print(f"[dim]☁️  Chroma Cloud Active: Tenant [bold]{self.tenant}[/bold], DB [bold]{self.database}[/bold][/dim]")
        except Exception as e:
            console.print(f"[red]Error initializing Chroma Cloud: {e}[/red]")
            self.active = False

    def memorize(self, paths: List[str], clear_first: bool = False) -> Dict[str, int]:
        """
        Ingests content from paths and stores in Chroma Cloud.
        """
        if not self.active:
            return {"added": 0, "errors": 1, "skipped": 0}

        if clear_first:
            console.print("🧹 [Cloud] Clearing collection...")
            self.clear()

        stats = {"added": 0, "errors": 0, "skipped": 0}

        for path in paths:
            if os.path.isfile(path):
                self._ingest_file(path, stats)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.md', '.txt', '.py', '.sh', '.json', '.yaml', '.yml')):
                            self._ingest_file(os.path.join(root, file), stats)

        return stats

    def _ingest_file(self, file_path: str, stats: Dict[str, int]):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                stats["skipped"] += 1
                return

            # Extract basic metadata
            doc_id = hashlib.md5(file_path.encode()).hexdigest()
            filename = os.path.basename(file_path)

            metadata = {
                "source": file_path,
                "filename": filename,
                "type": os.path.splitext(filename)[1].replace(".", "") or "text"
            }

            self.collection.upsert(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )

            console.print(f"[green]☁️  [Chroma Cloud] Indexed:[/green] {filename}")
            stats["added"] += 1

        except Exception as e:
            console.print(f"[red]Error indexing {file_path}: {e}[/red]")
            stats["errors"] += 1

    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries the cloud collection."""
        if not self.active or not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

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
        except Exception as e:
            console.print(f"[red]Chroma Cloud recall error: {e}[/red]")
            return []

    def clear(self) -> bool:
        """Clears the collection."""
        if not self.active: return False
        try:
            # For cloud, we might want to just delete items and keep collection configuration
            # but simple delete/create works too
            self.client.delete_collection("jcapy_knowledge")
            self.collection = self.client.get_or_create_collection(
                name="jcapy_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            console.print(f"[red]Error clearing Chroma Cloud: {e}[/red]")
            return False
