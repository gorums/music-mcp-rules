import pytest
from src.prompts.analyze_band import get_analyze_band_prompt


class TestAnalyzeBandPrompt:
    """Test suite for the analyze_band prompt implementation."""

    def test_default_prompt_structure(self):
        """Test that the default prompt has correct structure."""
        prompt = get_analyze_band_prompt()
        
        # Verify basic structure
        assert isinstance(prompt, dict)
        assert "name" in prompt
        assert "description" in prompt
        assert "arguments" in prompt
        assert "messages" in prompt
        
        # Verify prompt details
        assert prompt["name"] == "analyze_band"
        assert "analysis" in prompt["description"].lower()
        assert len(prompt["arguments"]) == 4  # band_name, albums, analyze_missing_albums, analysis_scope
        assert len(prompt["messages"]) == 1
        assert prompt["messages"][0]["role"] == "user"

    def test_prompt_arguments_structure(self):
        """Test that prompt arguments are correctly structured."""
        prompt = get_analyze_band_prompt()
        args = prompt["arguments"]
        
        # Check all expected arguments exist
        arg_names = [arg["name"] for arg in args]
        assert "band_name" in arg_names
        assert "albums" in arg_names
        assert "analyze_missing_albums" in arg_names
        assert "analysis_scope" in arg_names
        
        # Check band_name argument
        band_name_arg = next(arg for arg in args if arg["name"] == "band_name")
        assert band_name_arg["required"] is True
        assert "band" in band_name_arg["description"].lower()
        
        # Check albums argument
        albums_arg = next(arg for arg in args if arg["name"] == "albums")
        assert albums_arg["required"] is False
        assert "albums" in albums_arg["description"].lower()
        
        # Check analyze_missing_albums argument
        missing_arg = next(arg for arg in args if arg["name"] == "analyze_missing_albums")
        assert missing_arg["required"] is False
        assert "missing" in missing_arg["description"].lower()
        
        # Check analysis_scope argument
        scope_arg = next(arg for arg in args if arg["name"] == "analysis_scope")
        assert scope_arg["required"] is False
        assert "scope" in scope_arg["description"].lower()

    def test_full_scope_prompt_content(self):
        """Test prompt content for full analysis scope."""
        prompt = get_analyze_band_prompt(analysis_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that full prompt includes all necessary sections
        assert "ANALYSIS OBJECTIVES" in content
        assert "Overall Band Analysis" in content
        assert "Album-Specific Analysis" in content
        assert "Similar Bands Identification" in content
        assert "RATING GUIDELINES" in content
        assert "OUTPUT FORMAT" in content
        assert "ANALYSIS STRATEGY" in content
        assert "VALIDATION RULES" in content
        assert "USAGE EXAMPLE" in content
        
        # Check for JSON schema presence
        assert '"review"' in content
        assert '"rate"' in content
        assert '"albums"' in content
        assert '"album_name"' in content
        assert '"similar_bands"' in content

    def test_basic_scope_prompt_content(self):
        """Test prompt content for basic analysis scope."""
        prompt = get_analyze_band_prompt(analysis_scope="basic")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that basic prompt has appropriate content
        assert "Essential Band Analysis" in content
        assert "Similar Bands" in content
        assert "USAGE EXAMPLE" in content
        assert "OUTPUT FORMAT" in content
        
        # Should not include detailed album analysis
        assert "Album-Specific Analysis" not in content
        assert "albums" not in content.lower() or content.lower().count("albums") <= 2

    def test_albums_only_scope_prompt_content(self):
        """Test prompt content for albums-only scope."""
        prompt = get_analyze_band_prompt(analysis_scope="albums_only")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check that albums prompt focuses on album analysis
        assert "album analysis" in content.lower()
        assert "ALBUM ANALYSIS COMPONENTS" in content
        assert "album-by-album" in content.lower()
        assert "USAGE EXAMPLE" in content
        
        # Should focus primarily on albums
        assert "albums" in content.lower()

    def test_invalid_scope_defaults_to_full(self):
        """Test that invalid scope defaults to full."""
        prompt1 = get_analyze_band_prompt(analysis_scope="invalid")
        prompt2 = get_analyze_band_prompt(analysis_scope="full")
        
        # Both should produce the same content
        assert prompt1["messages"][0]["content"]["text"] == prompt2["messages"][0]["content"]["text"]

    def test_specific_band_name_prompt(self):
        """Test prompt generation with specific band name."""
        band_name = "Pink Floyd"
        prompt = get_analyze_band_prompt(band_name=band_name)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include the specific band name
        assert band_name in content
        assert f"Analyze the band '{band_name}'" in content

    def test_albums_list_integration(self):
        """Test prompt generation with albums list."""
        band_name = "The Beatles"
        albums = ["Abbey Road", "Sgt. Pepper's Lonely Hearts Club Band", "Revolver"]
        prompt = get_analyze_band_prompt(band_name=band_name, albums=albums)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include albums information
        assert "ALBUMS TO ANALYZE" in content
        assert "Abbey Road" in content
        assert "Sgt. Pepper's Lonely Hearts Club Band" in content
        assert "Revolver" in content

    def test_analyze_missing_albums_false(self):
        """Test prompt generation with analyze_missing_albums=False."""
        band_name = "Queen"
        albums = ["A Night at the Opera", "Bohemian Rhapsody"]
        prompt = get_analyze_band_prompt(
            band_name=band_name, 
            albums=albums, 
            analyze_missing_albums=False
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include note about only analyzing local albums
        assert "Only analyze albums that are available locally" in content
        assert "not marked as missing" in content

    def test_analyze_missing_albums_true(self):
        """Test prompt generation with analyze_missing_albums=True."""
        band_name = "Led Zeppelin"
        albums = ["Led Zeppelin IV", "Physical Graffiti"]
        prompt = get_analyze_band_prompt(
            band_name=band_name, 
            albums=albums, 
            analyze_missing_albums=True
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include note about analyzing all albums including missing
        assert "Include analysis for all albums" in content
        assert "including those marked as missing" in content

    def test_empty_albums_list(self):
        """Test prompt generation with empty albums list."""
        prompt = get_analyze_band_prompt(band_name="The Doors", albums=[])
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include albums section
        assert "ALBUMS TO ANALYZE" not in content

    def test_none_albums_handling(self):
        """Test prompt generation with None albums."""
        prompt = get_analyze_band_prompt(band_name="Radiohead", albums=None)
        content = prompt["messages"][0]["content"]["text"]
        
        # Should not include albums section
        assert "ALBUMS TO ANALYZE" not in content

    def test_rating_guidelines_coverage(self):
        """Test that rating guidelines cover important aspects."""
        prompt = get_analyze_band_prompt(analysis_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check rating guidelines
        assert "1-10 scale" in content
        assert "Overall Band Rating" in content
        assert "Album Rating" in content
        assert "masterpiece" in content.lower()

    def test_different_scopes_all_work(self):
        """Test that all analysis scopes produce valid prompts."""
        scopes = ["basic", "full", "albums_only"]
        
        for scope in scopes:
            prompt = get_analyze_band_prompt(analysis_scope=scope)
            
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
        prompt1 = get_analyze_band_prompt()
        prompt2 = get_analyze_band_prompt(band_name="", albums=[])
        
        # Metadata should be identical
        assert prompt1["name"] == prompt2["name"]
        assert prompt1["description"] == prompt2["description"]
        assert prompt1["arguments"] == prompt2["arguments"]

    def test_analysis_schema_validation_rules(self):
        """Test that analysis schema validation rules are present."""
        prompt = get_analyze_band_prompt(analysis_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Check validation rules specific to analysis
        assert "VALIDATION RULES" in content
        assert "1-10 integer" in content
        assert "substantial" in content.lower()
        assert "similar bands" in content.lower()

    def test_comprehensive_analysis_components(self):
        """Test that all analysis components are covered in full scope."""
        prompt = get_analyze_band_prompt(analysis_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Should cover all major analysis areas
        assert "musical style" in content.lower()
        assert "innovation" in content.lower()
        assert "influence" in content.lower()
        assert "legacy" in content.lower()
        assert "similar" in content.lower()
        assert "rating" in content.lower()

    def test_specific_band_with_full_parameters(self):
        """Test prompt generation with all parameters specified."""
        band_name = "Pink Floyd"
        albums = ["The Dark Side of the Moon", "The Wall", "Wish You Were Here"]
        prompt = get_analyze_band_prompt(
            band_name=band_name,
            albums=albums,
            analyze_missing_albums=True,
            analysis_scope="full"
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include all elements
        assert band_name in content
        assert "The Dark Side of the Moon" in content
        assert "The Wall" in content  
        assert "Wish You Were Here" in content
        assert "Include analysis for all albums" in content
        assert "ANALYSIS OBJECTIVES" in content

    def test_albums_only_scope_with_albums(self):
        """Test albums-only scope with specific albums list."""
        band_name = "Black Sabbath"
        albums = ["Paranoid", "Master of Reality", "Vol. 4"]
        prompt = get_analyze_band_prompt(
            band_name=band_name,
            albums=albums,
            analysis_scope="albums_only"
        )
        content = prompt["messages"][0]["content"]["text"]
        
        # Should focus on albums and include the specific albums
        assert "album analysis" in content.lower()
        assert "Paranoid" in content
        assert "Master of Reality" in content
        assert "Vol. 4" in content

    def test_basic_scope_similar_bands_requirement(self):
        """Test that basic scope includes similar bands requirement."""
        prompt = get_analyze_band_prompt(analysis_scope="basic")
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include similar bands in basic analysis
        assert "Similar Bands" in content
        assert "3-5 most relevant" in content
        assert "stylistic connections" in content

    def test_analysis_strategy_section(self):
        """Test that analysis strategy section is present and comprehensive."""
        prompt = get_analyze_band_prompt(analysis_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Should have comprehensive strategy guidance
        assert "ANALYSIS STRATEGY" in content
        assert "Research" in content
        assert "evolution" in content.lower()
        assert "context" in content.lower()
        assert "connections" in content.lower()

    def test_important_notes_section(self):
        """Test that important notes provide guidance on quality analysis."""
        prompt = get_analyze_band_prompt(analysis_scope="full")
        content = prompt["messages"][0]["content"]["text"]
        
        # Should include important guidance notes
        assert "IMPORTANT NOTES" in content
        assert "individual merit" in content.lower()
        assert "historical significance" in content.lower()
        assert "musical quality" in content.lower() 