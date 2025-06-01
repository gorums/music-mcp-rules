from typing import Dict, Any, List, Optional
from datetime import datetime


def get_collection_insights_prompt(
    collection_data: Dict[str, Any] = None,
    insights_scope: str = "comprehensive",
    focus_areas: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a prompt template for analyzing music collections and generating insights.
    
    This prompt guides the AI to create comprehensive collection analysis including:
    - Collection statistics analysis and trends
    - Actionable recommendations for improvement
    - Top-rated bands identification
    - Suggested album purchases for collection gaps
    - Overall collection health assessment
    
    Args:
        collection_data: Collection statistics and band data (optional parameter for dynamic prompts)
        insights_scope: Scope of analysis - "basic", "comprehensive", or "health_only" (default: "comprehensive")
        focus_areas: Specific areas to focus on: statistics, recommendations, purchases, health, trends
        
    Returns:
        Dict containing MCP prompt specification with messages for collection insights
    """
    focus_areas = focus_areas or []
    
    # Validate insights scope
    valid_scopes = ["basic", "comprehensive", "health_only"]
    if insights_scope not in valid_scopes:
        insights_scope = "comprehensive"
    
    # Build prompt content - if collection_data provided, create specific analysis prompt
    if collection_data:
        prompt_content = _build_specific_collection_analysis_prompt(collection_data, insights_scope, focus_areas)
    else:
        prompt_content = _build_general_insights_template(insights_scope, focus_areas)
    
    return {
        "name": "collection_insights",
        "description": "Generate comprehensive insights and analysis for music collections",
        "arguments": [
            {
                "name": "collection_data",
                "description": "Collection statistics and band data for analysis (optional)",
                "required": False
            },
            {
                "name": "insights_scope", 
                "description": "Scope of analysis: 'basic', 'comprehensive', or 'health_only'",
                "required": False
            },
            {
                "name": "focus_areas",
                "description": "Specific focus areas: statistics, recommendations, purchases, health, trends",
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


def _build_general_insights_template(insights_scope: str, focus_areas: List[str]) -> str:
    """Build a general insights template for any collection."""
    if insights_scope == "basic":
        return _build_basic_insights_template(focus_areas)
    elif insights_scope == "health_only":
        return _build_health_insights_template(focus_areas)
    else:  # comprehensive
        return _build_comprehensive_insights_template(focus_areas)


def _build_comprehensive_insights_template(focus_areas: List[str]) -> str:
    """Build the comprehensive collection insights template."""
    template = """You are tasked with generating comprehensive insights for a music collection. Analyze the collection data and provide actionable recommendations for improving and expanding the collection.

**INSTRUCTIONS:**
When provided with collection data including band information, statistics, and metadata, create detailed insights covering collection analysis, recommendations, and health assessment.

**ANALYSIS OBJECTIVES:**
1. Analyze collection composition, trends, and patterns
2. Identify strengths, weaknesses, and opportunities for improvement
3. Provide actionable recommendations for collection enhancement
4. Suggest specific album purchases to fill gaps
5. Assess overall collection health and completeness

**INSIGHT COMPONENTS:**

**Collection Analysis Insights:**
- Overall collection composition and size assessment
- Genre distribution analysis and diversity evaluation
- Completion rate analysis and missing album patterns
- Metadata coverage and data quality assessment
- Rating trends and quality indicators (if available)
- Historical collection development patterns

**Actionable Recommendations:**
- Specific actions to improve collection completeness
- Metadata enhancement recommendations
- Organization and cataloging improvements
- Focus areas for future acquisitions
- Data quality improvement suggestions
- Collection maintenance recommendations

**Top-Rated Bands Identification:**
- Bands with highest overall ratings or critical acclaim
- Most complete bands in terms of discography
- Bands with strongest metadata and analysis coverage
- Hidden gems or underappreciated artists in collection
- Bands representing collection's strongest areas

**Strategic Purchase Suggestions:**
- Missing albums from existing bands (priority acquisitions)
- Genre gaps that should be filled
- Essential albums missing from collection
- Albums that would improve collection balance
- Cult classics or critically acclaimed missing releases

**Collection Health Assessment:**
- Overall health status: Excellent, Good, Fair, or Poor
- Specific areas of strength and weakness
- Data integrity and completeness evaluation
- Organization and accessibility assessment
- Growth and development recommendations"""

    # Add focus area specific guidance
    if focus_areas:
        template += f"""

**FOCUS AREAS (prioritize these aspects):**
{_get_focus_area_guidance(focus_areas)}"""

    template += """

**INSIGHTS QUALITY GUIDELINES:**
1. **Actionable**: Provide specific, implementable recommendations
2. **Data-Driven**: Base insights on collection statistics and patterns
3. **Balanced**: Consider both strengths and areas for improvement
4. **Prioritized**: Rank recommendations by impact and feasibility
5. **Comprehensive**: Cover all major aspects of collection management
6. **Realistic**: Suggest achievable improvements within reasonable scope

**OUTPUT FORMAT:**
Return the insights in JSON format matching this schema:

```json
{
  "insights": [
    "Your collection shows strong representation in classic rock with 45% of albums from this genre",
    "Completion rate of 87% indicates excellent physical collection maintenance",
    "Missing albums are concentrated in 1990s releases, suggesting acquisition gap in that era",
    "High metadata coverage (92%) demonstrates good cataloging practices"
  ],
  "recommendations": [
    "Complete Pink Floyd discography - missing 3 essential albums including 'Animals'",
    "Add more female-fronted bands to improve gender diversity in collection",
    "Focus on acquiring 1990s alternative rock albums to fill identified gap",
    "Use analyze_band prompt to add ratings for 15 bands lacking analysis"
  ],
  "top_rated_bands": [
    "Pink Floyd",
    "Led Zeppelin", 
    "The Beatles",
    "Queen",
    "Deep Purple"
  ],
  "suggested_purchases": [
    "Pink Floyd - Animals",
    "Led Zeppelin - Physical Graffiti",
    "Radiohead - OK Computer",
    "Nirvana - Nevermind",
    "Soundgarden - Superunknown"
  ],
  "collection_health": "Good"
}
```

**COLLECTION HEALTH CRITERIA:**
- **Excellent**: >95% completion, >90% metadata coverage, balanced genres, comprehensive analysis
- **Good**: >80% completion, >70% metadata coverage, good genre variety, some analysis
- **Fair**: >60% completion, >50% metadata coverage, adequate variety, limited analysis
- **Poor**: <60% completion, <50% metadata coverage, narrow focus, minimal analysis

**ANALYSIS STRATEGY:**
1. Examine collection size, diversity, and completion metrics
2. Identify patterns in genre distribution and acquisition history
3. Assess data quality and metadata completeness
4. Evaluate collection balance and identify gaps
5. Prioritize recommendations by impact and feasibility
6. Suggest specific, actionable improvements

**VALIDATION RULES:**
- Insights must be specific and data-driven (minimum 3 insights)
- Recommendations must be actionable and prioritized (minimum 3 recommendations)
- Top-rated bands should reflect collection's actual strengths (3-8 bands)
- Purchase suggestions should address identified gaps (3-10 albums)
- Collection health must be one of: Excellent, Good, Fair, Poor
- All text should be substantial and meaningful (minimum 30 words per insight/recommendation)

**USAGE EXAMPLE:**
For a collection with 150 bands, 800 albums, 85% completion rate, strong in rock/metal but lacking jazz, you would provide insights about the collection's rock strength, recommendations to diversify into jazz, identify top rock bands, suggest essential jazz albums, and assess health as "Good" based on metrics.

**IMPORTANT NOTES:**
- Focus on patterns and trends rather than individual band details
- Balance positive observations with constructive improvement suggestions
- Consider collection size and scope when making recommendations
- Prioritize suggestions that provide maximum impact for effort invested
- Include both immediate actions and long-term strategic recommendations"""

    return template


def _build_basic_insights_template(focus_areas: List[str]) -> str:
    """Build the basic insights template focusing on essential elements."""
    template = """You are tasked with generating basic insights for a music collection. Focus on essential analysis and key recommendations.

**INSTRUCTIONS:**
When provided with collection data, create concise but meaningful insights covering the core elements.

**ANALYSIS COMPONENTS:**

**Essential Collection Insights:**
- Overall collection size and composition (2-3 key observations)
- Most significant strength or characteristic of the collection
- Primary area for improvement or growth
- Basic completion and quality assessment

**Key Recommendations:**
- Top 2-3 most impactful actions to improve the collection
- Focus on highest priority improvements

**Health Assessment:**
- Simple health status evaluation: Excellent, Good, Fair, or Poor
- Brief justification for health rating"""

    if focus_areas:
        template += f"""

**FOCUS AREAS (prioritize these aspects):**
{_get_focus_area_guidance(focus_areas)}"""

    template += """

**OUTPUT FORMAT:**
```json
{
  "insights": [
    "Collection demonstrates strong focus on classic rock with 180 albums",
    "Completion rate of 92% shows excellent physical collection management"
  ],
  "recommendations": [
    "Complete major band discographies - 12 bands missing key albums",
    "Add metadata for 25 bands lacking detailed information"
  ],
  "top_rated_bands": ["Pink Floyd", "Led Zeppelin", "The Beatles"],
  "suggested_purchases": [
    "Pink Floyd - Animals",
    "Led Zeppelin - IV",
    "The Beatles - Abbey Road"
  ],
  "collection_health": "Good"
}
```

**QUALITY GUIDELINES:**
- Keep insights concise but meaningful
- Focus on most impactful recommendations
- Provide 2-4 items per category
- Ensure health assessment is realistic"""

    return template


def _build_health_insights_template(focus_areas: List[str]) -> str:
    """Build the health-focused insights template."""
    template = """You are tasked with conducting a health assessment of a music collection. Focus on collection completeness, data quality, and maintenance recommendations.

**INSTRUCTIONS:**
When provided with collection data, evaluate the overall health and provide targeted recommendations for improvement.

**HEALTH ANALYSIS COMPONENTS:**

**Collection Health Metrics:**
- Completion rate analysis and missing album assessment
- Metadata coverage and data quality evaluation
- Organization and cataloging effectiveness
- Collection growth and maintenance patterns

**Health Recommendations:**
- Specific actions to improve collection completeness
- Data quality and metadata enhancement suggestions
- Organization and maintenance improvements
- Priority areas requiring immediate attention

**Health Status Assessment:**
- Overall health rating with detailed justification
- Specific strengths and weaknesses identification
- Improvement roadmap and priority actions"""

    if focus_areas:
        template += f"""

**FOCUS AREAS (prioritize these aspects):**
{_get_focus_area_guidance(focus_areas)}"""

    template += """

**OUTPUT FORMAT:**
```json
{
  "insights": [
    "Collection health is strong with 87% completion rate and good metadata coverage",
    "Data quality issues identified in 12% of band entries requiring attention"
  ],
  "recommendations": [
    "Complete missing album acquisitions for top 10 priority bands",
    "Update metadata for bands lacking formation dates and member information",
    "Run collection health scan to identify and resolve data inconsistencies"
  ],
  "top_rated_bands": ["Bands with complete data and high ratings"],
  "suggested_purchases": ["Priority missing albums for health improvement"],
  "collection_health": "Good"
}
```

**HEALTH ASSESSMENT CRITERIA:**
- Completion rate weight: 40%
- Metadata quality weight: 30% 
- Organization effectiveness weight: 20%
- Analysis coverage weight: 10%"""

    return template


def _build_specific_collection_analysis_prompt(
    collection_data: Dict[str, Any], 
    insights_scope: str,
    focus_areas: List[str]
) -> str:
    """Build specific collection analysis prompt with actual data."""
    
    # Extract key metrics from collection data
    stats = collection_data.get("stats", {})
    bands = collection_data.get("bands", [])
    insights = collection_data.get("insights", {})
    
    total_bands = stats.get("total_bands", 0)
    total_albums = stats.get("total_albums", 0)
    completion_rate = stats.get("completion_percentage", 0)
    metadata_coverage = stats.get("bands_with_metadata", 0) / max(total_bands, 1) * 100
    
    prompt = f"""Analyze this specific music collection and generate comprehensive insights.

**COLLECTION DATA SUMMARY:**
- Total Bands: {total_bands:,}
- Total Albums: {total_albums:,}
- Completion Rate: {completion_rate:.1f}%
- Metadata Coverage: {metadata_coverage:.1f}%
- Missing Albums: {stats.get("total_missing_albums", 0):,}
- Average Albums per Band: {stats.get("avg_albums_per_band", 0):.1f}

**GENRE DISTRIBUTION:**"""
    
    # Add genre information if available
    top_genres = stats.get("top_genres", {})
    if top_genres:
        for genre, count in sorted(top_genres.items(), key=lambda x: x[1], reverse=True)[:5]:
            prompt += f"\n- {genre}: {count} albums"
    else:
        prompt += "\n- Genre data not available"
    
    # Add band information
    if bands:
        prompt += f"\n\n**SAMPLE BANDS ({min(len(bands), 10)} of {len(bands)}):**"
        for band in bands[:10]:
            name = band.get("name", "Unknown")
            albums_count = band.get("albums_count", 0)
            missing = band.get("missing_albums_count", 0)
            has_metadata = "✓" if band.get("has_metadata", False) else "✗"
            has_analysis = "✓" if band.get("has_analysis", False) else "✗"
            
            prompt += f"\n- {name}: {albums_count} albums ({missing} missing) | Metadata: {has_metadata} | Analysis: {has_analysis}"
    
    # Add existing insights if available
    if insights:
        prompt += f"\n\n**EXISTING INSIGHTS:**"
        existing_insights = insights.get("insights", [])
        if existing_insights:
            for insight in existing_insights[:3]:
                prompt += f"\n- {insight}"
    
    prompt += f"""

**ANALYSIS REQUEST:**
Based on this collection data, provide {insights_scope} insights focusing on:"""
    
    if focus_areas:
        for area in focus_areas:
            prompt += f"\n- {area.title()} analysis and recommendations"
    else:
        prompt += "\n- Complete collection analysis across all areas"
    
    prompt += """

Generate insights in the specified JSON format with:
1. Data-driven insights based on the provided statistics
2. Specific recommendations addressing identified patterns
3. Top-rated bands from the actual collection (if ratings available)
4. Strategic purchase suggestions to address gaps
5. Accurate health assessment based on metrics

**IMPORTANT:** Base all insights and recommendations on the actual collection data provided above. Reference specific numbers, patterns, and bands from this collection."""
    
    return prompt


def _get_focus_area_guidance(focus_areas: List[str]) -> str:
    """Get specific guidance for focus areas."""
    guidance = []
    
    area_descriptions = {
        "statistics": "Analyze collection size, completion rates, genre distribution, and numerical trends",
        "recommendations": "Focus on actionable improvements for collection enhancement and organization", 
        "purchases": "Identify strategic album acquisitions to fill gaps and improve collection balance",
        "health": "Assess collection completeness, data quality, and maintenance requirements",
        "trends": "Identify patterns in collection development, genre evolution, and acquisition history"
    }
    
    for area in focus_areas:
        if area.lower() in area_descriptions:
            guidance.append(f"- **{area.title()}**: {area_descriptions[area.lower()]}")
    
    return "\n".join(guidance) if guidance else "- Focus on comprehensive analysis across all areas" 