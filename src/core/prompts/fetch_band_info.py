from typing import Dict, Any, List, Optional


def get_fetch_band_info_prompt(band_name: str = "", existing_albums: List[str] = None, information_scope: str = "full") -> Dict[str, Any]:
    """
    Generate a prompt template for fetching comprehensive band information using brave search.
    
    This prompt guides the AI to extract band metadata compatible with the enhanced schema,
    including basic information, discography, and missing album detection.
    
    Args:
        band_name: Name of the band to research (optional parameter for dynamic prompts)
        existing_albums: List of albums already in local collection (optional)
        information_scope: Scope of information needed - "basic", "full", or "albums_only" (default: "full")
        
    Returns:
        Dict containing MCP prompt specification with messages for band information retrieval
    """
    existing_albums = existing_albums or []
    
    # Validate information scope
    valid_scopes = ["basic", "full", "albums_only"]
    if information_scope not in valid_scopes:
        information_scope = "full"
    
    # Build prompt content - if no band_name provided, create a general template
    if band_name:
        prompt_content = _build_specific_band_prompt(band_name, existing_albums, information_scope)
    else:
        prompt_content = _build_general_prompt_template(information_scope)
    
    return {
        "name": "fetch_band_info",
        "description": "Retrieve comprehensive information about a band using web search",
        "arguments": [
            {
                "name": "band_name",
                "description": "Name of the band to research",
                "required": True
            },
            {
                "name": "existing_albums", 
                "description": "List of albums already in local collection (for missing album detection)",
                "required": False
            },
            {
                "name": "information_scope",
                "description": "Scope of information needed: 'basic', 'full', or 'albums_only'",
                "required": False
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt_content
                }
            }
        ]
    }


def _build_general_prompt_template(information_scope: str) -> str:
    """Build a general prompt template for any band."""
    if information_scope == "basic":
        return _build_basic_template()
    elif information_scope == "albums_only":
        return _build_albums_template()
    else:  # full
        return _build_full_template()


def _build_full_template() -> str:
    """Build the comprehensive information gathering template."""
    return """You are tasked with gathering comprehensive information about a music band for a music collection database. Use brave search to find accurate and up-to-date information.

**INSTRUCTIONS:**
When provided with a band name, research and compile complete band metadata following these guidelines:

**RESEARCH OBJECTIVES:**
1. Extract complete band metadata
2. Compile comprehensive discography 
3. Identify missing albums (compare with any provided local collection)
4. Ensure data quality and accuracy

**INFORMATION TO GATHER:**

**Basic Band Information:**
- Band name (verify correct spelling and official name)
- Formation year (YYYY format)
- Genres (comprehensive list of musical genres)
- Origin (country/city where band was formed)
- Members (current and notable past members with their roles)
- Description (band biography, musical style, notable achievements)

**Complete Discography:**
- All studio albums (include compilation and live albums if significant)
- Album release years (YYYY format)
- Album genres (may differ from band's overall genres)
- Track counts (if available)
- Album duration information (if available)

**DATA QUALITY GUIDELINES:**
1. **Accuracy**: Verify information across multiple sources
2. **Completeness**: Aim for comprehensive album listing
3. **Format Compliance**: Use YYYY format for years, proper genre names
4. **Missing Album Detection**: Compare discography with any provided existing local albums
5. **Fallback Instructions**: If some information is unavailable, mark fields as empty strings rather than guessing

**OUTPUT FORMAT:**
Return the information in JSON format matching this schema:

```json
{
  "band_name": "Official band name",
  "formed": "YYYY",
  "genres": ["Genre1", "Genre2"],
  "origin": "Country/City",
  "members": ["Member Name (role)", "Member Name (role)"],
  "description": "Comprehensive band biography and musical description",
  "albums": [
    {
      "album_name": "Album Title",
      "missing": false, // true if not in existing local albums
      "tracks_count": 0, // number if available, 0 if unknown
      "duration": "", // "XXmin" format if available, empty string if unknown
      "year": "YYYY", // release year
      "genres": ["Album Genre1", "Album Genre2"] // album-specific genres
    }
  ]
}
```

**SEARCH STRATEGY:**
1. Start with general band information search
2. Search for complete discography and album lists
3. Verify information across multiple reliable sources (Wikipedia, AllMusic, official websites)
4. Cross-reference album information for accuracy
5. Use official band websites or verified music databases when possible

**VALIDATION RULES:**
- Years must be 4-digit format (YYYY)
- Genres should use standard music genre names
- Member information should include roles when available
- Album information should be comprehensive but accurate
- Mark albums as "missing": true if they don't appear in any provided existing local collection

**USAGE EXAMPLE:**
When you receive a band name like "Pink Floyd", search for their information and provide the complete metadata in the JSON format above."""


