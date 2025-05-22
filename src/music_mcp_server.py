from fastmcp import FastMCP

mcp = FastMCP("music-collection-mcp")

# Import tool implementations and register with decorators
from tools.scanner import scan_music_folders
from tools.metadata import save_band_metadata, save_band_analyze, save_collection_insight
from tools.storage import get_band_list

@mcp.tool()
def scan_music_folders_tool():
    return scan_music_folders()

@mcp.tool()
def get_band_list_tool():
    return get_band_list()

@mcp.tool()
def save_band_metadata_tool():
    return save_band_metadata()

@mcp.tool()
def save_band_analyze_tool():
    return save_band_analyze()

@mcp.tool()
def save_collection_insight_tool():
    return save_collection_insight()

# Import resource implementations and register
from resources.band_info import get_band_info_markdown
from resources.collection_summary import get_collection_summary

@mcp.resource("band_info://{band_name}")
def band_info_resource(band_name: str):
    return get_band_info_markdown(band_name)

@mcp.resource("resource://collection_summary")
def collection_summary_resource():
    return get_collection_summary()

# Import prompt implementations and register
from prompts.fetch_band_info import get_fetch_band_info_prompt
from prompts.analyze_band import get_analyze_band_prompt
from prompts.compare_bands import get_compare_bands_prompt
from prompts.collection_insights import get_collection_insights_prompt

@mcp.prompt()
def fetch_band_info_prompt():
    return get_fetch_band_info_prompt()

@mcp.prompt()
def analyze_band_prompt():
    return get_analyze_band_prompt()

@mcp.prompt()
def compare_bands_prompt():
    return get_compare_bands_prompt()

@mcp.prompt()
def collection_insights_prompt():
    return get_collection_insights_prompt()

if __name__ == "__main__":
    mcp.run() 