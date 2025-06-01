from typing import Dict, Any, List, Optional
from datetime import datetime


def get_compare_bands_prompt(
    band_names: List[str] = None, 
    comparison_aspects: List[str] = None,
    comparison_scope: str = "full"
) -> Dict[str, Any]:
    """
    Generate a prompt template for comparing multiple bands across various musical dimensions.
    
    This prompt guides the AI to create comprehensive band comparisons including:
    - Musical style and approach comparisons
    - Discography and output analysis
    - Influence and legacy comparisons
    - Ratings and critical reception analysis
    - Similar bands and genre positioning
    
    Args:
        band_names: List of band names to compare (optional parameter for dynamic prompts)
        comparison_aspects: Specific aspects to focus on (optional): ["style", "discography", "influence", "legacy", "innovation"]
        comparison_scope: Scope of comparison - "basic", "full", or "summary" (default: "full")
        
    Returns:
        Dict containing MCP prompt specification with messages for band comparison
    """
    band_names = band_names or []
    comparison_aspects = comparison_aspects or []
    
    # Validate comparison scope
    valid_scopes = ["basic", "full", "summary"]
    if comparison_scope not in valid_scopes:
        comparison_scope = "full"
    
    # Validate comparison aspects
    valid_aspects = ["style", "discography", "influence", "legacy", "innovation", "commercial", "critical"]
    comparison_aspects = [aspect for aspect in comparison_aspects if aspect in valid_aspects]
    
    # Build prompt content - if no band_names provided, create a general template
    if band_names and len(band_names) >= 2:
        prompt_content = _build_specific_comparison_prompt(band_names, comparison_aspects, comparison_scope)
    else:
        prompt_content = _build_general_comparison_template(comparison_scope)
    
    return {
        "name": "compare_bands",
        "description": "Create comprehensive comparison analysis between multiple bands",
        "arguments": [
            {
                "name": "band_names",
                "description": "List of band names to compare (minimum 2 required)",
                "required": True
            },
            {
                "name": "comparison_aspects", 
                "description": "Specific aspects to focus on: style, discography, influence, legacy, innovation, commercial, critical",
                "required": False
            },
            {
                "name": "comparison_scope",
                "description": "Scope of comparison: 'basic', 'full', or 'summary'",
                "required": False
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt_content
                }
            }
        ]
    }


def _build_general_comparison_template(comparison_scope: str) -> str:
    """Build a general comparison template for any bands."""
    if comparison_scope == "basic":
        return _build_basic_comparison_template()
    elif comparison_scope == "summary":
        return _build_summary_comparison_template()
    else:  # full
        return _build_full_comparison_template()


