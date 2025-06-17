# MCP Client Prompt Examples

This guide provides comprehensive examples of prompts you can use in your MCP client (like Claude Desktop) to interact with the Music Collection MCP Server.

## 💬 Natural Language Examples

The MCP client will automatically call the appropriate tools based on your natural language requests. You can be as specific or as general as you like - the server will understand your intent and provide comprehensive results!

### 🔍 **Collection Scanning & Management**

**Initial setup and scanning:**
```
Scan my music collection to discover all bands and albums.
```

**Get an overview of my collection:**
```
Show me a summary of my music collection with statistics.
```

**List bands with filtering:**
```
Show me all bands that have missing albums, sorted by name.
```

```
List all Heavy Metal bands in my collection that have metadata.
```

### 🔍 **Advanced Album Search (New!)**

**Important:** Use exact parameter names and values from the tool documentation. All parameters are optional. Use comma-separated strings for multiple values.

**Search by album types (exact values required):**

```
Use advanced_search_albums_tool with album_types "EP" to find all EPs.
```

```
Search using album_types="Live,Demo" for live albums and demo recordings.
```

```
Find standard albums and compilations with album_types="Album,Compilation".
```

**Search by year ranges and decades:**

```
Find 1980s albums using decades="1980s".
```

```
Search albums from 1975-1985 using year_min=1975 and year_max=1985.
```

```
Find recent albums with year_min=2000.
```

**Search by ratings (1-10 scale):**

```
Find highly rated albums using min_rating=8.
```

```
Find albums rated 7-9 using min_rating=7 and max_rating=9.
```

**Search by specific bands (use exact band names):**

```
Search Metallica's discography using bands="Metallica".
```

```
Find albums by classic metal bands using bands="Iron Maiden,Judas Priest,Black Sabbath".
```

**Search by genres (use exact genre names from your collection):**

```
Find heavy metal albums using genres="Heavy Metal".
```

```
Search multiple metal genres using genres="Thrash Metal,Death Metal,Black Metal".
```

**Search for special editions (use exact edition names):**

```
Find deluxe editions using editions="Deluxe Edition".
```

```
Search for special releases using editions="Limited Edition,Anniversary Edition,Remastered".
```

**Search by availability status:**

```
Find missing albums (in metadata but not found locally) using is_local=false.
```

```
Search only albums you have locally using is_local=true.
```

**Search by track count (useful for finding EPs vs albums):**

```
Find short releases (EPs/Singles) using track_count_max=6.
```

```
Find full albums using track_count_min=8 and track_count_max=15.
```

**Complex multi-parameter searches:**

```
Find metal EPs from the 1980s with good ratings using:
album_types="EP", decades="1980s", genres="Heavy Metal,Thrash Metal", min_rating=7
```

```
Search for missing deluxe editions by specific bands using:
bands="Metallica,Iron Maiden", editions="Deluxe Edition", is_local=false
```

```
Find highly rated live albums from metal bands using:
album_types="Live", genres="Heavy Metal", min_rating=8, is_local=true
```

### 📊 **Collection Analytics & Insights (New!)**

**Comprehensive collection analysis:**

```
Run the analyze_collection_insights_tool to give me a complete analysis of my music collection including health score and maturity level.
```

**Get collection recommendations:**

```
Analyze my collection and tell me what album types I'm missing and should consider adding.
```

**Check collection health:**

```
Use the collection insights tool to analyze my collection's organization health and give me improvement recommendations.
```

**View advanced analytics report:**

```
Show me the collection://analytics resource for a detailed report of my collection analytics.
```

### 📝 **Band Information & Metadata**

**Get detailed band information:**

```
Show me detailed information about Pink Floyd including their albums and any analysis.
```

**Fetch external band information:**

```
Use the fetch_band_info prompt to find comprehensive information about Led Zeppelin including their discography.
```

**Save metadata for a single band:**

```
Save this metadata for The Beatles: formed in 1960, from Liverpool, genres include Rock and Pop, members include John Lennon, Paul McCartney, George Harrison, and Ringo Starr.
```

```
Save detailed metadata for Pink Floyds.
```

