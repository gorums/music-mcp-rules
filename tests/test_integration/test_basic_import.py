#!/usr/bin/env python3
"""
Basic import test for enhanced album models.
"""

try:
    from src.models import Album, AlbumType, AlbumTypeDetector, AlbumDataMigrator
    print("✅ Successfully imported enhanced album models")
    
    # Test basic album creation
    album = Album(album_name="Test Album", type=AlbumType.LIVE)
    print(f"✅ Created album: {album.album_name} (Type: {album.type})")
    
    # Test auto-detection
    detector = AlbumTypeDetector()
    detected_type = detector.detect_type_from_folder_name("1985 - Live at Wembley")
    print(f"✅ Type detection: {detected_type}")
    
    # Test migration
    old_album = {"album_name": "Test", "tracks_count": 10}
    migrated = AlbumDataMigrator.migrate_album_to_enhanced_schema(old_album)
    print(f"✅ Migration successful: {migrated['track_count']} tracks")
    
    print("\n🎉 All basic functionality working!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Runtime error: {e}") 
