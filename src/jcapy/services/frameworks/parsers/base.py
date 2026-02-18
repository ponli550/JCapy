from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseParser(ABC):
    """Abstract base class for all metadata parsers."""

    @abstractmethod
    def can_handle(self, doc_path: str, content: str) -> bool:
        """Check if this parser can handle the given content."""
        pass

    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        """Extract metadata from the content."""
        pass
