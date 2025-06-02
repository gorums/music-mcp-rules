"""
Album type validation and data migration utilities.

This module provides utilities for validating album types, detecting types from 
folder names, and migrating existing album data to the enhanced schema.
"""

from typing import List, Dict, Optional, Tuple
import re
from .band import Album, AlbumType


class AlbumTypeDetector:
    """
    Utility class for detecting album types and editions from folder names and metadata.
    """
    
    # Keywords for album type detection
    TYPE_KEYWORDS = {
        AlbumType.LIVE: [
            'live', 'concert', 'unplugged', 'acoustic', 'in concert',
            'live at', 'live in', 'live from', 'concert at'
        ],
        AlbumType.COMPILATION: [
            'greatest hits', 'best of', 'collection', 'anthology', 
            'compilation', 'hits', 'complete', 'essential'
        ],
        AlbumType.EP: ['ep', 'e.p.'],
        AlbumType.SINGLE: ['single'],
        AlbumType.DEMO: [
            'demo', 'demos', 'early recordings', 'unreleased',
            'rough mixes', 'rehearsal', 'pre-production'
        ],
        AlbumType.INSTRUMENTAL: ['instrumental', 'instrumentals'],
        AlbumType.SPLIT: ['split', 'vs.', 'vs', 'versus', 'with']
    }
    
    # Keywords for edition detection
    EDITION_KEYWORDS = [
        'deluxe edition', 'deluxe', 'limited edition', 'limited',
        'anniversary edition', 'remastered', 'remaster',
        'special edition', 'expanded edition', 'director\'s cut',
        'collector\'s edition', 'premium edition', 'ultimate edition'
    ]
    
    @classmethod
    def detect_type_from_folder_name(cls, folder_name: str, album_name: str = "") -> AlbumType:
        """
        Detect album type from folder name and album name.
        
        Args:
            folder_name: The album folder name
            album_name: The album name (optional)
            
        Returns:
            Detected AlbumType
        """
        folder_lower = folder_name.lower()
        name_lower = album_name.lower() if album_name else ""
        
        # Check for type indicators in folder name or album name
        for album_type, keywords in cls.TYPE_KEYWORDS.items():
            if any(keyword in folder_lower or keyword in name_lower for keyword in keywords):
                return album_type
        
        # Special case: Check track count heuristics for EP detection
        # This would be used when track count is known
        
        return AlbumType.ALBUM
    
    @classmethod
    def detect_edition_from_folder_name(cls, folder_name: str) -> str:
        """
        Detect edition information from folder name.
        
        Args:
            folder_name: The album folder name
            
        Returns:
            Detected edition string or empty string
        """
        # Look for content in parentheses that might be edition info
        parentheses_match = re.search(r'\(([^)]+)\)', folder_name)
        if parentheses_match:
            content = parentheses_match.group(1).strip()
            content_lower = content.lower()
            
            # Check if the parentheses content indicates an edition
            edition_indicators = [
                'deluxe edition', 'deluxe', 'limited edition', 'limited',
                'anniversary edition', 'remastered', 'remaster',
                'special edition', 'expanded edition', 'director\'s cut',
                'collector\'s edition', 'premium edition', 'ultimate edition',
                # Also include type indicators that can be editions when in parentheses
                'live', 'demo', 'instrumental', 'split'
            ]
            
            for indicator in edition_indicators:
                if indicator in content_lower:
                    # Return the original case content
                    return content
        
        return ""
    
    @classmethod
    def detect_year_from_folder_name(cls, folder_name: str) -> str:
        """
        Extract year from folder name using common patterns.
        
        Args:
            folder_name: The album folder name
            
        Returns:
            Detected year string (YYYY format) or empty string
        """
        # Look for YYYY pattern at the beginning
        year_match = re.search(r'^(\d{4})\s*-', folder_name)
        if year_match:
            year = int(year_match.group(1))
            # Validate reasonable year range (1950-2030)
            if 1950 <= year <= 2030:
                return str(year)
        
        # Look for (YYYY) pattern anywhere
        year_match = re.search(r'\((\d{4})\)', folder_name)
        if year_match:
            year = int(year_match.group(1))
            if 1950 <= year <= 2030:
                return str(year)
        
        return ""
    
    @classmethod
    def extract_album_name_from_folder(cls, folder_name: str) -> str:
        """
        Extract clean album name from folder name.
        
        Args:
            folder_name: The album folder name
            
        Returns:
            Cleaned album name
        """
        # Remove year prefix (YYYY - )
        name = re.sub(r'^\d{4}\s*-\s*', '', folder_name)
        
        # Remove edition suffixes in parentheses
        name = re.sub(r'\s*\([^)]*(?:edition|deluxe|limited|remaster|demo|instrumental|split|live)\)', '', name, flags=re.IGNORECASE)
        
        return name.strip()


