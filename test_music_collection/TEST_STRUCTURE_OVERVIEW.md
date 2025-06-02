# Test Music Collection Structure Overview

This test collection demonstrates various folder organization patterns for testing Phase 6: New Features implementation.

## Structure Types Represented

### 1. Default Structure: `Band Name/YYYY - Album Name (Edition?)`
**Bands**: Pink Floyd, The Beatles, Metallica, Nirvana (partial), Black Sabbath

**Examples**:
- `Pink Floyd/1973 - The Dark Side of the Moon/`
- `Pink Floyd/1979 - The Wall/`
- `The Beatles/1967 - Sgt. Pepper's Lonely Hearts Club Band (Deluxe Edition)/`
- `The Beatles/1969 - Abbey Road/`
- `Metallica/1982 - No Life 'Til Leather (Demo)/`
- `Metallica/1991 - The Black Album/`
- `Metallica/1998 - Garage Inc. (Compilation)/`
- `Metallica/1999 - S&M (Live)/`
- `Nirvana/1989 - Bleach (Demo)/`
- `Nirvana/1991 - Nevermind/`
- `Nirvana/1993 - In Utero/`
- `Black Sabbath/1969 - Early Demos/`
- `Black Sabbath/1970 - Paranoid/`
- `Black Sabbath/1970 - Paranoid (Deluxe Edition)/`

### 2. Enhanced Structure: `Band Name/Type/YYYY - Album Name (Edition?)`
**Bands**: AC/DC, Iron Maiden, Radiohead

**Examples**:
- `AC_DC/Album/1980 - Back in Black/`
- `AC_DC/Album/1990 - The Razors Edge/`
- `AC_DC/Live/1991 - Live at Donington/`
- `AC_DC/Compilation/2003 - The Complete Collection/`
- `Iron Maiden/Demo/1978 - The Soundhouse Tapes (Demo)/`
- `Iron Maiden/Album/1982 - The Number of the Beast/`
- `Iron Maiden/Album/1984 - Powerslave/`
- `Iron Maiden/Live/1985 - Live After Death/`
- `Iron Maiden/EP/1980 - Running Free EP/`
- `Iron Maiden/Compilation/1996 - Best of the Beast/`
- `Radiohead/Album/1997 - OK Computer/`
- `Radiohead/Single/1992 - Creep/`
- `Radiohead/EP/2000 - Kid A Mnesia EP/`

### 3. Legacy Structure: `Band Name/Album Name` (no years)
**Bands**: Led Zeppelin, Deep Purple

**Examples**:
- `Led Zeppelin/Led Zeppelin IV/`
- `Led Zeppelin/Led Zeppelin II/`
- `Led Zeppelin/Physical Graffiti/`
- `Deep Purple/Machine Head/`
- `Deep Purple/In Rock/`

### 4. Mixed Structure: Combination of patterns within same band
**Bands**: Queen, Nirvana (partial)

**Queen Examples**:
- `Queen/1975 - A Night at the Opera/` (Default)
- `Queen/Album/1986 - A Kind of Magic/` (Enhanced)
- `Queen/Live/1985 - Live Aid/` (Enhanced)

**Nirvana Examples**:
- `Nirvana/1989 - Bleach (Demo)/` (Default)
- `Nirvana/1991 - Nevermind/` (Default)
- `Nirvana/1993 - In Utero/` (Default)
- `Nirvana/Unplugged in New York/` (Legacy)

## Album Types Represented

### Album (Standard Studio Albums)
- Pink Floyd albums
- The Beatles albums
- AC/DC Album folder
- Iron Maiden Album folder
- Radiohead Album folder
- Metallica standard albums
- Nirvana albums
- Black Sabbath albums
- Led Zeppelin albums
- Deep Purple albums