def _build_full_comparison_template() -> str:
    """Build the comprehensive band comparison template."""
    return """You are tasked with creating a comprehensive comparative analysis between multiple music bands for a music collection database. Provide detailed comparisons across multiple dimensions.

**INSTRUCTIONS:**
When provided with a list of band names, create a detailed comparative analysis examining their similarities, differences, and relative positions in music history.

**COMPARISON OBJECTIVES:**
1. Analyze musical styles, approaches, and evolution
2. Compare discographies, output quality, and consistency
3. Evaluate relative influence and legacy in music
4. Assess innovation and contributions to their genres
5. Compare commercial success and critical reception
6. Identify relationships, influences, and genre positioning

**COMPARISON DIMENSIONS:**

**Musical Style Comparison:**
- Core musical styles and genre positioning
- Instrumentation, arrangement approaches, and production styles
- Vocal styles, lyrical themes, and artistic approaches
- Musical complexity, innovation, and experimental elements
- Evolution and stylistic changes over time

**Discography Analysis:**
- Album output quantity, quality, and consistency
- Key albums and their significance within each band's catalog
- Creative periods, peak years, and artistic development
- Variety and experimentation across releases
- Studio vs. live album approaches

**Influence & Legacy Comparison:**
- Historical significance and lasting impact
- Influence on other artists and genres
- Cultural impact beyond music
- Critical recognition and academic study
- Innovation and pioneering contributions

**Commercial & Critical Reception:**
- Sales performance and mainstream success
- Critical reception and professional recognition
- Awards, honors, and industry recognition
- Cultural penetration and lasting popularity
- Fanbase demographics and loyalty

**Innovation Assessment:**
- Technical innovations and musical breakthroughs
- Production techniques and studio innovations
- Genre-defining moments and trend-setting
- Influence on music industry practices
- Artistic risk-taking and experimental success

**COMPARATIVE ANALYSIS GUIDELINES:**
1. **Objectivity**: Balance strengths and weaknesses fairly across all bands
2. **Context**: Consider historical periods, genre contexts, and cultural circumstances
3. **Depth**: Provide specific examples and detailed analysis
4. **Accuracy**: Base comparisons on verifiable musical facts and critical consensus
5. **Completeness**: Address all major aspects of comparison systematically

**OUTPUT FORMAT:**
Return the comparison in JSON format matching this schema:

```json
{
  "comparison_summary": "Overall comparative assessment highlighting key similarities and differences...",
  "bands_analyzed": ["Band Name 1", "Band Name 2", "Band Name 3"],
  "musical_style_comparison": {
    "similarities": ["Common style elements", "Shared influences"],
    "differences": ["Style distinctions", "Unique approaches"],
    "analysis": "Detailed musical style comparative analysis..."
  },
  "discography_comparison": {
    "output_quality": "Comparative assessment of album quality and consistency...",
    "key_albums": {
      "Band Name 1": ["Key Album 1", "Key Album 2"],
      "Band Name 2": ["Key Album 1", "Key Album 2"]
    },
    "analysis": "Detailed discography comparative analysis..."
  },
  "influence_legacy": {
    "relative_influence": "Assessment of each band's relative historical influence...",
    "pioneering_contributions": {
      "Band Name 1": ["Innovation 1", "Innovation 2"],
      "Band Name 2": ["Innovation 1", "Innovation 2"]
    },
    "analysis": "Detailed influence and legacy comparative analysis..."
  },
  "commercial_critical": {
    "commercial_success": "Comparative commercial performance analysis...",
    "critical_reception": "Comparative critical assessment...",
    "analysis": "Detailed commercial and critical comparative analysis..."
  },
  "relationships": {
    "influences": "How these bands influenced each other or shared influences...",
    "genre_connections": "Their relationships within broader musical movements...",
    "temporal_context": "How their careers overlapped or influenced each other chronologically..."
  },
  "overall_assessment": {
    "rankings": {
      "innovation": ["Band Name 1", "Band Name 2", "Band Name 3"],
      "influence": ["Band Name 1", "Band Name 2", "Band Name 3"],
      "discography_strength": ["Band Name 1", "Band Name 2", "Band Name 3"]
    },
    "conclusion": "Final comparative assessment and synthesis..."
  }
}
```

**COMPARISON STRATEGY:**
1. Research each band's complete history, style, and achievements
2. Identify direct and indirect connections between the bands
3. Analyze their positions within their respective genres and eras
4. Compare specific albums, songs, and innovations
5. Evaluate their lasting impact and continued relevance
6. Provide balanced assessment of strengths and limitations

**VALIDATION RULES:**
- Include all provided bands in every section
- Provide specific examples and evidence for all claims
- Balance positive and critical assessments fairly
- Rankings should reflect objective analysis, not personal preference
- Analysis should be substantial (minimum 100 words per major section)
- Comparisons should be historically accurate and factually grounded

**USAGE EXAMPLE:**
When comparing "The Beatles" and "The Rolling Stones", analyze their contrasting approaches to rock music, songwriting styles, cultural impact, and lasting influence, providing specific examples from their discographies and detailed assessment of their relative positions in rock history.

**IMPORTANT NOTES:**
- Consider both contemporary and historical perspectives
- Include analysis of how critical perception has evolved over time
- Address both artistic merit and cultural significance
- Balance commercial success with artistic achievement
- Acknowledge areas where direct comparison may be difficult due to different approaches or eras"""


