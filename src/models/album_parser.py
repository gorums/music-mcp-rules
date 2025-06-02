"""
Album Naming Convention Processing and Parsing

This module provides comprehensive parsing functionality for album folder names,
supporting multiple folder structure patterns and extracting year, album name,
and edition information from folder paths.
"""

from typing import Optional, Tuple, Dict, List
import re
from pathlib import Path
from .band import AlbumType


class AlbumFolderParser:
    """
    Comprehensive album folder name parser supporting multiple naming conventions.
    
    Supports the following patterns:
    - Default: "YYYY - Album Name (Edition?)"
    - Legacy: "Album Name" (no year)
    - Enhanced: "Type/YYYY - Album Name (Edition?)"
    """
    
    # Year validation pattern (1950-2030 range)
    YEAR_PATTERN = re.compile(r'^(19[5-9]\d|20[0-2]\d|2030)$')
    
    # Main parsing patterns
    PATTERNS = {
        'default_with_edition': re.compile(r'^(\d{4})\s*-\s*(.+?)\s*\(([^)]+)\)$'),
        'default_no_edition': re.compile(r'^(\d{4})\s*-\s*(.+)$'),
        'legacy_with_edition': re.compile(r'^(.+?)\s*\(([^)]+)\)$'),
        'legacy_no_edition': re.compile(r'^(.+)$')
    }
    
    # Edition keywords for validation
    EDITION_KEYWORDS = [
        'deluxe edition', 'deluxe', 'limited edition', 'limited',
        'anniversary edition', 'remastered', 'remaster', 'remix',
        'special edition', 'expanded edition', 'director\'s cut',
        'collector\'s edition', 'premium edition', 'ultimate edition',
        'bonus edition', 'extended edition', 'platinum edition',
        'gold edition', 'complete edition', 'definitive edition',
        # Type keywords that can also be editions
        'live', 'demo', 'instrumental', 'split', 'acoustic', 'unplugged'
    ]
    
    # Type keywords for folder classification
    TYPE_KEYWORDS = {
        AlbumType.LIVE: ['live', 'concert', 'unplugged', 'acoustic'],
        AlbumType.COMPILATION: ['greatest hits', 'best of', 'collection', 'anthology', 'compilation'],
        AlbumType.EP: ['ep', 'e.p.'],
        AlbumType.SINGLE: ['single'],
        AlbumType.DEMO: ['demo', 'demos', 'early recordings', 'unreleased'],
        AlbumType.INSTRUMENTAL: ['instrumental', 'instrumentals'],
        AlbumType.SPLIT: ['split', 'vs.', 'vs', 'versus', 'with']
    }
    
    @classmethod
    def parse_folder_name(cls, folder_name: str) -> Dict[str, str]:
        """
        Parse album folder name to extract year, album name, and edition.
        
        Args:
            folder_name: The album folder name to parse
            
        Returns:
            Dictionary with keys: year, album_name, edition, pattern_type
        """
        if not folder_name:
            return {'year': '', 'album_name': '', 'edition': '', 'pattern_type': 'invalid'}
        
        folder_name = folder_name.strip()
        
        # Try default pattern with edition: "YYYY - Album Name (Edition)"
        match = cls.PATTERNS['default_with_edition'].match(folder_name)
        if match:
            year, album_name, edition = match.groups()
            if cls._is_valid_year(year) and cls._is_valid_edition(edition):
                return {
                    'year': year,
                    'album_name': album_name.strip(),
                    'edition': edition.strip(),
                    'pattern_type': 'default_with_edition'
                }
            elif cls._is_valid_year(year):
                # Year is valid but edition is not recognized - treat as no edition
                full_name = f"{album_name.strip()} ({edition.strip()})"
                return {
                    'year': year,
                    'album_name': full_name,
                    'edition': '',
                    'pattern_type': 'default_no_edition'
                }
        
        # Try default pattern without edition: "YYYY - Album Name"
        match = cls.PATTERNS['default_no_edition'].match(folder_name)
        if match:
            year, album_name = match.groups()
            if cls._is_valid_year(year):
                # Check if the album name contains parentheses that might be edition
                edition_match = re.search(r'\s*\(([^)]+)\)$', album_name)
                if edition_match and cls._is_valid_edition(edition_match.group(1)):
                    # Extract edition from album name
                    edition = edition_match.group(1).strip()
                    album_name = re.sub(r'\s*\([^)]+\)$', '', album_name).strip()
                    return {
                        'year': year,
                        'album_name': album_name,
                        'edition': edition,
                        'pattern_type': 'default_with_edition'
                    }
                else:
                    return {
                        'year': year,
                        'album_name': album_name.strip(),
                        'edition': '',
                        'pattern_type': 'default_no_edition'
                    }
        
        # Try legacy pattern with edition: "Album Name (Edition)"
        match = cls.PATTERNS['legacy_with_edition'].match(folder_name)
        if match:
            album_name, edition = match.groups()
            if cls._is_valid_edition(edition):
                return {
                    'year': '',
                    'album_name': album_name.strip(),
                    'edition': edition.strip(),
                    'pattern_type': 'legacy_with_edition'
                }
        
        # Fallback to legacy pattern without edition: "Album Name"
        return {
            'year': '',
            'album_name': folder_name.strip(),
            'edition': '',
            'pattern_type': 'legacy_no_edition'
        }
    
    @classmethod
    def parse_enhanced_folder_structure(cls, folder_path: str) -> Dict[str, str]:
        """
        Parse enhanced folder structure: "Band/Type/YYYY - Album Name (Edition?)"
        
        Args:
            folder_path: Full folder path including type directory
            
        Returns:
            Dictionary with keys: year, album_name, edition, pattern_type, album_type
        """
        path = Path(folder_path)
        
        # Check if this is an enhanced structure (has type folder)
        if len(path.parts) >= 2:
            potential_type = path.parts[-2]  # Parent directory
            album_folder = path.name
            
            # Check if parent directory is a valid album type folder name
            # This includes checking for exact matches with AlbumType enum values
            is_type_folder = False
            album_type = AlbumType.ALBUM
            
            # Check for exact type name matches
            for atype in AlbumType:
                if potential_type.lower() == atype.value.lower():
                    is_type_folder = True
                    album_type = atype
                    break
            
            # If not exact match, check keywords
            if not is_type_folder:
                detected_type = cls._detect_album_type_from_folder(potential_type)
                if detected_type != AlbumType.ALBUM or potential_type.lower() in ['album', 'albums']:
                    is_type_folder = True
                    album_type = detected_type
            
            if is_type_folder:
                # This is an enhanced structure
                parsed = cls.parse_folder_name(album_folder)
                parsed['album_type'] = album_type.value
                parsed['pattern_type'] = f"enhanced_{parsed['pattern_type']}"
                return parsed
        
        # Not an enhanced structure, parse as default
        parsed = cls.parse_folder_name(path.name)
        parsed['album_type'] = AlbumType.ALBUM.value
        return parsed
    
    @classmethod
    def detect_folder_structure_type(cls, band_folder_path: str) -> Dict[str, any]:
        """
        Detect the folder structure type used by a band.
        
        Args:
            band_folder_path: Path to the band's folder
            
        Returns:
            Dictionary with structure analysis results
        """
        band_path = Path(band_folder_path)
        
        if not band_path.exists() or not band_path.is_dir():
            return {
                'structure_type': 'unknown',
                'pattern_consistency': 'unknown',
                'albums_analyzed': 0,
                'patterns_found': [],
                'type_folders_found': [],
                'recommendations': []
            }
        
        # Analyze all album folders
        album_folders = [d for d in band_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        patterns_found = []
        type_folders_found = []
        has_type_structure = False
        direct_albums = 0
        
        for folder in album_folders:
            # Check if this is a type folder (contains album subfolders)
            subfolders = [d for d in folder.iterdir() if d.is_dir() and not d.name.startswith('.')]
            if subfolders:
                # Check if this folder name looks like a type using the same logic as enhanced parsing
                is_type_folder = False
                
                # Check for exact type name matches
                for atype in AlbumType:
                    if folder.name.lower() == atype.value.lower():
                        is_type_folder = True
                        break
                
                # If not exact match, check keywords
                if not is_type_folder:
                    detected_type = cls._detect_album_type_from_folder(folder.name)
                    if detected_type != AlbumType.ALBUM or folder.name.lower() in ['album', 'albums']:
                        is_type_folder = True
                
                if is_type_folder:
                    type_folders_found.append(folder.name)
                    has_type_structure = True
                    
                    # Analyze albums within type folder
                    for album_folder in subfolders:
                        parsed = cls.parse_folder_name(album_folder.name)
                        patterns_found.append(parsed['pattern_type'])
                else:
                    # Not a type folder, treat as direct album
                    parsed = cls.parse_folder_name(folder.name)
                    patterns_found.append(parsed['pattern_type'])
                    direct_albums += 1
            else:
                # Direct album folder (no subfolders)
                parsed = cls.parse_folder_name(folder.name)
                patterns_found.append(parsed['pattern_type'])
                direct_albums += 1
        
        # Determine overall structure type
        if has_type_structure and direct_albums == 0:
            structure_type = 'enhanced'
        elif has_type_structure and direct_albums > 0:
            structure_type = 'mixed'
        elif any('default' in p for p in patterns_found):
            structure_type = 'default'
        else:
            structure_type = 'legacy'
        
        # Calculate pattern consistency
        unique_patterns = set(patterns_found)
        if len(unique_patterns) <= 1:
            consistency = 'consistent'
        elif len(unique_patterns) <= 2:
            consistency = 'mostly_consistent'
        else:
            consistency = 'inconsistent'
        
        # Generate recommendations
        recommendations = cls._generate_structure_recommendations(
            structure_type, consistency, patterns_found, type_folders_found
        )
        
        return {
            'structure_type': structure_type,
            'pattern_consistency': consistency,
            'albums_analyzed': len(patterns_found),
            'patterns_found': list(unique_patterns),
            'type_folders_found': type_folders_found,
            'recommendations': recommendations
        }
    
    @classmethod
    def normalize_album_name(cls, album_name: str) -> str:
        """
        Normalize album name by removing common artifacts and standardizing format.
        
        Args:
            album_name: Raw album name
            
        Returns:
            Normalized album name
        """
        name = album_name.strip()
        
        # Remove multiple spaces
        name = re.sub(r'\s+', ' ', name)
        
        # Handle common punctuation normalization
        name = re.sub(r'\s*\.\s*', '. ', name)  # Normalize periods
        name = re.sub(r'\s*,\s*', ', ', name)   # Normalize commas
        name = re.sub(r'\s*:\s*', ': ', name)   # Normalize colons
        
        # Remove trailing periods/commas but not multiple consecutive ones
        name = re.sub(r'\.{2,}$', '', name)  # Remove trailing multiple periods
        name = re.sub(r',\s*$', '', name)    # Remove trailing comma with optional space
        
        return name.strip()
    
    @classmethod
    def normalize_edition(cls, edition: str) -> str:
        """
        Normalize edition string by standardizing common variations.
        
        Args:
            edition: Raw edition string
            
        Returns:
            Normalized edition string
        """
        if not edition:
            return ''
        
        edition = edition.strip()
        edition_lower = edition.lower()
        
        # Standardize common edition variations
        standardizations = {
            'deluxe': 'Deluxe Edition',
            'deluxe edition': 'Deluxe Edition',
            'limited': 'Limited Edition',
            'limited edition': 'Limited Edition',
            'remaster': 'Remastered',
            'remastered': 'Remastered',
            'anniversary': 'Anniversary Edition',
            'anniversary edition': 'Anniversary Edition',
            'special': 'Special Edition',
            'special edition': 'Special Edition',
            'expanded': 'Expanded Edition',
            'expanded edition': 'Expanded Edition',
            'collector\'s': 'Collector\'s Edition',
            'collector\'s edition': 'Collector\'s Edition',
            'demo': 'Demo',
            'instrumental': 'Instrumental',
            'live': 'Live',
            'split': 'Split'
        }
        
        return standardizations.get(edition_lower, edition)
    
    @classmethod
    def _is_valid_year(cls, year_str: str) -> bool:
        """Check if year string is valid (1950-2030)."""
        return bool(cls.YEAR_PATTERN.match(year_str))
    
    @classmethod
    def _is_valid_edition(cls, edition_str: str) -> bool:
        """Check if string contains valid edition keywords."""
        if not edition_str:
            return False
        
        edition_lower = edition_str.lower()
        return any(keyword in edition_lower for keyword in cls.EDITION_KEYWORDS)
    
    @classmethod
    def _detect_album_type_from_folder(cls, folder_name: str) -> AlbumType:
        """Detect album type from folder name."""
        folder_lower = folder_name.lower()
        
        # Check for exact type name matches first
        for album_type in AlbumType:
            if folder_lower == album_type.value.lower():
                return album_type
        
        # Check for keyword matches
        for album_type, keywords in cls.TYPE_KEYWORDS.items():
            if any(keyword in folder_lower for keyword in keywords):
                return album_type
        
        return AlbumType.ALBUM
    
    @classmethod
    def _detect_type_folder(cls, folder_name: str) -> Dict[str, any]:
        """
        Detect if a folder name represents an album type folder.
        
        Args:
            folder_name: The folder name to check
            
        Returns:
            Dictionary with is_type_folder boolean and album_type if detected
        """
        folder_lower = folder_name.lower()
        
        # Check for exact type name matches first
        for album_type in AlbumType:
            if folder_lower == album_type.value.lower():
                return {
                    'is_type_folder': True,
                    'album_type': album_type
                }
        
        # Check for plural versions of type names
        plural_mappings = {
            'albums': AlbumType.ALBUM,
            'eps': AlbumType.EP,
            'singles': AlbumType.SINGLE,
            'lives': AlbumType.LIVE,
            'demos': AlbumType.DEMO,
            'compilations': AlbumType.COMPILATION,
            'instrumentals': AlbumType.INSTRUMENTAL,
            'splits': AlbumType.SPLIT
        }
        
        if folder_lower in plural_mappings:
            return {
                'is_type_folder': True,
                'album_type': plural_mappings[folder_lower]
            }
        
        # Not a recognized type folder
        return {
            'is_type_folder': False,
            'album_type': None
        }
    
    @classmethod
    def detect_album_type_from_folder(cls, album_name: str, type_folder: str = '') -> AlbumType:
        """
        Public method to detect album type from folder name and optional type folder.
        
        Args:
            album_name: The album folder name
            type_folder: Optional type folder name (for enhanced structures)
            
        Returns:
            Detected AlbumType
        """
        # If we have a type folder, use that first
        if type_folder:
            type_info = cls._detect_type_folder(type_folder)
            if type_info['is_type_folder']:
                return type_info['album_type']
        
        # Otherwise, detect from album name
        return cls._detect_album_type_from_folder(album_name)
    
    @classmethod
    def _generate_structure_recommendations(cls, structure_type: str, consistency: str, 
                                          patterns: List[str], type_folders: List[str]) -> List[str]:
        """Generate recommendations for improving folder structure."""
        recommendations = []
        
        if consistency == 'inconsistent':
            recommendations.append("Consider standardizing folder naming patterns across all albums")
        
        if 'legacy' in str(patterns) and structure_type != 'legacy':
            recommendations.append("Add year prefix to albums missing year information")
        
        if structure_type == 'mixed':
            recommendations.append("Consider migrating to consistent enhanced structure with type folders")
        
        if structure_type == 'default' and len(type_folders) == 0:
            recommendations.append("Consider organizing albums by type (Album, Live, Demo, etc.) for better structure")
        
        # Check for missing common type folders
        common_types = ['Album', 'Live', 'Compilation', 'Demo']
        missing_types = [t for t in common_types if t not in type_folders]
        if structure_type == 'enhanced' and missing_types:
            recommendations.append(f"Consider adding folders for common types: {', '.join(missing_types)}")
        
        return recommendations

    @classmethod
    def parse_album_folder(cls, folder_name: str) -> Dict[str, str]:
        """
        Parse album folder name - alias for parse_folder_name.
        
        Args:
            folder_name: The album folder name to parse
            
        Returns:
            Dictionary with parsed album information
        """
        return cls.parse_folder_name(folder_name)


class FolderStructureValidator:
    """
    Validator for checking folder structure compliance and generating recommendations.
    """
    
    @classmethod
    def validate_folder_name(cls, folder_name: str, expected_pattern: str = 'default') -> Dict[str, any]:
        """
        Validate folder name against expected patterns.
        
        Args:
            folder_name: Folder name to validate
            expected_pattern: Expected pattern type ('default', 'enhanced', 'legacy')
            
        Returns:
            Validation results with compliance score and issues
        """
        parsed = AlbumFolderParser.parse_folder_name(folder_name)
        issues = []
        score = 100
        
        # Check year presence for non-legacy patterns
        if expected_pattern in ['default', 'enhanced'] and not parsed['year']:
            issues.append("Missing year prefix (YYYY - )")
            score -= 30
        
        # Check album name quality - including special case for "YYYY -" pattern
        album_name = parsed['album_name'].strip()
        if not album_name or album_name == '':
            issues.append("Missing or invalid album name")
            score -= 50
        elif album_name.endswith(' -') or album_name.endswith('-'):
            # Special case: album name ends with dash (like "2020 -")
            issues.append("Missing or invalid album name")
            score -= 50
        elif len(album_name) < 2:
            issues.append("Album name too short")
            score -= 20
        
        # Check for year format if present
        if parsed['year'] and not AlbumFolderParser._is_valid_year(parsed['year']):
            issues.append("Invalid year format (should be YYYY between 1950-2030)")
            score -= 25
        
        # Validate edition format if present
        if parsed['edition']:
            normalized = AlbumFolderParser.normalize_edition(parsed['edition'])
            if normalized != parsed['edition']:
                issues.append(f"Edition could be standardized: '{parsed['edition']}' → '{normalized}'")
                score -= 10
        
        return {
            'compliance_score': max(0, score),
            'issues': issues,
            'parsed_data': parsed,
            'recommended_name': cls._generate_recommended_name(parsed)
        }
    
    @classmethod
    def _generate_recommended_name(cls, parsed_data: Dict[str, str]) -> str:
        """Generate recommended folder name based on parsed data."""
        year = parsed_data.get('year', '')
        album_name = AlbumFolderParser.normalize_album_name(parsed_data.get('album_name', ''))
        edition = AlbumFolderParser.normalize_edition(parsed_data.get('edition', ''))
        
        if year and album_name:
            if edition:
                return f"{year} - {album_name} ({edition})"
            else:
                return f"{year} - {album_name}"
        elif album_name:
            if edition:
                return f"{album_name} ({edition})"
            else:
                return album_name
        else:
            return "Invalid Album Name" 