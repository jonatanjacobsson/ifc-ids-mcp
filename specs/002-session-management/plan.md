# Implementation Plan: Session Management with FastMCP Context

**Branch**: `claude/002-session-management` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Implement session-based state management using FastMCP Context for automatic session identification and lifecycle management. This feature enables stateful conversations where IDS documents persist across multiple tool calls within the same session, with automatic cleanup of abandoned sessions.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - Provides Context object with session_id
- `ifctester` - IDS document objects stored in sessions
- `pydantic` - Session metadata validation
- `asyncio` - Background cleanup tasks

**Storage**: In-memory dictionary keyed by session_id (development)
**Testing**: pytest with async support
**Target Platform**: Cross-platform Python
**Project Type**: Single project
**Performance Goals**:
- Session lookup <1ms
- Cleanup task runs every hour
- Support 1000+ concurrent sessions

**Constraints**:
- Must not leak memory from abandoned sessions
- Thread-safe session access
- Automatic session ID from FastMCP Context

**Scale/Scope**:
- Support unlimited sessions (limited by memory)
- Each session can have 1 IDS document
- Automatic cleanup after 24-hour inactivity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Required Checks:**

- ✅ FastMCP Context supports session_id attribute
- ✅ Context object is automatically injected into tools
- ✅ Session storage is thread-safe
- ✅ No manual session ID parameters required
- ✅ Cleanup mechanism prevents memory leaks

**Post-Design Checks:**

- ✅ All tools receive Context automatically
- ✅ Session state persists across tool calls
- ✅ Abandoned sessions are cleaned up

## Project Structure

### Documentation (this feature)

```text
specs/002-session-management/
├── plan.md              # This file
├── research.md          # FastMCP Context research
├── data-model.md        # Session data models
├── quickstart.md        # Session usage guide
├── contracts/           # Session management contracts
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
src/ids_mcp_server/
├── session/
│   ├── __init__.py
│   ├── manager.py           # Session lifecycle management
│   ├── storage.py           # In-memory session storage
│   ├── cleanup.py           # Background cleanup task
│   └── models.py            # Session metadata models

tests/
├── unit/
│   └── session/
│       ├── test_storage.py
│       ├── test_manager.py
│       └── test_cleanup.py
├── component/
│   └── test_session_lifecycle.py
└── integration/
    └── test_session_context.py
```

**Structure Decision**: Created `session/` module to encapsulate all session-related functionality. Manager provides high-level API, storage handles data persistence, cleanup manages lifecycle.

## Complexity Tracking

> **No violations - standard session management pattern**

---

## Phase 0: Research

**Objectives:**
1. Verify FastMCP Context.session_id behavior
2. Test Context injection into tools
3. Research Context lifecycle (request vs session scoped)
4. Identify thread-safety requirements
5. Research asyncio background tasks for cleanup

**Research Questions:**
- How does FastMCP generate session_ids?
- Is Context.session_id stable across multiple tool calls?
- Can we access Context.session_id from multiple tools in the same session?
- What happens to Context when session ends?
- How to implement background cleanup without blocking server?

**Deliverable**: `research.md` with Context behavior findings

---

## Phase 1: Design

**Objectives:**
1. Design session storage schema
2. Define session lifecycle (create, access, cleanup)
3. Design Context integration patterns
4. Define cleanup strategy
5. Create session metadata models

**Design Artifacts:**

### 1. Session Data Models (`data-model.md`)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ifctester import ids

class SessionMetadata(BaseModel):
    """Metadata about a session."""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    ids_title: Optional[str] = None  # Title of current IDS

class SessionData:
    """Complete session data including IDS object."""
    metadata: SessionMetadata
    ids_obj: Optional[ids.Ids]  # The actual IDS document

    def __init__(self, session_id: str):
        self.metadata = SessionMetadata(session_id=session_id)
        self.ids_obj = None

    def update_last_accessed(self):
        """Update last accessed timestamp."""
        self.metadata.last_accessed = datetime.now()
```

### 2. Session Manager Contract (`contracts/session_manager.md`)

```python
from fastmcp import Context
from ifctester import ids

async def get_or_create_session(ctx: Context) -> ids.Ids:
    """
    Get existing IDS for session or create new one.

    Args:
        ctx: FastMCP Context with session_id

    Returns:
        IDS object for this session

    Contract:
        - MUST use ctx.session_id for identification
        - MUST create new session if not exists
        - MUST update last_accessed timestamp
        - MUST log session access via ctx.info()
    """

async def create_session_from_file(ctx: Context, filepath: str) -> ids.Ids:
    """
    Load IDS from file and store in session.

    Args:
        ctx: FastMCP Context
        filepath: Path to IDS XML file

    Returns:
        Loaded IDS object

    Contract:
        - MUST replace existing session IDS if any
        - MUST use ids.open() from IfcTester
        - MUST validate file exists
        - MUST handle file read errors
    """