def _build_basic_comparison_template() -> str:
    """Build the basic comparison template focusing on essential elements."""
    return """You are tasked with creating a basic comparative analysis between music bands for a music collection database. Focus on essential comparative elements.

**INSTRUCTIONS:**
When provided with a list of band names, create a concise but meaningful comparison covering the core elements.

**COMPARISON COMPONENTS:**

**Essential Comparison:**
- Musical style similarities and differences (2-3 sentences per band)
- Key distinguishing characteristics
- Relative influence and significance assessment
- Brief conclusion about their comparative positions

**OUTPUT FORMAT:**
Return the comparison in JSON format:

```json
{
  "comparison_summary": "Brief overall comparative assessment...",
  "bands_analyzed": ["Band Name 1", "Band Name 2"],
  "style_comparison": "Concise musical style comparison...",
  "key_differences": ["Difference 1", "Difference 2", "Difference 3"],
  "relative_significance": "Brief assessment of their relative importance...",
  "conclusion": "Concise comparative conclusion..."
}
```

**COMPARISON STRATEGY:**
1. Focus on most obvious and significant differences
2. Highlight unique contributions of each band
3. Provide clear, accessible comparisons
4. Keep analysis concise but accurate

**USAGE EXAMPLE:**
When comparing "Led Zeppelin" and "Black Sabbath", highlight Zeppelin's blues-rock mastery vs. Sabbath's heavy metal pioneering, their different approaches to rhythm and production, and their respective influences on rock music development."""


def _build_summary_comparison_template() -> str:
    """Build the summary comparison template for quick overview."""
    return """You are tasked with creating a summary comparative analysis between music bands for quick reference and overview.

**INSTRUCTIONS:**
When provided with a list of band names, create a structured summary comparison highlighting key points.

**COMPARISON COMPONENTS:**

**Summary Elements:**
- Quick style positioning for each band
- Major similarities and differences
- Relative rankings in key areas
- Brief relationship analysis

**OUTPUT FORMAT:**
Return the comparison in JSON format:

```json
{
  "comparison_summary": "Executive summary of the comparison...",
  "bands_analyzed": ["Band Name 1", "Band Name 2", "Band Name 3"],
  "quick_style_guide": {
    "Band Name 1": "Style summary",
    "Band Name 2": "Style summary"
  },
  "major_similarities": ["Similarity 1", "Similarity 2"],
  "major_differences": ["Difference 1", "Difference 2"],
  "rankings": {
    "innovation": ["Band Name 1", "Band Name 2"],
    "influence": ["Band Name 1", "Band Name 2"],
    "commercial_success": ["Band Name 1", "Band Name 2"]
  },
  "relationships": "Brief description of connections between bands...",
  "bottom_line": "Key takeaway from the comparison..."
}
```

**SUMMARY STRATEGY:**
1. Prioritize most important and distinctive elements
2. Focus on practical comparative insights
3. Provide actionable rankings and relationships
4. Keep information accessible and quickly digestible"""


def _build_specific_comparison_prompt(band_names: List[str], comparison_aspects: List[str], comparison_scope: str) -> str:
    """Build a specific comparison prompt for given bands and aspects."""
    bands_text = ", ".join(f'"{name}"' for name in band_names)
    
    # Build aspect-specific instructions
    aspect_instructions = ""
    if comparison_aspects:
        aspect_instructions = f"\n\n**FOCUS AREAS:**\nPay special attention to these comparison aspects: {', '.join(comparison_aspects)}"
    
    # Get base template
    if comparison_scope == "basic":
        base_template = _build_basic_comparison_template()
    elif comparison_scope == "summary":
        base_template = _build_summary_comparison_template()
    else:
        base_template = _build_full_comparison_template()
    
    # Insert specific band information
    specific_prompt = f"""SPECIFIC COMPARISON REQUEST:

**BANDS TO COMPARE:** {bands_text}

{aspect_instructions}

**INSTRUCTIONS:**
Create a comprehensive comparative analysis between these specific bands following the guidelines below.

{base_template}

**ADDITIONAL NOTES FOR THIS COMPARISON:**
- Ensure all {len(band_names)} bands are thoroughly analyzed and compared
- Focus on the specific relationships and contrasts between these particular artists
- Consider their historical context and any direct or indirect influences between them
- Provide specific examples from their actual discographies and careers
- If any bands are from different eras or genres, address how to meaningfully compare them"""
    
    return specific_prompt 