class AlbumDataMigrator:
    """
    Utility class for migrating existing album data to enhanced schema.
    """
    
    @classmethod
    def migrate_album_to_enhanced_schema(cls, album_dict: Dict) -> Dict:
        """
        Migrate an album dictionary to the enhanced schema.
        
        Args:
            album_dict: Original album dictionary
            
        Returns:
            Enhanced album dictionary with type and edition fields
        """
        # Handle field name changes
        if 'tracks_count' in album_dict and 'track_count' not in album_dict:
            album_dict['track_count'] = album_dict.pop('tracks_count')
        
        # Ensure all required fields exist
        enhanced_album = {
            'album_name': album_dict.get('album_name', ''),
            'year': album_dict.get('year', ''),
            'type': album_dict.get('type', AlbumType.ALBUM.value),
            'edition': album_dict.get('edition', ''),
            'track_count': album_dict.get('track_count', 0),
            'missing': album_dict.get('missing', False),
            'duration': album_dict.get('duration', ''),
            'genres': album_dict.get('genres', []),
            'folder_path': album_dict.get('folder_path', '')
        }
        
        # Auto-detect missing metadata if folder_path is available and fields are not set
        if enhanced_album['folder_path']:
            # Only auto-detect type if it's the default Album type
            if enhanced_album['type'] == AlbumType.ALBUM.value:
                detected_type = AlbumTypeDetector.detect_type_from_folder_name(
                    enhanced_album['folder_path'], 
                    enhanced_album['album_name']
                )
                if detected_type != AlbumType.ALBUM:
                    enhanced_album['type'] = detected_type.value
            
            # Only auto-detect edition if not already set
            if not enhanced_album['edition']:
                enhanced_album['edition'] = AlbumTypeDetector.detect_edition_from_folder_name(
                    enhanced_album['folder_path']
                )
            
            # Only auto-detect year if not already set
            if not enhanced_album['year']:
                enhanced_album['year'] = AlbumTypeDetector.detect_year_from_folder_name(
                    enhanced_album['folder_path']
                )
        
        return enhanced_album
    
    @classmethod
    def migrate_band_metadata(cls, band_metadata_dict: Dict) -> Dict:
        """
        Migrate a complete band metadata dictionary to enhanced schema.
        
        Args:
            band_metadata_dict: Original band metadata dictionary
            
        Returns:
            Enhanced band metadata dictionary
        """
        enhanced_metadata = band_metadata_dict.copy()
        
        # Migrate albums
        if 'albums' in enhanced_metadata:
            enhanced_albums = []
            for album_dict in enhanced_metadata['albums']:
                enhanced_album = cls.migrate_album_to_enhanced_schema(album_dict)
                enhanced_albums.append(enhanced_album)
            enhanced_metadata['albums'] = enhanced_albums
        
        return enhanced_metadata


class AlbumValidator:
    """
    Validation utilities for album data.
    """
    
    @classmethod
    def validate_album_type(cls, album_type: str) -> bool:
        """
        Validate if album type is valid.
        
        Args:
            album_type: Album type string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            AlbumType(album_type)
            return True
        except ValueError:
            return False
    
    @classmethod
    def validate_year_format(cls, year: str) -> bool:
        """
        Validate year format (YYYY).
        
        Args:
            year: Year string to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not year:
            return True  # Empty year is allowed
        
        return bool(re.match(r'^\d{4}$', year))
    
    @classmethod
    def validate_album_data(cls, album_dict: Dict) -> Tuple[bool, List[str]]:
        """
        Validate complete album data dictionary.
        
        Args:
            album_dict: Album dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        if not album_dict.get('album_name'):
            errors.append("album_name is required")
        
        # Validate album type
        album_type = album_dict.get('type', '')
        if album_type and not cls.validate_album_type(album_type):
            errors.append(f"Invalid album type: {album_type}")
        
        # Validate year format
        year = album_dict.get('year', '')
        if not cls.validate_year_format(year):
            errors.append(f"Invalid year format: {year}. Must be YYYY format")
        
        # Validate track count
        track_count = album_dict.get('track_count', 0)
        if not isinstance(track_count, int) or track_count < 0:
            errors.append("track_count must be a non-negative integer")
        
        # Validate missing flag
        missing = album_dict.get('missing', False)
        if not isinstance(missing, bool):
            errors.append("missing must be a boolean")
        
        return len(errors) == 0, errors


def get_album_type_distribution(albums: List[Album]) -> Dict[str, int]:
    """
    Calculate distribution of album types in a collection.
    
    Args:
        albums: List of Album instances
        
    Returns:
        Dictionary with album type counts
    """
    distribution = {}
    for album in albums:
        album_type = album.type.value if hasattr(album.type, 'value') else str(album.type)
        distribution[album_type] = distribution.get(album_type, 0) + 1
    
    return distribution


def get_edition_distribution(albums: List[Album]) -> Dict[str, int]:
    """
    Calculate distribution of album editions in a collection.
    
    Args:
        albums: List of Album instances
        
    Returns:
        Dictionary with edition counts
    """
    distribution = {}
    for album in albums:
        edition = album.edition if album.edition else "Standard"
        distribution[edition] = distribution.get(edition, 0) + 1
    
    return distribution


def filter_albums_by_type(albums: List[Album], album_type: AlbumType) -> List[Album]:
    """
    Filter albums by type.
    
    Args:
        albums: List of Album instances
        album_type: AlbumType to filter by
        
    Returns:
        Filtered list of albums
    """
    return [album for album in albums if album.type == album_type]


def search_albums_by_criteria(
    albums: List[Album], 
    album_type: Optional[AlbumType] = None,
    year: Optional[str] = None,
    edition: Optional[str] = None,
    missing: Optional[bool] = None
) -> List[Album]:
    """
    Search albums by multiple criteria.
    
    Args:
        albums: List of Album instances
        album_type: Filter by album type (optional)
        year: Filter by year (optional)
        edition: Filter by edition (optional)
        missing: Filter by missing status (optional)
        
    Returns:
        Filtered list of albums
    """
    filtered_albums = albums
    
    if album_type is not None:
        filtered_albums = [a for a in filtered_albums if a.type == album_type]
    
    if year is not None:
        filtered_albums = [a for a in filtered_albums if a.year == year]
    
    if edition is not None:
        filtered_albums = [a for a in filtered_albums if a.edition == edition]
    
    if missing is not None:
        filtered_albums = [a for a in filtered_albums if a.missing == missing]
    
    return filtered_albums 