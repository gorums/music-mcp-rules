from dataclasses import dataclass
from typing import List

@dataclass
class BandIndexEntry:
    name: str
    albums_count: int
    folder_path: str

@dataclass
class CollectionIndex:
    total_bands: int
    total_albums: int
    last_scan: str
    bands: List[BandIndexEntry] 