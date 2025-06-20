import pytest
from src.core.prompts.fetch_band_info import get_fetch_band_info_prompt


class TestFetchBandInfoPrompt:
    """Test suite for the fetch_band_info prompt implementation."""

    def test_default_prompt_structure(self):
        """Test that the default prompt has correct structure."""
        prompt = get_fetch_band_info_prompt()
        
        # Verify basic structure
        assert isinstance(prompt, dict)
        assert "name" in prompt
        assert "description" in prompt
        assert "arguments" in prompt
        assert "messages" in prompt
        
        # Verify prompt details
        assert prompt["name"] == "fetch_band_info"
        assert "band" in prompt["description"].lower()
        assert len(prompt["arguments"]) == 3  # band_name, existing_albums, information_scope
        assert len(prompt["messages"]) == 1
        assert prompt["messages"][0]["role"] == "user"

    def test_prompt_arguments_structure(self):
        """Test that prompt arguments are correctly structured."""
        prompt = get_fetch_band_info_prompt()
        args = prompt["arguments"]
        
        # Check all expected arguments exist
        arg_names = [arg["name"] for arg in args]
        assert "band_name" in arg_names
        assert "existing_albums" in arg_names
        assert "information_scope" in arg_names
        
        # Check band_name argument
        band_name_arg = next(arg for arg in args if arg["name"] == "band_name")
        assert band_name_arg["required"] is True
        assert "band" in band_name_arg["description"].lower()
        
        # Check existing_albums argument
        existing_albums_arg = next(arg for arg in args if arg["name"] == "existing_albums")
        assert existing_albums_arg["required"] is False
        assert "collection" in existing_albums_arg["description"].lower()
        
        # Check information_scope argument
        scope_arg = next(arg for arg in args if arg["name"] == "information_scope")
        assert scope_arg["required"] is False
        assert "scope" in scope_arg["description"].lower()

    def test_full_scope_prompt_content(self):
        """Test prompt content for full information scope."""
        prompt = get_fetch_band_info_prompt(information_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that full prompt includes all necessary sections
        assert "RESEARCH OBJECTIVES" in content
        assert "Basic Band Information" in content
        assert "Complete Discography" in content
        assert "DATA QUALITY GUIDELINES" in content
        assert "OUTPUT FORMAT" in content
        assert "SEARCH STRATEGY" in content
        assert "VALIDATION RULES" in content
        assert "USAGE EXAMPLE" in content
        
        # Check for JSON schema presence
        assert '"band_name"' in content
        assert '"formed"' in content
        assert '"genres"' in content
        assert '"albums"' in content
        assert '"missing"' in content

    def test_basic_scope_prompt_content(self):
        """Test prompt content for basic information scope."""
        prompt = get_fetch_band_info_prompt(information_scope="basic")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that basic prompt has appropriate content
        assert "Basic Band Information Only" in content
        assert "USAGE EXAMPLE" in content
        assert "OUTPUT FORMAT" in content
        
        # Should not include discography details
        assert "Complete Discography" not in content
        assert "albums" not in content.lower() or content.lower().count("albums") <= 2  # May appear in general context

    def test_albums_only_scope_prompt_content(self):
        """Test prompt content for albums-only scope."""
        prompt = get_fetch_band_info_prompt(information_scope="albums_only")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that albums prompt focuses on discography
        assert "discography" in content.lower()
        assert "ALBUM INFORMATION TO GATHER" in content
        assert "albums" in content.lower()
        assert "USAGE EXAMPLE" in content
        
        # Should not include basic band info details
        assert "Basic Band Information" not in content

    def test_invalid_scope_defaults_to_full(self):
        """Test that invalid scope defaults to full."""
        prompt1 = get_fetch_band_info_prompt(information_scope="invalid")
        prompt2 = get_fetch_band_info_prompt(information_scope="full")
        
        # Both should produce the same content
        assert prompt1["messages"][0]["content"]["text"] == prompt2["messages"][0]["content"]["text"]

    def test_specific_band_name_prompt(self):
        """Test prompt generation with specific band name."""
        band_name = "Pink Floyd"
        prompt = get_fetch_band_info_prompt(band_name=band_name)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include the specific band name
        assert band_name in content
        assert f"Research the band '{band_name}'" in content

    def test_existing_albums_integration(self):
        """Test prompt generation with existing albums list."""
        band_name = "The Beatles"
        existing_albums = ["Abbey Road", "Sgt. Pepper's Lonely Hearts Club Band"]
        prompt = get_fetch_band_info_prompt(band_name=band_name, existing_albums=existing_albums)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include existing albums information
        assert "EXISTING LOCAL ALBUMS" in content
        assert "Abbey Road" in content
        assert "Sgt. Pepper's Lonely Hearts Club Band" in content
        assert "missing" in content.lower()

    def test_empty_existing_albums_list(self):
        """Test prompt generation with empty existing albums list."""
        prompt = get_fetch_band_info_prompt(band_name="Led Zeppelin", existing_albums=[])
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include existing albums section
        assert "EXISTING LOCAL ALBUMS" not in content

    def test_none_existing_albums_handling(self):
        """Test prompt generation with None existing albums."""
        prompt = get_fetch_band_info_prompt(band_name="Queen", existing_albums=None)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include existing albums section
        assert "EXISTING LOCAL ALBUMS" not in content

    def test_message_format_structure(self):
        """Test that message format follows MCP specification."""
        prompt = get_fetch_band_info_prompt()
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
        prompt = get_fetch_band_info_prompt(information_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check JSON schema blocks are present
        assert "```json" in content
        assert "```" in content
        
        # Check essential schema fields
        schema_fields = [
            '"band_name"',
            '"formed"', 
            '"genres"',
            '"origin"',
            '"members"',
            '"description"',
            '"albums"'
        ]
        
        for field in schema_fields:
            assert field in content

    def test_search_strategy_guidelines(self):
        """Test that search strategy guidelines are comprehensive."""
        prompt = get_fetch_band_info_prompt(information_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check search strategy mentions reliable sources
        assert "Wikipedia" in content
        assert "AllMusic" in content
        assert "official websites" in content
        assert "verified" in content.lower()

    def test_validation_rules_coverage(self):
        """Test that validation rules cover important aspects."""
        prompt = get_fetch_band_info_prompt(information_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check validation rules
        assert "YYYY format" in content
        assert "genre names" in content.lower()
        assert "roles" in content.lower()
        assert "accurate" in content.lower()

    def test_different_scopes_all_work(self):
        """Test that all information scopes produce valid prompts."""
        scopes = ["basic", "full", "albums_only"]
        
        for scope in scopes:
            prompt = get_fetch_band_info_prompt(information_scope=scope)
            
            # Each should be a valid prompt structure
            assert isinstance(prompt, dict)
            assert "messages" in prompt
            assert len(prompt["messages"]) > 0
            assert len(prompt["messages"][0]["content"]["text"]) > 50
            
            content = prompt["messages"][0]["content"]["text"]
            # Each should have some basic structure
            assert "OUTPUT FORMAT" in content
            assert "```json" in content

    def test_prompt_consistency(self):
        """Test that prompt metadata is consistent across calls."""
        prompt1 = get_fetch_band_info_prompt()
        prompt2 = get_fetch_band_info_prompt(band_name="", existing_albums=[])
        
        # Metadata should be identical
        assert prompt1["name"] == prompt2["name"]
        assert prompt1["description"] == prompt2["description"]
        assert prompt1["arguments"] == prompt2["arguments"]

    def test_content_length_reasonable(self):
        """Test that prompt content is substantial but not excessive."""
        for scope in ["basic", "full", "albums_only"]:
            prompt = get_fetch_band_info_prompt(information_scope=scope)
            content = prompt["messages"][0]["content"]["text"]
            
            # Should have substantial content
            assert len(content) > 500  # At least 500 characters
            assert len(content) < 10000  # But not excessive
            
            # Should have multiple sections
            assert content.count("**") >= 4  # Multiple bold sections 
