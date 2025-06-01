import unittest
from unittest.mock import patch
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from prompts.collection_insights import (
    get_collection_insights_prompt,
    _build_general_insights_template,
    _build_comprehensive_insights_template,
    _build_basic_insights_template,
    _build_health_insights_template,
    _build_specific_collection_analysis_prompt,
    _get_focus_area_guidance
)


class TestGetCollectionInsightsPrompt(unittest.TestCase):
    """Test cases for get_collection_insights_prompt function."""
    
    def test_prompt_basic_structure(self):
        """Test basic prompt structure and required fields."""
        result = get_collection_insights_prompt()
        
        # Check basic structure
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)
        self.assertIn("description", result)
        self.assertIn("arguments", result)
        self.assertIn("messages", result)
        
        # Check prompt name and description
        self.assertEqual(result["name"], "collection_insights")
        self.assertIn("insights", result["description"].lower())
        self.assertIn("collection", result["description"].lower())
        
        # Check messages structure
        self.assertIsInstance(result["messages"], list)
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["role"], "user")
        self.assertIn("content", result["messages"][0])
        self.assertIn("text", result["messages"][0]["content"])
    
    def test_prompt_arguments(self):
        """Test prompt arguments configuration."""
        result = get_collection_insights_prompt()
        
        args = result["arguments"]
        self.assertIsInstance(args, list)
        self.assertEqual(len(args), 3)
        
        # Check argument names
        arg_names = [arg["name"] for arg in args]
        self.assertIn("collection_data", arg_names)
        self.assertIn("insights_scope", arg_names)
        self.assertIn("focus_areas", arg_names)
        
        # Check all arguments are optional
        for arg in args:
            self.assertFalse(arg["required"])
    
    def test_default_comprehensive_scope(self):
        """Test default comprehensive scope generates appropriate content."""
        result = get_collection_insights_prompt()
        content = result["messages"][0]["content"]["text"]
        
        # Should contain comprehensive analysis elements
        self.assertIn("comprehensive insights", content.lower())
        self.assertIn("**Collection Analysis Insights:**", content)
        self.assertIn("actionable recommendations", content)
        self.assertIn("**Top-Rated Bands Identification:**", content)
        self.assertIn("**Strategic Purchase Suggestions:**", content)
        self.assertIn("collection health", content)
    
    def test_basic_insights_scope(self):
        """Test basic insights scope parameter."""
        result = get_collection_insights_prompt(insights_scope="basic")
        content = result["messages"][0]["content"]["text"]
        
        # Should contain basic analysis elements
        self.assertIn("basic insights", content.lower())
        self.assertIn("essential", content.lower())
        self.assertIn("concise", content.lower())
    
    def test_health_only_scope(self):
        """Test health_only insights scope parameter."""
        result = get_collection_insights_prompt(insights_scope="health_only")
        content = result["messages"][0]["content"]["text"]
        
        # Should contain health-focused elements
        self.assertIn("health assessment", content.lower())
        self.assertIn("health metrics", content.lower())
        self.assertIn("completion rate", content.lower())
    
    def test_invalid_scope_defaults_to_comprehensive(self):
        """Test invalid scope parameter defaults to comprehensive."""
        result = get_collection_insights_prompt(insights_scope="invalid_scope")
        content = result["messages"][0]["content"]["text"]
        
        # Should default to comprehensive
        self.assertIn("comprehensive insights", content.lower())
    
    def test_focus_areas_parameter(self):
        """Test focus_areas parameter integration."""
        focus_areas = ["statistics", "recommendations"]
        result = get_collection_insights_prompt(focus_areas=focus_areas)
        content = result["messages"][0]["content"]["text"]
        
        # Should contain focus area guidance
        self.assertIn("FOCUS AREAS", content)
        self.assertIn("Statistics", content)
        self.assertIn("Recommendations", content)
    
    def test_collection_data_parameter(self):
        """Test collection_data parameter triggers specific analysis."""
        collection_data = {
            "stats": {
                "total_bands": 50,
                "total_albums": 300,
                "completion_percentage": 85.5,
                "bands_with_metadata": 40,
                "total_missing_albums": 20,
                "avg_albums_per_band": 6.0
            },
            "bands": [
                {"name": "Pink Floyd", "albums_count": 15, "missing_albums_count": 2, "has_metadata": True, "has_analysis": True}
            ]
        }
        
        result = get_collection_insights_prompt(collection_data=collection_data)
        content = result["messages"][0]["content"]["text"]
        
        # Should contain specific collection data
        self.assertIn("50", content)  # total_bands
        self.assertIn("300", content)  # total_albums
        self.assertIn("85.5%", content)  # completion_percentage
        self.assertIn("Pink Floyd", content)  # band name


