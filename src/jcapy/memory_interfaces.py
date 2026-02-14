# SPDX-License-Identifier: Apache-2.0
from typing import List, Dict, Any, Protocol

class MemoryInterface(Protocol):
    """
    Protocol for JCapy Memory Banks (Local or Remote).
    """
    def memorize(self, paths: List[str], clear_first: bool = False) -> Dict[str, int]:
        """Ingest content from paths."""
        ...

    def recall(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant content."""
        ...

    def clear(self) -> bool:
        """Clear all memory."""
        ...
