# SPDX-License-Identifier: Apache-2.0
import os
import time
import hashlib
from typing import List, Dict, Any, Optional
from rich.console import Console
from jcapy.memory_interfaces import MemoryInterface

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

console = Console()

class RemoteMemoryBank(MemoryInterface):
    """
    Pro Tier: Remote memory implementation using Pinecone with built-in Inference.
    """
    def __init__(self):
        if not Pinecone:
            console.print("[red]Error: 'pinecone' package not installed.[/red]")
            self.active = False
            return

        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX", "jcapy")
        self.model_name = os.getenv("PINECONE_MODEL", "llama-text-embed-v2")

        if not self.api_key:
             console.print("[yellow]Warning: PINECONE_API_KEY not set. Remote memory disabled.[/yellow]")
             self.active = False
             return

        try:
            self.pc = Pinecone(api_key=self.api_key)
            self.index = self.pc.Index(self.index_name)
            self.active = True
            console.print(f"[dim]☁️  Remote Memory Active: [bold]{self.index_name}[/bold] using {self.model_name}[/dim]")
        except Exception as e:
             console.print(f"[red]Error initializing Remote Memory: {e}[/red]")
             self.active = False

    def memorize(self, paths: List[str], clear_first: bool = False) -> Dict[str, int]:
        """
        Upserts content from files to Pinecone after chunking and embedding.
        """
        if not self.active:
            console.print("[red]Remote memory not active. Check API Key and dependencies.[/red]")
            return {"added": 0, "errors": 1, "skipped": 0}

        if clear_first:
            console.print("[yellow]Warning: Remote 'clear_first' not supported via CLI for safety.[/yellow]")

        stats = {"added": 0, "errors": 0, "skipped": 0}

        for path in paths:
             if os.path.isfile(path):
                 self._ingest_file(path, stats)
             elif os.path.isdir(path):
                 console.print(f"[dim]Scanning directory: {path}[/dim]")
                 for root, _, files in os.walk(path):
                     for file in files:
                         if file.lower().endswith(('.md', '.txt', '.py', '.json', '.yaml', '.yml')):
                             self._ingest_file(os.path.join(root, file), stats)

        return stats

    def _ingest_file(self, file_path: str, stats: Dict[str, int]):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                stats["skipped"] += 1
                return

            # Simple Chunking (2000 chars)
            chunks = self._chunk_text(content)

            # Generate Embeddings in batch
            try:
                # Pinecone Inference handles batching well, but we'll still rescue it
                embeddings_response = self.pc.inference.embed(
                    model=self.model_name,
                    inputs=chunks,
                    parameters={"input_type": "passage"}
                )
            except Exception as e:
                console.print(f"[red]Inference error for {file_path}: {e}[/red]")
                stats["errors"] += 1
                return

            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_response)):
                chunk_id = hashlib.md5(f"{file_path}_{i}".encode()).hexdigest()

                vectors.append({
                    "id": chunk_id,
                    "values": embedding.values,
                    "metadata": {
                        "path": file_path,
                        "filename": os.path.basename(file_path),
                        "chunk_index": i,
                        "content": chunk[:2000] # Pinecone metadata limit check
                    }
                })

            # Upsert in batches of 50 (Safer for Free Tier write units)
            for i in range(0, len(vectors), 50):
                batch = vectors[i:i + 50]
                self._upsert_with_retry(batch)

            console.print(f"[green]☁️  [Remote] Indexed:[/green] {os.path.basename(file_path)} ({len(chunks)} chunks)")
            stats["added"] += 1

        except Exception as e:
             console.print(f"[red]Error indexing {file_path}: {e}[/red]")
             stats["errors"] += 1

    def _upsert_with_retry(self, vectors, max_retries=3):
        """Helper to handle rate limits with exponential backoff."""
        for attempt in range(max_retries):
            try:
                self.index.upsert(vectors=vectors)
                return
            except Exception as e:
                if "429" in str(e) or "limit" in str(e).lower():
                    wait = (2 ** attempt) + 1
                    console.print(f"[yellow]⚠️  Rate limit reached. Retrying in {wait}s...[/yellow]")
                    time.sleep(wait)
                else:
                    raise e
        console.print("[red]❌ Failed to upsert after multiple retries.[/red]")

    def _chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """Simple sliding window chunking."""
        chunks = []
        if len(text) <= chunk_size:
            return [text]

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks

    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries the cloud index."""
        if not self.active:
             return []

        try:
            # Embed query
            query_embedding = self.pc.inference.embed(
                model=self.model_name,
                inputs=[query],
                parameters={"input_type": "query"}
            )[0]

            # Query Pinecone
            response = self.index.query(
                vector=query_embedding.values,
                top_k=n_results,
                include_metadata=True
            )

            hits = []
            for match in response['matches']:
                hits.append({
                    "id": match['id'],
                    "distance": 1.0 - match['score'], # Convert score to distance-like for JCapy UI
                    "metadata": match['metadata'],
                    "content": match['metadata'].get('content', '')
                })
            return hits
        except Exception as e:
            console.print(f"[red]Remote recall error: {e}[/red]")
            return []

    def clear(self) -> bool:
        """Dangerous operation, disabled by default."""
        console.print("[red]Remote memory cannot be cleared via CLI for safety.[/red]")
        return False