class TestGeneralInsightsTemplates(unittest.TestCase):
    """Test cases for general insights template functions."""
    
    def test_build_general_insights_template_comprehensive(self):
        """Test comprehensive template building."""
        result = _build_general_insights_template("comprehensive", [])
        
        # Should contain comprehensive elements
        self.assertIn("comprehensive insights", result.lower())
        self.assertIn("**Collection Analysis Insights:**", result)
        self.assertIn("actionable recommendations", result)
        self.assertIn("JSON format", result)
        self.assertIn("collection_health", result)
    
    def test_build_general_insights_template_basic(self):
        """Test basic template building."""
        result = _build_general_insights_template("basic", [])
        
        # Should contain basic elements
        self.assertIn("basic insights", result.lower())
        self.assertIn("essential", result.lower())
        self.assertIn("concise", result.lower())
    
    def test_build_general_insights_template_health_only(self):
        """Test health-only template building."""
        result = _build_general_insights_template("health_only", [])
        
        # Should contain health elements
        self.assertIn("health assessment", result.lower())
        self.assertIn("completeness", result.lower())
        self.assertIn("data quality", result.lower())
    
    def test_build_general_insights_template_with_focus_areas(self):
        """Test template building with focus areas."""
        focus_areas = ["statistics", "health"]
        result = _build_general_insights_template("comprehensive", focus_areas)
        
        # Should contain focus area guidance
        self.assertIn("FOCUS AREAS", result)
        self.assertIn("Statistics", result)
        self.assertIn("Health", result)


class TestComprehensiveInsightsTemplate(unittest.TestCase):
    """Test cases for comprehensive insights template."""
    
    def test_comprehensive_template_structure(self):
        """Test comprehensive template contains all required sections."""
        result = _build_comprehensive_insights_template([])
        
        # Check major sections
        self.assertIn("INSTRUCTIONS:", result)
        self.assertIn("ANALYSIS OBJECTIVES:", result)
        self.assertIn("INSIGHT COMPONENTS:", result)
        self.assertIn("Collection Analysis Insights:", result)
        self.assertIn("Actionable Recommendations:", result)
        self.assertIn("Top-Rated Bands Identification:", result)
        self.assertIn("Strategic Purchase Suggestions:", result)
        self.assertIn("Collection Health Assessment:", result)
    
    def test_comprehensive_template_quality_guidelines(self):
        """Test comprehensive template includes quality guidelines."""
        result = _build_comprehensive_insights_template([])
        
        # Should include quality guidelines
        self.assertIn("INSIGHTS QUALITY GUIDELINES:", result)
        self.assertIn("Actionable", result)
        self.assertIn("Data-Driven", result)
        self.assertIn("Balanced", result)
        self.assertIn("Prioritized", result)
        self.assertIn("Comprehensive", result)
        self.assertIn("Realistic", result)
    
    def test_comprehensive_template_output_format(self):
        """Test comprehensive template includes proper output format."""
        result = _build_comprehensive_insights_template([])
        
        # Should include JSON output format
        self.assertIn("OUTPUT FORMAT:", result)
        self.assertIn("```json", result)
        self.assertIn('"insights":', result)
        self.assertIn('"recommendations":', result)
        self.assertIn('"top_rated_bands":', result)
        self.assertIn('"suggested_purchases":', result)
        self.assertIn('"collection_health":', result)
    
    def test_comprehensive_template_health_criteria(self):
        """Test comprehensive template includes health criteria."""
        result = _build_comprehensive_insights_template([])
        
        # Should include health assessment criteria
        self.assertIn("COLLECTION HEALTH CRITERIA:", result)
        self.assertIn("Excellent", result)
        self.assertIn("Good", result)
        self.assertIn("Fair", result)
        self.assertIn("Poor", result)
        self.assertIn(">95% completion", result)
    
    def test_comprehensive_template_validation_rules(self):
        """Test comprehensive template includes validation rules."""
        result = _build_comprehensive_insights_template([])
        
        # Should include validation rules
        self.assertIn("VALIDATION RULES:", result)
        self.assertIn("minimum 3 insights", result)
        self.assertIn("minimum 3 recommendations", result)
        self.assertIn("3-8 bands", result)
        self.assertIn("3-10 albums", result)
    
    def test_comprehensive_template_with_focus_areas(self):
        """Test comprehensive template with focus areas."""
        focus_areas = ["statistics", "recommendations"]
        result = _build_comprehensive_insights_template(focus_areas)
        
        # Should include focus area section
        self.assertIn("FOCUS AREAS (prioritize these aspects):", result)
        self.assertIn("Statistics", result)
        self.assertIn("Recommendations", result)


