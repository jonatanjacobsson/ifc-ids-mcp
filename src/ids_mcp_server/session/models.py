"""Session data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionMetadata(BaseModel):
    """Metadata about a session."""

    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    ids_title: Optional[str] = None


class SessionData:
    """
    Complete session data including IDS object.

    Note: We don't use Pydantic here because ids.Ids is from IfcTester
    and we want to store it directly without wrapping.
    """

    def __init__(self, session_id: str):
        """
        Initialize session data.

        Args:
            session_id: Unique session identifier
        """
        self.metadata = SessionMetadata(session_id=session_id)
        self.ids_obj = None  # Will be ifctester.ids.Ids object

    def update_last_accessed(self) -> None:
        """Update last accessed timestamp."""
        self.metadata.last_accessed = datetime.now()

    def set_ids_title(self, title: str) -> None:
        """Update IDS title in metadata."""
        self.metadata.ids_title = title
