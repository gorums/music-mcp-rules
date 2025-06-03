#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

from tools.scanner import MusicFolderScanner

def main():
    scanner = MusicFolderScanner()
    result = scanner.scan_band_folder('test_music_collection/Radiohead')
    print(f"Scan result: {result}")
    
    # Check if metadata file was created
    metadata_path = 'test_music_collection/Radiohead/.band_metadata.json'
    if os.path.exists(metadata_path):
        print(f"Metadata file created: {metadata_path}")
        with open(metadata_path, 'r') as f:
            content = f.read()
            print(f"File size: {len(content)} characters")
    else:
        print(f"Metadata file NOT created: {metadata_path}")

if __name__ == "__main__":
    main() 