class TestBasicInsightsTemplate(unittest.TestCase):
    """Test cases for basic insights template."""
    
    def test_basic_template_structure(self):
        """Test basic template contains essential sections."""
        result = _build_basic_insights_template([])
        
        # Check essential sections
        self.assertIn("basic insights", result.lower())
        self.assertIn("INSTRUCTIONS:", result)
        self.assertIn("ANALYSIS COMPONENTS:", result)
        self.assertIn("Essential Collection Insights:", result)
        self.assertIn("Key Recommendations:", result)
        self.assertIn("Health Assessment:", result)
    
    def test_basic_template_concise_focus(self):
        """Test basic template emphasizes conciseness."""
        result = _build_basic_insights_template([])
        
        # Should emphasize conciseness
        self.assertIn("concise", result.lower())
        self.assertIn("essential", result.lower())
        self.assertIn("2-3", result)  # Limited number of items
        self.assertIn("2-4 items", result)
    
    def test_basic_template_output_format(self):
        """Test basic template includes simplified output format."""
        result = _build_basic_insights_template([])
        
        # Should include JSON output format
        self.assertIn("OUTPUT FORMAT:", result)
        self.assertIn("```json", result)
        self.assertIn('"insights":', result)
        self.assertIn('"recommendations":', result)
        self.assertIn('"collection_health":', result)
    
    def test_basic_template_with_focus_areas(self):
        """Test basic template with focus areas."""
        focus_areas = ["health"]
        result = _build_basic_insights_template(focus_areas)
        
        # Should include focus area section
        self.assertIn("FOCUS AREAS", result)
        self.assertIn("Health", result)


class TestHealthInsightsTemplate(unittest.TestCase):
    """Test cases for health insights template."""
    
    def test_health_template_structure(self):
        """Test health template contains health-focused sections."""
        result = _build_health_insights_template([])
        
        # Check health-focused sections
        self.assertIn("health assessment", result.lower())
        self.assertIn("HEALTH ANALYSIS COMPONENTS:", result)
        self.assertIn("Collection Health Metrics:", result)
        self.assertIn("Health Recommendations:", result)
        self.assertIn("Health Status Assessment:", result)
    
    def test_health_template_assessment_criteria(self):
        """Test health template includes assessment criteria."""
        result = _build_health_insights_template([])
        
        # Should include health assessment criteria
        self.assertIn("HEALTH ASSESSMENT CRITERIA:", result)
        self.assertIn("Completion rate weight: 40%", result)
        self.assertIn("Metadata quality weight: 30%", result)
        self.assertIn("Organization effectiveness weight: 20%", result)
        self.assertIn("Analysis coverage weight: 10%", result)
    
    def test_health_template_specific_metrics(self):
        """Test health template focuses on specific health metrics."""
        result = _build_health_insights_template([])
        
        # Should focus on health metrics
        self.assertIn("completion rate", result.lower())
        self.assertIn("metadata coverage", result.lower())
        self.assertIn("data quality", result.lower())
        self.assertIn("organization", result.lower())
    
    def test_health_template_with_focus_areas(self):
        """Test health template with focus areas."""
        focus_areas = ["statistics", "health"]
        result = _build_health_insights_template(focus_areas)
        
        # Should include focus area section
        self.assertIn("FOCUS AREAS", result)
        self.assertIn("Statistics", result)
        self.assertIn("Health", result)


