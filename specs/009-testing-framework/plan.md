# Implementation Plan: Testing Framework & TDD Infrastructure

**Branch**: `claude/009-testing-framework` | **Date**: 2025-11-01 | **Spec**: [DESIGN_SPECIFICATION.md](../../DESIGN_SPECIFICATION.md)

## Summary

Establish comprehensive Test-Driven Development (TDD) infrastructure with pytest, coverage tools, and continuous integration. This phase creates the testing foundation that enforces TDD methodology across all development, ensuring 95%+ code coverage and validation of all IDS output using IfcTester API.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support
- `black` - Code formatting
- `ruff` - Linting

**Testing**: TDD with Red-Green-Refactor cycle
**Target Platform**: Cross-platform Python
**Project Type**: Single project
**Performance Goals**: Test suite <30s for full run
**Constraints**:
- Minimum 95% code coverage
- All tests must validate using IfcTester API
- TDD enforced via pre-commit hooks

**Scale/Scope**:
- 200+ unit tests
- 50+ integration tests
- 20+ validation tests

## Constitution Check

**Required Checks:**
- ✅ pytest supports async tests
- ✅ Coverage tool integrates with pytest
- ✅ Pre-commit hooks can enforce TDD
- ✅ CI/CD can run test suite
- ✅ IfcTester available in test environment

## Project Structure

```text
specs/009-testing-framework/
└── plan.md

# Testing infrastructure
tests/
├── conftest.py              # Pytest configuration and fixtures
├── __init__.py
├── fixtures/
│   ├── sample_ids_files/    # Example IDS files
│   ├── expected_outputs/    # Expected XML outputs
│   └── ifc_files/           # Sample IFC files (for validation tests)
├── unit/
│   ├── __init__.py
│   ├── session/
│   ├── tools/
│   └── utils/
├── component/
│   ├── __init__.py
│   └── test_*.py
├── integration/
│   ├── __init__.py
│   └── test_*.py
└── validation/
    ├── __init__.py
    ├── test_xsd_compliance.py
    ├── test_buildingsmart_examples.py
    └── test_round_trip.py

# Configuration files
pytest.ini                   # Pytest configuration
.coveragerc                  # Coverage configuration
.pre-commit-config.yaml      # Pre-commit hooks
.github/
└── workflows/
    └── test.yml             # CI/CD pipeline

# Development tools
pyproject.toml               # Updated with dev dependencies
requirements-dev.txt         # Development dependencies
```

**Structure Decision**: Organized tests by type (unit/component/integration/validation) with shared fixtures in conftest.py. Pre-commit hooks enforce TDD and code quality.

## Phase 1: Design

### Test Categories

**1. Unit Tests** - Test individual functions/classes
- Session storage operations
- Facet creation functions
- Restriction builders
- Helper utilities

**2. Component Tests** - Test business logic
- Session lifecycle
- Specification management
- Facet management workflows
- Validation services

**3. Integration Tests** - Test complete workflows
- End-to-end IDS creation
- Full MCP tool chains
- Context integration
- File I/O operations

**4. Validation Tests** - Test IDS compliance
- XSD schema validation
- buildingSMART example files
- Round-trip tests (create → export → load → export)
- IfcTester API validation

### Pytest Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    component: Component tests
    integration: Integration tests
    validation: Validation tests
    slow: Slow-running tests
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src/ids_mcp_server
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=95
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = src/ids_mcp_server
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args:
          - tests/
          - --cov=src/ids_mcp_server
          - --cov-fail-under=95
          - -v
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: TDD Validation

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          ruff check src/ tests/
          black --check src/ tests/

      - name: Run tests with coverage
        run: |
          pytest tests/ -v \
            --cov=src/ids_mcp_server \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=95

      - name: Run validation tests
        run: |
          pytest tests/validation/ -v --strict-markers

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

## Phase 2: Test-Driven Implementation

### Milestone 1: Pytest Infrastructure

**RED: Write failing tests for test infrastructure**

