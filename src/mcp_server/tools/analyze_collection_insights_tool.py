#!/usr/bin/env python3
"""
Music Collection MCP Server - Analyze Collection Insights Tool

This module contains the analyze_collection_insights_tool implementation.
"""

import logging
from typing import Any, Dict

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler

# Import required modules and functions
from src.core.tools.storage import load_collection_index, load_band_metadata

# Configure logging
logger = logging.getLogger(__name__)


class AnalyzeCollectionInsightsHandler(BaseToolHandler):
    """Handler for the analyze_collection_insights tool."""
    
    def __init__(self):
        super().__init__("analyze_collection_insights", "1.0.0")
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """Execute the analyze collection insights tool logic."""
        from src.models.analytics import CollectionAnalyzer
        
        # Load collection index and band metadata
        collection_index = load_collection_index()
        if not collection_index:
            raise ValueError("Collection index not found. Please run scan_music_folders first.")
        
        band_metadata = {}
        
        # Load metadata for all bands
        for band_entry in collection_index.bands:
            try:
                metadata = load_band_metadata(band_entry.name)
                if metadata:
                    band_metadata[band_entry.name] = metadata
            except Exception as e:
                logger.warning(f"Could not load metadata for band {band_entry.name}: {str(e)}")
        
        if not band_metadata:
            raise ValueError('No band metadata available for analysis. Try scanning your collection first.')
        
        # Perform comprehensive analysis
        insights = CollectionAnalyzer.analyze_collection(collection_index, band_metadata)
        
        # Create summary sections for easy consumption
        health_summary = {
            'overall_health': insights.health_metrics.get_health_level(),
            'overall_score': insights.health_metrics.overall_score,
            'key_strengths': insights.health_metrics.strengths[:3],
            'main_weaknesses': insights.health_metrics.weaknesses[:3],
            'top_recommendations': insights.health_metrics.recommendations[:5]
        }
        
        type_analysis_summary = {
            'dominant_types': insights.type_analysis.dominant_types,
            'missing_types': insights.type_analysis.missing_types,
            'diversity_score': insights.type_analysis.type_diversity_score,
            'album_to_ep_ratio': insights.type_analysis.album_to_ep_ratio,
            'live_percentage': insights.type_analysis.live_percentage,
            'demo_percentage': insights.type_analysis.demo_percentage
        }
        
        recommendations_summary = {
            'type_recommendations_count': len(insights.type_recommendations),
            'high_priority_type_recs': [
                rec.model_dump() for rec in insights.type_recommendations 
                if rec.priority == "High"
            ][:5],
            'edition_upgrades_count': len(insights.edition_upgrades),
            'organization_recommendations': insights.organization_recommendations[:5]
        }
        
        # Convert insights to serializable format
        insights_dict = insights.model_dump()
        
        return {
            'status': 'success',
            'insights': insights_dict,
            'collection_maturity': insights.collection_maturity,
            'health_summary': health_summary,
            'type_analysis_summary': type_analysis_summary,
            'recommendations_summary': recommendations_summary,
            'analytics_metadata': {
                'total_bands_analyzed': len(band_metadata),
                'total_albums_analyzed': sum(
                    len(metadata.albums) + len(metadata.albums_missing) 
                    for metadata in band_metadata.values()
                ),
                'analysis_timestamp': insights.generated_at,
                'collection_scan_date': collection_index.last_scan
            },
            'tool_info': self._create_tool_info(
                analysis_features=[
                    'type_distribution_analysis',
                    'health_metrics_scoring',
                    'maturity_assessment',
                    'recommendation_generation',
                    'value_scoring',
                    'discovery_potential',
                    'organization_analysis'
                ]
            )
        }


# Create handler instance
_handler = AnalyzeCollectionInsightsHandler()

@mcp.tool()
def analyze_collection_insights_tool() -> Dict[str, Any]:
    """
    Generate comprehensive collection analytics and insights.
    
    This tool performs deep analysis of your entire music collection and provides actionable insights.
    No parameters needed - it analyzes your complete collection automatically.
    
    WHAT THIS TOOL ANALYZES:
    
    1. Collection Maturity Assessment:
       - Beginner: 1-9 bands, 1-24 albums, 1-2 album types
       - Intermediate: 10-24 bands, 25-74 albums, 3-4 album types  
       - Advanced: 25-49 bands, 75-199 albums, 5-6 album types
       - Expert: 50-99 bands, 200-499 albums, 6-7 album types
       - Master: 100+ bands, 500+ albums, 7-8 album types
    
    2. Album Type Distribution Analysis:
       - Compares your collection against ideal ratios
       - Ideal: Album 55%, EP 15%, Demo 10%, Live 8%, Compilation 5%, Instrumental 4%, Split 2%, Single 1%
       - Identifies missing or underrepresented album types
       - Calculates type diversity score (0-100)
    
    3. Collection Health Metrics (0-100 scores):
       - Overall Health: Composite score of all factors
       - Type Diversity: How well-balanced your album types are
       - Genre Diversity: Variety of musical genres represented
       - Completion Score: Ratio of local vs missing albums
       - Organization Score: Folder structure and naming compliance
       - Quality Score: Based on ratings and analysis data
    
    4. Edition Analysis:
       - Tracks Deluxe, Limited, Anniversary, Remastered editions
       - Identifies upgrade opportunities (Standard → Deluxe)
       - Calculates edition prevalence percentages
    
    5. Personalized Recommendations:
       - Missing album type suggestions for each band
       - Edition upgrade opportunities
       - Organization improvement suggestions
       - Collection completion strategies
    
    6. Value and Rarity Assessment:
       - Collection value score based on rare items
       - Limited editions, early albums, demos boost value
       - Instrumental and split releases add rarity points
    
    7. Discovery Potential:
       - Identifies opportunities for music discovery
       - Based on collection patterns and similar band networks
       - Suggests expansion directions
    
    8. Pattern Analysis:
       - Decade distribution (which eras you prefer)
       - Genre trends and preferences
       - Band completion rates (how complete each band's discography is)
       - Collection growth patterns
    
    EXAMPLE INSIGHTS YOU'LL GET:
    - "Your collection is Expert level with strong Metal representation"
    - "You're missing EPs for 12 bands - consider adding Metallica's 'Creeping Death EP'"
    - "85% of your albums are local, 15% missing - good completion rate"
    - "Your collection value is High due to 23 limited editions and 15 demo recordings"
    - "Type diversity: 78/100 - well-balanced but could use more Live albums"
    - "Discovery potential: High - 47 similar bands identified for expansion"
    
    WHEN TO USE THIS TOOL:
    - After scanning your collection for the first time
    - To get recommendations for collection improvement
    - To track your collection's growth and health over time
    - To identify gaps in your collection
    - To understand your music preferences and patterns
    - Before planning music purchases or acquisitions
    
    Returns:
        Dict containing comprehensive collection insights:
        - status: 'success' or 'error' 
        - insights: Complete analytics object with all detailed analysis
        - collection_maturity: Your collection's maturity level (Beginner to Master)
        - health_summary: Key health metrics and top recommendations
        - type_analysis_summary: Album type distribution vs ideal ratios
        - recommendations_summary: Top recommendations by category with counts
        - analytics_metadata: Analysis details (bands analyzed, timestamp, etc.)
    """
    return _handler.execute() 