### Live Albums
- `AC_DC/Live/1991 - Live at Donington/`
- `Iron Maiden/Live/1985 - Live After Death/`
- `Queen/Live/1985 - Live Aid/`
- `Metallica/1999 - S&M (Live)/`
- `Nirvana/Unplugged in New York/`

### Compilations
- `AC_DC/Compilation/2003 - The Complete Collection/`
- `Iron Maiden/Compilation/1996 - Best of the Beast/`
- `Metallica/1998 - Garage Inc. (Compilation)/`

### EPs
- `Iron Maiden/EP/1980 - Running Free EP/`
- `Radiohead/EP/2000 - Kid A Mnesia EP/`

### Singles
- `Radiohead/Single/1992 - Creep/`

### Demos
- `Iron Maiden/Demo/1978 - The Soundhouse Tapes (Demo)/`
- `Metallica/1982 - No Life 'Til Leather (Demo)/`
- `Nirvana/1989 - Bleach (Demo)/`
- `Black Sabbath/1969 - Early Demos/`

### Instrumentals
- `Iron Maiden/Instrumental/1986 - Losfer Words (Big 'Orra) (Instrumental)/`
- `Metallica/1988 - ...And Justice for All (Instrumental)/`
- `Deep Purple/Machine Head (Instrumental)/`

### Splits
- `Radiohead/Split/2001 - Split Series Vol. 1 (Split)/`
- `Nirvana/2005 - Nirvana vs. Foo Fighters (Split)/`

## Edition Types Represented

### Deluxe Editions
- `The Beatles/1967 - Sgt. Pepper's Lonely Hearts Club Band (Deluxe Edition)/`
- `Black Sabbath/1970 - Paranoid (Deluxe Edition)/`

### Compilation Editions
- `Metallica/1998 - Garage Inc. (Compilation)/`

### Live Editions
- `Metallica/1999 - S&M (Live)/`

### Demo Editions
- `Iron Maiden/Demo/1978 - The Soundhouse Tapes (Demo)/`
- `Metallica/1982 - No Life 'Til Leather (Demo)/`
- `Nirvana/1989 - Bleach (Demo)/`

### Instrumental Editions
- `Iron Maiden/Instrumental/1986 - Losfer Words (Big 'Orra) (Instrumental)/`
- `Metallica/1988 - ...And Justice for All (Instrumental)/`

### Split Editions
- `Radiohead/Split/2001 - Split Series Vol. 1 (Split)/`
- `Nirvana/2005 - Nirvana vs. Foo Fighters (Split)/`

## Testing Scenarios Covered

### Structure Detection
- **Default Structure**: Consistent year prefixes with optional editions
- **Enhanced Structure**: Type-based folders with year prefixes
- **Legacy Structure**: No year prefixes, album names only
- **Mixed Structure**: Combination of patterns within same band

### Compliance Validation
- **Compliant**: Proper year prefixes and edition suffixes
- **Non-compliant**: Missing year prefixes (legacy albums)
- **Mixed compliance**: Some albums compliant, others not

### Album Type Classification
- **Standard Albums**: Regular studio releases
- **Live Albums**: Concert recordings and live performances
- **Compilations**: Best-of and collection albums
- **EPs**: Extended plays with fewer tracks
- **Singles**: Individual song releases
- **Demos**: Early recordings and rough versions
- **Instrumentals**: Albums without vocals or instrumental versions
- **Splits**: Albums shared between multiple artists

### Edition Detection
- **Deluxe Editions**: Enhanced versions with bonus content
- **Live Editions**: Live performance versions
- **Compilation Editions**: Collection-specific releases
- **Demo Editions**: Early and demo versions
- **Instrumental Editions**: Instrumental or vocal-free versions
- **Split Editions**: Multi-artist collaborative releases

### Migration Testing
- **Default to Enhanced**: Bands ready for type-based organization
- **Legacy to Default**: Bands needing year prefix addition
- **Mixed to Enhanced**: Bands with inconsistent organization

## Band Count by Structure Type

