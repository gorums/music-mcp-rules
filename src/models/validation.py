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
    Enhanced utility class for intelligent album type detection from folder names, metadata, and heuristics.
    
    Features:
    - Intelligent keyword-based detection with confidence scoring
    - Heuristics for ambiguous cases (track count, naming patterns)
    - Manual type specification and override rules
    - Special case handling (soundtracks, tributes, covers)
    - Customizable type mapping rules
    """
    
    # Enhanced keywords for album type detection with confidence levels
    TYPE_KEYWORDS = {
        AlbumType.LIVE: {
            'high_confidence': [
                'live at', 'live in', 'live from', 'concert at', 'live recording',
                'unplugged', 'acoustic session', 'in concert', 'live performance'
            ],
            'medium_confidence': [
                'live', 'concert', 'acoustic', 'session', 'performance'
            ],
            'low_confidence': [
                'on stage', 'tour', 'festival'
            ]
        },
        AlbumType.COMPILATION: {
            'high_confidence': [
                'greatest hits', 'best of', 'anthology', 'collection',
                'complete works', 'essential', 'hits collection'
            ],
            'medium_confidence': [
                'compilation', 'hits', 'complete', 'selected', 'retrospective'
            ],
            'low_confidence': [
                'works', 'selected songs'
            ]
        },
        AlbumType.EP: {
            'high_confidence': [
                'ep', 'e.p.', 'extended play'
            ],
            'medium_confidence': [
                'mini album', 'short album'
            ],
            'low_confidence': []
        },
        AlbumType.SINGLE: {
            'high_confidence': [
                'single', 'maxi single', 'cd single'
            ],
            'medium_confidence': [
                'promo single', 'radio single'
            ],
            'low_confidence': []
        },
        AlbumType.DEMO: {
            'high_confidence': [
                'demo', 'demos', 'early recordings', 'rehearsal recordings',
                'pre-production', 'rough mixes', 'work in progress'
            ],
            'medium_confidence': [
                'unreleased', 'rehearsal', 'rough', 'early', 'unfinished'
            ],
            'low_confidence': [
                'rare', 'bootleg'
            ]
        },
        AlbumType.INSTRUMENTAL: {
            'high_confidence': [
                'instrumental', 'instrumentals', 'instrumental version',
                'no vocals', 'music only'
            ],
            'medium_confidence': [
                'karaoke version', 'backing tracks'
            ],
            'low_confidence': []
        },
        AlbumType.SPLIT: {
            'high_confidence': [
                'split', 'split album', 'split release', 'versus', 'vs.',
                'with', 'collaboration'
            ],
            'medium_confidence': [
                'shared album', 'joint release', 'collaborative'
            ],
            'low_confidence': [
                'featuring', 'feat.'
            ]
        }
    }
    
    # Special case keywords for enhanced detection
    SPECIAL_CASE_KEYWORDS = {
        'soundtrack': {
            'keywords': ['soundtrack', 'ost', 'original soundtrack', 'film score', 'movie soundtrack'],
            'type': AlbumType.COMPILATION
        },
        'tribute': {
            'keywords': ['tribute', 'tribute to', 'covers', 'cover album', 'covers album'],
            'type': AlbumType.COMPILATION
        },
        'remix': {
            'keywords': ['remix', 'remixes', 'remixed', 'reworked', 'reconstructed'],
            'type': AlbumType.COMPILATION
        },
        'remaster': {
            'keywords': ['remaster', 'remastered', 'digitally remastered', 'restored'],
            'type': AlbumType.ALBUM  # Keep as Album type but note as special edition
        }
    }
    
    # Track count heuristics for ambiguous cases
    TRACK_COUNT_HEURISTICS = {
        AlbumType.SINGLE: {'min': 1, 'max': 4},
        AlbumType.EP: {'min': 3, 'max': 8},
        AlbumType.ALBUM: {'min': 8, 'max': 50}
    }
    
    # Manual type override rules (can be customized)
    _manual_overrides: Dict[str, AlbumType] = {}
    _custom_keywords: Dict[AlbumType, List[str]] = {}
    
    @classmethod
    def set_manual_override(cls, album_identifier: str, album_type: AlbumType) -> None:
        """
        Set manual type override for specific album.
        
        Args:
            album_identifier: Album name or folder pattern to override
            album_type: Type to assign to this album
        """
        cls._manual_overrides[album_identifier.lower()] = album_type
    
    @classmethod
    def add_custom_keyword(cls, album_type: AlbumType, keyword: str, confidence: str = 'medium') -> None:
        """
        Add custom keyword for album type detection.
        
        Args:
            album_type: Album type to associate with keyword
            keyword: Keyword to add
            confidence: Confidence level ('high', 'medium', 'low')
        """
        if album_type not in cls._custom_keywords:
            cls._custom_keywords[album_type] = []
        cls._custom_keywords[album_type].append(keyword.lower())
        
        # Also add to main keywords dict
        if album_type not in cls.TYPE_KEYWORDS:
            cls.TYPE_KEYWORDS[album_type] = {'high_confidence': [], 'medium_confidence': [], 'low_confidence': []}
        
        confidence_key = f'{confidence}_confidence'
        if confidence_key in cls.TYPE_KEYWORDS[album_type]:
            cls.TYPE_KEYWORDS[album_type][confidence_key].append(keyword.lower())
    
    @classmethod
    def detect_type_with_intelligence(
        cls, 
        folder_name: str, 
        album_name: str = "", 
        track_count: Optional[int] = None,
        genres: Optional[List[str]] = None,
        existing_metadata: Optional[Dict] = None
    ) -> Tuple[AlbumType, float, Dict[str, any]]:
        """
        Intelligent album type detection with confidence scoring and detailed analysis.
        
        Args:
            folder_name: The album folder name
            album_name: The album name (optional)
            track_count: Number of tracks (for heuristics)
            genres: List of genres (for context)
            existing_metadata: Any existing metadata that might help
            
        Returns:
            Tuple of (detected_type, confidence_score, analysis_details)
        """
        analysis = {
            'method_used': [],
            'keyword_matches': [],
            'heuristic_factors': [],
            'special_cases': [],
            'confidence_factors': []
        }
        
        # Step 1: Check manual overrides first
        for identifier, override_type in cls._manual_overrides.items():
            if identifier in folder_name.lower() or identifier in album_name.lower():
                analysis['method_used'].append('manual_override')
                analysis['confidence_factors'].append(f"Manual override for '{identifier}'")
                return override_type, 1.0, analysis
        
        # Step 2: Check special cases
        special_type, special_confidence = cls._detect_special_cases(folder_name, album_name, analysis)
        if special_type:
            return special_type, special_confidence, analysis
        
        # Step 3: Enhanced keyword detection with confidence scoring
        keyword_type, keyword_confidence = cls._detect_with_enhanced_keywords(folder_name, album_name, analysis)
        
        # Step 4: Apply heuristics for ambiguous cases
        heuristic_type, heuristic_confidence = cls._apply_heuristics(
            track_count, genres, keyword_type, keyword_confidence, analysis
        )
        
        # Step 5: Combine results and determine final type
        final_type, final_confidence = cls._combine_detection_results(
            keyword_type, keyword_confidence,
            heuristic_type, heuristic_confidence,
            analysis
        )
        
        return final_type, final_confidence, analysis
    
    @classmethod
    def _detect_special_cases(cls, folder_name: str, album_name: str, analysis: Dict) -> Tuple[Optional[AlbumType], float]:
        """Detect special cases like soundtracks, tributes, remixes."""
        text_to_check = f"{folder_name} {album_name}".lower()
        
        for case_name, case_info in cls.SPECIAL_CASE_KEYWORDS.items():
            for keyword in case_info['keywords']:
                if keyword in text_to_check:
                    analysis['method_used'].append('special_case')
                    analysis['special_cases'].append(f"{case_name}: {keyword}")
                    analysis['confidence_factors'].append(f"Special case detection: {case_name}")
                    return case_info['type'], 0.85
        
        return None, 0.0
    
    @classmethod
    def _detect_with_enhanced_keywords(cls, folder_name: str, album_name: str, analysis: Dict) -> Tuple[AlbumType, float]:
        """Enhanced keyword detection with confidence scoring."""
        text_to_check = f"{folder_name} {album_name}".lower()
        best_type = AlbumType.ALBUM
        best_confidence = 0.0
        
        for album_type, confidence_levels in cls.TYPE_KEYWORDS.items():
            type_confidence = 0.0
            matches = []
            
            # Check high confidence keywords
            for keyword in confidence_levels.get('high_confidence', []):
                if keyword in text_to_check:
                    type_confidence = max(type_confidence, 0.9)
                    matches.append(f"HIGH: {keyword}")
            
            # Check medium confidence keywords
            for keyword in confidence_levels.get('medium_confidence', []):
                if keyword in text_to_check:
                    type_confidence = max(type_confidence, 0.7)
                    matches.append(f"MED: {keyword}")
            
            # Check low confidence keywords
            for keyword in confidence_levels.get('low_confidence', []):
                if keyword in text_to_check:
                    type_confidence = max(type_confidence, 0.4)
                    matches.append(f"LOW: {keyword}")
            
            if type_confidence > best_confidence:
                best_confidence = type_confidence
                best_type = album_type
                analysis['keyword_matches'] = matches
        
        if best_confidence > 0:
            analysis['method_used'].append('enhanced_keywords')
            analysis['confidence_factors'].append(f"Keyword detection: {best_confidence:.1f}")
        
        return best_type, best_confidence
    
    @classmethod
    def _apply_heuristics(
        cls, 
        track_count: Optional[int], 
        genres: Optional[List[str]], 
        keyword_type: AlbumType, 
        keyword_confidence: float,
        analysis: Dict
    ) -> Tuple[AlbumType, float]:
        """Apply heuristics for ambiguous cases."""
        heuristic_type = keyword_type
        heuristic_confidence = keyword_confidence
        
        # Track count heuristics
        if track_count is not None:
            for album_type, constraints in cls.TRACK_COUNT_HEURISTICS.items():
                if constraints['min'] <= track_count <= constraints['max']:
                    # If keyword detection was weak, use track count heuristic
                    if keyword_confidence < 0.6:
                        confidence_boost = 0.6 - keyword_confidence
                        if album_type == keyword_type:
                            heuristic_confidence += confidence_boost
                        else:
                            # Track count suggests different type
                            if confidence_boost > 0.3:
                                heuristic_type = album_type
                                heuristic_confidence = 0.6
                        
                        analysis['method_used'].append('track_count_heuristic')
                        analysis['heuristic_factors'].append(
                            f"Track count {track_count} suggests {album_type.value if hasattr(album_type, 'value') else str(album_type)}"
                        )
                        break
        
        # Genre-based heuristics
        if genres:
            genre_text = ' '.join(genres).lower()
            if 'live' in genre_text and keyword_confidence < 0.7:
                heuristic_type = AlbumType.LIVE
                heuristic_confidence = max(heuristic_confidence, 0.6)
                analysis['method_used'].append('genre_heuristic')
                analysis['heuristic_factors'].append("Genre suggests live album")
        
        return heuristic_type, heuristic_confidence
    
    @classmethod
    def _combine_detection_results(
        cls,
        keyword_type: AlbumType, keyword_confidence: float,
        heuristic_type: AlbumType, heuristic_confidence: float,
        analysis: Dict
    ) -> Tuple[AlbumType, float]:
        """Combine detection results for final determination."""
        # If both methods agree, increase confidence
        if keyword_type == heuristic_type:
            final_confidence = min(1.0, (keyword_confidence + heuristic_confidence) / 2 + 0.1)
            analysis['confidence_factors'].append("Multiple methods agree")
            return keyword_type, final_confidence
        
        # If they disagree, use the one with higher confidence
        if heuristic_confidence > keyword_confidence:
            analysis['confidence_factors'].append("Heuristic override keyword detection")
            return heuristic_type, heuristic_confidence
        else:
            analysis['confidence_factors'].append("Keyword detection preferred")
            return keyword_type, keyword_confidence
    
    @classmethod
    def detect_type_from_folder_name(cls, folder_name: str, album_name: str = "") -> AlbumType:
        """
        Legacy method for backward compatibility - detect album type from folder name and album name.
        
        Args:
            folder_name: The album folder name
            album_name: The album name (optional)
            
        Returns:
            Detected AlbumType based on name patterns
        """
        # Use the enhanced detection but only return the type (for backward compatibility)
        detected_type, _, _ = cls.detect_type_with_intelligence(folder_name, album_name)
        return detected_type
    
    @classmethod
    def batch_detect_types(
        cls, 
        albums_data: List[Dict], 
        confidence_threshold: float = 0.6
    ) -> List[Dict]:
        """
        Batch process multiple albums for type detection.
        
        Args:
            albums_data: List of album dictionaries with folder_name, album_name, etc.
            confidence_threshold: Minimum confidence to accept detection
            
        Returns:
            List of enhanced album dictionaries with detected types and confidence scores
        """
        results = []
        
        for album_data in albums_data:
            folder_name = album_data.get('folder_path', album_data.get('folder_name', ''))
            album_name = album_data.get('album_name', '')
            track_count = album_data.get('track_count')
            genres = album_data.get('genres', [])
            
            detected_type, confidence, analysis = cls.detect_type_with_intelligence(
                folder_name, album_name, track_count, genres
            )
            
            enhanced_album = album_data.copy()
            enhanced_album.update({
                'detected_type': detected_type.value if hasattr(detected_type, 'value') else str(detected_type),
                'detection_confidence': confidence,
                'detection_analysis': analysis,
                'type_detection_used': confidence >= confidence_threshold
            })
            
            # Only update type if confidence is high enough
            if confidence >= confidence_threshold:
                enhanced_album['type'] = detected_type.value if hasattr(detected_type, 'value') else str(detected_type)
            
            results.append(enhanced_album)
        
        return results
    
    @classmethod
    def get_detection_statistics(cls, albums_data: List[Dict]) -> Dict[str, any]:
        """
        Get statistics about type detection performance.
        
        Args:
            albums_data: List of album dictionaries
            
        Returns:
            Dictionary with detection statistics
        """
        results = cls.batch_detect_types(albums_data)
        
        total_albums = len(results)
        high_confidence = len([r for r in results if r['detection_confidence'] >= 0.8])
        medium_confidence = len([r for r in results if 0.6 <= r['detection_confidence'] < 0.8])
        low_confidence = len([r for r in results if r['detection_confidence'] < 0.6])
        
        type_distribution = {}
        for result in results:
            detected_type = result['detected_type']
            type_distribution[detected_type] = type_distribution.get(detected_type, 0) + 1
        
        return {
            'total_albums': total_albums,
            'high_confidence_detections': high_confidence,
            'medium_confidence_detections': medium_confidence,
            'low_confidence_detections': low_confidence,
            'confidence_distribution': {
                'high': high_confidence / total_albums if total_albums > 0 else 0,
                'medium': medium_confidence / total_albums if total_albums > 0 else 0,
                'low': low_confidence / total_albums if total_albums > 0 else 0
            },
            'type_distribution': type_distribution
        }

    # Original methods preserved for backward compatibility
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
            'type': album_dict.get('type', AlbumType.ALBUM.value if hasattr(AlbumType.ALBUM, 'value') else str(AlbumType.ALBUM)),
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
            if enhanced_album['type'] == (AlbumType.ALBUM.value if hasattr(AlbumType.ALBUM, 'value') else str(AlbumType.ALBUM)):
                detected_type = AlbumTypeDetector.detect_type_from_folder_name(
                    enhanced_album['folder_path'], 
                    enhanced_album['album_name']
                )
                if detected_type != AlbumType.ALBUM:
                    enhanced_album['type'] = detected_type.value if hasattr(detected_type, 'value') else str(detected_type)
            
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