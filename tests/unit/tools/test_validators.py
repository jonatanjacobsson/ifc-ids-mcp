"""Tests for validation helper functions."""

import pytest
from ifctester import ids
from fastmcp.exceptions import ToolError

from ids_mcp_server.tools.validators import (
    validate_single_entity_in_applicability,
    validate_property_set_required,
    count_facets_by_type
)


class TestValidateSingleEntityInApplicability:
    """Tests for validate_single_entity_in_applicability function."""

    def test_allows_first_entity_facet(self):
        """Test that first entity facet is allowed."""
        spec = ids.Specification(name="Test", ifcVersion=["IFC4"])

        # Should not raise
        validate_single_entity_in_applicability(spec, "applicability")

    def test_blocks_second_entity_facet(self):
        """Test that second entity facet is blocked."""
        spec = ids.Specification(name="Test Spec", ifcVersion=["IFC4"])
        spec.applicability.append(ids.Entity(name="IFCWALL"))

        # Should raise with clear error message
        with pytest.raises(ToolError) as exc_info:
            validate_single_entity_in_applicability(spec, "applicability")

        error_msg = str(exc_info.value)
        assert "IDS 1.0 XSD constraint violation" in error_msg
        assert "Only ONE entity facet" in error_msg
        assert "WORKAROUND" in error_msg
        assert "Test Spec" in error_msg  # Includes spec name

    def test_allows_entity_in_requirements(self):
        """Test that entities in requirements section are allowed."""
        spec = ids.Specification(name="Test", ifcVersion=["IFC4"])
        spec.requirements.append(ids.Entity(name="IFCWALL"))
        spec.requirements.append(ids.Entity(name="IFCDOOR"))

        # Should not raise for requirements location
        validate_single_entity_in_applicability(spec, "requirements")

    def test_multiple_entities_in_requirements_allowed(self):
        """Test that multiple entity facets in requirements is allowed."""
        spec = ids.Specification(name="Test", ifcVersion=["IFC4"])

        # Add entity to applicability
        spec.applicability.append(ids.Entity(name="IFCWALL"))

        # Add multiple entities to requirements - should not raise
        validate_single_entity_in_applicability(spec, "requirements")
        spec.requirements.append(ids.Entity(name="IFCDOOR"))
        validate_single_entity_in_applicability(spec, "requirements")

    def test_counts_only_entity_facets(self):
        """Test that validator only counts entity facets, not other types."""
        spec = ids.Specification(name="Test", ifcVersion=["IFC4"])

        # Add non-entity facets to applicability
        spec.applicability.append(ids.Property(baseName="FireRating", propertySet="Pset_WallCommon"))
        spec.applicability.append(ids.Attribute(name="Name"))

        # First entity should still be allowed
        validate_single_entity_in_applicability(spec, "applicability")

        # Add first entity
        spec.applicability.append(ids.Entity(name="IFCWALL"))

        # Second entity should be blocked
        with pytest.raises(ToolError):
            validate_single_entity_in_applicability(spec, "applicability")


class TestValidatePropertySetRequired:
    """Tests for validate_property_set_required function."""

    def test_raises_error_with_none(self):
        """Test that None property_set raises error."""
        with pytest.raises(ToolError) as exc_info:
            validate_property_set_required(None, "FireRating")

        error_msg = str(exc_info.value)
        assert "property_set" in error_msg.lower()
        assert "required" in error_msg.lower()
        assert "FireRating" in error_msg  # Includes property name

    def test_raises_error_with_empty_string(self):
        """Test that empty property_set raises error."""
        with pytest.raises(ToolError):
            validate_property_set_required("", "FireRating")

    def test_raises_error_with_whitespace_only(self):
        """Test that whitespace-only property_set raises error."""
        with pytest.raises(ToolError):
            validate_property_set_required("   ", "FireRating")

        with pytest.raises(ToolError):
            validate_property_set_required("\t\n", "FireRating")

    def test_passes_with_valid_property_set(self):
        """Test that valid property_set passes validation."""
        # Should not raise
        validate_property_set_required("Pset_WallCommon", "FireRating")
        validate_property_set_required("Pset_Common", "CustomProperty")
        validate_property_set_required("MyCustomPropertySet", "MyProperty")

    def test_error_includes_common_property_sets(self):
        """Test that error message includes helpful examples."""
        with pytest.raises(ToolError) as exc_info:
            validate_property_set_required(None, "FireRating")

        error_msg = str(exc_info.value)
        assert "Pset_WallCommon" in error_msg
        assert "Pset_DoorCommon" in error_msg
        assert "Pset_WindowCommon" in error_msg
        assert "COMMON PROPERTY SETS" in error_msg

    def test_error_includes_custom_options(self):
        """Test that error message suggests custom property sets."""
        with pytest.raises(ToolError) as exc_info:
            validate_property_set_required(None, "CustomProp")

        error_msg = str(exc_info.value)
        assert "Pset_Common" in error_msg
        assert "CUSTOM PROPERTY SETS" in error_msg


