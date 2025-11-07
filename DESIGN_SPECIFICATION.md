# IDS MCP Server - Software Design Specification

**Version:** 2.2
**Date:** 2025-11-01
**Status:** Draft

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [IDS Standard Deep Dive](#3-ids-standard-deep-dive)
4. [FastMCP Framework Architecture](#4-fastmcp-framework-architecture)
5. [System Architecture](#5-system-architecture)
6. [MCP Tool Design](#6-mcp-tool-design)
7. [Data Models](#7-data-models)
8. [Validation and Compliance](#8-validation-and-compliance)
9. [Error Handling Strategy](#9-error-handling-strategy)
10. [Testing Strategy](#10-testing-strategy)
11. [Deployment Considerations](#11-deployment-considerations)
12. [Future Enhancements](#12-future-enhancements)

---

## 1. Executive Summary

### 1.1 Purpose

This document specifies the design for an MCP (Model Context Protocol) server that enables AI agents to deterministically create buildingSMART IDS (Information Delivery Specification) files that are 100% compliant with the IDS 1.0 standard.

### 1.2 Goals

- **100% IDS Schema Compliance**: All generated IDS files must validate against the official XSD schema at `https://standards.buildingsmart.org/IDS/1.0/ids.xsd`
- **Deterministic Generation**: Given the same input, the system must produce identical, valid IDS files
- **AI-Friendly Interface**: Provide simple, intuitive tools that AI agents can reliably use
- **Comprehensive Coverage**: Support all IDS facets, restrictions, and cardinalities defined in the standard

### 1.3 Technology Stack

- **Framework**: FastMCP (Python) - https://github.com/jlowin/fastmcp
- **IDS Library**: IfcTester (part of IfcOpenShell) - https://docs.ifcopenshell.org/ifctester.html
- **Target Standard**: buildingSMART IDS 1.0
- **Schema Source**: https://standards.buildingsmart.org/IDS/1.0/ids.xsd
- **Language**: Python 3.8+
- **Key Dependencies**:
  - `fastmcp` - MCP server framework
  - `ifctester` - IDS authoring, reading, and validation (official IfcOpenShell library)
  - `ifcopenshell` - IFC file processing (included with ifctester)
  - `pydantic` - Data validation and modeling for MCP tool parameters

---

## 2. System Overview

### 2.1 What is IDS?

Information Delivery Specification (IDS) is a buildingSMART standard for specifying and checking information requirements from IFC (Industry Foundation Classes) models. It provides:

- Computer-interpretable XML format for defining requirements
- Automatic compliance checking of IFC models
- Standardized approach to model validation
- Unambiguous interpretation across different software tools

### 2.2 What is MCP?

Model Context Protocol (MCP) is a standardized protocol for connecting AI assistants to external tools and data sources. FastMCP provides a Python framework for building MCP servers with:

- `@mcp.tool` decorator for exposing Python functions as tools
- `@mcp.resource` decorator for exposing read-only data
- Automatic parameter validation and type conversion
- Built-in error handling and client integration

### 2.3 System Purpose

This MCP server acts as a bridge between AI agents and the complex IDS specification, providing:

1. **Simple Tools**: AI agents call simple MCP tools to build IDS files incrementally
2. **IfcTester Integration**: Leverages the official IfcOpenShell IfcTester library for IDS operations
3. **Validation**: Each operation validates against IDS schema rules using IfcTester
4. **State Management**: Server maintains IDS document state during construction
5. **Export & Import**: Read existing IDS files and export new ones as compliant XML
6. **IFC Validation**: Optional capability to validate IFC models against created IDS files

---

## 3. IDS Standard Deep Dive

### 3.1 IDS File Structure

Based on the official specification, an IDS file has this XML structure:

```xml
<ids:ids xmlns:xs="http://www.w3.org/2001/XMLSchema"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://standards.buildingsmart.org/IDS
                             http://standards.buildingsmart.org/IDS/1.0/ids.xsd"
         xmlns:ids="http://standards.buildingsmart.org/IDS">

  <ids:info>
    <ids:title>Example IDS</ids:title>
    <ids:version>1.0</ids:version>
    <ids:author>[email protected]</ids:author>
    <ids:date>2024-01-06</ids:date>
    <ids:description>Optional description</ids:description>
    <ids:copyright>Optional copyright</ids:copyright>
    <ids:milestone>Optional milestone</ids:milestone>
    <ids:purpose>Optional purpose</ids:purpose>
  </ids:info>

  <ids:specifications>
    <ids:specification ifcVersion="IFC4X3"
                       name="Specification Name"
                       identifier="S1"
                       minOccurs="0"
                       maxOccurs="unbounded"
                       description="Optional description"
                       instructions="Optional instructions">
      <ids:applicability>
        <!-- Facets that identify relevant model elements -->
      </ids:applicability>
      <ids:requirements>
        <!-- Facets that specify required information -->
      </ids:requirements>
    </ids:specification>
  </ids:specifications>
</ids:ids>
```

### 3.2 IDS Information Model

#### 3.2.1 Info Element (Required)

Metadata about the IDS file itself:

| Element | Required | Type | Description |
|---------|----------|------|-------------|
| `title` | Yes | string | Human-readable title |
| `version` | No | string | Version identifier |
| `author` | No | string | Author email/name |
| `date` | No | date | Creation/modification date |
| `description` | No | string | Detailed description |
| `copyright` | No | string | Copyright information |
| `milestone` | No | string | Project milestone |
| `purpose` | No | string | Purpose of this IDS |

#### 3.2.2 Specification Element

Each specification has three parts:

1. **Description Fields**
   - `name` (required): Specification name
   - `identifier` (optional): Unique identifier
   - `description` (optional): Why this information is required
   - `instructions` (optional): How to fulfill requirements
   - `ifcVersion` (required): One or more IFC versions (IFC2X3, IFC4, IFC4X3, etc.)

2. **Applicability Section** (required)
   - Identifies subset of model being specified
   - Uses facets to filter IFC elements
   - At least one facet required

3. **Requirements Section** (required)
   - Specifies what information is required
   - Uses facets with cardinality (required, optional, prohibited)
   - Can have zero or more facets

#### 3.2.3 Cardinality

Each specification and requirement facet can specify:

- **Required** (default): Information must be present
- **Optional**: Information may be present (recommendations)
- **Prohibited**: Information must NOT be present

Cardinality is specified via:
- `minOccurs` and `maxOccurs` attributes on specification
- `cardinality` attribute on requirement facets (not available on entity facets in requirements)

### 3.3 The Six Facets

Based on the official documentation, IDS supports exactly six facet types:

#### 3.3.1 Entity Facet

Identifies IFC entity types (e.g., IfcWall, IfcDoor).

**Parameters:**
- `name` (required): IFC entity class name (e.g., "IFCWALL")
- `predefinedType` (optional): Specific type from enum (e.g., "MOVEABLE" for IfcWallTypeEnum)

**Usage:**
- In Applicability: Filters to specific entity types
- In Requirements: Requires specific entity type (cardinality always "required")

**Example:**
```xml
<ids:entity>
  <ids:name>
    <ids:simpleValue>IFCWALL</ids:simpleValue>
  </ids:name>
  <ids:predefinedType>
    <ids:simpleValue>MOVEABLE</ids:simpleValue>
  </ids:predefinedType>
</ids:entity>
```

#### 3.3.2 Attribute Facet

IFC attributes like Name, Description, Tag, ObjectType, PredefinedType.

**Parameters:**
- `name` (required): Attribute name (e.g., "Name", "Description")
- `value` (optional): Required value or pattern

**Usage:**
- In Applicability: Filters by attribute values
- In Requirements: Requires specific attribute values with cardinality

**Example:**
```xml
<ids:attribute cardinality="required">
  <ids:name>
    <ids:simpleValue>Name</ids:simpleValue>
  </ids:name>
  <ids:value>
    <ids:restriction base="xs:string">
      <xs:pattern value="EW-.*"/>
    </ids:restriction>
  </ids:value>
</ids:attribute>
```

#### 3.3.3 Property Facet

IFC properties and quantities (property sets).

**Parameters:**
- `propertySet` (optional): Property set name (e.g., "Pset_WallCommon")
- `baseName` (required): Property name (e.g., "FireRating")
- `dataType` (optional): IFC data type (uppercase, e.g., "IFCBOOLEAN")
- `value` (optional): Required value or pattern
- `location` (optional): Where property is attached ("instance", "type", or "any")

**Usage:**
- Most common facet for requirements
- Can specify property set, property name, and value constraints

**Example:**
```xml
<ids:property cardinality="required" dataType="IFCLABEL">
  <ids:propertySet>
    <ids:simpleValue>Pset_WallCommon</ids:simpleValue>
  </ids:propertySet>
  <ids:baseName>
    <ids:simpleValue>FireRating</ids:simpleValue>
  </ids:baseName>
  <ids:value>
    <ids:restriction base="xs:string">
      <xs:enumeration value="REI30"/>
      <xs:enumeration value="REI60"/>
      <xs:enumeration value="REI90"/>
    </ids:restriction>
  </ids:value>
</ids:property>
```

#### 3.3.4 Classification Facet

Classification systems (e.g., Uniclass, OmniClass).

**Parameters:**
- `system` (optional): Classification system URI or name
- `value` (required): Classification code or pattern

**Usage:**
- Requires elements to have specific classifications
- Can reference bSDD (buildingSMART Data Dictionary) via URI

**Example:**
```xml
<ids:classification cardinality="required">
  <ids:system>
    <ids:simpleValue>Uniclass 2015</ids:simpleValue>
  </ids:system>
  <ids:value>
    <ids:simpleValue>EF_25_10_25</ids:simpleValue>
  </ids:value>
</ids:classification>
```

#### 3.3.5 Material Facet

Material assignments.

**Parameters:**
- `value` (required): Material name, category, or URI

**Usage:**
- Requires specific materials
- Can reference material URIs (e.g., from bSDD)

**Example:**
```xml
<ids:material cardinality="required">
  <ids:value>
    <ids:simpleValue>Concrete</ids:simpleValue>
  </ids:value>
</ids:material>
```

#### 3.3.6 PartOf Facet

Relationship requirements (containment, aggregation).

**Parameters:**
- `relation` (required): Relationship type (e.g., "IFCRELAGGREGATES", "IFCRELCONTAINEDINSPATIALSTRUCTURE")
- `entity` (required): Parent entity specification (entity facet)

**Usage:**
- Requires specific structural relationships
- E.g., "Door must be part of a Space"

**Example:**
```xml
<ids:partOf cardinality="required" relation="IFCRELCONTAINEDINSPATIALSTRUCTURE">
  <ids:entity>
    <ids:name>
      <ids:simpleValue>IFCSPACE</ids:simpleValue>
    </ids:name>
  </ids:entity>
</ids:partOf>
```

### 3.4 Facet Parameters and Restrictions

#### 3.4.1 Simple Values

The simplest form - exact string match:

```xml
<ids:simpleValue>IFCWALL</ids:simpleValue>
```

#### 3.4.2 Restrictions (Complex Values)

For advanced constraints using XML Schema facets:

**Enumeration** (list of valid values):
```xml
<ids:restriction base="xs:string">
  <xs:enumeration value="REI30"/>
  <xs:enumeration value="REI60"/>
  <xs:enumeration value="REI90"/>
</ids:restriction>
```

**Pattern** (regex matching):
```xml
<ids:restriction base="xs:string">
  <xs:pattern value="EW-[0-9]{3}"/>
</ids:restriction>
```

**Bounds** (numeric ranges):
```xml
<ids:restriction base="xs:double">
  <xs:minInclusive value="2.4"/>
  <xs:maxInclusive value="3.0"/>
</ids:restriction>
```

**Length constraints**:
```xml
<ids:restriction base="xs:string">
  <xs:length value="10"/>
</ids:restriction>
```

```xml
<ids:restriction base="xs:string">
  <xs:minLength value="5"/>
  <xs:maxLength value="50"/>
</ids:restriction>
```

#### 3.4.3 Base Types

Restrictions must specify a base XML Schema type:

- `xs:string` - Text values
- `xs:integer` - Integer numbers
- `xs:double` - Decimal numbers
- `xs:boolean` - True/false
- `xs:date` - Date values
- `xs:time` - Time values
- `xs:dateTime` - Date and time

### 3.5 IFC Versions

Supported IFC versions (case-insensitive, space-separated list):

- `IFC2X3`
- `IFC4`
- `IFC4X3` (also known as IFC4.3)

Multiple versions can be specified:
```xml
<ids:specification ifcVersion="IFC2X3 IFC4 IFC4X3" ...>
```

---

## 4. FastMCP Framework Architecture

### 4.1 Core Concepts

FastMCP provides three building blocks:

1. **Tools** (`@mcp.tool`): Execute actions, perform computations
2. **Resources** (`@mcp.resource`): Expose read-only data via URIs
3. **Prompts** (`@mcp.prompt`): Reusable LLM interaction templates

For this IDS MCP server, we'll primarily use **Tools**.

### 4.2 Tool Design Pattern

```python
from fastmcp import FastMCP

mcp = FastMCP("IDS MCP Server")

@mcp.tool
def create_specification(
    name: str,
    ifc_versions: list[str],
    description: str = None
) -> dict:
    """
    Create a new IDS specification.

    Args:
        name: Specification name
        ifc_versions: List of IFC versions (e.g., ["IFC4", "IFC4X3"])
        description: Optional description

    Returns:
        Dictionary with specification ID and status
    """
    # Implementation
    return {"spec_id": "S1", "status": "created"}
```

Key features:
- **Type hints** drive automatic parameter validation
- **Docstrings** provide tool descriptions to AI agents
- **Return types** are automatically serialized
- **Errors** can be raised as `ToolError` for user-friendly messages

### 4.3 Error Handling

FastMCP provides two error modes:

1. **ToolError**: User-facing errors (validation failures, business logic errors)
   ```python
   from fastmcp import ToolError
   raise ToolError("Invalid IFC version: IFC99")
   ```

2. **Masked Errors**: Internal errors masked in production to prevent information leakage
   ```python
   mcp = FastMCP("IDS Server", mask_error_details=True)
   ```

### 4.4 State Management

FastMCP doesn't provide built-in state management. For this server, we'll need:

- **Session-based state**: Store IDS document being built
- **Context parameter**: Access to MCP context for logging
- **In-memory storage**: During development
- **Persistent storage**: For production (optional)

### 4.5 Testing Pattern

FastMCP provides built-in testing via in-memory client:

```python
from fastmcp import FastMCP
from fastmcp.client import Client

async with Client(mcp) as client:
    result = await client.call_tool("create_ids", {
        "title": "Test IDS",
        "author": "test@example.com"
    })
```

### 4.5 IfcTester Integration

IfcTester is the official Python library from IfcOpenShell for working with IDS files. It provides a complete, tested, and maintained implementation of the IDS specification.

#### 4.5.1 Why IfcTester?

Using IfcTester provides significant advantages:

1. **Official Implementation**: Developed and maintained by the IfcOpenShell team
2. **Battle-Tested**: Used in production by the BIM industry
3. **Complete Coverage**: Supports all IDS 1.0 features
4. **Built-in Validation**: Validates against official XSD schema
5. **IFC Integration**: Can validate IFC models against IDS (bonus feature)
6. **Community Support**: Active development and issue tracking

#### 4.5.2 IfcTester Core API

**Creating IDS Documents:**
```python
from ifctester import ids

# Create new IDS
my_ids = ids.Ids(
    title="My IDS",
    author="[email protected]",
    description="Project requirements"
)

# Add specification
spec = ids.Specification(
    name="Wall Fire Rating",
    ifcVersion=["IFC4"],
    description="All walls must have fire rating"
)

# Add applicability (what to check)
spec.applicability.append(ids.Entity(name="IFCWALL"))

# Add requirements (what to require)
requirement = ids.Property(
    baseName="FireRating",
    propertySet="Pset_WallCommon",
    cardinality="required"
)
spec.requirements.append(requirement)

# Add to IDS
my_ids.specifications.append(spec)

# Save to file
my_ids.to_xml("output.ids")
```

**Reading IDS Documents:**
```python
# Load from file
my_ids = ids.open("existing.ids")

# Or from string
xml_string = "..."
my_ids = ids.from_string(xml_string)

# Access specifications
for spec in my_ids.specifications:
    print(spec.name)
    print(spec.applicability)
    print(spec.requirements)
```

**IDS Facet Classes:**

IfcTester provides classes for all six facet types:

- `ids.Entity(name, predefinedType=None)`
- `ids.Property(baseName, propertySet=None, value=None, dataType=None, cardinality="required")`
- `ids.Attribute(name, value=None, cardinality="required")`
- `ids.Classification(value, system=None, cardinality="required")`
- `ids.Material(value, cardinality="required")`
- `ids.PartOf(entity, relation, cardinality="required")`

**Restrictions:**

IfcTester supports IDS restrictions using the `Restriction` class or simple values:

```python
# Simple value
ids.Entity(name="IFCWALL")

# Enumeration restriction
restriction = ids.Restriction(
    base="xs:string",
    options={"enumeration": ["REI30", "REI60", "REI90"]}
)
ids.Property(baseName="FireRating", value=restriction)

# Pattern restriction
restriction = ids.Restriction(
    base="xs:string",
    options={"pattern": "EW-[0-9]{3}"}
)

# Bounds restriction
restriction = ids.Restriction(
    base="xs:double",
    options={"minInclusive": 2.4, "maxInclusive": 3.0}
)
```

#### 4.5.3 Validation Capabilities

```python
import ifcopenshell

# Validate IFC model against IDS
ifc_file = ifcopenshell.open("model.ifc")
my_ids.validate(ifc_file)

# Check validation results
for spec in my_ids.specifications:
    print(f"Specification: {spec.name}")
    print(f"Status: {spec.status}")
    print(f"Passed: {len(spec.passed_entities)}")
    print(f"Failed: {len(spec.failed_entities)}")

# Generate reports
from ifctester import reporter

# Console report
reporter.Console(my_ids).report()

# HTML report
html_reporter = reporter.Html(my_ids)
html_reporter.report()
html_reporter.to_file("report.html")

# JSON report
json_reporter = reporter.Json(my_ids)
json_reporter.to_file("report.json")
```

#### 4.5.4 Integration Strategy

Our MCP server will:

1. **Wrap IfcTester**: Use IfcTester as the underlying IDS engine
2. **Simplify Interface**: Provide simple MCP tools that map to IfcTester API
3. **Maintain State**: Keep `ids.Ids` object in session for incremental building
4. **Validate Early**: Use IfcTester's validation at each step
5. **Extend Functionality**: Add AI-friendly abstractions on top of IfcTester

---

## 5. System Architecture

### 5.1 Architectural Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Agent                              │
│                    (Claude, GPT, etc.)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ MCP Protocol
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   FastMCP Server                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              MCP Tools Layer                          │  │
│  │  - create_ids()      - load_ids()                     │  │
│  │  - add_specification()                                │  │
│  │  - add_entity_facet()                                 │  │
│  │  - add_property_facet()                               │  │
│  │  - add_attribute_facet()                              │  │
│  │  - add_restriction()                                  │  │
│  │  - export_ids()      - validate_ids()                 │  │
│  │  - validate_ifc_model() (bonus)                       │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │           Business Logic Layer                        │  │
│  │  - IDSSessionManager (manages sessions)               │  │
│  │  - IDSBuilder (orchestrates IDS creation)             │  │
│  │  - FacetFactory (creates IfcTester facets)            │  │
│  │  - RestrictionFactory (creates restrictions)          │  │
│  │  - ValidationService (validates operations)           │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │          IfcTester Integration Layer                  │  │
│  │                                                        │  │
│  │  Session State: ids.Ids object                        │  │
│  │                                                        │  │
│  │  IfcTester Classes:                                   │  │
│  │  - ids.Ids (root document)                            │  │
│  │  - ids.Specification                                  │  │
│  │  - ids.Entity, ids.Property, ids.Attribute            │  │
│  │  - ids.Classification, ids.Material, ids.PartOf       │  │
│  │  - ids.Restriction (value constraints)                │  │
│  │                                                        │  │
│  │  IfcTester Operations:                                │  │
│  │  - ids.open() / ids.from_string()                     │  │
│  │  - to_xml() / to_string()                             │  │
│  │  - validate(ifc_file)                                 │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ XML I/O
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    IDS XML File                              │
│         (100% compliant with IDS 1.0 XSD)                    │
│         Created/validated by IfcTester                       │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Layer Responsibilities

#### 5.2.1 MCP Tools Layer

- Exposes simple, atomic operations to AI agents
- Validates input parameters using Pydantic (for MCP interface only)
- Maintains conversation context and session IDs
- Delegates to business logic layer
- Returns user-friendly responses
- Handles errors and provides clear feedback

#### 5.2.2 Business Logic Layer

- Orchestrates IDS document construction using IfcTester
- Manages session lifecycle and state
- Translates MCP tool calls to IfcTester operations
- Creates IfcTester facets and restrictions via factories
- Validates business constraints before delegating to IfcTester
- Coordinates complex multi-step operations

#### 5.2.3 IfcTester Integration Layer

- **Core Responsibility**: Direct interaction with IfcTester library
- Maintains `ids.Ids` object as session state
- Creates and manages `ids.Specification` objects
- Instantiates IfcTester facet objects (Entity, Property, etc.)
- Builds `ids.Restriction` objects for value constraints
- Handles XML serialization via `to_xml()` and `to_string()`
- Handles XML deserialization via `ids.open()` and `ids.from_string()`
- Performs XSD validation (built into IfcTester)
- Optional: Validates IFC models against IDS specifications

**Key Point**: This layer directly uses IfcTester classes without wrapping them in custom models. The `ids.Ids` object IS our data model.

### 5.3 State Management Architecture (Session-Based with FastMCP Context)

**Decision**: Use **Session-Based** state management with **FastMCP Context** for automatic session handling.

#### 5.3.1 FastMCP Context Overview

FastMCP provides a `Context` object with powerful capabilities:

- **Automatic Session Management**: `ctx.session_id` automatically identifies client sessions
- **Logging**: `ctx.info()`, `ctx.debug()`, `ctx.warning()`, `ctx.error()`
- **Progress Reporting**: `ctx.report_progress()` for long operations
- **Request Metadata**: `ctx.request_id`, `ctx.client_id`
- **Server Access**: `ctx.server` for accessing FastMCP instance
- **Request-Scoped State**: `ctx.set_state()` / `ctx.get_state()` for within-request data

**Critical Understanding**: Context state is **request-scoped**, not session-scoped. For session-level persistence (our IDS documents across multiple tool calls), we need a global store keyed by `session_id`.

#### 5.3.2 Implementation Strategy

**Two-Level State Management:**

1. **Session-Level (Persistent)**: Global dictionary for IDS documents, keyed by `ctx.session_id`
2. **Request-Level (Transient)**: Context state for within-request data

**Advantages:**
- ✅ Automatic session ID management via FastMCP
- ✅ No manual session tracking required
- ✅ Built-in logging and progress reporting
- ✅ Natural conversation flow
- ✅ Clean separation of concerns

**Trade-offs:**
- ⚠️ Requires cleanup of abandoned sessions
- ⚠️ In-memory storage (consider persistence for production)

#### 5.3.3 Implementation with FastMCP Context

```python
from typing import Dict
from ifctester import ids
from fastmcp import Context

# Session-level storage: persists across requests within same session
_session_storage: Dict[str, ids.Ids] = {}

async def get_or_create_session(ctx: Context) -> ids.Ids:
    """
    Get existing IDS for this session or create new one.

    Uses ctx.session_id for automatic session identification.
    """
    session_id = ctx.session_id

    if session_id not in _session_storage:
        await ctx.info(f"Creating new IDS session: {session_id}")
        _session_storage[session_id] = ids.Ids(title="Untitled")
    else:
        await ctx.debug(f"Retrieved existing session: {session_id}")

    return _session_storage[session_id]

async def create_session_from_file(ctx: Context, filepath: str) -> ids.Ids:
    """Load IDS from file and store in session."""
    session_id = ctx.session_id

    await ctx.info(f"Loading IDS from {filepath}")
    _session_storage[session_id] = ids.open(filepath)

    return _session_storage[session_id]

async def create_session_from_string(ctx: Context, xml_string: str) -> ids.Ids:
    """Load IDS from XML string and store in session."""
    session_id = ctx.session_id

    await ctx.info("Loading IDS from XML string")
    _session_storage[session_id] = ids.from_string(xml_string)

    return _session_storage[session_id]

def cleanup_session(session_id: str) -> None:
    """Remove session data."""
    if session_id in _session_storage:
        del _session_storage[session_id]
```

#### 5.3.4 Tool Implementation Example

```python
from fastmcp import FastMCP, Context, ToolError

mcp = FastMCP("IDS MCP Server")

@mcp.tool
async def create_ids(
    title: str,
    ctx: Context,  # Automatically injected by FastMCP
    author: str = None,
    version: str = None,
    description: str = None
) -> dict:
    """
    Create a new IDS document for this session.

    Session is automatically tracked by FastMCP.
    No need to pass session_id parameter!
    """
    try:
        await ctx.info(f"Creating IDS: {title}")

        # Create new IDS
        ids_obj = ids.Ids(
            title=title,
            author=author,
            version=version,
            description=description
        )

        # Store in session
        session_id = ctx.session_id
        _session_storage[session_id] = ids_obj

        await ctx.info(f"IDS created successfully for session {session_id}")

        return {
            "status": "created",
            "session_id": session_id,
            "title": title
        }

    except Exception as e:
        await ctx.error(f"Failed to create IDS: {str(e)}")
        raise ToolError(f"Failed to create IDS: {str(e)}")

@mcp.tool
async def add_specification(
    name: str,
    ifc_versions: list[str],
    ctx: Context,
    identifier: str = None,
    description: str = None
) -> dict:
    """
    Add specification to the session's IDS document.

    Automatically uses the current session - no session_id parameter needed!
    """
    try:
        # Get IDS from current session
        ids_obj = await get_or_create_session(ctx)

        await ctx.info(f"Adding specification: {name}")

        # Create specification
        spec = ids.Specification(
            name=name,
            ifcVersion=ifc_versions,
            identifier=identifier,
            description=description
        )

        # Add to IDS
        ids_obj.specifications.append(spec)

        await ctx.info(f"Specification added: {name}")

        return {
            "status": "added",
            "spec_id": identifier or spec.name,
            "ifc_versions": ifc_versions
        }

    except Exception as e:
        await ctx.error(f"Failed to add specification: {str(e)}")
        raise ToolError(f"Failed to add specification: {str(e)}")
```

#### 5.3.5 Session Cleanup Strategy

**Development:**
- Manual cleanup via dedicated tool
- Sessions persist until server restart

**Production:**
```python
import asyncio
from datetime import datetime, timedelta

# Track last access time
_session_last_access: Dict[str, datetime] = {}

async def session_cleanup_task():
    """Background task to clean up abandoned sessions."""
    while True:
        await asyncio.sleep(3600)  # Run every hour

        cutoff = datetime.now() - timedelta(hours=24)
        abandoned = [
            sid for sid, last_access in _session_last_access.items()
            if last_access < cutoff
        ]

        for session_id in abandoned:
            cleanup_session(session_id)
            del _session_last_access[session_id]

# Start cleanup task on server startup
asyncio.create_task(session_cleanup_task())
```

#### 5.3.6 Context Features We'll Use

1. **Session ID**: `ctx.session_id` - Automatic session tracking
2. **Logging**: `ctx.info()`, `ctx.debug()`, `ctx.warning()`, `ctx.error()`
3. **Progress**: `ctx.report_progress()` - For long operations like validation
4. **Request ID**: `ctx.request_id` - For debugging and tracing
5. **Server Access**: `ctx.server` - Access to MCP server instance if needed

#### 5.3.7 Key Benefits

✅ **No Manual Session IDs**: FastMCP handles session identification
✅ **Cleaner API**: Tools don't need `session_id` parameters
✅ **Built-in Logging**: Consistent logging via Context
✅ **Progress Reporting**: Real-time feedback for long operations
✅ **Request Tracing**: Every request has unique ID for debugging

---

## 6. MCP Tool Design

### 6.1 Tool Categorization

Tools are grouped by functionality:

1. **Document Management**: Create, load, configure, export IDS files
2. **Specification Management**: Add, update specifications
3. **Facet Management**: Add facets to applicability/requirements
4. **Restriction Management**: Configure value constraints
5. **Validation**: Validate IDS document and IFC models
6. **Introspection**: Query document structure

### 6.2 Core Tools Specification

**Note**: All tools use `ctx: Context` for automatic session management. No `session_id` parameter needed!

#### 6.2.1 Document Management Tools

**create_ids**
```python
@mcp.tool
async def create_ids(
    title: str,
    ctx: Context,
    author: str = None,
    version: str = None,
    date: str = None,
    description: str = None,
    copyright: str = None,
    milestone: str = None,
    purpose: str = None
) -> dict:
    """
    Create a new IDS document for this session.

    Session is automatically tracked by FastMCP - no session_id parameter needed!

    Args:
        title: Document title (required)
        ctx: FastMCP Context (auto-injected)
        author: Author email or name
        version: Version string
        date: Date in YYYY-MM-DD format
        description: Document description
        copyright: Copyright notice
        milestone: Project milestone
        purpose: Purpose of this IDS

    Returns:
        {
            "status": "created",
            "session_id": "auto-generated-by-fastmcp",
            "title": "..."
        }

    Implementation:
        Creates ids.Ids object and stores in session via ctx.session_id
    """
```

**export_ids**
```python
@mcp.tool
async def export_ids(
    ctx: Context,
    output_path: str = None,
    validate: bool = True
) -> dict:
    """
    Export IDS document to XML file using IfcTester.

    Uses current session automatically - no session_id parameter needed!

    Args:
        ctx: FastMCP Context (auto-injected)
        output_path: File path (optional, returns XML string if not provided)
        validate: Whether to validate against XSD (default: True)

    Returns:
        {
            "status": "exported",
            "xml": "...",  # If no output_path
            "file_path": "...",  # If output_path provided
            "validation_result": {"valid": true, "errors": []}
        }

    Implementation:
        Uses ids.Ids.to_xml(filepath) or ids.Ids.to_string()
        Gets IDS from session via ctx.session_id
    """
```

**load_ids**
```python
@mcp.tool
async def load_ids(
    source: str,
    ctx: Context,
    source_type: str = "file"
) -> dict:
    """
    Load an existing IDS file into the current session.

    Replaces any existing IDS in this session.

    Args:
        source: File path or XML string
        ctx: FastMCP Context (auto-injected)
        source_type: "file" or "string"

    Returns:
        {
            "status": "loaded",
            "session_id": "auto-generated-by-fastmcp",
            "title": "...",
            "specification_count": 3,
            "specifications": [...]
        }

    Implementation:
        Uses ids.open(filepath) or ids.from_string(xml)
        Stores in session via ctx.session_id
    """
```

**get_ids_info**
```python
@mcp.tool
async def get_ids_info(ctx: Context) -> dict:
    """
    Get current session's IDS document structure.

    Uses current session automatically - no session_id parameter needed!

    Args:
        ctx: FastMCP Context (auto-injected)

    Returns:
        {
            "title": "...",
            "author": "...",
            "specification_count": 3,
            "specifications": [
                {
                    "identifier": "S1",
                    "name": "Wall Fire Rating",
                    "ifc_versions": ["IFC4"],
                    "applicability_facets": 1,
                    "requirement_facets": 2
                }
            ]
        }

    Implementation:
        Gets IDS from session via ctx.session_id
    """
```

#### 6.2.2 Specification Management Tools

**add_specification**
```python
@mcp.tool
async def add_specification(
    name: str,
    ifc_versions: list[str],
    ctx: Context,
    identifier: str = None,
    description: str = None,
    instructions: str = None,
    min_occurs: int = 0,
    max_occurs: int | str = "unbounded"
) -> dict:
    """
    Add a specification to the current session's IDS document.

    Args:
        name: Specification name
        ifc_versions: List of IFC versions (e.g., ["IFC4", "IFC4X3"])
        ctx: FastMCP Context (auto-injected)
        identifier: Optional unique identifier
        description: Why this information is required
        instructions: How to fulfill requirements
        min_occurs: Minimum occurrences (0 = optional)
        max_occurs: Maximum occurrences (int or "unbounded")

    Returns:
        {
            "status": "added",
            "spec_id": "S1",
            "ifc_versions": ["IFC4"]
        }

    Implementation:
        Gets IDS from ctx.session_id, creates ids.Specification, appends to specifications
    """
```

#### 6.2.3 Facet Management Tools

**Note**: All facet tools follow the same pattern:
- Use `ctx: Context` for automatic session access
- Require `spec_id` to identify which specification to modify
- `location` parameter specifies "applicability" or "requirements"
- Return facet details including generated `facet_id`

**add_entity_facet**
```python
@mcp.tool
async def add_entity_facet(
    spec_id: str,
    location: str,
    entity_name: str,
    ctx: Context,
    predefined_type: str = None,
    cardinality: str = "required"
) -> dict:
    """
    Add an entity facet to a specification.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        entity_name: IFC entity name (e.g., "IFCWALL")
        ctx: FastMCP Context (auto-injected)
        predefined_type: Optional predefined type
        cardinality: "required", "optional", or "prohibited" (requirements only)

    Returns:
        {
            "status": "added",
            "facet_type": "entity",
            "spec_id": "S1"
        }

    Implementation:
        Creates ids.Entity and appends to spec.applicability or spec.requirements
    """
```

**add_property_facet**
```python
@mcp.tool
async def add_property_facet(
    spec_id: str,
    location: str,
    property_name: str,
    ctx: Context,
    property_set: str = None,
    data_type: str = None,
    property_location: str = "any",
    cardinality: str = "required"
) -> dict:
    """
    Add a property facet to a specification.

    Args:
        spec_id: Specification identifier
        location: "applicability" or "requirements"
        property_name: Property name (e.g., "FireRating")
        ctx: FastMCP Context (auto-injected)
        property_set: Property set name (e.g., "Pset_WallCommon")
        data_type: IFC data type (e.g., "IFCLABEL")
        property_location: "instance", "type", or "any"
        cardinality: "required", "optional", or "prohibited"

    Returns:
        {
            "status": "added",
            "facet_type": "property",
            "spec_id": "S1"
        }

    Implementation:
        Creates ids.Property and appends to spec.applicability or spec.requirements
    """
```

**Other Facet Tools** (follow same pattern):
- `add_attribute_facet(spec_id, location, attribute_name, ctx, cardinality="required")`
- `add_classification_facet(spec_id, location, classification_value, ctx, classification_system=None, cardinality="required")`
- `add_material_facet(spec_id, location, material_value, ctx, cardinality="required")`
- `add_partof_facet(spec_id, location, relation, parent_entity, ctx, parent_predefined_type=None, cardinality="required")`

All create corresponding IfcTester facet objects and append to the appropriate specification section.

#### 6.2.4 Restriction Management Tools

**Note**: Restriction tools work with facets directly using IfcTester's `ids.Restriction` class.

**Pattern for all restriction tools**:
- Take `spec_id` and `parameter_name` (which facet parameter to constrain)
- Use `ctx: Context` for session access
- Create `ids.Restriction` object with appropriate options
- Apply to facet in current session's IDS

**Available restriction tools**:

**add_enumeration_restriction**
```python
@mcp.tool
async def add_enumeration_restriction(
    spec_id: str,
    parameter_name: str,  # e.g., "value", "name"
    base_type: str,       # "xs:string", "xs:integer", etc.
    values: list[str],
    ctx: Context
) -> dict:
    """
    Add enumeration restriction (list of valid values).

    Example: FireRating must be one of ["REI30", "REI60", "REI90"]

    Implementation:
        Creates ids.Restriction(base=base_type, options={"enumeration": values})
    """
```

**add_pattern_restriction**
```python
@mcp.tool
async def add_pattern_restriction(
    spec_id: str,
    parameter_name: str,
    base_type: str,
    pattern: str,  # Regex pattern
    ctx: Context
) -> dict:
    """
    Add pattern restriction (regex matching).

    Example: Name must match pattern "EW-[0-9]{3}"

    Implementation:
        Creates ids.Restriction(base=base_type, options={"pattern": pattern})
    """
```

**Other Restriction Tools**:
- `add_bounds_restriction(spec_id, parameter_name, base_type, ctx, min_inclusive=None, max_inclusive=None, ...)`
- `add_length_restriction(spec_id, parameter_name, base_type, ctx, length=None, min_length=None, max_length=None)`

All create `ids.Restriction` objects with appropriate options dict.

#### 6.2.5 Validation Tools

**validate_ids**
```python
@mcp.tool
async def validate_ids(ctx: Context) -> dict:
    """
    Validate current session's IDS document.

    Uses IfcTester's built-in validation by attempting to serialize to XML.

    Args:
        ctx: FastMCP Context (auto-injected)

    Returns:
        {
            "valid": true,
            "errors": [],
            "specifications_count": 3
            "warnings": []
        }
    """
```

**validate_ifc_model** (Bonus Feature)
```python
@mcp.tool
async def validate_ifc_model(
    ifc_file_path: str,
    ctx: Context,
    report_format: str = "json"  # "console", "json", "html"
) -> dict:
    """
    Validate an IFC model against the current session's IDS specifications.

    This bonus feature leverages IfcTester's IFC validation capabilities.

    Args:
        ifc_file_path: Path to IFC file
        ctx: FastMCP Context (auto-injected)
        report_format: "console", "json", or "html"

    Returns:
        {
            "status": "validation_complete",
            "report": "..." # If format is json
            "html": "..." # If format is html
        }

    Implementation:
        Uses ifcopenshell.open() and ids_obj.validate(ifc_file)
        Then reporter.Json/Html/Console to generate reports
    """
```

### 6.3 Tool Design Principles

1. **Automatic Session Management**: All tools use `ctx: Context` - no manual session_id tracking
2. **Async by Default**: All tools are async to leverage Context's async methods
3. **Atomic Operations**: Each tool does one thing well
4. **Progressive Construction**: Build IDS incrementally
5. **Immediate Validation**: Validate at each step via IfcTester
6. **Clear Errors**: Provide actionable error messages using `ctx.error()` and `ToolError`
7. **Idempotency**: Same input = same output
8. **Logging**: Use `ctx.info()`, `ctx.debug()` for transparency
9. **Stateful Session**: Maintain document state across calls via `ctx.session_id`

---

## 7. Data Models

### 7.1 Using IfcTester Models Directly

**Key Design Decision**: Instead of creating custom Pydantic models for IDS, we directly use IfcTester's native classes.

**Rationale:**
- IfcTester already provides complete, validated IDS models
- Avoids duplication and potential inconsistencies
- Leverages battle-tested implementation
- Simplifies maintenance and updates
- Direct mapping to IDS XML structure

**What Pydantic Is Used For:**
- MCP tool parameter validation only
- Input/output DTOs for tool interfaces
- NOT for IDS document representation

### 7.2 IfcTester Model Reference

#### 7.2.1 Root Document: `ids.Ids`

The main container for an IDS document.

```python
from ifctester import ids

# Create new IDS
my_ids = ids.Ids(
    title="Project Requirements",
    author="[email protected]",
    version="1.0",
    description="BIM requirements for Project X",
    copyright="© 2025 Company",
    date="2025-01-15",
    purpose="Design stage requirements",
    milestone="LOD 300"
)

# Properties
my_ids.info  # Dict with metadata
my_ids.specifications  # List of Specification objects
my_ids.filepath  # Source file path (if loaded)

# Methods
my_ids.to_xml("output.ids")  # Export to file
xml_string = my_ids.to_string()  # Export to string
my_ids.validate(ifc_file)  # Validate IFC model
```

#### 7.2.2 Specification: `ids.Specification`

Individual requirement specifications within an IDS.

```python
# Create specification
spec = ids.Specification(
    name="Wall Fire Rating",
    ifcVersion=["IFC4", "IFC4X3"],
    identifier="WFR-001",
    description="All load-bearing walls must have fire rating",
    instructions="Ensure Pset_WallCommon.FireRating is populated",
    minOccurs=1,
    maxOccurs="unbounded"
)

# Properties
spec.applicability  # List of facet objects
spec.requirements  # List of facet objects
spec.status  # Validation status (after validate())
spec.applicable_entities  # IFC entities that match (after validate())
spec.passed_entities  # Entities that pass (after validate())
spec.failed_entities  # Entities that fail (after validate())

# Methods
spec.validate(ifc_file)  # Validate against IFC
spec.asdict()  # Convert to dictionary
```

#### 7.2.3 Facet Classes

**Entity Facet:**
```python
entity = ids.Entity(
    name="IFCWALL",
    predefinedType="SOLIDWALL"  # Optional
)
```

**Property Facet:**
```python
prop = ids.Property(
    baseName="FireRating",
    propertySet="Pset_WallCommon",
    dataType="IfcLabel",  # Optional
    value="REI60",  # Optional
    cardinality="required",  # For requirements
    uri="https://identifier.buildingsmart.org/uri/..."  # Optional
)
```

**Attribute Facet:**
```python
attr = ids.Attribute(
    name="Name",
    value="EW-.*",  # Optional pattern/value
    cardinality="required"
)
```

**Classification Facet:**
```python
classification = ids.Classification(
    value="EF_25_10_25",
    system="Uniclass 2015",  # Optional
    cardinality="required"
)
```

**Material Facet:**
```python
material = ids.Material(
    value="Concrete",
    cardinality="required"
)
```

**PartOf Facet:**
```python
# Create parent entity reference
parent = ids.Entity(name="IFCSPACE")

# Create partOf facet
part_of = ids.PartOf(
    entity=parent,
    relation="IFCRELCONTAINEDINSPATIALSTRUCTURE",
    cardinality="required"
)
```

#### 7.2.4 Restriction Class: `ids.Restriction`

For complex value constraints:

```python
# Enumeration restriction
restriction = ids.Restriction(
    base="xs:string",
    options={
        "enumeration": ["REI30", "REI60", "REI90"]
    }
)

# Pattern restriction
restriction = ids.Restriction(
    base="xs:string",
    options={
        "pattern": "EW-[0-9]{3}"
    }
)

# Bounds restriction
restriction = ids.Restriction(
    base="xs:double",
    options={
        "minInclusive": 2.4,
        "maxInclusive": 3.0
    }
)

# Length restriction
restriction = ids.Restriction(
    base="xs:string",
    options={
        "minLength": 5,
        "maxLength": 50
    }
)

# Use in facet
prop = ids.Property(
    baseName="Height",
    value=restriction
)
```

### 7.3 MCP Tool Parameter Models (Pydantic)

While we use IfcTester for IDS models, we still use Pydantic for MCP tool parameters:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CreateIDSParams(BaseModel):
    """Parameters for create_ids tool."""
    title: str
    author: Optional[str] = None
    version: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    copyright: Optional[str] = None
    milestone: Optional[str] = None
    purpose: Optional[str] = None

class AddSpecificationParams(BaseModel):
    """Parameters for add_specification tool."""
    session_id: str
    name: str
    ifc_versions: List[str]
    identifier: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    min_occurs: int = 0
    max_occurs: int | str = "unbounded"

class AddPropertyFacetParams(BaseModel):
    """Parameters for add_property_facet tool."""
    session_id: str
    spec_id: str
    location: str  # "applicability" or "requirements"
    property_name: str
    property_set: Optional[str] = None
    data_type: Optional[str] = None
    cardinality: str = "required"

# ... more parameter models for each tool
```

### 7.4 Helper Functions for Model Conversion

```python
def create_ids_from_params(params: CreateIDSParams) -> ids.Ids:
    """Convert MCP parameters to IfcTester Ids object."""
    return ids.Ids(
        title=params.title,
        author=params.author,
        version=params.version,
        date=params.date,
        description=params.description,
        copyright=params.copyright,
        milestone=params.milestone,
        purpose=params.purpose
    )

def create_specification_from_params(params: AddSpecificationParams) -> ids.Specification:
    """Convert MCP parameters to IfcTester Specification."""
    return ids.Specification(
        name=params.name,
        ifcVersion=params.ifc_versions,
        identifier=params.identifier,
        description=params.description,
        instructions=params.instructions,
        minOccurs=params.min_occurs,
        maxOccurs=params.max_occurs
    )

def create_property_facet_from_params(params: AddPropertyFacetParams) -> ids.Property:
    """Convert MCP parameters to IfcTester Property facet."""
    return ids.Property(
        baseName=params.property_name,
        propertySet=params.property_set,
        dataType=params.data_type,
        cardinality=params.cardinality if params.location == "requirements" else None
    )
```

---

## 8. Validation and Compliance

### 8.1 Simplified Validation with IfcTester

**Key Advantage**: IfcTester handles most validation automatically, significantly simplifying our implementation.

### 8.2 Multi-Level Validation Strategy

#### Level 1: MCP Tool Parameter Validation (Pydantic)

- Validates MCP tool parameters only
- Catches type errors, missing required fields
- Ensures valid input before creating IfcTester objects

```python
from pydantic import BaseModel, validator

class AddSpecificationParams(BaseModel):
    session_id: str
    name: str
    ifc_versions: list[str]

    @validator('ifc_versions')
    def validate_ifc_versions(cls, v):
        """Validate IFC versions."""
        valid = {"IFC2X3", "IFC4", "IFC4X3"}
        for version in v:
            if version.upper() not in valid:
                raise ValueError(
                    f"Invalid IFC version: {version}. "
                    f"Valid versions: {', '.join(valid)}"
                )
        return [version.upper() for version in v]
```

#### Level 2: IfcTester Internal Validation

- **Built-in to IfcTester**: Automatically validates IDS structure
- Enforces IDS specification rules
- Validates facet relationships
- Ensures compliance during object construction

```python
from ifctester import ids

# IfcTester validates automatically
try:
    spec = ids.Specification(
        name="Test",
        ifcVersion=["INVALID"]  # IfcTester will raise error
    )
except Exception as e:
    # Handle IfcTester validation errors
    print(f"Validation failed: {e}")
```

#### Level 3: XSD Schema Validation (IfcTester Built-in)

- **Handled by IfcTester**: Uses built-in XSD validation
- Can be explicitly invoked with `validate=True` parameter
- Ensures 100% compliance with official schema

```python
from ifctester import ids

# Load with validation
try:
    my_ids = ids.open("file.ids", validate=True)
except ids.IdsXmlValidationError as e:
    print(f"XSD validation failed: {e.xml_error}")

# Or validate explicitly using ids.get_schema()
schema = ids.get_schema()
# IfcTester uses this internally
```

#### Level 4: Business Logic Validation (Our Layer)

Lightweight validation for AI-agent-specific concerns:

```python
class ValidationService:
    """Lightweight business logic validation."""

    def validate_session_exists(self, session_id: str) -> None:
        """Ensure session exists."""
        if session_id not in _sessions:
            raise ToolError(f"Session not found: {session_id}")

    def validate_specification_exists(
        self,
        ids_obj: ids.Ids,
        spec_id: str
    ) -> ids.Specification:
        """Find and return specification by ID."""
        for spec in ids_obj.specifications:
            if getattr(spec, 'identifier', None) == spec_id:
                return spec
        raise ToolError(f"Specification not found: {spec_id}")

    def validate_can_export(self, ids_obj: ids.Ids) -> None:
        """Check if IDS is ready for export."""
        if not ids_obj.specifications:
            raise ToolError("Cannot export: IDS has no specifications")

        for spec in ids_obj.specifications:
            if not spec.applicability:
                raise ToolError(
                    f"Specification '{spec.name}' has no applicability facets"
                )
```

### 8.3 Validation Checkpoints

Validation occurs at these points:

1. **Tool Input** (Pydantic): Validate MCP tool parameters
2. **Object Creation** (IfcTester): IfcTester validates during instantiation
3. **Pre-Export** (Business Logic): Check IDS completeness
4. **Export** (IfcTester XSD): Validate against schema when calling `to_xml()`
5. **On-Demand** (`validate_ids()` tool): Explicit validation check

### 8.4 Validation Tool Implementation

```python
@mcp.tool
def validate_ids(session_id: str) -> dict:
    """
    Validate IDS document.

    Uses IfcTester's built-in validation.
    """
    try:
        # Validate session
        if session_id not in _sessions:
            raise ToolError(f"Session not found: {session_id}")

        ids_obj = _sessions[session_id]

        # Check basic completeness
        if not ids_obj.specifications:
            return {
                "valid": False,
                "errors": ["IDS has no specifications"]
            }

        # Validate by attempting to serialize
        try:
            xml_string = ids_obj.to_string()
            # If this succeeds, IDS is valid
            return {
                "valid": True,
                "errors": [],
                "specifications_count": len(ids_obj.specifications)
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)]
            }

    except ToolError as e:
        raise
    except Exception as e:
        raise ToolError(f"Validation error: {str(e)}")
```

### 8.5 IFC Model Validation (Bonus Feature)

IfcTester can validate IFC models against IDS specifications:

```python
@mcp.tool
def validate_ifc_model(
    session_id: str,
    ifc_file_path: str,
    report_format: str = "json"  # "console", "json", "html"
) -> dict:
    """
    Validate an IFC model against the IDS specifications.

    This is a bonus feature leveraging IfcTester's validation capabilities.
    """
    import ifcopenshell
    from ifctester import reporter

    try:
        # Get IDS
        ids_obj = _sessions[session_id]

        # Load IFC file
        ifc_file = ifcopenshell.open(ifc_file_path)

        # Validate
        ids_obj.validate(ifc_file)

        # Generate report
        if report_format == "console":
            reporter.Console(ids_obj).report()
            return {"status": "validation_complete"}

        elif report_format == "json":
            json_reporter = reporter.Json(ids_obj)
            json_reporter.report()
            return {
                "status": "validation_complete",
                "report": json_reporter.to_string()
            }

        elif report_format == "html":
            html_reporter = reporter.Html(ids_obj)
            html_reporter.report()
            return {
                "status": "validation_complete",
                "html": html_reporter.to_string()
            }

    except FileNotFoundError:
        raise ToolError(f"IFC file not found: {ifc_file_path}")
    except Exception as e:
        raise ToolError(f"IFC validation error: {str(e)}")
```

### 8.6 Error Reporting

Errors are reported with clear, actionable messages:

```python
from pydantic import BaseModel
from typing import List, Optional

class ValidationResult(BaseModel):
    """Validation result from validate_ids tool."""
    valid: bool
    errors: List[str]
    warnings: List[str] = []
    specifications_count: Optional[int] = None
```

---

## 9. Error Handling Strategy

### 9.1 Error Categories

1. **User Input Errors** (ToolError)
   - Invalid parameters
   - Missing required fields
   - Business rule violations

2. **System Errors** (masked in production)
   - XML generation failures
   - Schema loading errors
   - Internal bugs

3. **Validation Errors** (ToolError)
   - Schema validation failures
   - Constraint violations

### 9.2 Error Handling Pattern

```python
from fastmcp import ToolError

@mcp.tool
def add_specification(
    session_id: str,
    name: str,
    ifc_versions: list[str],
    **kwargs
) -> dict:
    """Add specification."""
    try:
        # Validate session
        if session_id not in _sessions:
            raise ToolError(f"Invalid session ID: {session_id}")

        # Validate IFC versions
        valid_versions = {"IFC2X3", "IFC4", "IFC4X3"}
        for version in ifc_versions:
            if version.upper() not in valid_versions:
                raise ToolError(
                    f"Invalid IFC version: {version}. "
                    f"Valid versions: {', '.join(valid_versions)}"
                )

        # Create specification
        spec = Specification(
            name=name,
            ifc_versions=[v.upper() for v in ifc_versions],
            **kwargs
        )

        # Add to document
        doc = _sessions[session_id]
        spec_id = doc.add_specification(spec)

        return {
            "status": "added",
            "spec_id": spec_id,
            "ifc_versions": spec.ifc_versions
        }

    except ToolError:
        # Re-raise ToolErrors as-is
        raise
    except ValueError as e:
        # Convert validation errors to ToolError
        raise ToolError(f"Validation error: {str(e)}")
    except Exception as e:
        # Log internal errors
        logger.exception("Internal error in add_specification")
        # Mask in production
        if mcp.config.mask_error_details:
            raise ToolError("An internal error occurred")
        else:
            raise ToolError(f"Internal error: {str(e)}")
```

### 9.3 Logging Strategy

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ids_mcp_server")

# Log all tool calls
logger.info(f"Tool called: add_specification(session_id={session_id}, name={name})")

# Log validation failures
logger.warning(f"Validation failed: {errors}")

# Log errors
logger.error(f"Error in tool execution: {str(e)}")
logger.exception("Full stack trace")
```

---

## 10. Testing Strategy - Test-Driven Development (TDD)

### 10.1 TDD Methodology

**This project uses Test-Driven Development (TDD) exclusively.** All features must be developed following the Red-Green-Refactor cycle.

#### 10.1.1 TDD Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD Cycle                                 │
│                                                              │
│  1. RED: Write a failing test                               │
│     ├─ Define expected behavior                             │
│     ├─ Write test that exercises new functionality          │
│     └─ Run test: MUST FAIL (if it passes, test is wrong)    │
│                                                              │
│  2. GREEN: Make the test pass                               │
│     ├─ Write minimal implementation                         │
│     ├─ Run test: MUST PASS                                  │
│     └─ If fails: FIX IMPLEMENTATION (not the test!)         │
│                                                              │
│  3. REFACTOR: Improve code quality                          │
│     ├─ Clean up implementation                              │
│     ├─ Remove duplication                                   │
│     └─ All tests still pass                                 │
│                                                              │
│  4. REPEAT: For next feature                                │
└─────────────────────────────────────────────────────────────┘
```

#### 10.1.2 TDD Rules

1. **Write tests FIRST** - No production code without a failing test
2. **Tests must fail initially** - Proves test is testing something
3. **Fix implementation, not tests** - If tests fail after implementation, fix the code
4. **One test at a time** - Focus on one behavior per test
5. **Validate with IfcTester** - Use IfcTester API to ensure correctness

### 10.2 IfcTester-Based Validation

**Critical**: All tests must validate using IfcTester API to ensure:
- MCP input is correctly transformed to IfcTester objects
- IfcTester objects are correctly configured
- Generated IDS XML is valid and correct

#### 10.2.1 Three-Level Validation

```python
from ifctester import ids
from fastmcp import FastMCP
from fastmcp.client import Client
import pytest

async def test_create_specification_with_property():
    """
    Test creating a specification with property requirement.

    Validates at 3 levels:
    1. MCP tool input → IfcTester object creation
    2. IfcTester object structure
    3. Generated IDS XML output
    """
    # LEVEL 1: MCP Input → IfcTester
    mcp = create_ids_mcp_server()

    async with Client(mcp) as client:
        # Create IDS
        result = await client.call_tool("create_ids", {
            "title": "Test IDS"
        })

        # Add specification
        result = await client.call_tool("add_specification", {
            "name": "Wall Fire Rating",
            "ifc_versions": ["IFC4"]
        })
        spec_id = result["spec_id"]

        # Add property facet
        result = await client.call_tool("add_property_facet", {
            "spec_id": spec_id,
            "location": "requirements",
            "property_name": "FireRating",
            "property_set": "Pset_WallCommon",
            "cardinality": "required"
        })

    # LEVEL 2: Validate IfcTester Object Structure
    # Access the internal IfcTester object from session
    ids_obj = _session_storage[client.session_id]

    # Verify ids.Ids object
    assert isinstance(ids_obj, ids.Ids)
    assert ids_obj.info["title"] == "Test IDS"

    # Verify ids.Specification object
    assert len(ids_obj.specifications) == 1
    spec = ids_obj.specifications[0]
    assert isinstance(spec, ids.Specification)
    assert spec.name == "Wall Fire Rating"
    assert spec.ifcVersion == ["IFC4"]

    # Verify ids.Property facet
    assert len(spec.requirements) == 1
    prop = spec.requirements[0]
    assert isinstance(prop, ids.Property)
    assert prop.baseName == "FireRating"
    assert prop.propertySet == "Pset_WallCommon"
    assert prop.cardinality == "required"

    # LEVEL 3: Validate Generated XML
    xml_string = ids_obj.to_string()

    # Validate against XSD schema
    schema = ids.get_schema()
    # IfcTester's built-in validation
    validated_ids = ids.from_string(xml_string, validate=True)
    assert validated_ids is not None

    # Verify XML contains expected elements
    assert "<ids:title>Test IDS</ids:title>" in xml_string
    assert "<ids:name>Wall Fire Rating</ids:name>" in xml_string
    assert 'ifcVersion="IFC4"' in xml_string or 'ifcVersion="IFC4 "' in xml_string
    assert "<ids:baseName>" in xml_string
    assert "FireRating" in xml_string
```

### 10.3 Test Categories and Examples

#### 10.3.1 Unit Tests - IfcTester Object Creation

Test that MCP tools correctly create IfcTester objects.

**Example: Entity Facet Creation**
```python
import pytest
from ifctester import ids

def test_entity_facet_creation():
    """
    RED: Write test first - entity facet with predefined type.
    Test MUST fail initially (no implementation yet).
    """
    # Create entity facet using our factory
    from facet_factory import create_entity_facet

    # This will fail initially - function doesn't exist yet
    facet = create_entity_facet(
        entity_name="IFCWALL",
        predefined_type="SOLIDWALL"
    )

    # Validate using IfcTester API
    assert isinstance(facet, ids.Entity)
    assert facet.name == "IFCWALL"
    assert facet.predefinedType == "SOLIDWALL"

# GREEN: Now implement create_entity_facet() to make test pass
# Implementation in facet_factory.py:
def create_entity_facet(entity_name: str, predefined_type: str = None) -> ids.Entity:
    return ids.Entity(
        name=entity_name,
        predefinedType=predefined_type
    )
```

**Example: Restriction Creation**
```python
def test_enumeration_restriction():
    """
    Test creating enumeration restriction for property values.
    """
    from restriction_factory import create_enumeration_restriction

    # Create restriction
    restriction = create_enumeration_restriction(
        base_type="xs:string",
        values=["REI30", "REI60", "REI90"]
    )

    # Validate using IfcTester API
    assert isinstance(restriction, ids.Restriction)
    assert restriction.base == "xs:string"
    assert "enumeration" in restriction.options
    assert restriction.options["enumeration"] == ["REI30", "REI60", "REI90"]
```

#### 10.3.2 Component Tests - Business Logic

Test that business logic correctly orchestrates IfcTester objects.

```python
def test_add_specification_to_session():
    """
    Test adding specification to session storage.
    Validates session management and IfcTester integration.
    """
    from session_manager import add_specification_to_session
    from ifctester import ids

    # Setup session with empty IDS
    session_id = "test-session"
    _session_storage[session_id] = ids.Ids(title="Test")

    # Add specification
    spec_id = add_specification_to_session(
        session_id=session_id,
        name="Wall Requirements",
        ifc_versions=["IFC4", "IFC4X3"]
    )

    # Validate using IfcTester API
    ids_obj = _session_storage[session_id]
    assert len(ids_obj.specifications) == 1

    spec = ids_obj.specifications[0]
    assert isinstance(spec, ids.Specification)
    assert spec.name == "Wall Requirements"
    assert set(spec.ifcVersion) == {"IFC4", "IFC4X3"}
```

#### 10.3.3 Integration Tests - Full MCP Workflows

Test complete workflows from MCP tool calls to valid IDS files.

```python
@pytest.mark.asyncio
async def test_complete_ids_creation_workflow():
    """
    Integration test: Create complete IDS file with all facet types.

    This test validates:
    1. MCP tool calls work correctly
    2. IfcTester objects are created properly
    3. Final IDS XML is valid
    """
    mcp = create_ids_mcp_server()

    async with Client(mcp) as client:
        # 1. Create IDS document
        result = await client.call_tool("create_ids", {
            "title": "Project Requirements",
            "author": "test@example.com",
            "description": "Complete test of all features"
        })
        assert result["status"] == "created"

        # 2. Add specification
        result = await client.call_tool("add_specification", {
            "name": "Wall Fire Rating",
            "ifc_versions": ["IFC4"]
        })
        spec_id = result["spec_id"]

        # 3. Add entity facet to applicability
        await client.call_tool("add_entity_facet", {
            "spec_id": spec_id,
            "location": "applicability",
            "entity_name": "IFCWALL"
        })

        # 4. Add property facet to requirements
        await client.call_tool("add_property_facet", {
            "spec_id": spec_id,
            "location": "requirements",
            "property_name": "FireRating",
            "property_set": "Pset_WallCommon",
            "cardinality": "required"
        })

        # 5. Add enumeration restriction
        await client.call_tool("add_enumeration_restriction", {
            "spec_id": spec_id,
            "parameter_name": "value",
            "base_type": "xs:string",
            "values": ["REI30", "REI60", "REI90"]
        })

        # 6. Export and validate
        result = await client.call_tool("export_ids")

        # Validate result
        assert result["status"] == "exported"
        assert "xml" in result
        xml_string = result["xml"]

    # CRITICAL: Validate using IfcTester
    # This ensures the generated XML is truly valid
    validated_ids = ids.from_string(xml_string, validate=True)

    # Verify structure using IfcTester API
    assert validated_ids.info["title"] == "Project Requirements"
    assert len(validated_ids.specifications) == 1

    spec = validated_ids.specifications[0]
    assert spec.name == "Wall Fire Rating"
    assert len(spec.applicability) == 1
    assert isinstance(spec.applicability[0], ids.Entity)
    assert len(spec.requirements) == 1
    assert isinstance(spec.requirements[0], ids.Property)
```

#### 10.3.4 Validation Tests - Against buildingSMART Examples

Test that we can load and validate official IDS examples.

```python
def test_load_buildingsmart_example():
    """
    Test loading official buildingSMART IDS examples.
    Ensures our implementation can handle real-world IDS files.
    """
    # Load example from buildingSMART repository
    example_path = "tests/examples/buildingsmart/wall-fire-rating.ids"

    # Use IfcTester to load and validate
    ids_obj = ids.open(example_path, validate=True)

    # Verify it loaded correctly
    assert ids_obj is not None
    assert len(ids_obj.specifications) > 0

    # Re-export and validate round-trip
    xml_string = ids_obj.to_string()
    reloaded = ids.from_string(xml_string, validate=True)

    # Verify round-trip integrity
    assert reloaded.info["title"] == ids_obj.info["title"]
    assert len(reloaded.specifications) == len(ids_obj.specifications)
```

### 10.4 Test Organization

```
tests/
├── unit/
│   ├── test_facet_creation.py       # Test individual facet creation
│   ├── test_restriction_creation.py  # Test restriction objects
│   └── test_ids_creation.py          # Test IDS object creation
├── component/
│   ├── test_session_manager.py       # Test session management
│   ├── test_specification_builder.py # Test specification building
│   └── test_validation_service.py    # Test validation logic
├── integration/
│   ├── test_mcp_tools.py             # Test all MCP tools
│   ├── test_complete_workflows.py    # Test end-to-end scenarios
│   └── test_context_integration.py   # Test FastMCP Context usage
├── validation/
│   ├── test_buildingsmart_examples.py # Test official examples
│   ├── test_xsd_compliance.py         # Test XSD validation
│   └── test_round_trip.py             # Test load→modify→save
└── fixtures/
    ├── example_ids_files/             # Sample IDS files
    └── expected_outputs/              # Expected XML outputs
```

### 10.5 Test Coverage Requirements

**Mandatory Coverage Targets:**

| Test Type | Coverage | Validation Method |
|-----------|----------|-------------------|
| Unit Tests | 95%+ | IfcTester API assertions |
| Component Tests | 100% of business logic | IfcTester object validation |
| Integration Tests | All MCP tools | XML validation via IfcTester |
| Validation Tests | All official examples | XSD schema validation |

**Coverage Enforcement:**
```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-fail-under=95

# All tests must validate using IfcTester
pytest -v --strict-markers
```

### 10.6 TDD Example: Implementing a New Tool

**Scenario**: Add support for Material facets

**Step 1: RED - Write Failing Test**
```python
@pytest.mark.asyncio
async def test_add_material_facet():
    """Test adding material facet to specification."""
    mcp = create_ids_mcp_server()

    async with Client(mcp) as client:
        # Setup
        await client.call_tool("create_ids", {"title": "Test"})
        result = await client.call_tool("add_specification", {
            "name": "Concrete Walls",
            "ifc_versions": ["IFC4"]
        })
        spec_id = result["spec_id"]

        # Add material facet - THIS WILL FAIL (tool doesn't exist yet)
        result = await client.call_tool("add_material_facet", {
            "spec_id": spec_id,
            "location": "requirements",
            "material_value": "Concrete",
            "cardinality": "required"
        })

        # Validate using IfcTester
        ids_obj = _session_storage[client.session_id]
        spec = ids_obj.specifications[0]

        assert len(spec.requirements) == 1
        material = spec.requirements[0]
        assert isinstance(material, ids.Material)
        assert material.value == "Concrete"
        assert material.cardinality == "required"

# Run test: pytest -v test_material_facet.py
# Result: FAIL - "add_material_facet" tool not found
# ✅ Test fails as expected!
```

**Step 2: GREEN - Implement to Pass**
```python
@mcp.tool
async def add_material_facet(
    spec_id: str,
    location: str,
    material_value: str,
    ctx: Context,
    cardinality: str = "required"
) -> dict:
    """Add material facet to specification."""
    # Get session
    ids_obj = await get_or_create_session(ctx)

    # Find specification
    spec = find_specification(ids_obj, spec_id)

    # Create IfcTester Material facet
    material = ids.Material(
        value=material_value,
        cardinality=cardinality if location == "requirements" else None
    )

    # Add to appropriate section
    if location == "applicability":
        spec.applicability.append(material)
    else:
        spec.requirements.append(material)

    await ctx.info(f"Added material facet: {material_value}")

    return {
        "status": "added",
        "facet_type": "material",
        "spec_id": spec_id
    }

# Run test: pytest -v test_material_facet.py
# Result: PASS
# ✅ Implementation works!
```

**Step 3: REFACTOR - If Needed**
```python
# Extract common facet-adding logic
def add_facet_to_spec(spec, facet, location):
    """Common logic for adding facets."""
    if location == "applicability":
        spec.applicability.append(facet)
    else:
        spec.requirements.append(facet)
```

### 10.7 Continuous Testing

**Pre-commit Hooks:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run all tests
pytest tests/ -v

# Check coverage
pytest --cov=src --cov-fail-under=95

# Validate against IfcTester
pytest tests/validation/ -v

# If any fail, prevent commit
if [ $? -ne 0 ]; then
    echo "Tests failed! Fix before committing."
    exit 1
fi
```

**CI/CD Pipeline:**
```yaml
# .github/workflows/test.yml
name: TDD Validation
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: |
          pip install fastmcp ifctester pytest pytest-cov
      - name: Run TDD tests
        run: |
          pytest tests/ -v --cov=src --cov-fail-under=95
      - name: Validate with IfcTester
        run: |
          pytest tests/validation/ -v --strict-markers
```

### 10.8 Key Testing Principles

1. **Always write tests FIRST** - No exceptions
2. **Tests must fail initially** - Proves they test something
3. **Fix implementation, not tests** - Tests define correct behavior
4. **Validate with IfcTester API** - Ensures real correctness
5. **Test at all levels** - MCP input → IfcTester objects → XML output
6. **Use official examples** - Validate against buildingSMART test suite
7. **Maintain high coverage** - 95%+ for confidence
8. **Run tests frequently** - On every change
9. **Automate validation** - Pre-commit hooks and CI/CD

---

## 11. Deployment Considerations

### 11.1 Development Environment

**Local Development:**
```bash
# Install dependencies
pip install fastmcp lxml pydantic

# Run server
python -m ids_mcp_server
```

**Claude Desktop Integration:**
```json
{
  "mcpServers": {
    "ids-mcp": {
      "command": "python",
      "args": ["-m", "ids_mcp_server"],
      "env": {
        "IDS_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 11.2 Production Deployment

**Configuration:**
```python
mcp = FastMCP(
    "IDS MCP Server",
    mask_error_details=True,  # Hide internal errors
    rate_limit="100/hour"     # Rate limiting
)
```

**Environment Variables:**
```bash
IDS_LOG_LEVEL=WARNING
IDS_XSD_CACHE_DIR=/var/cache/ids-mcp
IDS_SESSION_TIMEOUT=3600
```

### 11.3 Performance Considerations

1. **XSD Caching**: Cache downloaded XSD schema locally
2. **Session Cleanup**: Implement timeout-based session cleanup
3. **Memory Management**: Limit session count, document size
4. **XML Generation**: Stream large documents instead of in-memory

### 11.4 Security Considerations

1. **Input Validation**: All inputs validated via Pydantic
2. **Output Sanitization**: XML special characters escaped
3. **Rate Limiting**: Prevent abuse
4. **Error Masking**: No sensitive information in errors
5. **Session Isolation**: Each session independent

---

## 12. Future Enhancements

### 12.1 Phase 2 Features

1. **IDS Import**: Parse existing IDS files
2. **Template Library**: Pre-built specification templates
3. **Validation Reports**: Detailed HTML/PDF reports
4. **Batch Operations**: Create multiple specifications at once

### 12.2 Phase 3 Features

1. **IFC Validation**: Validate IFC models against IDS
2. **Interactive Builder**: Web UI for visual IDS building
3. **Version Control**: Track IDS file changes over time
4. **Collaboration**: Multi-user editing

### 12.3 Integration Opportunities

1. **BIM Software**: Plugins for Revit, ArchiCAD, etc.
2. **Model Checkers**: Integration with Solibri, ifctester
3. **bSDD Integration**: Automatic property/classification lookup
4. **CI/CD Pipelines**: Automated IFC validation in build pipelines

---

## 13. Implementation Roadmap

### Phase 1: Core Functionality (MVP)

**Week 1-2: Foundation**
- [ ] Set up project structure
- [ ] Implement Pydantic data models
- [ ] Create FastMCP server skeleton
- [ ] Implement session management

**Week 3-4: Basic Tools**
- [ ] Document management tools (create, export)
- [ ] Specification management tools
- [ ] Entity facet support
- [ ] Property facet support
- [ ] Simple value restrictions

**Week 5-6: Advanced Features**
- [ ] All facet types (attribute, classification, material, partOf)
- [ ] All restriction types (enumeration, pattern, bounds, length)
- [ ] XML generation with lxml
- [ ] XSD validation

**Week 7-8: Testing & Documentation**
- [ ] Unit tests (90% coverage)
- [ ] Integration tests
- [ ] Validate against buildingSMART examples
- [ ] User documentation

### Phase 2: Enhancement & Polish

**Week 9-10: Advanced Validation**
- [ ] Comprehensive business logic validation
- [ ] Detailed error messages
- [ ] Validation reports

**Week 11-12: Production Readiness**
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Deployment documentation
- [ ] Production configuration

---

## 14. Appendix

### 14.1 IFC Version Reference

| Version | Year | Full Name | Schema URL |
|---------|------|-----------|------------|
| IFC2X3 | 2006 | IFC 2x3 TC1 | https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ |
| IFC4 | 2013 | IFC 4.0.2.1 | https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/ |
| IFC4X3 | 2024 | IFC 4.3.2.0 | https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/ |

### 14.2 Common IFC Entities

- IFCWALL
- IFCDOOR
- IFCWINDOW
- IFCSLAB
- IFCBEAM
- IFCCOLUMN
- IFCSPACE
- IFCBUILDING
- IFCBUILDINGSTOREY
- IFCSITE

### 14.3 Common Property Sets

- Pset_WallCommon
- Pset_DoorCommon
- Pset_WindowCommon
- Pset_SpaceCommon
- Qto_WallBaseQuantities
- Qto_DoorBaseQuantities

### 14.4 Common IFC Data Types

- IFCLABEL
- IFCTEXT
- IFCBOOLEAN
- IFCINTEGER
- IFCREAL
- IFCLENGTHMEASURE
- IFCAREAMEASURE
- IFCVOLUMEMEASURE

### 14.5 References

1. **buildingSMART IDS GitHub**: https://github.com/buildingSMART/IDS
2. **IDS 1.0 Standard**: https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/
3. **IDS XSD Schema**: https://standards.buildingsmart.org/IDS/1.0/ids.xsd
4. **IDS Documentation**: https://github.com/buildingSMART/IDS/tree/development/Documentation
5. **IfcTester Documentation**: https://docs.ifcopenshell.org/ifctester.html
6. **IfcOpenShell**: https://ifcopenshell.org/
7. **IfcOpenShell GitHub**: https://github.com/IfcOpenShell/IfcOpenShell
8. **FastMCP Framework**: https://github.com/jlowin/fastmcp
9. **FastMCP Documentation**: https://gofastmcp.com/

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-01 | IDS MCP Design Team | Initial design specification |
| 2.0 | 2025-11-01 | IDS MCP Design Team | **Major Update**: Integrated IfcTester library for IDS operations. Replaced custom XML generation layer with IfcTester. Simplified architecture by using IfcTester's native models. Added IDS import capability (load_ids tool). Added IFC model validation bonus feature. Simplified validation strategy leveraging IfcTester's built-in validation. |
| 2.1 | 2025-11-01 | IDS MCP Design Team | **Context Integration**: Implemented FastMCP Context for automatic session management. Removed manual session_id parameters from all tools. Updated section 5.3 with comprehensive Context implementation guide. All tools now async and use `ctx: Context` for automatic session tracking, logging, and progress reporting. Cleaner API with automatic session handling. Added session cleanup strategy. Updated tool signatures throughout section 6. |
| 2.2 | 2025-11-01 | IDS MCP Design Team | **TDD Methodology**: Complete rewrite of Section 10 (Testing Strategy) to enforce Test-Driven Development. Added mandatory TDD workflow (Red-Green-Refactor). Introduced three-level validation using IfcTester API (MCP input → IfcTester objects → XML output). Added comprehensive test examples for all test categories. Included full TDD implementation example. Added test organization structure, coverage requirements (95%+), pre-commit hooks, and CI/CD pipeline configuration. All tests must validate using IfcTester API to ensure correctness at every level. |

---

**END OF DOCUMENT**