async def create_session_from_string(ctx: Context, xml_string: str) -> ids.Ids:
    """
    Load IDS from XML string and store in session.

    Args:
        ctx: FastMCP Context
        xml_string: IDS XML content

    Returns:
        Loaded IDS object

    Contract:
        - MUST replace existing session IDS if any
        - MUST use ids.from_string() from IfcTester
        - MUST validate XML is well-formed
    """

def cleanup_session(session_id: str) -> None:
    """
    Remove session data.

    Args:
        session_id: Session to remove

    Contract:
        - MUST be safe to call on non-existent session
        - MUST free all session resources
    """
```

### 3. Session Storage Contract (`contracts/storage.md`)

```python
# Thread-safe session storage

from typing import Dict, Optional
import threading

class SessionStorage:
    """
    Thread-safe in-memory session storage.

    Contract:
        - MUST be thread-safe for concurrent access
        - MUST support get/set/delete operations
        - MUST track metadata automatically
    """

    def __init__(self):
        self._storage: Dict[str, SessionData] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Optional[SessionData]:
        """Get session data (thread-safe)."""
        ...

    def set(self, session_id: str, data: SessionData) -> None:
        """Set session data (thread-safe)."""
        ...

    def delete(self, session_id: str) -> None:
        """Delete session (thread-safe)."""
        ...

    def get_all_session_ids(self) -> list[str]:
        """Get all active session IDs."""
        ...
```

**Deliverables**:
- `data-model.md` - Session schemas
- `contracts/` - API contracts
- `quickstart.md` - Usage examples

---

## Phase 2: Test-Driven Implementation

**TDD Workflow**: Red → Green → Refactor for each feature

### Milestone 1: Session Storage

**RED: Write failing tests**

```python
# tests/unit/session/test_storage.py
import pytest
from ids_mcp_server.session.storage import SessionStorage
from ids_mcp_server.session.models import SessionData

def test_storage_initialization():
    """Test creating empty storage."""
    storage = SessionStorage()
    assert storage is not None
    assert storage.get_all_session_ids() == []

def test_storage_set_and_get():
    """Test storing and retrieving session data."""
    storage = SessionStorage()
    session_data = SessionData(session_id="test-123")

    storage.set("test-123", session_data)
    retrieved = storage.get("test-123")

    assert retrieved is not None
    assert retrieved.metadata.session_id == "test-123"