```python
# tests/test_infrastructure.py
def test_pytest_configured():
    """Test that pytest is properly configured."""
    import pytest
    assert pytest is not None

def test_async_support():
    """Test that async tests work."""
    import pytest
    import asyncio

    @pytest.mark.asyncio
    async def async_test():
        await asyncio.sleep(0.01)
        return True

    # If this runs without error, async support works
    assert True

def test_coverage_installed():
    """Test that coverage tool is available."""
    import coverage
    assert coverage is not None
```

**GREEN: Implementation**
1. Install pytest and plugins
2. Create pytest.ini
3. Run tests → PASS

### Milestone 2: Shared Test Fixtures

**RED: Write tests for fixtures**

```python
# tests/conftest.py
import pytest
from fastmcp import FastMCP
from ids_mcp_server.server import create_server
from ids_mcp_server.config import IDSMCPConfig

@pytest.fixture
def mcp_config():
    """Provide test configuration."""
    return IDSMCPConfig()

@pytest.fixture
def test_server(mcp_config):
    """Provide configured test server."""
    return create_server(mcp_config)

@pytest.fixture
def mock_context():
    """Provide mock FastMCP Context."""
    from unittest.mock import AsyncMock, MagicMock

    ctx = MagicMock()
    ctx.session_id = "test-session-123"
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()

    return ctx

@pytest.fixture
def sample_ids_xml():
    """Provide sample IDS XML."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://standards.buildingsmart.org/IDS
                                 http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
        <ids:info>
            <ids:title>Test IDS</ids:title>
        </ids:info>
        <ids:specifications></ids:specifications>
    </ids:ids>"""

@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Clean up sessions after each test."""
    yield
    # Cleanup code
    from ids_mcp_server.session.storage import _session_storage
    _session_storage.clear()
```

### Milestone 3: IfcTester Validation Helpers

```python
# tests/utils/ifctester_validators.py
from ifctester import ids

def validate_ids_structure(ids_obj: ids.Ids) -> None:
    """
    Validate IDS object structure using IfcTester API.

    This is the CRITICAL validation that ensures MCP tools
    correctly create IfcTester objects.
    """
    assert isinstance(ids_obj, ids.Ids)
    assert ids_obj.info is not None
    assert "title" in ids_obj.info

def validate_specification(spec: ids.Specification) -> None:
    """Validate specification structure."""
    assert isinstance(spec, ids.Specification)
    assert spec.name is not None
    assert spec.ifcVersion is not None
    assert isinstance(spec.ifcVersion, list)

def validate_entity_facet(facet: ids.Entity) -> None:
    """Validate entity facet."""
    assert isinstance(facet, ids.Entity)
    assert facet.name is not None

def validate_property_facet(facet: ids.Property) -> None:
    """Validate property facet."""
    assert isinstance(facet, ids.Property)
    assert facet.baseName is not None

def validate_xml_against_xsd(xml_string: str) -> None:
    """
    Validate XML against IDS XSD schema using IfcTester.

    This is the ultimate validation - if IfcTester can load
    and validate the XML, it's 100% compliant.
    """
    validated_ids = ids.from_string(xml_string, validate=True)
    assert validated_ids is not None
```

### Milestone 4: Example Test Suite

