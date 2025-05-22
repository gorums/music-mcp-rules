from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Album:
    album_name: str
    missing: bool = False
    tracks_count: int = 0
    duration: str = ""
    year: str = ""
    genre: List[str] = None

@dataclass
class AlbumAnalysis:
    review: str = ""
    rate: int = 0  # 1-10 scale

@dataclass
class BandAnalysis:
    review: str = ""
    rate: int = 0  # 1-10 scale
    albums: List[AlbumAnalysis] = None
    similar_bands: List[str] = None

@dataclass
class BandMetadata:
    band_name: str
    formed: str = ""
    genre: List[str] = None
    origin: str = ""
    members: List[str] = None
    albums_count: int = 0
    description: str = ""
    albums: List[Album] = None
    last_updated: str = ""
    analyze: Optional[BandAnalysis] = None 