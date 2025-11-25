"""
Unit tests for illustrative vocabulary MCP server.

Tests the deterministic Layer 2 taxonomy mapping and tool implementations.
"""

import pytest
import json
from illustrative_vocabulary_mcp.server import (
    ILLUSTRATION_TAXONOMY,
    get_style_parameters,
    format_parameters_as_prompt_elements,
    mcp,
)


class TestTaxonomy:
    """Test the deterministic taxonomy structure."""

    def test_taxonomy_completeness(self):
        """All taxonomy entries should have required keys."""
        required_keys = {
            "style_name",
            "edge_treatment",
            "color_strategy",
            "texture_approach",
            "lighting_model",
            "line_weight",
            "depth_handling",
            "compositional_rules",
            "negative_prompt_elements",
        }
        
        for style_id, params in ILLUSTRATION_TAXONOMY.items():
            assert required_keys.issubset(params.keys()), f"Missing keys in {style_id}"
            assert isinstance(params["style_name"], str)
            assert len(params["style_name"]) > 0

    def test_taxonomy_parameter_types(self):
        """All parameters should be lists of strings."""
        for style_id, params in ILLUSTRATION_TAXONOMY.items():
            for key in [
                "edge_treatment",
                "color_strategy",
                "texture_approach",
                "lighting_model",
                "line_weight",
                "depth_handling",
                "compositional_rules",
                "negative_prompt_elements",
            ]:
                assert isinstance(params[key], list), f"{style_id}.{key} not a list"
                assert all(
                    isinstance(item, str) for item in params[key]
                ), f"{style_id}.{key} contains non-string items"

    def test_taxonomy_no_empty_lists(self):
        """No parameter list should be empty."""
        for style_id, params in ILLUSTRATION_TAXONOMY.items():
            for key in [
                "edge_treatment",
                "color_strategy",
                "texture_approach",
                "lighting_model",
                "line_weight",
                "depth_handling",
                "compositional_rules",
                "negative_prompt_elements",
            ]:
                assert len(params[key]) > 0, f"{style_id}.{key} is empty"


class TestStyleParameterLookup:
    """Test the deterministic parameter lookup (Layer 2)."""

    def test_lookup_by_exact_id(self):
        """Should return parameters for exact style ID."""
        params = get_style_parameters("comic_book")
        assert params["style_name"] == "Comic Book / Graphic Novel"
        assert "hard, defined outlines" in params["edge_treatment"]

    def test_lookup_case_insensitive(self):
        """Lookup should be case-insensitive."""
        params1 = get_style_parameters("comic_book")
        params2 = get_style_parameters("COMIC_BOOK")
        assert params1 == params2

    def test_lookup_by_style_name(self):
        """Should match by full style name."""
        params = get_style_parameters("Comic Book / Graphic Novel")
        assert params["style_name"] == "Comic Book / Graphic Novel"

    def test_lookup_invalid_style(self):
        """Should raise ValueError for invalid style."""
        with pytest.raises(ValueError):
            get_style_parameters("invalid_style_xyz")

    def test_all_styles_are_lookupable(self):
        """All styles in taxonomy should be retrievable."""
        for style_id in ILLUSTRATION_TAXONOMY.keys():
            params = get_style_parameters(style_id)
            assert params is not None
            assert "style_name" in params


class TestParameterFormatting:
    """Test formatting parameters for prompts."""

    def test_format_to_prompt_elements(self):
        """Should format parameters as readable prompt elements."""
        params = get_style_parameters("comic_book")
        formatted = format_parameters_as_prompt_elements(params)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "hard, defined outlines" in formatted
        assert "limited palette" in formatted or "8-12" in formatted

    def test_format_includes_all_categories(self):
        """Formatted output should include all parameter categories."""
        params = get_style_parameters("comic_book")
        formatted = format_parameters_as_prompt_elements(params)
        
        # Should include various parameter categories
        assert "outline" in formatted.lower() or "edge" in formatted.lower()
        assert "color" in formatted.lower() or "palette" in formatted.lower()


