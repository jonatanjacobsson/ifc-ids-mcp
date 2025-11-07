# Implementation Plan: Project Setup & Infrastructure

**Branch**: `claude/001-project-setup` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Establish the foundational project structure, dependencies, and basic FastMCP server setup for the IDS MCP Server. This phase creates the skeleton application with proper Python packaging, dependency management, and initial server configuration that will serve as the foundation for all subsequent features.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `fastmcp` - MCP server framework
- `ifctester` (part of IfcOpenShell) - IDS authoring and validation
- `ifcopenshell` - IFC file processing (included with ifctester)
- `pydantic` - Data validation for MCP tool parameters
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage

**Storage**: In-memory session storage (development), extensible to persistent storage
**Testing**: pytest with TDD methodology
**Target Platform**: Linux/macOS/Windows (cross-platform Python)
**Project Type**: Single project (Python package)
**Performance Goals**: Fast tool response (<100ms for non-IO operations)
**Constraints**:
- Must support Python 3.8+ for broad compatibility
- Zero-config startup for development
- Easy integration with Claude Desktop

**Scale/Scope**:
- ~10-15 MCP tools
- Support for 1000+ concurrent sessions (future)
- IDS files up to 10MB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Required Checks:**

- ✅ Project structure follows Python best practices (src layout)
- ✅ All dependencies are open source and actively maintained
- ✅ FastMCP version compatibility verified
- ✅ IfcTester library version supports IDS 1.0 standard
- ✅ Development environment can be set up without external dependencies
- ✅ Testing framework supports TDD methodology

**Post-Design Checks:**

- ✅ Project can be installed via pip
- ✅ Entry points configured for MCP server execution
- ✅ Configuration supports both development and production modes

## Project Structure

### Documentation (this feature)

```text
specs/001-project-setup/
├── plan.md              # This file
├── research.md          # Dependencies research & FastMCP setup
├── data-model.md        # Project configuration models
├── quickstart.md        # Setup and run instructions
├── contracts/           # API contracts for server initialization
└── tasks.md             # Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Single project structure
src/
├── ids_mcp_server/
│   ├── __init__.py
│   ├── __main__.py          # Entry point for python -m ids_mcp_server
│   ├── server.py            # FastMCP server instance
│   ├── config.py            # Configuration management
│   └── version.py           # Version information

tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── unit/
│   └── __init__.py
├── component/
│   └── __init__.py
├── integration/
│   └── __init__.py
└── validation/
    └── __init__.py

# Project root
pyproject.toml              # Python project configuration (PEP 621)
setup.py                    # Setup script (if needed for compatibility)
README.md                   # Project overview
.gitignore                  # Git ignore patterns
requirements.txt            # Production dependencies
requirements-dev.txt        # Development dependencies
pytest.ini                  # Pytest configuration
.pre-commit-config.yaml     # Pre-commit hooks (optional)
```

**Structure Decision**: Selected single project structure as this is a focused MCP server without frontend/backend separation. The `src` layout provides clean separation between source and tests, with `ids_mcp_server` as the main package.

## Complexity Tracking

> **No violations - standard Python project structure**

---

## Phase 0: Research

**Objectives:**
1. Verify FastMCP installation and basic usage
2. Verify IfcTester installation and IDS 1.0 support
3. Research FastMCP Context capabilities for session management
4. Identify project structure best practices for MCP servers
5. Document development environment setup

**Research Questions:**
- What is the recommended way to structure a FastMCP project?
- How to configure FastMCP server for development vs production?
- What are the IfcTester version requirements for IDS 1.0?
- How to set up pytest for async testing with FastMCP?
- What configuration options does FastMCP expose?

**Deliverable**: `research.md` with findings

---

## Phase 1: Design

**Objectives:**
1. Design project configuration schema (Pydantic models)
2. Define server initialization contract
3. Design logging configuration
4. Define entry point behavior
5. Create quickstart documentation

**Design Artifacts:**

### 1. Configuration Data Model (`data-model.md`)

```python
from pydantic import BaseModel, Field
from typing import Optional

class ServerConfig(BaseModel):
    """FastMCP server configuration."""
    name: str = "IDS MCP Server"
    mask_error_details: bool = False  # True in production
    log_level: str = "INFO"

class SessionConfig(BaseModel):
    """Session management configuration."""
    cleanup_interval: int = 3600  # seconds
    session_timeout: int = 86400  # 24 hours

class IDSMCPConfig(BaseModel):
    """Root configuration for IDS MCP Server."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
```

### 2. Server Initialization Contract (`contracts/server_init.md`)

```python
# Contract: FastMCP Server Initialization
from fastmcp import FastMCP

def create_server(config: IDSMCPConfig) -> FastMCP:
    """
    Create and configure FastMCP server instance.

    Args:
        config: Server configuration

    Returns:
        Configured FastMCP instance

    Contract:
        - MUST return initialized FastMCP instance
        - MUST configure error masking based on config
        - MUST set up logging
        - MUST be idempotent (can call multiple times)
    """
```

### 3. Entry Point Contract (`contracts/entry_point.md`)

```python
# Contract: Main Entry Point
def main() -> None:
    """
    Main entry point for IDS MCP Server.

    Behavior:
        1. Load configuration from environment
        2. Initialize logging
        3. Create FastMCP server
        4. Run server (blocking)

    Environment Variables:
        - IDS_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        - IDS_MASK_ERRORS: Mask error details (true/false)
        - IDS_SESSION_TIMEOUT: Session timeout in seconds
    """
```

**Deliverables**:
- `data-model.md` - Configuration schemas
- `contracts/` - API contracts
- `quickstart.md` - Setup instructions

