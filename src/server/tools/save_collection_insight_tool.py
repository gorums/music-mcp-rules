#!/usr/bin/env python3
"""
Music Collection MCP Server - Save Collection Insight Tool

This module contains the save_collection_insight_tool implementation.
"""

import logging
from typing import Any, Dict

from ..core import mcp

# Import tool implementation - using absolute imports
from src.tools.storage import save_collection_insight
from src.models.collection import CollectionInsight

# Configure logging
logger = logging.getLogger(__name__)

@mcp.tool()
def save_collection_insight_tool(
    insights: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save collection-wide insights and analytics.
    
    This tool stores comprehensive collection insights including:
    - Collection insights and analysis text
    - Actionable recommendations for the collection
    - Top-rated bands listing
    - Suggested album purchases
    - Overall collection health assessment
    - Generated at timestamp for tracking
    
    Args:
        insights: Insights data dictionary containing collection analytics
        
    Returns:
        Dict containing comprehensive operation status with validation results,
        file operations, collection sync, and insights summary
    
    INSIGHTS SCHEMA:
    ===============
    The insights parameter must be a dictionary with the following structure:
    
    OPTIONAL FIELDS:
    ================
    - insights (array of strings): Collection insight text descriptions
    - recommendations (array of strings): Actionable recommendations for improving collection
    - top_rated_bands (array of strings): Names of highest rated bands in collection
    - suggested_purchases (array of strings): Albums suggested for acquisition
    - collection_health (string): Overall collection health ('Excellent', 'Good', 'Fair', 'Poor')
    
    COLLECTION HEALTH VALUES:
    =========================
    - 'Excellent': Collection is in optimal state
    - 'Good': Collection is in good condition with minor improvements needed
    - 'Fair': Collection has some issues that should be addressed
    - 'Poor': Collection has significant issues requiring attention
    
    EXAMPLE INSIGHTS:
    =================
    {
        "insights": [
            "Your collection shows strong representation in rock and metal genres",
            "Missing albums are concentrated in 1990s releases",
            "Average collection rating is 7.8/10 indicating high quality selection"
        ],
        "recommendations": [
            "Consider adding more jazz albums to diversify genres",
            "Focus on completing Pink Floyd discography - 3 albums missing",
            "Review low-rated albums for potential removal"
        ],
        "top_rated_bands": ["Pink Floyd", "Led Zeppelin", "The Beatles"],
        "suggested_purchases": [
            "Pink Floyd - Wish You Were Here",
            "Led Zeppelin - Physical Graffiti",
            "The Beatles - Revolver"
        ],
        "collection_health": "Good"
    """
    try:
        # Validate input parameters
        if insights is None:
            return {
                'status': 'error',
                'message': 'Invalid insights parameter: insights is required and must be a dictionary',
                'validation_results': {
                    "schema_valid": False,
                    "validation_errors": ["insights is required and must be a dictionary"],
                    "insights_count": 0,
                    "recommendations_count": 0,
                    "top_rated_bands_count": 0,
                    "suggested_purchases_count": 0,
                    "collection_health_valid": False
                },
                'tool_info': {
                    'tool_name': 'save_collection_insight',
                    'version': '1.0.0'
                }
            }
            
        if not isinstance(insights, dict):
            return {
                'status': 'error',
                'message': 'Invalid insights parameter: must be dictionary',
                'validation_results': {
                    "schema_valid": False,
                    "validation_errors": ["Invalid insights parameter: must be dictionary"],
                    "insights_count": 0,
                    "recommendations_count": 0,
                    "top_rated_bands_count": 0,
                    "suggested_purchases_count": 0,
                    "collection_health_valid": False
                },
                'tool_info': {
                    'tool_name': 'save_collection_insight',
                    'version': '1.0.0'
                }
            }
        
        # Convert dictionary to CollectionInsight object with validation
        try:
            # Custom validation to provide specific error messages
            validation_errors = []
            
            # Validate insights field
            if 'insights' in insights:
                if not isinstance(insights['insights'], list):
                    validation_errors.append("Field 'insights' must be a list of strings")
                else:
                    for item in insights['insights']:
                        if not isinstance(item, str):
                            validation_errors.append("All items in 'insights' must be strings")
                            break
            
            # Validate recommendations field
            if 'recommendations' in insights:
                if not isinstance(insights['recommendations'], list):
                    validation_errors.append("Field 'recommendations' must be a list of strings")
                else:
                    for item in insights['recommendations']:
                        if not isinstance(item, str):
                            validation_errors.append("All items in 'recommendations' must be strings")
                            break
            
            # Validate top_rated_bands field
            if 'top_rated_bands' in insights:
                if not isinstance(insights['top_rated_bands'], list):
                    validation_errors.append("Field 'top_rated_bands' must be a list of strings")
                else:
                    for item in insights['top_rated_bands']:
                        if not isinstance(item, str):
                            validation_errors.append("All items in 'top_rated_bands' must be strings")
                            break
            
            # Validate suggested_purchases field
            if 'suggested_purchases' in insights:
                if not isinstance(insights['suggested_purchases'], list):
                    validation_errors.append("Field 'suggested_purchases' must be a list of strings")
                else:
                    for item in insights['suggested_purchases']:
                        if not isinstance(item, str):
                            validation_errors.append("All items in 'suggested_purchases' must be strings")
                            break
            
            # Validate collection_health field
            if 'collection_health' in insights:
                if not isinstance(insights['collection_health'], str):
                    validation_errors.append("Field 'collection_health' must be a string")
                elif insights['collection_health'] not in ['Excellent', 'Good', 'Fair', 'Poor']:
                    validation_errors.append("Field 'collection_health' must be one of: ['Excellent', 'Good', 'Fair', 'Poor']")
            
            # If there are validation errors, return them
            if validation_errors:
                return {
                    'status': 'error',
                    'message': 'Insights validation failed',
                    'validation_results': {
                        "schema_valid": False,
                        "validation_errors": validation_errors,
                        "insights_count": 0,
                        "recommendations_count": 0,
                        "top_rated_bands_count": 0,
                        "suggested_purchases_count": 0,
                        "collection_health_valid": False
                    },
                    'tool_info': {
                        'tool_name': 'save_collection_insight',
                        'version': '1.0.0'
                    }
                }
            
            collection_insight = CollectionInsight(**insights)
        except Exception as validation_error:
            return {
                'status': 'error',
                'message': f'Insights validation failed: {str(validation_error)}',
                'validation_results': {
                    "schema_valid": False,
                    "validation_errors": [str(validation_error)],
                    "insights_count": 0,
                    "recommendations_count": 0,
                    "top_rated_bands_count": 0,
                    "suggested_purchases_count": 0,
                    "collection_health_valid": False
                },
                'tool_info': {
                    'tool_name': 'save_collection_insight',
                    'version': '1.0.0'
                }
            }
        
        result = save_collection_insight(collection_insight)
        
        # Build comprehensive response structure
        insights_count = len(collection_insight.insights)
        recommendations_count = len(collection_insight.recommendations)
        top_rated_bands_count = len(collection_insight.top_rated_bands)
        suggested_purchases_count = len(collection_insight.suggested_purchases)
        
        # Build comprehensive response
        comprehensive_result = {
            'status': result.get('status', 'success'),
            'message': f"Collection insights saved successfully with {insights_count} insights and {recommendations_count} recommendations",
            'validation_results': {
                'schema_valid': True,
                'validation_errors': [],
                'fields_validated': list(insights.keys()),
                'insights_count': insights_count,
                'recommendations_count': recommendations_count,
                'top_rated_bands_count': top_rated_bands_count,
                'suggested_purchases_count': suggested_purchases_count,
                'collection_health_valid': True
            },
            'file_operations': {
                'backup_created': True,
                'merged_with_existing': result.get('file_existed_before', False),
                'last_updated': result.get('generated_at', ''),
                'collection_index_file': result.get('file_path', '')
            },
            'collection_sync': {
                'index_updated': True,
                'insights_added': True,
                'index_errors': []
            },
            'insights_summary': {
                'insights_count': insights_count,
                'recommendations_count': recommendations_count,
                'top_rated_bands_count': top_rated_bands_count,
                'suggested_purchases_count': suggested_purchases_count,
                'collection_health': collection_insight.collection_health,
                'has_insights': insights_count > 0,
                'has_recommendations': recommendations_count > 0,
                'generated_at': result.get('generated_at', '')
            },
            'tool_info': {
                'tool_name': 'save_collection_insight',
                'version': '1.0.0',
                'parameters_used': {
                    'insights_fields': list(insights.keys())
                }
            }
        }
        
        return comprehensive_result
        
    except Exception as e:
        logger.error(f"Error in save_collection_insight tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'tool_info': {
                'tool_name': 'save_collection_insight',
                'version': '1.0.0'
            }
        } 