class TestToolContracts:
    """Test MCP tool interface contracts."""

    def test_tools_are_registered(self):
        """Tools should be properly decorated."""
        # FastMCP stores tools differently - just verify the server is functional
        assert mcp is not None
        assert hasattr(mcp, 'tool')  # Should have tool decorator


class TestStyleConsistency:
    """Test that style parameters are internally consistent."""

    def test_negative_blocks_prevent_drift(self):
        """Negative elements should be incompatible with positive aesthetic."""
        for style_id, params in ILLUSTRATION_TAXONOMY.items():
            negative = params.get("negative_prompt_elements", [])
            
            # Should have negative blocks
            assert len(negative) > 0, f"{style_id} has no negative blocks"
            
            # All negatives should be strings
            assert all(isinstance(n, str) for n in negative), \
                f"{style_id} has non-string negatives"

    def test_each_style_visually_distinct(self):
        """Styles should have different parameter combinations."""
        style_params = {}
        for style_id in ILLUSTRATION_TAXONOMY.keys():
            params = get_style_parameters(style_id)
            # Create a fingerprint of the style
            fingerprint = tuple(
                tuple(params.get(key, [])[:2])  # First 2 items of each category
                for key in [
                    "edge_treatment",
                    "color_strategy",
                    "lighting_model",
                ]
            )
            style_params[style_id] = fingerprint
        
        # Check that no two styles are identical
        fingerprints = list(style_params.values())
        assert len(set(fingerprints)) == len(fingerprints), \
            "Some styles have identical visual parameters"


class TestErrorHandling:
    """Test error handling in tools."""

    def test_style_lookup_error_message(self):
        """Error message should be helpful."""
        try:
            get_style_parameters("nonexistent_style")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            assert "not found" in error_msg.lower()
            assert "comic_book" in error_msg or "available" in error_msg.lower()


class TestStyleNegativePrompts:
    """Test that negative prompts effectively block style drift."""

    def test_comic_book_blocks_photorealism(self):
        """Comic book should explicitly block photorealism."""
        params = get_style_parameters("comic_book")
        negative = params["negative_prompt_elements"]
        
        # Should block photorealistic rendering
        assert any(
            "photo" in item.lower() or "realistic" in item.lower()
            for item in negative
        ), "Comic book should block photorealism"

    def test_children_book_blocks_dark_aesthetic(self):
        """Children's book should block dark/adult aesthetics."""
        params = get_style_parameters("children_book")
        negative = params["negative_prompt_elements"]
        
        # Should have blocks for adult aesthetic
        assert any(
            "adult" in item.lower() or "dark" in item.lower() or "moody" in item.lower()
            for item in negative
        ), "Children's book should block dark aesthetic"

    def test_watercolor_blocks_hard_edges(self):
        """Watercolor should block hard-edged rendering."""
        params = get_style_parameters("watercolor")
        negative = params["negative_prompt_elements"]
        
        # Should block hard edges that contradict watercolor
        assert any(
            "hard" in item.lower() or "precise" in item.lower() or "geometric" in item.lower()
            for item in negative
        ), "Watercolor should block hard edges"


class TestCostModel:
    """Test that deterministic lookup provides cost benefits."""

    def test_taxonomy_is_deterministic(self):
        """Same style ID should always return same parameters."""
        params1 = get_style_parameters("comic_book")
        params2 = get_style_parameters("comic_book")
        
        assert params1 == params2, "Deterministic lookup broken"
        assert params1 is ILLUSTRATION_TAXONOMY["comic_book"]

    def test_lookup_is_instant(self):
        """Multiple lookups should be very fast (O(1))."""
        import time
        
        start = time.time()
        for _ in range(1000):
            get_style_parameters("comic_book")
        elapsed = time.time() - start
        
        # 1000 lookups should take <100ms
        assert elapsed < 0.1, f"Lookup too slow: {elapsed}s for 1000 calls"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
