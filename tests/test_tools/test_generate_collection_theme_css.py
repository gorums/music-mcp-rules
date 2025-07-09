import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from src.mcp_server.tools.generate_collection_theme_css_tool import generate_collection_theme_css_tool
from src.di.dependencies import clear_dependencies

@pytest.fixture
def temp_collection_dir(monkeypatch):
    # Create a temp dir and chdir into it for isolation
    orig_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    monkeypatch.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(orig_cwd)
    shutil.rmtree(temp_dir)

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def test_generate_theme_css_normal_collection(temp_collection_dir, monkeypatch):
    # Setup: normal collection with genre distribution
    collection_index = {
        "stats": {
            "top_genres": {"Rock": 3, "Metal": 2, "Jazz": 1},
            "total_bands": 1,
            "total_albums": 2,
            "total_local_albums": 2,
            "total_missing_albums": 0,
            "bands_with_metadata": 1,
            "avg_albums_per_band": 2.0,
            "completion_percentage": 100.0,
            "album_type_distribution": {},
            "edition_distribution": {}
        },
        "bands": [],
        "last_scan": "2024-01-01T00:00:00",
        "insights": None,
        "metadata_version": "1.0"
    }
    write_json(temp_collection_dir / ".collection_index.json", collection_index)
    # Patch MUSIC_ROOT_PATH to temp dir
    monkeypatch.setenv("MUSIC_ROOT_PATH", str(temp_collection_dir))
    clear_dependencies()
    # Run tool
    result = generate_collection_theme_css_tool(output_path="_index.css", force=True)
    if result["status"] != "success":
        print("TOOL ERROR RESULT:", result)
    assert result["status"] == "success"
    css_path = temp_collection_dir / "_index.css"
    assert css_path.exists()
    css = css_path.read_text(encoding="utf-8")
    assert "AUTO-GENERATED FILE" in css
    assert "--genre-rock" in css
    assert "--genre-metal" in css
    assert ".badge-genre-rock" in css
    assert ".badge-genre-metal" in css
    assert ".badge-genre-jazz" in css
    # Check that the number of genre variables matches
    genre_var_lines = [line for line in css.splitlines() if line.strip().startswith("--genre-") and line.strip().endswith(";")]
    assert len(genre_var_lines) == 3

def test_generate_theme_css_empty_collection(temp_collection_dir, monkeypatch):
    # Setup: collection index with no genres
    collection_index = {
        "stats": {
            "top_genres": {},
            "total_bands": 0,
            "total_albums": 0,
            "total_local_albums": 0,
            "total_missing_albums": 0,
            "bands_with_metadata": 0,
            "avg_albums_per_band": 0.0,
            "completion_percentage": 100.0,
            "album_type_distribution": {},
            "edition_distribution": {}
        },
        "bands": [],
        "last_scan": "2024-01-01T00:00:00",
        "insights": None,
        "metadata_version": "1.0"
    }
    write_json(temp_collection_dir / ".collection_index.json", collection_index)
    monkeypatch.setenv("MUSIC_ROOT_PATH", str(temp_collection_dir))
    clear_dependencies()
    result = generate_collection_theme_css_tool(output_path="_index.css", force=True)
    assert result["status"] == "error"
    assert "No genre data found" in result["message"]
    css_path = temp_collection_dir / "_index.css"
    assert not css_path.exists() 