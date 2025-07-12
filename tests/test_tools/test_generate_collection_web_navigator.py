import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from src.mcp_server.tools.generate_collection_web_navigator_tool import generate_collection_web_navigator_tool
from src.di import clear_dependencies

@pytest.fixture(autouse=True)
def clear_di_cache():
    clear_dependencies()

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


def get_music_root():
    path = Path(os.environ["MUSIC_ROOT_PATH"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_generate_index_html_normal_collection(temp_collection_dir, monkeypatch):
    monkeypatch.setenv("MUSIC_ROOT_PATH", str(temp_collection_dir))
    music_root = get_music_root()
    print(f"[DEBUG] MUSIC_ROOT_PATH: {music_root}")
    # Create dummy CSS file for tool check
    (music_root / "_index.css").write_text("body { background: #000; }", encoding="utf-8")
    # Setup: normal collection with one band and one album
    collection_index = {
        "total_bands": 1,
        "total_albums": 1,
        "bands": [
            {"band_name": "Test Band"}
        ],
        "genre_distribution": {"Rock": 1},
        "title": "Test Collection",
        "version": "1.0"
    }
    band_metadata = {
        "band_name": "Test Band",
        "formed": 2000,
        "genre": ["Rock"],
        "origin": "Testland",
        "albums": [
            {"title": "Test Album", "year": 2001, "type": "Album", "edition": None}
        ],
        "albums_missing": [],
        "analysis": {"review": "Great band!", "rating": 9, "similar_bands": [], "similar_bands_missing": []}
    }
    write_json(music_root / ".collection_index.json", collection_index)
    write_json(music_root / "Test Band.band_metadata.json", band_metadata)
    print(f"[DEBUG] Input files: {music_root / '.collection_index.json'}, {music_root / 'Test Band.band_metadata.json'}")
    # Run tool
    result = generate_collection_web_navigator_tool(
        output_path="_index.html", css_path="_index.css", force=True
    )
    print(f"[DEBUG] Tool result: {result}")
    assert result["status"] == "success"
    html_path = music_root / "_index.html"
    print(f"[DEBUG] Output HTML path: {html_path}")
    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")
    # Print HTML for debugging if assertion fails
    if 'id="collection-title"' not in html:
        print("HTML OUTPUT:", html)
    assert 'id="collection-title"' in html
    assert "Test Band" in html or "band-link" in html
    assert "Test Album" not in html  # Album names are rendered dynamically


def test_generate_index_html_empty_collection(temp_collection_dir, monkeypatch):
    monkeypatch.setenv("MUSIC_ROOT_PATH", str(temp_collection_dir))
    music_root = get_music_root()
    print(f"[DEBUG] MUSIC_ROOT_PATH: {music_root}")
    # Create dummy CSS file for tool check
    (music_root / "_index.css").write_text("body { background: #000; }", encoding="utf-8")
    # Setup: empty collection
    collection_index = {
        "total_bands": 0,
        "total_albums": 0,
        "bands": [],
        "genre_distribution": {},
        "title": "Empty Collection",
        "version": "1.0"
    }
    write_json(music_root / ".collection_index.json", collection_index)
    print(f"[DEBUG] Input file: {music_root / '.collection_index.json'}")
    # Run tool
    result = generate_collection_web_navigator_tool(
        output_path="_index.html", css_path="_index.css", force=True
    )
    print(f"[DEBUG] Tool result: {result}")
    assert result["status"] == "success"
    html_path = music_root / "_index.html"
    print(f"[DEBUG] Output HTML path: {html_path}")
    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")
    if 'id="collection-title"' not in html:
        print("HTML OUTPUT:", html)
    assert 'id="collection-title"' in html
    # Only check for static structure, not dynamic JS-rendered content
    assert "AUTO-GENERATED FILE" in html
    assert "_index.css" in html
    assert "<script>" in html


def test_generate_index_html_corrupt_json(temp_collection_dir, monkeypatch):
    monkeypatch.setenv("MUSIC_ROOT_PATH", str(temp_collection_dir))
    music_root = get_music_root()
    print(f"[DEBUG] MUSIC_ROOT_PATH: {music_root}")
    # Create dummy CSS file for tool check
    (music_root / "_index.css").write_text("body { background: #000; }", encoding="utf-8")
    # Setup: corrupt .collection_index.json
    with open(music_root / ".collection_index.json", "w", encoding="utf-8") as f:
        f.write("{ this is not valid json }")
    print(f"[DEBUG] Input file: {music_root / '.collection_index.json'}")
    # Run tool (should still generate HTML, but JS will fail at runtime)
    result = generate_collection_web_navigator_tool(
        output_path="_index.html", css_path="_index.css", force=True
    )
    print(f"[DEBUG] Tool result: {result}")
    assert result["status"] == "success"
    html_path = music_root / "_index.html"
    print(f"[DEBUG] Output HTML path: {html_path}")
    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")
    # The HTML is generated regardless of JSON validity
    assert "AUTO-GENERATED FILE" in html 