def _build_basic_template() -> str:
    """Build the basic information only template."""
    return """You are tasked with gathering basic information about a music band for a music collection database. Use brave search to find accurate information.

**INSTRUCTIONS:**
When provided with a band name, research and compile basic band information only.

**INFORMATION TO GATHER:**

**Basic Band Information Only:**
- Band name (verify correct spelling and official name)
- Formation year (YYYY format) 
- Genres (main musical genres)
- Origin (country/city where band was formed)
- Members (current lineup with roles)
- Description (brief band biography and musical style)

**DATA QUALITY GUIDELINES:**
1. **Accuracy**: Verify information across multiple sources
2. **Format Compliance**: Use YYYY format for years
3. **Brevity**: Focus on essential information only
4. **Fallback Instructions**: If information is unavailable, use empty strings

**OUTPUT FORMAT:**
Return the information in JSON format:

```json
{
  "band_name": "Official band name",
  "formed": "YYYY",
  "genres": ["Genre1", "Genre2"],
  "origin": "Country/City", 
  "members": ["Member Name (role)", "Member Name (role)"],
  "description": "Brief band biography and musical description"
}
```

**SEARCH STRATEGY:**
1. Search for general band information
2. Verify across reliable sources (Wikipedia, AllMusic, official websites)
3. Focus on current and accurate information

**USAGE EXAMPLE:**
When you receive a band name like "The Beatles", search for their basic information and provide it in the JSON format above."""


def _build_albums_template() -> str:
    """Build the albums-focused discovery template."""
    return """You are tasked with discovering the complete discography of a music band for a music collection database. Use brave search to find comprehensive album information.

**INSTRUCTIONS:**
When provided with a band name, research and compile their complete discography.

**RESEARCH OBJECTIVES:**
1. Find complete band discography
2. Identify missing albums (compare with any provided local collection)
3. Gather detailed album metadata

**ALBUM INFORMATION TO GATHER:**
- All studio albums, compilations, and significant live albums
- Album release years (YYYY format)
- Album-specific genres (may differ from band's overall style)
- Track counts (if available)
- Album duration information (if available)

**DATA QUALITY GUIDELINES:**
1. **Completeness**: Aim for comprehensive album listing
2. **Accuracy**: Verify album information across sources
3. **Format Compliance**: Use YYYY format for years
4. **Missing Detection**: Compare with any provided existing local albums

**OUTPUT FORMAT:**
Return the information in JSON format:

```json
{
  "albums": [
    {
      "album_name": "Album Title",
      "missing": false, // true if not in existing local albums
      "tracks_count": 0, // number if available, 0 if unknown
      "duration": "", // "XXmin" format if available
      "year": "YYYY", // release year
      "genres": ["Album Genre1", "Album Genre2"]
    }
  ]
}
```

**SEARCH STRATEGY:**
1. Search for complete discography listings
2. Check official band websites and verified music databases
3. Cross-reference across multiple sources for accuracy
4. Include studio albums, compilations, and significant releases

**USAGE EXAMPLE:**
When you receive a band name like "Led Zeppelin", search for their complete discography and provide it in the JSON format above."""


def _build_specific_band_prompt(band_name: str, existing_albums: List[str], information_scope: str) -> str:
    """Build a prompt for a specific band."""
    existing_albums_text = ""
    if existing_albums:
        albums_list = "\n".join(f"- {album}" for album in existing_albums)
        existing_albums_text = f"""

**EXISTING LOCAL ALBUMS:**
{albums_list}

Use this list to identify missing albums that should be marked with "missing": true in the albums array.
"""
    
    if information_scope == "basic":
        base_prompt = _build_basic_template()
    elif information_scope == "albums_only":
        base_prompt = _build_albums_template()
    else:  # full
        base_prompt = _build_full_template()
    
    # Replace the general instruction with specific band instruction
    specific_prompt = base_prompt.replace(
        "When provided with a band name,", 
        f"Research the band '{band_name}' and"
    )
    
    # Add existing albums information if provided
    if existing_albums_text:
        specific_prompt = specific_prompt.replace(
            "**SEARCH STRATEGY:**",
            f"{existing_albums_text}\n\n**SEARCH STRATEGY:**"
        )
    
    return specific_prompt 