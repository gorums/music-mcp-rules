"""
Band Structure Detection System

This module provides comprehensive analysis of band folder organization patterns,
structure consistency scoring, and recommendations for folder organization improvement.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from .band import AlbumType
from .album_parser import AlbumFolderParser


class StructureType(str, Enum):
    """
    Enumeration of folder structure types.
    
    Values:
        DEFAULT: Standard flat structure with "YYYY - Album Name (Edition?)" pattern
        ENHANCED: Type-based structure with "Type/YYYY - Album Name (Edition?)" pattern
        MIXED: Combination of both default and enhanced structures
        LEGACY: Albums without year prefix, just "Album Name" pattern
        UNKNOWN: Unable to determine structure type
    """
    DEFAULT = "default"
    ENHANCED = "enhanced"
    MIXED = "mixed"
    LEGACY = "legacy"
    UNKNOWN = "unknown"


class StructureConsistency(str, Enum):
    """
    Enumeration of structure consistency levels.
    
    Values:
        CONSISTENT: All albums follow the same pattern (90-100% consistency)
        MOSTLY_CONSISTENT: Most albums follow the same pattern (70-89% consistency)
        INCONSISTENT: Albums use multiple different patterns (below 70% consistency)
        UNKNOWN: Unable to determine consistency
    """
    CONSISTENT = "consistent"
    MOSTLY_CONSISTENT = "mostly_consistent"
    INCONSISTENT = "inconsistent"
    UNKNOWN = "unknown"


class FolderStructure(BaseModel):
    """
    Folder structure metadata for a band.
    
    Attributes:
        structure_type: Primary structure type used by the band
        consistency: Consistency level of folder organization
        consistency_score: Numerical score (0-100) representing consistency
        albums_analyzed: Number of albums analyzed for structure detection
        albums_with_year_prefix: Count of albums following year prefix pattern
        albums_without_year_prefix: Count of albums missing year prefix
        albums_with_type_folders: Count of albums organized in type folders
        detected_patterns: List of folder patterns found in band
        type_folders_found: List of type folders found (Album, Live, Demo, etc.)
        structure_score: Overall structure organization score (0-100)
        recommendations: List of specific improvement recommendations
        issues: List of identified structure issues
    """
    model_config = ConfigDict(
        # Serialize enums by value to eliminate Pydantic serialization warnings
        use_enum_values=True
    )
    
    structure_type: StructureType = Field(default=StructureType.UNKNOWN, description="Primary structure type")
    consistency: StructureConsistency = Field(default=StructureConsistency.UNKNOWN, description="Structure consistency level")
    consistency_score: int = Field(default=0, ge=0, le=100, description="Consistency score (0-100)")
    albums_analyzed: int = Field(default=0, ge=0, description="Number of albums analyzed")
    albums_with_year_prefix: int = Field(default=0, ge=0, description="Albums with year prefix")
    albums_without_year_prefix: int = Field(default=0, ge=0, description="Albums without year prefix")
    albums_with_type_folders: int = Field(default=0, ge=0, description="Albums in type folders")
    detected_patterns: List[str] = Field(default_factory=list, description="List of detected patterns")
    type_folders_found: List[str] = Field(default_factory=list, description="List of type folders found")
    structure_score: int = Field(default=0, ge=0, le=100, description="Overall structure score")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    issues: List[str] = Field(default_factory=list, description="Identified structure issues")

    def get_primary_pattern(self) -> str:
        """Get the most common pattern used by this band."""
        if not self.detected_patterns:
            return "unknown"
        
        # Return first pattern since we no longer have analysis_metadata
        return self.detected_patterns[0] if self.detected_patterns else "unknown"
    
    def get_organization_health(self) -> str:
        """Get overall organization health assessment."""
        if self.structure_score >= 90:
            return "excellent"
        elif self.structure_score >= 75:
            return "good"
        elif self.structure_score >= 50:
            return "fair"
        elif self.structure_score >= 25:
            return "poor"
        else:
            return "critical"
    
    def is_migration_recommended(self) -> bool:
        """Check if structure migration is recommended."""
        return (
            self.structure_type == StructureType.MIXED or
            self.consistency == StructureConsistency.INCONSISTENT or
            self.structure_score < 70
        )


class BandStructureDetector:
    """
    Comprehensive band structure detection and analysis system.
    
    Analyzes folder organization patterns within a band's directory,
    calculates consistency scores, and provides recommendations.
    """
    
    def __init__(self):
        """Initialize the structure detector."""
        self.parser = AlbumFolderParser()
    
    def detect_band_structure(self, band_folder_path: str) -> FolderStructure:
        """
        Detect and analyze folder structure for a band.
        
        Args:
            band_folder_path: Path to the band's folder
            
        Returns:
            FolderStructure object with complete analysis
        """
        band_path = Path(band_folder_path)
        
        if not band_path.exists() or not band_path.is_dir():
            return FolderStructure(
                structure_type=StructureType.UNKNOWN,
                consistency=StructureConsistency.UNKNOWN,
                issues=["Band folder not found or inaccessible"]
            )
        
        # Get raw structure analysis from existing parser
        raw_analysis = self.parser.detect_folder_structure_type(str(band_path))
        
        # Perform detailed album analysis
        album_analysis = self._analyze_albums_in_detail(band_path)
        
        # Calculate scores and metrics
        structure_metrics = self._calculate_structure_metrics(album_analysis)
        
        # Generate comprehensive recommendations
        recommendations = self._generate_comprehensive_recommendations(
            album_analysis, structure_metrics, raw_analysis
        )
        
        # Identify specific issues
        issues = self._identify_structure_issues(album_analysis, structure_metrics)
        
        # Create FolderStructure object
        return FolderStructure(
            structure_type=StructureType(raw_analysis['structure_type']),
            consistency=self._determine_consistency_level(structure_metrics['consistency_score']),
            consistency_score=structure_metrics['consistency_score'],
            albums_analyzed=album_analysis['total_albums'],
            albums_with_year_prefix=album_analysis['albums_with_year'],
            albums_without_year_prefix=album_analysis['albums_without_year'],
            albums_with_type_folders=album_analysis['albums_in_type_folders'],
            detected_patterns=list(album_analysis['pattern_counts'].keys()),
            type_folders_found=album_analysis['type_folders'],
            structure_score=structure_metrics['overall_score'],
            recommendations=recommendations,
            issues=issues
        )
    
    def _analyze_albums_in_detail(self, band_path: Path) -> Dict[str, Any]:
        """
        Perform detailed analysis of all albums in band folder.
        
        Args:
            band_path: Path to band folder
            
        Returns:
            Detailed album analysis data
        """
        analysis = {
            'total_albums': 0,
            'albums_with_year': 0,
            'albums_without_year': 0,
            'albums_in_type_folders': 0,
            'pattern_counts': {},
            'type_folders': [],
            'type_folder_details': {},
            'album_details': [],
            'direct_albums': 0,
            'nested_albums': 0
        }
        
        # Get all direct subdirectories
        subdirectories = [d for d in band_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        for folder in subdirectories:
            # Check if this is a type folder (contains album subfolders)
            subfolders = [d for d in folder.iterdir() if d.is_dir() and not d.name.startswith('.')]
            
            if subfolders and self._is_type_folder(folder.name):
                # This is a type folder
                analysis['type_folders'].append(folder.name)
                type_detail = {
                    'albums': [],
                    'total_albums': len(subfolders),
                    'patterns': {}
                }
                
                for album_folder in subfolders:
                    album_info = self._analyze_single_album(album_folder, True)
                    analysis['total_albums'] += 1
                    analysis['albums_in_type_folders'] += 1
                    analysis['nested_albums'] += 1
                    
                    # Update pattern counts
                    pattern = album_info['pattern_type']
                    analysis['pattern_counts'][pattern] = analysis['pattern_counts'].get(pattern, 0) + 1
                    type_detail['patterns'][pattern] = type_detail['patterns'].get(pattern, 0) + 1
                    
                    # Update year statistics
                    if album_info['has_year']:
                        analysis['albums_with_year'] += 1
                    else:
                        analysis['albums_without_year'] += 1
                    
                    type_detail['albums'].append(album_info)
                    analysis['album_details'].append(album_info)
                
                analysis['type_folder_details'][folder.name] = type_detail
                
            else:
                # This is a direct album folder
                album_info = self._analyze_single_album(folder, False)
                analysis['total_albums'] += 1
                analysis['direct_albums'] += 1
                
                # Update pattern counts
                pattern = album_info['pattern_type']
                analysis['pattern_counts'][pattern] = analysis['pattern_counts'].get(pattern, 0) + 1
                
                # Update year statistics
                if album_info['has_year']:
                    analysis['albums_with_year'] += 1
                else:
                    analysis['albums_without_year'] += 1
                
                analysis['album_details'].append(album_info)
        
        return analysis
    
    def _analyze_single_album(self, album_path: Path, in_type_folder: bool) -> Dict[str, Any]:
        """
        Analyze a single album folder.
        
        Args:
            album_path: Path to album folder
            in_type_folder: Whether album is in a type folder
            
        Returns:
            Album analysis data
        """
        parsed = self.parser.parse_folder_name(album_path.name)
        
        return {
            'folder_name': album_path.name,
            'folder_path': str(album_path),
            'pattern_type': parsed['pattern_type'],
            'has_year': bool(parsed['year']),
            'year': parsed['year'],
            'album_name': parsed['album_name'],
            'edition': parsed['edition'],
            'in_type_folder': in_type_folder,
            'type_folder': album_path.parent.name if in_type_folder else '',
            'compliance_score': self._calculate_album_compliance_score(parsed, in_type_folder)
        }
    
    def _calculate_album_compliance_score(self, parsed: Dict[str, str], in_type_folder: bool) -> int:
        """Calculate compliance score for a single album."""
        score = 100
        
        # Year prefix scoring
        if not parsed['year']:
            score -= 30
        elif not self.parser._is_valid_year(parsed['year']):
            score -= 15
        
        # Album name scoring
        if not parsed['album_name'] or len(parsed['album_name'].strip()) < 2:
            score -= 40
        
        # Edition scoring (bonus for having editions)
        if parsed['edition']:
            normalized = self.parser.normalize_edition(parsed['edition'])
            if normalized == parsed['edition']:
                score += 5  # Bonus for properly formatted edition
            else:
                score -= 5  # Penalty for non-standard edition format
        
        # Type folder organization bonus
        if in_type_folder:
            score += 10
        
        return max(0, min(100, score))
    
    def _is_type_folder(self, folder_name: str) -> bool:
        """Check if folder name represents an album type folder."""
        # Check for exact type name matches
        for album_type in AlbumType:
            if folder_name.lower() == album_type.value.lower():
                return True
        
        # Check for keyword matches
        type_keywords = {
            'album': AlbumType.ALBUM,
            'albums': AlbumType.ALBUM,
            'live': AlbumType.LIVE,
            'compilation': AlbumType.COMPILATION,
            'compilations': AlbumType.COMPILATION,
            'ep': AlbumType.EP,
            'eps': AlbumType.EP,
            'single': AlbumType.SINGLE,
            'singles': AlbumType.SINGLE,
            'demo': AlbumType.DEMO,
            'demos': AlbumType.DEMO,
            'instrumental': AlbumType.INSTRUMENTAL,
            'instrumentals': AlbumType.INSTRUMENTAL,
            'split': AlbumType.SPLIT,
            'splits': AlbumType.SPLIT
        }
        
        return folder_name.lower() in type_keywords
    
    def _calculate_structure_metrics(self, album_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive structure metrics.
        
        Args:
            album_analysis: Detailed album analysis data
            
        Returns:
            Structure metrics and scores
        """
        if album_analysis['total_albums'] == 0:
            return {
                'consistency_score': 0,
                'overall_score': 0,
                'compliance_distribution': {},
                'health_indicators': {}
            }
        
        # Calculate consistency score
        pattern_counts = album_analysis['pattern_counts']
        total_albums = album_analysis['total_albums']
        
        if pattern_counts:
            # Find most common pattern
            most_common_count = max(pattern_counts.values())
            consistency_score = int((most_common_count / total_albums) * 100)
        else:
            consistency_score = 0
        
        # Calculate compliance distribution
        compliance_scores = [album['compliance_score'] for album in album_analysis['album_details']]
        compliance_distribution = {
            'excellent': len([s for s in compliance_scores if s >= 90]),
            'good': len([s for s in compliance_scores if 70 <= s < 90]),
            'fair': len([s for s in compliance_scores if 50 <= s < 70]),
            'poor': len([s for s in compliance_scores if 25 <= s < 50]),
            'critical': len([s for s in compliance_scores if s < 25])
        }
        
        # Calculate overall structure score
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        year_prefix_ratio = album_analysis['albums_with_year'] / total_albums
        type_organization_bonus = 0
        
        # Bonus for type folder organization
        if album_analysis['type_folders']:
            type_organization_ratio = album_analysis['albums_in_type_folders'] / total_albums
            type_organization_bonus = int(type_organization_ratio * 20)  # Up to 20 point bonus
        
        overall_score = int(
            avg_compliance * 0.6 +  # 60% weight on individual album compliance
            consistency_score * 0.3 +  # 30% weight on pattern consistency
            year_prefix_ratio * 10 +  # Up to 10 points for year prefix usage
            type_organization_bonus  # Up to 20 points for type organization
        )
        overall_score = min(100, max(0, overall_score))
        
        # Health indicators
        health_indicators = {
            'has_year_prefixes': album_analysis['albums_with_year'] > 0,
            'consistent_patterns': consistency_score >= 70,
            'uses_type_folders': len(album_analysis['type_folders']) > 0,
            'good_compliance': avg_compliance >= 70,
            'minimal_issues': compliance_distribution['poor'] + compliance_distribution['critical'] <= total_albums * 0.2
        }
        
        return {
            'consistency_score': consistency_score,
            'overall_score': overall_score,
            'compliance_distribution': compliance_distribution,
            'health_indicators': health_indicators,
            'average_compliance': avg_compliance,
            'year_prefix_ratio': year_prefix_ratio
        }
    
    def _determine_consistency_level(self, consistency_score: int) -> StructureConsistency:
        """Determine consistency level from score."""
        if consistency_score >= 90:
            return StructureConsistency.CONSISTENT
        elif consistency_score >= 70:
            return StructureConsistency.MOSTLY_CONSISTENT
        else:
            return StructureConsistency.INCONSISTENT
    
    def _generate_comprehensive_recommendations(
        self, 
        album_analysis: Dict[str, Any], 
        structure_metrics: Dict[str, Any],
        raw_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate comprehensive improvement recommendations."""
        recommendations = []
        
        # Pattern consistency recommendations
        if structure_metrics['consistency_score'] < 70:
            most_common_pattern = max(album_analysis['pattern_counts'].items(), key=lambda x: x[1])[0] \
                if album_analysis['pattern_counts'] else None
            if most_common_pattern:
                recommendations.append(
                    f"Standardize all albums to use '{most_common_pattern}' pattern for consistency"
                )
        
        # Year prefix recommendations
        if album_analysis['albums_without_year'] > 0:
            recommendations.append(
                f"Add year prefix to {album_analysis['albums_without_year']} album(s) missing year information"
            )
        
        # Type folder organization recommendations
        structure_type = raw_analysis.get('structure_type', 'unknown')
        if structure_type == 'mixed':
            recommendations.append(
                "Consider migrating to consistent enhanced structure with type folders for all albums"
            )
        elif structure_type == 'default' and album_analysis['total_albums'] >= 5:
            recommendations.append(
                "Consider organizing albums by type (Album, Live, Demo, etc.) for better structure with larger collection"
            )
        
        # Compliance improvements
        poor_compliance_count = structure_metrics['compliance_distribution'].get('poor', 0) + \
                               structure_metrics['compliance_distribution'].get('critical', 0)
        if poor_compliance_count > 0:
            recommendations.append(
                f"Improve folder naming for {poor_compliance_count} album(s) with compliance issues"
            )
        
        # Type folder completeness
        if album_analysis['type_folders']:
            common_types = ['Album', 'Live', 'Compilation', 'Demo']
            missing_types = [t for t in common_types if t not in album_analysis['type_folders']]
            if missing_types and len(album_analysis['type_folders']) >= 2:
                recommendations.append(
                    f"Consider adding folders for common types: {', '.join(missing_types)}"
                )
        
        # Edition standardization
        edition_issues = []
        for album in album_analysis['album_details']:
            if album['edition']:
                normalized = self.parser.normalize_edition(album['edition'])
                if normalized != album['edition']:
                    edition_issues.append(album['folder_name'])
        
        if edition_issues:
            recommendations.append(
                f"Standardize edition formatting for {len(edition_issues)} album(s)"
            )
        
        return recommendations
    
    def _identify_structure_issues(
        self, 
        album_analysis: Dict[str, Any], 
        structure_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify specific structure issues."""
        issues = []
        
        # Critical compliance issues
        critical_albums = [
            album for album in album_analysis['album_details'] 
            if album['compliance_score'] < 25
        ]
        if critical_albums:
            issues.append(f"{len(critical_albums)} album(s) have critical naming issues")
        
        # Pattern inconsistency issues
        if len(album_analysis['pattern_counts']) > 3:
            issues.append("Too many different naming patterns reduce organization clarity")
        
        # Year prefix inconsistency
        year_ratio = structure_metrics.get('year_prefix_ratio', 0)
        if 0.1 < year_ratio < 0.9:  # Partial year prefix usage
            issues.append("Inconsistent year prefix usage across albums")
        
        # Mixed structure issues
        if album_analysis['direct_albums'] > 0 and album_analysis['nested_albums'] > 0:
            issues.append("Mixed organization with both direct albums and type folders")
        
        # Empty type folders
        for type_folder, details in album_analysis['type_folder_details'].items():
            if details['total_albums'] == 0:
                issues.append(f"Empty type folder: {type_folder}")
        
        return issues


class StructureAnalyzer:
    """
    High-level structure analysis utilities for collections and reporting.
    """
    
    @staticmethod
    def compare_structures(structures: List[FolderStructure]) -> Dict[str, Any]:
        """
        Compare structures across multiple bands.
        
        Args:
            structures: List of FolderStructure objects
            
        Returns:
            Comparative analysis results
        """
        if not structures:
            return {}
        
        structure_types = [s.structure_type for s in structures]
        consistency_levels = [s.consistency for s in structures]
        scores = [s.structure_score for s in structures]
        
        return {
            'total_bands': len(structures),
            'structure_type_distribution': {
                st.value: structure_types.count(st) for st in StructureType
            },
            'consistency_distribution': {
                cl.value: consistency_levels.count(cl) for cl in StructureConsistency
            },
            'average_structure_score': sum(scores) / len(scores),
            'score_distribution': {
                'excellent': len([s for s in scores if s >= 90]),
                'good': len([s for s in scores if 75 <= s < 90]),
                'fair': len([s for s in scores if 50 <= s < 75]),
                'poor': len([s for s in scores if 25 <= s < 50]),
                'critical': len([s for s in scores if s < 25])
            },
            'migration_recommended': len([s for s in structures if s.is_migration_recommended()]),
            'most_common_structure': max(structure_types, key=structure_types.count) if structure_types else None,
            'most_common_consistency': max(consistency_levels, key=consistency_levels.count) if consistency_levels else None
        }
    
    @staticmethod
    def generate_collection_structure_report(structures: List[FolderStructure]) -> str:
        """
        Generate a comprehensive structure report for a collection.
        
        Args:
            structures: List of FolderStructure objects
            
        Returns:
            Formatted report string
        """
        if not structures:
            return "No band structures to analyze."
        
        analysis = StructureAnalyzer.compare_structures(structures)
        
        report = f"""# Collection Structure Analysis Report

## Overview
- **Total Bands Analyzed**: {analysis['total_bands']}
- **Average Structure Score**: {analysis['average_structure_score']:.1f}/100
- **Bands Needing Migration**: {analysis['migration_recommended']}

## Structure Type Distribution
"""
        
        for struct_type, count in analysis['structure_type_distribution'].items():
            if count > 0:
                percentage = (count / analysis['total_bands']) * 100
                report += f"- **{struct_type.title()}**: {count} bands ({percentage:.1f}%)\n"
        
        report += f"""
## Consistency Distribution
"""
        
        for consistency, count in analysis['consistency_distribution'].items():
            if count > 0:
                percentage = (count / analysis['total_bands']) * 100
                report += f"- **{consistency.replace('_', ' ').title()}**: {count} bands ({percentage:.1f}%)\n"
        
        report += f"""
## Score Distribution
"""
        
        for level, count in analysis['score_distribution'].items():
            if count > 0:
                percentage = (count / analysis['total_bands']) * 100
                report += f"- **{level.title()}**: {count} bands ({percentage:.1f}%)\n"
        
        # Add recommendations
        if analysis['migration_recommended'] > 0:
            report += f"""
## Recommendations
- Consider migrating {analysis['migration_recommended']} band(s) to improve organization
- Most common structure type: **{analysis['most_common_structure'].title()}**
- Focus on bands with poor or critical scores for maximum impact
"""
        
        return report 