---

## Phase 2: Test-Driven Implementation

**TDD Workflow**: Red → Green → Refactor for each feature

### Milestone 1: Project Structure & Dependencies

**RED: Write failing tests**

```python
# tests/unit/test_project_structure.py
def test_package_importable():
    """Test that ids_mcp_server package can be imported."""
    import ids_mcp_server
    assert ids_mcp_server is not None

def test_version_defined():
    """Test that version is defined."""
    from ids_mcp_server import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)
```

**GREEN: Implementation**
1. Create package structure
2. Add `__init__.py` with version
3. Run tests → PASS

**REFACTOR**: Clean up if needed

### Milestone 2: Configuration Management

**RED: Write failing tests**

```python
# tests/unit/test_config.py
def test_default_config_creation():
    """Test creating default configuration."""
    from ids_mcp_server.config import IDSMCPConfig

    config = IDSMCPConfig()

    assert config.server.name == "IDS MCP Server"
    assert config.server.log_level == "INFO"
    assert config.server.mask_error_details == False

def test_config_from_env(monkeypatch):
    """Test loading config from environment."""
    from ids_mcp_server.config import load_config_from_env

    monkeypatch.setenv("IDS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("IDS_MASK_ERRORS", "true")

    config = load_config_from_env()

    assert config.server.log_level == "DEBUG"
    assert config.server.mask_error_details == True
```

**GREEN: Implementation**
1. Create `config.py` with Pydantic models
2. Implement `load_config_from_env()`
3. Run tests → PASS

### Milestone 3: FastMCP Server Initialization

**RED: Write failing tests**

```python
# tests/unit/test_server.py
import pytest
from fastmcp import FastMCP

def test_create_server():
    """Test server creation with default config."""
    from ids_mcp_server.server import create_server
    from ids_mcp_server.config import IDSMCPConfig

    config = IDSMCPConfig()
    server = create_server(config)

    assert isinstance(server, FastMCP)
    assert server.name == "IDS MCP Server"

def test_server_tools_registered():
    """Test that initial tools are registered."""
    from ids_mcp_server.server import create_server
    from ids_mcp_server.config import IDSMCPConfig

    server = create_server(IDSMCPConfig())

    # At this phase, just verify server is ready
    # (No tools registered yet)
    assert server is not None
```

**GREEN: Implementation**
1. Create `server.py` with `create_server()`
2. Initialize FastMCP instance
3. Run tests → PASS

### Milestone 4: Entry Point

**RED: Write failing tests**

```python
# tests/integration/test_entry_point.py
def test_main_entry_point_exists():
    """Test that __main__.py exists and is executable."""
    import ids_mcp_server.__main__
    assert hasattr(ids_mcp_server.__main__, 'main')

def test_package_runnable_as_module(monkeypatch):
    """Test that package can be run with python -m."""
    from ids_mcp_server.__main__ import main

    # Mock the server run to avoid blocking
    def mock_run(*args, **kwargs):
        pass

    monkeypatch.setattr("ids_mcp_server.server.mcp.run", mock_run)

    # Should not raise
    try:
        main()
    except SystemExit:
        pass  # OK if exits cleanly
```

**GREEN: Implementation**
1. Create `__main__.py` with `main()` function
2. Implement server startup logic
3. Run tests → PASS

### Milestone 5: Development Environment Setup

**Deliverables:**
- `pyproject.toml` with all dependencies
- `requirements.txt` and `requirements-dev.txt`
- `pytest.ini` configuration
- `README.md` with setup instructions
- `.gitignore` for Python projects

**Verification Tests:**

```python
# tests/integration/test_installation.py
def test_all_dependencies_importable():
    """Test that all required dependencies can be imported."""
    import fastmcp
    import ifctester
    import ifcopenshell
    import pydantic
    import pytest

    assert all([fastmcp, ifctester, ifcopenshell, pydantic, pytest])
```

---

## Phase 3: Validation

**Validation Checklist:**

- ✅ All unit tests pass (pytest tests/unit/)
- ✅ Package can be imported
- ✅ Package can be run with `python -m ids_mcp_server`
- ✅ Configuration loads from environment variables
- ✅ FastMCP server starts without errors
- ✅ All dependencies install correctly
- ✅ Test coverage ≥ 95%
- ✅ README.md has complete setup instructions
- ✅ Project can be installed in fresh virtual environment

**Success Criteria:**

```bash
# Fresh environment test
python -m venv test_env
source test_env/bin/activate
pip install -e .
python -m ids_mcp_server  # Should start server

# Test suite
pytest tests/ -v --cov=src/ids_mcp_server --cov-report=html
# Should show 95%+ coverage, all tests pass
```

---

## Dependencies

**Production:**
```text
fastmcp>=0.4.0
ifctester>=0.0.1
pydantic>=2.0.0
```

**Development:**
```text
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
ruff>=0.1.0
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| IfcTester version incompatibility | High | Pin specific version, test during research |
| FastMCP API changes | Medium | Pin version, monitor releases |
| Python version compatibility | Medium | Test on multiple Python versions (3.8-3.12) |
| Dependency conflicts | Low | Use virtual environments, document versions |

---

## Success Metrics

- ✅ Server starts in <1 second
- ✅ Configuration loads correctly
- ✅ All tests pass with 95%+ coverage
- ✅ Package installable via pip
- ✅ Documentation enables setup in <5 minutes

---

## Next Steps

After Phase 001 completion:
1. Proceed to **002-session-management** - Implement FastMCP Context-based session handling
2. Begin building core MCP tools on top of this foundation