class TestSpecificCollectionAnalysis(unittest.TestCase):
    """Test cases for specific collection analysis prompt building."""
    
    def test_specific_analysis_with_complete_data(self):
        """Test specific analysis with complete collection data."""
        collection_data = {
            "stats": {
                "total_bands": 100,
                "total_albums": 500,
                "completion_percentage": 92.5,
                "bands_with_metadata": 85,
                "total_missing_albums": 38,
                "avg_albums_per_band": 5.0,
                "top_genres": {"Rock": 150, "Metal": 100, "Pop": 75}
            },
            "bands": [
                {"name": "Pink Floyd", "albums_count": 15, "missing_albums_count": 2, "has_metadata": True, "has_analysis": True},
                {"name": "Led Zeppelin", "albums_count": 12, "missing_albums_count": 1, "has_metadata": True, "has_analysis": False}
            ],
            "insights": {
                "insights": ["Existing insight 1", "Existing insight 2"]
            }
        }
        
        result = _build_specific_collection_analysis_prompt(collection_data, "comprehensive", [])
        
        # Should include specific collection data
        self.assertIn("100", result)  # total_bands with formatting
        self.assertIn("500", result)  # total_albums with formatting
        self.assertIn("92.5%", result)  # completion_percentage
        self.assertIn("85.0%", result)  # metadata coverage
        self.assertIn("38", result)  # missing albums
        self.assertIn("5.0", result)  # avg albums per band
        
        # Should include genre distribution
        self.assertIn("Rock: 150", result)
        self.assertIn("Metal: 100", result)
        self.assertIn("Pop: 75", result)
        
        # Should include band information
        self.assertIn("Pink Floyd", result)
        self.assertIn("Led Zeppelin", result)
        self.assertIn("15 albums (2 missing)", result)
        
        # Should include existing insights
        self.assertIn("EXISTING INSIGHTS:", result)
        self.assertIn("Existing insight 1", result)
    
    def test_specific_analysis_minimal_data(self):
        """Test specific analysis with minimal collection data."""
        collection_data = {
            "stats": {
                "total_bands": 5,
                "total_albums": 25
            }
        }
        
        result = _build_specific_collection_analysis_prompt(collection_data, "basic", [])
        
        # Should handle missing data gracefully
        self.assertIn("5", result)  # total_bands
        self.assertIn("25", result)  # total_albums
        self.assertIn("0.0%", result)  # default completion_percentage
        self.assertIn("Genre data not available", result)
    
    def test_specific_analysis_with_focus_areas(self):
        """Test specific analysis with focus areas."""
        collection_data = {"stats": {"total_bands": 10, "total_albums": 50}}
        focus_areas = ["statistics", "health"]
        
        result = _build_specific_collection_analysis_prompt(collection_data, "comprehensive", focus_areas)
        
        # Should include focus area information
        self.assertIn("Statistics analysis and recommendations", result)
        self.assertIn("Health analysis and recommendations", result)
    
    def test_specific_analysis_no_focus_areas(self):
        """Test specific analysis without focus areas."""
        collection_data = {"stats": {"total_bands": 10, "total_albums": 50}}
        
        result = _build_specific_collection_analysis_prompt(collection_data, "comprehensive", [])
        
        # Should default to complete analysis
        self.assertIn("Complete collection analysis across all areas", result)