- **Default Structure**: 4 bands (Pink Floyd, The Beatles, Metallica, Black Sabbath)
- **Enhanced Structure**: 3 bands (AC/DC, Iron Maiden, Radiohead)
- **Legacy Structure**: 2 bands (Led Zeppelin, Deep Purple)
- **Mixed Structure**: 2 bands (Queen, Nirvana)

**Total**: 11 bands with 60+ albums across all structure types

## File Structure Summary

```
test_music_collection/
├── Pink Floyd/ (Default Structure)
│   ├── 1973 - The Dark Side of the Moon/
│   ├── 1979 - The Wall/
│   └── The Wall/ (Legacy - for comparison)
├── The Beatles/ (Default Structure)
│   ├── 1967 - Sgt. Pepper's Lonely Hearts Club Band (Deluxe Edition)/
│   ├── 1969 - Abbey Road/
│   └── Abbey Road/ (Legacy - for comparison)
├── AC_DC/ (Enhanced Structure)
│   ├── Album/
│   │   ├── 1980 - Back in Black/
│   │   └── 1990 - The Razors Edge/
│   ├── Live/
│   │   └── 1991 - Live at Donington/
│   └── Compilation/
│       └── 2003 - The Complete Collection/
├── Queen/ (Mixed Structure)
│   ├── 1975 - A Night at the Opera/
│   ├── Album/
│   │   └── 1986 - A Kind of Magic/
│   └── Live/
│       └── 1985 - Live Aid/
├── Led Zeppelin/ (Legacy Structure)
│   ├── Led Zeppelin IV/
│   ├── Led Zeppelin II/
│   └── Physical Graffiti/
├── Metallica/ (Default Structure)
│   ├── 1982 - No Life 'Til Leather (Demo)/
│   ├── 1988 - ...And Justice for All (Instrumental)/
│   ├── 1991 - The Black Album/
│   ├── 1998 - Garage Inc. (Compilation)/
│   └── 1999 - S&M (Live)/
├── Nirvana/ (Mixed Structure)
│   ├── 1989 - Bleach (Demo)/
│   ├── 1991 - Nevermind/
│   ├── 1993 - In Utero/
│   ├── 2005 - Nirvana vs. Foo Fighters (Split)/
│   └── Unplugged in New York/
├── Iron Maiden/ (Enhanced Structure)
│   ├── Demo/
│   │   └── 1978 - The Soundhouse Tapes (Demo)/
│   ├── Album/
│   │   ├── 1982 - The Number of the Beast/
│   │   └── 1984 - Powerslave/
│   ├── Live/
│   │   └── 1985 - Live After Death/
│   ├── EP/
│   │   └── 1980 - Running Free EP/
│   ├── Compilation/
│   │   └── 1996 - Best of the Beast/
│   └── Instrumental/
│       └── 1986 - Losfer Words (Big 'Orra) (Instrumental)/
├── Black Sabbath/ (Default Structure)
│   ├── 1969 - Early Demos/
│   ├── 1970 - Paranoid/
│   └── 1970 - Paranoid (Deluxe Edition)/
├── Deep Purple/ (Legacy Structure)
│   ├── Machine Head/
│   ├── In Rock/
│   └── Machine Head (Instrumental)/
└── Radiohead/ (Enhanced Structure)
    ├── Album/
    │   └── 1997 - OK Computer/
    ├── Single/
    │   └── 1992 - Creep/
    ├── EP/
    │   └── 2000 - Kid A Mnesia EP/
    └── Split/
        └── 2001 - Split Series Vol. 1 (Split)/
```

This comprehensive test structure enables thorough testing of all Phase 6 features including:
- Album type classification and detection (8 types: Album, Live, Compilation, EP, Single, Demo, Instrumental, Split)
- Folder structure pattern recognition
- Compliance validation and scoring
- Migration path testing
- Edition parsing and management
- Mixed structure handling
- Legacy support and modernization 