```python
# tests/validation/test_buildingsmart_examples.py
import pytest
from pathlib import Path
from ifctester import ids

def get_buildingsmart_examples():
    """Get list of buildingSMART example IDS files."""
    examples_dir = Path(__file__).parent / "fixtures" / "buildingsmart_examples"
    if examples_dir.exists():
        return list(examples_dir.glob("*.ids"))
    return []

@pytest.mark.parametrize("ids_file", get_buildingsmart_examples())
def test_load_buildingsmart_example(ids_file):
    """
    Test that we can load official buildingSMART examples.

    This validates that our implementation is compatible
    with real-world IDS files.
    """
    # Load example
    ids_obj = ids.open(str(ids_file), validate=True)

    assert ids_obj is not None
    assert len(ids_obj.specifications) > 0

    # Re-export and validate round-trip
    xml_string = ids_obj.to_string()
    reloaded = ids.from_string(xml_string, validate=True)

    assert reloaded.info["title"] == ids_obj.info["title"]
    assert len(reloaded.specifications) == len(ids_obj.specifications)

# tests/validation/test_round_trip.py
@pytest.mark.asyncio
async def test_round_trip_preservation():
    """
    Critical test: Ensure no data loss in create → export → load → export.
    """
    from fastmcp.client import Client

    mcp = create_test_server()

    async with Client(mcp) as client:
        # Create complete IDS
        await create_complete_ids(client)

        # Export 1
        export1 = await client.call_tool("export_ids", {})
        xml1 = export1["xml"]

        # Load
        await client.call_tool("load_ids", {
            "source": xml1,
            "source_type": "string"
        })

        # Export 2
        export2 = await client.call_tool("export_ids", {})
        xml2 = export2["xml"]

        # Validate both with IfcTester
        ids1 = ids.from_string(xml1, validate=True)
        ids2 = ids.from_string(xml2, validate=True)

        # Compare critical fields
        assert ids1.info["title"] == ids2.info["title"]
        assert len(ids1.specifications) == len(ids2.specifications)

        for spec1, spec2 in zip(ids1.specifications, ids2.specifications):
            assert spec1.name == spec2.name
            assert len(spec1.applicability) == len(spec2.applicability)
            assert len(spec1.requirements) == len(spec2.requirements)
```

## Phase 3: Validation

**Validation Checklist:**
- ✅ Pytest configured with all plugins
- ✅ Test coverage reporting works
- ✅ Pre-commit hooks installed
- ✅ CI/CD pipeline runs successfully
- ✅ All IfcTester validators implemented
- ✅ Sample fixtures available
- ✅ Documentation for TDD workflow

**Coverage Requirements:**
```bash
# Must achieve 95%+ coverage
pytest tests/ --cov=src/ids_mcp_server --cov-report=html --cov-fail-under=95

# Breakdown by module:
# - session/: 95%+
# - tools/: 95%+
# - validation/: 95%+
# - utils/: 90%+ (helper functions)
```

## TDD Workflow Documentation

```markdown
# TDD Workflow Guide

## Red-Green-Refactor Cycle

### 1. RED - Write Failing Test

```python
# Example: Adding new tool
def test_new_tool():
    """Test new tool functionality."""
    # This test MUST fail initially
    result = call_new_tool(params)
    assert result["status"] == "success"

# Run: pytest tests/test_new_tool.py
# Result: FAIL (good! test is testing something)
```

### 2. GREEN - Implement Minimum Code

```python
# Implement just enough to make test pass
@mcp.tool
async def new_tool(ctx: Context) -> dict:
    return {"status": "success"}

# Run: pytest tests/test_new_tool.py
# Result: PASS (implementation works!)
```

### 3. REFACTOR - Improve Code

```python
# Clean up, extract helpers, remove duplication
# All tests must still pass

# Run: pytest tests/
# Result: ALL PASS
```

## Validation with IfcTester

Every test that creates IDS objects MUST validate using IfcTester:

```python
# ❌ BAD - No validation
def test_create_spec():
    result = create_spec()
    assert result["status"] == "ok"

# ✅ GOOD - IfcTester validation
def test_create_spec():
    result = create_spec()

    # Validate using IfcTester API
    from ids_mcp_server.session.storage import _session_storage
    ids_obj = _session_storage.get(session_id).ids_obj

    assert isinstance(ids_obj.specifications[0], ids.Specification)
    assert ids_obj.specifications[0].name == "Expected Name"
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/validation/ -v

# Run with coverage
pytest tests/ --cov=src/ids_mcp_server --cov-report=html

# Run specific test
pytest tests/unit/test_specific.py::test_function -v

# Run in watch mode (requires pytest-watch)
ptw tests/
```
```

## Success Metrics

- ✅ All 200+ tests pass
- ✅ Coverage ≥ 95% across all modules
- ✅ Pre-commit hooks enforced
- ✅ CI/CD pipeline green
- ✅ All buildingSMART examples load successfully
- ✅ Round-trip tests pass

## Next Steps

After Phase 009:
1. **All implementation phases complete!**
2. Ready for production deployment
3. Documentation and user guides
4. Performance optimization if needed
5. Community feedback and iteration
