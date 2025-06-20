#!/usr/bin/env python3
"""
Debug specific test failures.
"""

from src.models import Album, AlbumType

def test_album_type_validation():
    """Debug album type validation."""
    print("Testing album type validation...")
    
    try:
        # Valid type as enum
        album = Album(album_name="Test", type=AlbumType.LIVE)
        print(f"✅ Enum type: {album.type}")
        
        # Valid type as string
        album = Album(album_name="Test", type="Demo")
        print(f"✅ String type: {album.type}")
        
        # Invalid type
        try:
            album = Album(album_name="Test", type="InvalidType")
            print(f"❌ Should have failed with invalid type")
        except ValueError as e:
            print(f"✅ Correctly caught invalid type: {e}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_auto_detect_metadata():
    """Debug auto-detect metadata."""
    print("\nTesting auto-detect metadata...")
    
    try:
        album = Album(
            album_name="Live at Wembley",
            folder_path="1985 - Live at Wembley (Live)"
        )
        print(f"Before auto-detect: type={album.type}, edition='{album.edition}'")
        
        album.auto_detect_metadata()
        print(f"After auto-detect: type={album.type}, edition='{album.edition}'")
        
        if album.type == AlbumType.LIVE and album.edition == "Live":
            print("✅ Auto-detect working correctly")
        else:
            print(f"❌ Auto-detect failed: expected type=LIVE, edition='Live'")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_detect_edition_from_folder():
    """Debug edition detection."""
    print("\nTesting edition detection...")
    
    try:
        # Deluxe edition
        album = Album(album_name="Test Album", folder_path="2012 - Album Name (Deluxe Edition)")
        edition = album.detect_edition_from_folder()
        print(f"Deluxe edition: '{edition}' (expected: 'Deluxe Edition')")
        
        # Limited edition
        album = Album(album_name="Test Album", folder_path="2012 - Album Name (Limited Edition)")
        edition = album.detect_edition_from_folder()
        print(f"Limited edition: '{edition}' (expected: 'Limited Edition')")
        
        # Remastered
        album = Album(album_name="Test Album", folder_path="2012 - Album Name (Remastered)")
        edition = album.detect_edition_from_folder()
        print(f"Remastered: '{edition}' (expected: 'Remastered')")
        
        # No edition
        album = Album(album_name="Test Album", folder_path="2012 - Album Name")
        edition = album.detect_edition_from_folder()
        print(f"No edition: '{edition}' (expected: '')")
        
        # Live edition (the failing case)
        album = Album(album_name="Live at Wembley", folder_path="1985 - Live at Wembley (Live)")
        edition = album.detect_edition_from_folder()
        print(f"Live edition: '{edition}' (expected: 'Live')")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_album_type_validation()
    test_auto_detect_metadata()
    test_detect_edition_from_folder() 