class TestCountFacetsByType:
    """Tests for count_facets_by_type utility function."""

    def test_counts_entity_facets(self):
        """Test counting entity facets."""
        facets = [
            ids.Entity(name="IFCWALL"),
            ids.Property(baseName="FireRating", propertySet="Pset_WallCommon"),
            ids.Entity(name="IFCDOOR"),
            ids.Attribute(name="Name")
        ]

        assert count_facets_by_type(facets, ids.Entity) == 2

    def test_counts_property_facets(self):
        """Test counting property facets."""
        facets = [
            ids.Entity(name="IFCWALL"),
            ids.Property(baseName="FireRating", propertySet="Pset_WallCommon"),
            ids.Property(baseName="LoadBearing", propertySet="Pset_WallCommon"),
            ids.Attribute(name="Name")
        ]

        assert count_facets_by_type(facets, ids.Property) == 2

    def test_counts_attribute_facets(self):
        """Test counting attribute facets."""
        facets = [
            ids.Entity(name="IFCWALL"),
            ids.Attribute(name="Name"),
            ids.Attribute(name="Description")
        ]

        assert count_facets_by_type(facets, ids.Attribute) == 2

    def test_returns_zero_for_missing_type(self):
        """Test that zero is returned when no facets of type exist."""
        facets = [
            ids.Entity(name="IFCWALL"),
            ids.Property(baseName="FireRating", propertySet="Pset_WallCommon")
        ]

        assert count_facets_by_type(facets, ids.Classification) == 0
        assert count_facets_by_type(facets, ids.Material) == 0
        assert count_facets_by_type(facets, ids.PartOf) == 0

    def test_handles_empty_list(self):
        """Test that empty list returns zero."""
        assert count_facets_by_type([], ids.Entity) == 0
        assert count_facets_by_type([], ids.Property) == 0

    def test_counts_all_facet_types(self):
        """Test counting all different facet types."""
        facets = [
            ids.Entity(name="IFCWALL"),
            ids.Property(baseName="FireRating", propertySet="Pset_WallCommon"),
            ids.Attribute(name="Name"),
            ids.Classification(value="Ss_25_10_20", system="Uniclass"),
            ids.Material(value="Concrete"),
            ids.PartOf(name="IFCSPACE", relation="IFCRELCONTAINEDINSPATIALSTRUCTURE")
        ]

        assert count_facets_by_type(facets, ids.Entity) == 1
        assert count_facets_by_type(facets, ids.Property) == 1
        assert count_facets_by_type(facets, ids.Attribute) == 1
        assert count_facets_by_type(facets, ids.Classification) == 1
        assert count_facets_by_type(facets, ids.Material) == 1
        assert count_facets_by_type(facets, ids.PartOf) == 1


class TestValidatorsIntegration:
    """Integration tests for validators working together."""

    def test_realistic_specification_validation(self):
        """Test validators on a realistic specification."""
        spec = ids.Specification(
            name="Wall Fire Rating Requirements",
            ifcVersion=["IFC4"],
            description="Walls must have fire rating"
        )

        # First entity should be allowed
        validate_single_entity_in_applicability(spec, "applicability")
        spec.applicability.append(ids.Entity(name="IFCWALL"))

        # Second entity should fail
        with pytest.raises(ToolError):
            validate_single_entity_in_applicability(spec, "applicability")

        # Property without property_set should fail
        with pytest.raises(ToolError):
            validate_property_set_required(None, "FireRating")

        # Property with property_set should pass
        validate_property_set_required("Pset_WallCommon", "FireRating")