def test_storage_thread_safety():
    """Test concurrent access to storage."""
    import threading

    storage = SessionStorage()
    errors = []

    def create_session(sid):
        try:
            data = SessionData(session_id=sid)
            storage.set(sid, data)
        except Exception as e:
            errors.append(e)

    # Create 100 sessions concurrently
    threads = [
        threading.Thread(target=create_session, args=(f"session-{i}",))
        for i in range(100)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(storage.get_all_session_ids()) == 100
```

**GREEN: Implementation**
1. Create `storage.py` with `SessionStorage` class
2. Implement thread-safe get/set/delete
3. Run tests → PASS

### Milestone 2: Session Manager with Context Integration

**RED: Write failing tests**

```python
# tests/component/test_session_lifecycle.py
import pytest
from fastmcp import Context
from ifctester import ids
from ids_mcp_server.session.manager import (
    get_or_create_session,
    create_session_from_string
)

@pytest.mark.asyncio
async def test_get_or_create_session_new():
    """Test creating new session via Context."""
    # Create mock context with session_id
    ctx = MockContext(session_id="test-session-1")

    ids_obj = await get_or_create_session(ctx)

    assert ids_obj is not None
    assert isinstance(ids_obj, ids.Ids)

@pytest.mark.asyncio
async def test_get_or_create_session_existing():
    """Test retrieving existing session."""
    ctx = MockContext(session_id="test-session-2")

    # First call creates
    ids_obj1 = await get_or_create_session(ctx)
    ids_obj1.info["title"] = "Test IDS"

    # Second call retrieves same object
    ids_obj2 = await get_or_create_session(ctx)

    assert ids_obj2.info["title"] == "Test IDS"
    assert ids_obj1 is ids_obj2  # Same object reference

@pytest.mark.asyncio
async def test_create_session_from_string():
    """Test loading IDS from XML string."""
    ctx = MockContext(session_id="test-session-3")

    xml_string = """<?xml version="1.0" encoding="UTF-8"?>
    <ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS">
        <ids:info>
            <ids:title>Test IDS</ids:title>
        </ids:info>
        <ids:specifications></ids:specifications>
    </ids:ids>"""

    ids_obj = await create_session_from_string(ctx, xml_string)

    assert ids_obj.info["title"] == "Test IDS"

    # Verify it's stored in session
    ids_obj2 = await get_or_create_session(ctx)
    assert ids_obj2.info["title"] == "Test IDS"
```

**GREEN: Implementation**
1. Create `manager.py` with session functions
2. Integrate with Context
3. Use IfcTester for IDS operations
4. Run tests → PASS

### Milestone 3: Background Cleanup Task

**RED: Write failing tests**

```python
# tests/unit/session/test_cleanup.py
import pytest
import asyncio
from datetime import datetime, timedelta
from ids_mcp_server.session.cleanup import (
    cleanup_abandoned_sessions,
    start_cleanup_task
)
from ids_mcp_server.session.storage import SessionStorage
from ids_mcp_server.session.models import SessionData

@pytest.mark.asyncio
async def test_cleanup_old_sessions():
    """Test that old sessions are removed."""
    storage = SessionStorage()

    # Create old session (25 hours old)
    old_session = SessionData(session_id="old-session")
    old_session.metadata.last_accessed = datetime.now() - timedelta(hours=25)
    storage.set("old-session", old_session)

    # Create recent session (1 hour old)
    recent_session = SessionData(session_id="recent-session")
    recent_session.metadata.last_accessed = datetime.now() - timedelta(hours=1)
    storage.set("recent-session", recent_session)

    # Run cleanup (24 hour timeout)
    cleanup_abandoned_sessions(storage, timeout_hours=24)

    # Old session removed, recent session kept
    assert storage.get("old-session") is None
    assert storage.get("recent-session") is not None

@pytest.mark.asyncio
async def test_cleanup_task_runs_periodically():
    """Test that cleanup task runs in background."""
    storage = SessionStorage()
    cleanup_count = []

    async def mock_cleanup():
        cleanup_count.append(1)

    # Start task with 1-second interval
    task = asyncio.create_task(
        start_cleanup_task(storage, interval_seconds=1)
    )

    # Wait 2.5 seconds
    await asyncio.sleep(2.5)

    # Cancel task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Should have run at least 2 times
    assert len(cleanup_count) >= 2
```

**GREEN: Implementation**
1. Create `cleanup.py` with cleanup functions
2. Implement background asyncio task
3. Run tests → PASS

**REFACTOR**: Optimize cleanup efficiency if needed

### Milestone 4: Integration with FastMCP Tools

**RED: Write failing tests**

```python
# tests/integration/test_session_context.py
import pytest
from fastmcp import FastMCP
from fastmcp.client import Client
from ifctester import ids

@pytest.mark.asyncio
async def test_session_persists_across_tool_calls():
    """Test that session state persists across multiple tool calls."""
    # Create simple MCP server with test tool
    mcp = FastMCP("Test Server")

    from ids_mcp_server.session.manager import get_or_create_session

    @mcp.tool
    async def set_title(title: str, ctx: Context) -> dict:
        """Set IDS title in session."""
        ids_obj = await get_or_create_session(ctx)
        ids_obj.info["title"] = title
        return {"status": "ok"}

    @mcp.tool
    async def get_title(ctx: Context) -> dict:
        """Get IDS title from session."""
        ids_obj = await get_or_create_session(ctx)
        return {"title": ids_obj.info.get("title")}

    # Test session persistence
    async with Client(mcp) as client:
        # Set title
        await client.call_tool("set_title", {"title": "My IDS"})

        # Get title - should be same session
        result = await client.call_tool("get_title", {})

        assert result["title"] == "My IDS"
```

**GREEN: Implementation**
1. Integrate session manager with server.py
2. Ensure Context is passed to all tools
3. Run tests → PASS

---

## Phase 3: Validation

**Validation Checklist:**

- ✅ All unit tests pass
- ✅ Session storage is thread-safe
- ✅ Context.session_id used for all session identification
- ✅ Sessions persist across tool calls
- ✅ Cleanup task removes abandoned sessions
- ✅ No manual session_id parameters in tool signatures
- ✅ Test coverage ≥ 95%

**Success Criteria:**

```bash
# Test session functionality
pytest tests/unit/session/ -v
pytest tests/component/test_session_lifecycle.py -v
pytest tests/integration/test_session_context.py -v

# Coverage check
pytest tests/ --cov=src/ids_mcp_server/session --cov-report=html
# Should show 95%+ coverage
```

---

## Dependencies

Inherits from **001-project-setup**:
- fastmcp (provides Context)
- ifctester (IDS objects)
- pytest, pytest-asyncio

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Memory leaks from abandoned sessions | High | Implement automatic cleanup task |
| Thread-safety bugs | High | Use threading.Lock, comprehensive tests |
| Context.session_id not stable | Critical | Research and verify in Phase 0 |
| Cleanup task blocks server | Medium | Use asyncio, non-blocking operations |

---

## Success Metrics

- ✅ Session creation <1ms
- ✅ Session retrieval <1ms
- ✅ Cleanup runs without blocking
- ✅ 1000+ concurrent sessions supported
- ✅ No memory leaks over 24+ hours

---

## Next Steps

After Phase 002 completion:
1. Proceed to **003-document-management** - Build MCP tools for IDS document CRUD
2. All subsequent tools will use Context-based session management