class TestFocusAreaGuidance(unittest.TestCase):
    """Test cases for focus area guidance function."""
    
    def test_valid_focus_areas(self):
        """Test focus area guidance with valid areas."""
        focus_areas = ["statistics", "recommendations", "health"]
        result = _get_focus_area_guidance(focus_areas)
        
        # Should include guidance for each area
        self.assertIn("**Statistics**:", result)
        self.assertIn("**Recommendations**:", result)
        self.assertIn("**Health**:", result)
        
        # Should include area descriptions
        self.assertIn("collection size", result.lower())
        self.assertIn("actionable improvements", result.lower())
        self.assertIn("completeness", result.lower())
    
    def test_mixed_valid_invalid_focus_areas(self):
        """Test focus area guidance with mixed valid/invalid areas."""
        focus_areas = ["statistics", "invalid_area", "health"]
        result = _get_focus_area_guidance(focus_areas)
        
        # Should include only valid areas
        self.assertIn("**Statistics**:", result)
        self.assertIn("**Health**:", result)
        self.assertNotIn("invalid_area", result)
    
    def test_empty_focus_areas(self):
        """Test focus area guidance with empty list."""
        result = _get_focus_area_guidance([])
        
        # Should provide default guidance
        self.assertIn("Focus on comprehensive analysis across all areas", result)
    
    def test_all_focus_areas(self):
        """Test focus area guidance with all valid areas."""
        focus_areas = ["statistics", "recommendations", "purchases", "health", "trends"]
        result = _get_focus_area_guidance(focus_areas)
        
        # Should include all areas
        self.assertIn("**Statistics**:", result)
        self.assertIn("**Recommendations**:", result)
        self.assertIn("**Purchases**:", result)
        self.assertIn("**Health**:", result)
        self.assertIn("**Trends**:", result)
    
    def test_case_insensitive_focus_areas(self):
        """Test focus area guidance is case insensitive."""
        focus_areas = ["STATISTICS", "Health", "recommendations"]
        result = _get_focus_area_guidance(focus_areas)
        
        # Should handle case variations
        self.assertIn("**Statistics**:", result)
        self.assertIn("**Health**:", result)
        self.assertIn("**Recommendations**:", result)


class TestPromptIntegration(unittest.TestCase):
    """Test cases for prompt integration scenarios."""
    
    def test_general_template_prompt(self):
        """Test general template prompt generation."""
        result = get_collection_insights_prompt()
        
        # Should generate valid prompt structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "collection_insights")
        
        # Content should be comprehensive template
        content = result["messages"][0]["content"]["text"]
        self.assertIn("comprehensive insights", content.lower())
    
    def test_specific_collection_prompt(self):
        """Test specific collection prompt generation."""
        collection_data = {
            "stats": {"total_bands": 25, "total_albums": 150},
            "bands": [{"name": "Test Band", "albums_count": 6}]
        }
        
        result = get_collection_insights_prompt(collection_data=collection_data)
        
        # Should generate specific analysis prompt
        content = result["messages"][0]["content"]["text"]
        self.assertIn("25", content)
        self.assertIn("150", content)
        self.assertIn("Test Band", content)
    
    def test_parameter_combinations(self):
        """Test various parameter combinations."""
        # Basic scope with focus areas
        result1 = get_collection_insights_prompt(
            insights_scope="basic",
            focus_areas=["health"]
        )
        content1 = result1["messages"][0]["content"]["text"]
        self.assertIn("basic insights", content1.lower())
        self.assertIn("FOCUS AREAS", content1)
        
        # Health-only scope with collection data
        collection_data = {"stats": {"total_bands": 10}}
        result2 = get_collection_insights_prompt(
            collection_data=collection_data,
            insights_scope="health_only"
        )
        content2 = result2["messages"][0]["content"]["text"]
        self.assertIn("10", content2)
        self.assertIn("health", content2.lower())
    
    def test_prompt_content_quality(self):
        """Test prompt content meets quality standards."""
        result = get_collection_insights_prompt()
        content = result["messages"][0]["content"]["text"]
        
        # Should be substantial content
        self.assertGreater(len(content), 1000)
        
        # Should include key guidance elements
        self.assertIn("INSTRUCTIONS:", content)
        self.assertIn("OUTPUT FORMAT:", content)
        self.assertIn("json", content.lower())
        self.assertIn("insights", content.lower())
        self.assertIn("recommendations", content.lower())


if __name__ == '__main__':
    unittest.main() 