```
Save comprehensive information for Metallica: formed 1981 in Los Angeles, California. Genres: Thrash Metal, Heavy Metal, Hard Rock. Current members: James Hetfield, Lars Ulrich, Kirk Hammett, Robert Trujillo. Former members include Cliff Burton, Jason Newsted, Dave Mustaine. Record labels: Megaforce, Elektra, Blackened. Grammy Awards: 9. Inducted into Rock and Roll Hall of Fame in 2009.
```

**Save metadata for multiple bands at once:**

```
Save metadata for these classic rock bands:
- Led Zeppelin: formed 1968, England, Hard Rock/Blues Rock, members Jimmy Page, Robert Plant, John Paul Jones, John Bonham
- Deep Purple: formed 1968, England, Hard Rock/Heavy Metal, key members Ian Gillan, Ritchie Blackmore, Jon Lord
- Black Sabbath: formed 1968, Birmingham England, Heavy Metal, members Tony Iommi, Ozzy Osbourne, Geezer Butler, Bill Ward
```

```
Batch save thrash metal band information:
Metallica (formed 1981, Los Angeles), Slayer (formed 1981, Huntington Park), Megadeth (formed 1983, Los Angeles), Anthrax (formed 1981, New York). All are considered part of the Big Four of Thrash Metal.
```

```
Save information for these progressive rock pioneers:
- Yes: formed 1968, London, Progressive Rock, known for complex compositions and virtuoso musicianship
- Genesis: formed 1967, England, Progressive Rock transitioning to Pop Rock, notable for theatrical live performances
- King Crimson: formed 1968, London, Progressive Rock/Experimental, influential in developing heavy metal and alternative rock
- Emerson Lake & Palmer: formed 1970, England, Progressive Rock, known for keyboard-driven compositions and classical influences
```

### 🎯 **Band Analysis & Reviews**

**Analyze a specific band:**
```
Use the analyze_band prompt to create a comprehensive analysis of Queen including ratings and similar bands.
```

**Compare multiple bands:**

```
Use the compare_bands prompt to compare The Beatles, The Rolling Stones, and Led Zeppelin in terms of musical style, influence, and commercial success.
```

**Save band analysis with ratings:**

```
Save an analysis for Iron Maiden: rate the band 9/10, rate "The Number of the Beast" album 10/10, similar bands include Judas Priest and Black Sabbath.
```

### 🔍 **Resource Access**

**View band details:**
```
Show me the band://info/Metallica resource with their complete information.
```

**Collection summary:**

```
Display the collection://summary resource showing my collection statistics.
```

**Advanced analytics:**

```
Show me the collection://analytics resource for comprehensive collection insights.
```

### ⚙️ **Data Validation & Management**

**Validate metadata before saving:**

```
Validate this band metadata for AC/DC before saving: formed 1973, from Australia, genre Hard Rock, members include Angus Young and Brian Johnson.
```

**Save collection insights:**

```
Save insights about my collection: 75% completion rate, strong in Rock genres, missing more Live albums, recommended to add more EPs.
```

### 🎵 **Album Type Specific Searches**

**Find missing album types:**

```
Search for bands that have Albums but are missing EPs or Live recordings.
```

**Discover rare album types:**

```
Use advanced search to find all Demo, Instrumental, and Split releases in my collection.
```

**Edition analysis:**

```
Find all standard albums that have Deluxe or Limited Edition versions available.
```

### 📈 **Collection Improvement**

**Get personalized recommendations:**

```
Based on my collection analysis, what specific albums or album types should I prioritize adding next?
```

**Organization improvement:**

```
Analyze my collection's folder structure and compliance, then suggest organization improvements.
```

**Collection goals:**

```
Help me set collection goals based on my current collection maturity level and missing album types.
```

### 🔄 **Combined Workflows**

**Complete collection assessment:**

```
Please:
1. Run collection insights analysis for overall health
2. Use advanced search to find all albums rated 9 or higher
3. Suggest missing album types based on my top-rated bands
```

**Discovery workflow:**

```
Analyze my collection, identify my favorite genres and highest-rated bands, then search for similar bands I might be missing.
```

---

**💡 Tip:** The MCP client will automatically call the appropriate tools based on your natural language requests. You can be as specific or as general as you like - the server will understand your intent and provide comprehensive results! 