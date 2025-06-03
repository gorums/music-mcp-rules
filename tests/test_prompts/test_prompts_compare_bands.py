import pytest
from src.prompts.compare_bands import get_compare_bands_prompt


class TestCompareBandsPrompt:
    """Test suite for the compare_bands prompt implementation."""

    def test_default_prompt_structure(self):
        """Test that the default prompt has correct structure."""
        prompt = get_compare_bands_prompt()
        
        # Verify basic structure
        assert isinstance(prompt, dict)
        assert "name" in prompt
        assert "description" in prompt
        assert "arguments" in prompt
        assert "messages" in prompt
        
        # Verify prompt details
        assert prompt["name"] == "compare_bands"
        assert "comparison" in prompt["description"].lower()
        assert len(prompt["arguments"]) == 3  # band_names, comparison_aspects, comparison_scope
        assert len(prompt["messages"]) == 1
        assert prompt["messages"][0]["role"] == "user"

    def test_prompt_arguments_structure(self):
        """Test that prompt arguments are correctly structured."""
        prompt = get_compare_bands_prompt()
        args = prompt["arguments"]
        
        # Check all expected arguments exist
        arg_names = [arg["name"] for arg in args]
        assert "band_names" in arg_names
        assert "comparison_aspects" in arg_names
        assert "comparison_scope" in arg_names
        
        # Check band_names argument
        band_names_arg = next(arg for arg in args if arg["name"] == "band_names")
        assert band_names_arg["required"] is True
        assert "minimum 2" in band_names_arg["description"].lower()
        
        # Check comparison_aspects argument
        aspects_arg = next(arg for arg in args if arg["name"] == "comparison_aspects")
        assert aspects_arg["required"] is False
        assert "style" in aspects_arg["description"]
        assert "discography" in aspects_arg["description"]
        
        # Check comparison_scope argument
        scope_arg = next(arg for arg in args if arg["name"] == "comparison_scope")
        assert scope_arg["required"] is False
        assert "basic" in scope_arg["description"]
        assert "full" in scope_arg["description"]
        assert "summary" in scope_arg["description"]

    def test_full_scope_prompt_content(self):
        """Test prompt content for full comparison scope."""
        prompt = get_compare_bands_prompt(comparison_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that full prompt includes all necessary sections
        assert "COMPARISON OBJECTIVES" in content
        assert "Musical Style Comparison" in content
        assert "Discography Analysis" in content
        assert "Influence & Legacy Comparison" in content
        assert "Commercial & Critical Reception" in content
        assert "Innovation Assessment" in content
        assert "COMPARATIVE ANALYSIS GUIDELINES" in content
        assert "OUTPUT FORMAT" in content
        assert "COMPARISON STRATEGY" in content
        assert "VALIDATION RULES" in content
        assert "USAGE EXAMPLE" in content
        
        # Check for JSON schema presence
        assert '"comparison_summary"' in content
        assert '"bands_analyzed"' in content
        assert '"musical_style_comparison"' in content
        assert '"overall_assessment"' in content

    def test_basic_scope_prompt_content(self):
        """Test prompt content for basic comparison scope."""
        prompt = get_compare_bands_prompt(comparison_scope="basic")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that basic prompt has appropriate content
        assert "Essential Comparison" in content
        assert "USAGE EXAMPLE" in content
        assert "OUTPUT FORMAT" in content
        assert "style_comparison" in content
        assert "key_differences" in content
        
        # Should not include detailed analysis sections
        assert "Commercial & Critical Reception" not in content
        assert "Innovation Assessment" not in content

    def test_summary_scope_prompt_content(self):
        """Test prompt content for summary comparison scope."""
        prompt = get_compare_bands_prompt(comparison_scope="summary")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that summary prompt focuses on key points
        assert "Summary Elements" in content
        assert "Quick style positioning" in content
        assert "rankings" in content.lower()
        assert "bottom_line" in content
        
        # Should be more concise than full
        assert "COMPARISON OBJECTIVES" not in content

    def test_invalid_scope_defaults_to_full(self):
        """Test that invalid scope defaults to full."""
        prompt1 = get_compare_bands_prompt(comparison_scope="invalid")
        prompt2 = get_compare_bands_prompt(comparison_scope="full")
        
        # Both should produce the same content
        assert prompt1["messages"][0]["content"]["text"] == prompt2["messages"][0]["content"]["text"]

    def test_specific_band_names_prompt(self):
        """Test prompt generation with specific band names."""
        band_names = ["The Beatles", "The Rolling Stones"]
        prompt = get_compare_bands_prompt(band_names=band_names)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include the specific band names
        assert "The Beatles" in content
        assert "The Rolling Stones" in content
        assert "BANDS TO COMPARE" in content
        assert "SPECIFIC COMPARISON REQUEST" in content

    def test_multiple_band_names_handling(self):
        """Test prompt generation with multiple band names."""
        band_names = ["Pink Floyd", "Led Zeppelin", "Queen", "The Who"]
        prompt = get_compare_bands_prompt(band_names=band_names)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include all band names
        for band in band_names:
            assert band in content
        
        # Should mention the number of bands
        assert str(len(band_names)) in content
        assert "4 bands" in content

    def test_comparison_aspects_integration(self):
        """Test prompt generation with specific comparison aspects."""
        band_names = ["Black Sabbath", "Deep Purple"]
        aspects = ["style", "influence", "innovation"]
        prompt = get_compare_bands_prompt(band_names=band_names, comparison_aspects=aspects)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include focus areas section
        assert "FOCUS AREAS" in content
        assert "style" in content
        assert "influence" in content
        assert "innovation" in content

    def test_empty_band_names_uses_template(self):
        """Test that empty band names list uses general template."""
        prompt = get_compare_bands_prompt(band_names=[])
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include specific band information
        assert "BANDS TO COMPARE" not in content
        assert "SPECIFIC COMPARISON REQUEST" not in content

    def test_single_band_name_uses_template(self):
        """Test that single band name uses general template (needs minimum 2)."""
        prompt = get_compare_bands_prompt(band_names=["Queen"])
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include specific band information since minimum 2 required
        assert "BANDS TO COMPARE" not in content
        assert "SPECIFIC COMPARISON REQUEST" not in content

    def test_comparison_aspects_validation(self):
        """Test that comparison aspects are validated correctly."""
        valid_aspects = ["style", "discography", "influence", "legacy", "innovation", "commercial", "critical"]
        invalid_aspects = ["invalid1", "invalid2"]
        mixed_aspects = valid_aspects[:3] + invalid_aspects
        
        prompt = get_compare_bands_prompt(
            band_names=["Band1", "Band2"], 
            comparison_aspects=mixed_aspects
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should only include valid aspects
        for valid_aspect in valid_aspects[:3]:
            assert valid_aspect in content
        
        # Invalid aspects should not appear in focus areas
        focus_start = content.find("FOCUS AREAS")
        if focus_start != -1:
            focus_section = content[focus_start:focus_start + 200]
            for invalid_aspect in invalid_aspects:
                assert invalid_aspect not in focus_section

    def test_message_format_structure(self):
        """Test that message format follows MCP specification."""
        prompt = get_compare_bands_prompt()
        message = prompt["messages"][0]
        
        # Verify message structure
        assert "role" in message
        assert "content" in message
        assert message["role"] == "user"
        assert "type" in message["content"]
        assert "text" in message["content"]
        assert message["content"]["type"] == "text"
        assert isinstance(message["content"]["text"], str)
        assert len(message["content"]["text"]) > 100  # Should be substantial content

    def test_json_schema_formatting(self):
        """Test that JSON schema in prompt is properly formatted."""
        prompt = get_compare_bands_prompt(comparison_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check JSON schema blocks are present
        assert "```json" in content
        assert "```" in content
        
        # Check essential schema fields for full comparison
        schema_fields = [
            '"comparison_summary"',
            '"bands_analyzed"',
            '"musical_style_comparison"',
            '"discography_comparison"',
            '"influence_legacy"',
            '"overall_assessment"'
        ]
        
        for field in schema_fields:
            assert field in content

    def test_comparison_strategy_guidelines(self):
        """Test that comparison strategy guidelines are comprehensive."""
        prompt = get_compare_bands_prompt(comparison_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check strategy mentions important elements
        assert "research" in content.lower()
        assert "connections" in content.lower()
        assert "genres" in content.lower()
        assert "specific examples" in content.lower()

    def test_validation_rules_coverage(self):
        """Test that validation rules cover important aspects."""
        prompt = get_compare_bands_prompt(comparison_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check validation rules are comprehensive
        assert "VALIDATION RULES" in content
        assert "objective analysis" in content.lower()
        assert "historically accurate" in content.lower()
        assert "specific examples" in content.lower()

    def test_different_scopes_all_work(self):
        """Test that all comparison scopes produce valid prompts."""
        scopes = ["basic", "full", "summary"]
        
        for scope in scopes:
            prompt = get_compare_bands_prompt(comparison_scope=scope)
            
            # All should have basic structure
            assert prompt["name"] == "compare_bands"
            assert len(prompt["messages"]) == 1
            assert isinstance(prompt["messages"][0]["content"]["text"], str)
            assert len(prompt["messages"][0]["content"]["text"]) > 50

    def test_prompt_consistency(self):
        """Test that prompts are consistent across calls."""
        # Same parameters should produce identical prompts
        prompt1 = get_compare_bands_prompt()
        prompt2 = get_compare_bands_prompt(band_names=[], comparison_aspects=[])
        
        assert prompt1["messages"][0]["content"]["text"] == prompt2["messages"][0]["content"]["text"]

    def test_content_length_reasonable(self):
        """Test that prompt content length is reasonable."""
        prompt = get_compare_bands_prompt(comparison_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Should be substantial but not excessive
        assert 1000 < len(content) < 20000  # Reasonable range for comprehensive prompt

    def test_usage_examples_present(self):
        """Test that usage examples are included in prompts."""
        prompt = get_compare_bands_prompt(comparison_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include usage examples
        assert "USAGE EXAMPLE" in content
        assert "Beatles" in content or "Rolling Stones" in content  # Common examples

    def test_empty_aspects_list_handling(self):
        """Test handling of empty comparison aspects list."""
        prompt = get_compare_bands_prompt(
            band_names=["Band1", "Band2"],
            comparison_aspects=[]
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include focus areas section
        assert "FOCUS AREAS" not in content

    def test_none_aspects_handling(self):
        """Test handling of None comparison aspects."""
        prompt = get_compare_bands_prompt(
            band_names=["Band1", "Band2"],
            comparison_aspects=None
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include focus areas section
        assert "FOCUS AREAS" not in content

    def test_comprehensive_integration(self):
        """Test comprehensive integration of all parameters."""
        band_names = ["Pink Floyd", "Genesis", "Yes"]
        aspects = ["style", "innovation", "influence"]
        scope = "full"
        
        prompt = get_compare_bands_prompt(
            band_names=band_names,
            comparison_aspects=aspects,
            comparison_scope=scope
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include all elements
        assert "SPECIFIC COMPARISON REQUEST" in content
        assert "FOCUS AREAS" in content
        assert "Pink Floyd" in content
        assert "Genesis" in content
        assert "Yes" in content
        assert "style" in content
        assert "innovation" in content
        assert "influence" in content
        
        # Should have comprehensive content
        assert "COMPARISON OBJECTIVES" in content
        assert "Musical Style Comparison" in content
        assert "overall_assessment" in content

    def test_additional_notes_for_specific_comparison(self):
        """Test that additional notes are included for specific comparisons."""
        band_names = ["The Beatles", "The Beach Boys"]
        prompt = get_compare_bands_prompt(band_names=band_names)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include additional notes section
        assert "ADDITIONAL NOTES FOR THIS COMPARISON" in content
        assert "specific relationships" in content.lower()
        assert "different eras or genres" in content.lower()

    def test_specific_prompt_includes_band_count(self):
        """Test that specific prompts include accurate band count."""
        # Test with 2 bands
        band_names_2 = ["Band1", "Band2"]
        prompt_2 = get_compare_bands_prompt(band_names=band_names_2)
        content_2 = prompt_2["messages"][0]["content"]["text"]
        assert "all 2 bands" in content_2
        
        # Test with 3 bands
        band_names_3 = ["Band1", "Band2", "Band3"]
        prompt_3 = get_compare_bands_prompt(band_names=band_names_3)
        content_3 = prompt_3["messages"][0]["content"]["text"]
        assert "all 3 bands" in content_3 