"""
Folder Structure Compliance and Validation System

This module provides comprehensive compliance checking, validation scoring,
and folder organization recommendations for music collections.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field
import re

from .band import Album, AlbumType, FolderCompliance
from .album_parser import AlbumFolderParser, FolderStructureValidator


class ComplianceLevel(str, Enum):
    """
    Enumeration of compliance levels.
    
    Values:
        EXCELLENT: 90-100% compliance score
        GOOD: 75-89% compliance score
        FAIR: 50-74% compliance score
        POOR: 25-49% compliance score
        CRITICAL: 0-24% compliance score
    """
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class ComplianceIssueType(str, Enum):
    """
    Types of compliance issues that can be detected.
    
    Values:
        MISSING_YEAR: Album folder missing year prefix
        INVALID_YEAR: Album folder has invalid year format
        MISSING_ALBUM_NAME: Album folder missing or invalid album name
        POOR_EDITION_FORMAT: Edition not properly formatted
        WRONG_TYPE_FOLDER: Album in wrong type folder
        INCONSISTENT_PATTERN: Album doesn't match band's primary pattern
        MISSING_TYPE_ORGANIZATION: Album could benefit from type folder organization
        SPECIAL_CHARACTERS: Folder name contains problematic characters
    """
    MISSING_YEAR = "missing_year"
    INVALID_YEAR = "invalid_year"
    MISSING_ALBUM_NAME = "missing_album_name"
    POOR_EDITION_FORMAT = "poor_edition_format"
    WRONG_TYPE_FOLDER = "wrong_type_folder"
    INCONSISTENT_PATTERN = "inconsistent_pattern"
    MISSING_TYPE_ORGANIZATION = "missing_type_organization"
    SPECIAL_CHARACTERS = "special_characters"


class ComplianceIssue(BaseModel):
    """
    Individual compliance issue detected in folder organization.
    
    Attributes:
        issue_type: Type of compliance issue
        severity: Severity level (critical, high, medium, low)
        description: Human-readable description of the issue
        suggestion: Recommended action to fix the issue
        impact_score: Numerical impact on compliance score
        album_path: Path to the album with the issue
    """
    issue_type: ComplianceIssueType = Field(..., description="Type of compliance issue")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Description of the issue")
    suggestion: str = Field(..., description="Recommended fix")
    impact_score: int = Field(default=0, ge=0, le=100, description="Impact on compliance score")
    album_path: str = Field(default="", description="Path to album with issue")


class BandComplianceReport(BaseModel):
    """
    Comprehensive compliance report for a band.
    
    Attributes:
        band_name: Name of the band
        overall_compliance_score: Overall compliance score (0-100)
        compliance_level: Overall compliance level
        total_albums: Total number of albums analyzed
        compliant_albums: Number of albums meeting compliance standards
        albums_needing_fixes: Number of albums with compliance issues
        issues: List of all detected compliance issues
        recommendations: List of prioritized recommendations
        migration_candidates: Albums that would benefit from migration
        compliance_distribution: Distribution of compliance scores
        analysis_metadata: Additional analysis information
    """
    band_name: str = Field(..., description="Band name")
    overall_compliance_score: int = Field(default=0, ge=0, le=100, description="Overall compliance score")
    compliance_level: ComplianceLevel = Field(default=ComplianceLevel.CRITICAL, description="Overall compliance level")
    total_albums: int = Field(default=0, ge=0, description="Total albums analyzed")
    compliant_albums: int = Field(default=0, ge=0, description="Albums meeting compliance standards")
    albums_needing_fixes: int = Field(default=0, ge=0, description="Albums with issues")
    issues: List[ComplianceIssue] = Field(default_factory=list, description="All detected issues")
    recommendations: List[str] = Field(default_factory=list, description="Prioritized recommendations")
    migration_candidates: List[str] = Field(default_factory=list, description="Albums for migration")
    compliance_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of scores")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analysis data")

    def get_critical_issues(self) -> List[ComplianceIssue]:
        """Get list of critical severity issues."""
        return [issue for issue in self.issues if issue.severity == "critical"]
    
    def get_high_impact_fixes(self) -> List[ComplianceIssue]:
        """Get list of high-impact fixes that would improve compliance most."""
        return sorted([issue for issue in self.issues if issue.impact_score >= 20], 
                     key=lambda x: x.impact_score, reverse=True)
    
    def needs_migration(self) -> bool:
        """Check if band would benefit from structure migration."""
        return len(self.migration_candidates) > 0 or self.overall_compliance_score < 70


class ComplianceValidator:
    """
    Comprehensive compliance validation system for music collection organization.
    
    Validates folder organization against best practices and provides detailed
    recommendations for improvement.
    """
    
    def __init__(self):
        """Initialize the compliance validator."""
        self.parser = AlbumFolderParser()
        self.validator = FolderStructureValidator()
    
    def validate_album_compliance(self, album: Album, band_structure_type: str = "default") -> FolderCompliance:
        """
        Validate compliance for a single album.
        
        Args:
            album: Album object to validate
            band_structure_type: Type of structure used by the band
            
        Returns:
            FolderCompliance object with detailed compliance information
        """
        if not album.folder_path:
            return FolderCompliance(
                compliance_score=0,
                issues=["No folder path available for compliance checking"],
                original_path="",
                recommended_path="Unknown",
                needs_migration=True
            )
        
        # Use existing validation logic
        validation_result = self.validator.validate_folder_name(album.folder_path, band_structure_type)
        
        # Parse folder for detailed analysis
        parsed = self.parser.parse_folder_name(album.folder_path)
        
        # Determine compliance fields
        has_year_prefix = bool(parsed.get('year'))
        has_edition_suffix = bool(parsed.get('edition'))
        using_type_folders = band_structure_type == "enhanced"
        
        # Calculate recommended path
        recommended_path = self._generate_recommended_path(album, band_structure_type)
        
        # Determine if migration is needed
        needs_migration = (
            validation_result['compliance_score'] < 75 or
            recommended_path != album.folder_path
        )
        
        return FolderCompliance(
            has_year_prefix=has_year_prefix,
            has_edition_suffix=has_edition_suffix,
            using_type_folders=using_type_folders,
            compliance_score=validation_result['compliance_score'],
            issues=validation_result['issues'],
            recommended_path=recommended_path,
            original_path=album.folder_path,
            needs_migration=needs_migration
        )
    
    def validate_band_compliance(self, albums: List[Album], band_name: str, 
                                band_structure_type: str = "default") -> BandComplianceReport:
        """
        Generate comprehensive compliance report for a band.
        
        Args:
            albums: List of albums to validate
            band_name: Name of the band
            band_structure_type: Structure type used by the band
            
        Returns:
            BandComplianceReport with complete analysis
        """
        if not albums:
            return BandComplianceReport(
                band_name=band_name,
                compliance_level=ComplianceLevel.CRITICAL,
                recommendations=["No albums found for compliance analysis"]
            )
        
        # Validate each album
        album_compliances = []
        all_issues = []
        migration_candidates = []
        
        for album in albums:
            if album.missing:
                continue  # Skip missing albums
                
            compliance = self.validate_album_compliance(album, band_structure_type)
            album_compliances.append(compliance)
            
            # Note: compliance is no longer stored on Album model
            
            # Collect issues
            for issue_text in compliance.issues:
                issue = self._classify_issue(issue_text, album.folder_path)
                all_issues.append(issue)
            
            # Check for migration candidates
            if compliance.needs_migration:
                migration_candidates.append(album.folder_path)
        
        # Calculate overall metrics
        if album_compliances:
            compliance_scores = [c.compliance_score for c in album_compliances]
            overall_score = int(sum(compliance_scores) / len(compliance_scores))
            compliant_count = len([c for c in album_compliances if c.is_compliant()])
        else:
            overall_score = 0
            compliant_count = 0
        
        # Determine compliance level
        compliance_level = self._determine_compliance_level(overall_score)
        
        # Generate compliance distribution
        compliance_distribution = self._calculate_compliance_distribution(album_compliances)
        
        # Generate recommendations
        recommendations = self._generate_band_recommendations(
            all_issues, album_compliances, band_structure_type
        )
        
        # Analysis metadata
        analysis_metadata = {
            'average_score': overall_score,
            'score_range': {
                'min': min(compliance_scores) if compliance_scores else 0,
                'max': max(compliance_scores) if compliance_scores else 0
            },
            'issue_types': self._count_issue_types(all_issues),
            'structure_type': band_structure_type,
            'albums_by_compliance': {
                level.value: len([c for c in album_compliances 
                                if self._determine_compliance_level(c.compliance_score) == level])
                for level in ComplianceLevel
            }
        }
        
        return BandComplianceReport(
            band_name=band_name,
            overall_compliance_score=overall_score,
            compliance_level=compliance_level,
            total_albums=len(album_compliances),
            compliant_albums=compliant_count,
            albums_needing_fixes=len(album_compliances) - compliant_count,
            issues=all_issues,
            recommendations=recommendations,
            migration_candidates=migration_candidates,
            compliance_distribution=compliance_distribution,
            analysis_metadata=analysis_metadata
        )
    
    def generate_collection_compliance_report(self, band_reports: List[BandComplianceReport]) -> Dict[str, Any]:
        """
        Generate collection-wide compliance report.
        
        Args:
            band_reports: List of band compliance reports
            
        Returns:
            Collection compliance summary
        """
        if not band_reports:
            return {'error': 'No band reports provided'}
        
        total_albums = sum(report.total_albums for report in band_reports)
        total_compliant = sum(report.compliant_albums for report in band_reports)
        overall_score = sum(report.overall_compliance_score for report in band_reports) / len(band_reports)
        
        # Distribution by compliance level
        level_distribution = {}
        for level in ComplianceLevel:
            count = len([r for r in band_reports if r.compliance_level == level])
            level_distribution[level.value] = count
        
        # Issue analysis
        all_issues = []
        for report in band_reports:
            all_issues.extend(report.issues)
        
        issue_type_counts = self._count_issue_types(all_issues)
        
        # Migration candidates
        total_migration_candidates = sum(len(report.migration_candidates) for report in band_reports)
        
        return {
            'total_bands': len(band_reports),
            'total_albums': total_albums,
            'total_compliant_albums': total_compliant,
            'overall_compliance_score': round(overall_score, 1),
            'overall_compliance_level': self._determine_compliance_level(int(overall_score)).value,
            'compliance_percentage': round((total_compliant / total_albums * 100), 1) if total_albums > 0 else 0,
            'band_compliance_distribution': level_distribution,
            'total_issues': len(all_issues),
            'issue_type_breakdown': issue_type_counts,
            'migration_candidates': total_migration_candidates,
            'bands_needing_attention': len([r for r in band_reports if r.overall_compliance_score < 75]),
            'top_recommendations': self._generate_collection_recommendations(band_reports)
        }
    
    def _generate_recommended_path(self, album: Album, structure_type: str) -> str:
        """Generate recommended folder path for an album."""
        year = album.year or "UNKNOWN"
        name = album.album_name or "Unknown Album"
        edition = album.edition
        
        # Clean up album name
        name = re.sub(r'[<>:"/\\|?*]', '', name)  # Remove problematic characters
        
        if structure_type == "enhanced":
            # Enhanced structure with type folders
            type_folder = album.type.value
            if edition:
                return f"{type_folder}/{year} - {name} ({edition})"
            else:
                return f"{type_folder}/{year} - {name}"
        else:
            # Default structure
            if edition:
                return f"{year} - {name} ({edition})"
            else:
                return f"{year} - {name}"
    
    def _classify_issue(self, issue_text: str, album_path: str) -> ComplianceIssue:
        """Classify an issue based on its text description."""
        issue_text_lower = issue_text.lower()
        
        if "missing year" in issue_text_lower:
            return ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_YEAR,
                severity="high",
                description=issue_text,
                suggestion="Add year prefix in format 'YYYY - Album Name'",
                impact_score=30,
                album_path=album_path
            )
        elif "invalid year" in issue_text_lower:
            return ComplianceIssue(
                issue_type=ComplianceIssueType.INVALID_YEAR,
                severity="medium",
                description=issue_text,
                suggestion="Use valid year format (YYYY between 1950-2030)",
                impact_score=25,
                album_path=album_path
            )
        elif "album name" in issue_text_lower:
            return ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_ALBUM_NAME,
                severity="critical",
                description=issue_text,
                suggestion="Provide proper album name after year prefix",
                impact_score=50,
                album_path=album_path
            )
        elif "edition" in issue_text_lower or "standardized" in issue_text_lower:
            return ComplianceIssue(
                issue_type=ComplianceIssueType.POOR_EDITION_FORMAT,
                severity="low",
                description=issue_text,
                suggestion="Standardize edition format (e.g., 'Deluxe Edition')",
                impact_score=10,
                album_path=album_path
            )
        else:
            return ComplianceIssue(
                issue_type=ComplianceIssueType.INCONSISTENT_PATTERN,
                severity="medium",
                description=issue_text,
                suggestion="Follow consistent naming pattern",
                impact_score=15,
                album_path=album_path
            )
    
    def _determine_compliance_level(self, score: int) -> ComplianceLevel:
        """Determine compliance level from score."""
        if score >= 90:
            return ComplianceLevel.EXCELLENT
        elif score >= 75:
            return ComplianceLevel.GOOD
        elif score >= 50:
            return ComplianceLevel.FAIR
        elif score >= 25:
            return ComplianceLevel.POOR
        else:
            return ComplianceLevel.CRITICAL
    
    def _calculate_compliance_distribution(self, compliances: List[FolderCompliance]) -> Dict[str, int]:
        """Calculate distribution of compliance levels."""
        distribution = {level.value: 0 for level in ComplianceLevel}
        
        for compliance in compliances:
            level = self._determine_compliance_level(compliance.compliance_score)
            distribution[level.value] += 1
        
        return distribution
    
    def _count_issue_types(self, issues: List[ComplianceIssue]) -> Dict[str, int]:
        """Count occurrences of each issue type."""
        counts = {issue_type.value: 0 for issue_type in ComplianceIssueType}
        
        for issue in issues:
            counts[issue.issue_type.value] += 1
        
        return counts
    
    def _generate_band_recommendations(self, issues: List[ComplianceIssue], 
                                      compliances: List[FolderCompliance],
                                      structure_type: str) -> List[str]:
        """Generate prioritized recommendations for a band."""
        recommendations = []
        
        # Critical issues first
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            recommendations.append(
                f"Fix {len(critical_issues)} critical album naming issues immediately"
            )
        
        # Year prefix issues
        missing_year_count = len([i for i in issues if i.issue_type == ComplianceIssueType.MISSING_YEAR])
        if missing_year_count > 0:
            recommendations.append(
                f"Add year prefixes to {missing_year_count} album(s)"
            )
        
        # Edition standardization
        edition_issues = len([i for i in issues if i.issue_type == ComplianceIssueType.POOR_EDITION_FORMAT])
        if edition_issues > 0:
            recommendations.append(
                f"Standardize edition formatting for {edition_issues} album(s)"
            )
        
        # Structure migration
        low_compliance_count = len([c for c in compliances if c.compliance_score < 75])
        if low_compliance_count > len(compliances) * 0.3:  # More than 30% need fixes
            if structure_type == "default":
                recommendations.append(
                    "Consider migrating to enhanced structure with type folders"
                )
            else:
                recommendations.append(
                    "Consider standardizing folder organization patterns"
                )
        
        return recommendations
    
    def _generate_collection_recommendations(self, band_reports: List[BandComplianceReport]) -> List[str]:
        """Generate collection-wide recommendations."""
        recommendations = []
        
        poor_bands = len([r for r in band_reports if r.overall_compliance_score < 50])
        if poor_bands > 0:
            recommendations.append(
                f"Prioritize fixing {poor_bands} band(s) with poor compliance scores"
            )
        
        migration_bands = len([r for r in band_reports if r.needs_migration()])
        if migration_bands > 0:
            recommendations.append(
                f"Consider structure migration for {migration_bands} band(s)"
            )
        
        # Issue-specific recommendations
        all_issues = []
        for report in band_reports:
            all_issues.extend(report.issues)
        
        issue_counts = self._count_issue_types(all_issues)
        
        if issue_counts.get('missing_year', 0) > 10:
            recommendations.append(
                "Implement year prefix standardization across collection"
            )
        
        if issue_counts.get('poor_edition_format', 0) > 5:
            recommendations.append(
                "Standardize edition formatting collection-wide"
            )
        
        return recommendations[:5]  # Limit to top 5 recommendations 