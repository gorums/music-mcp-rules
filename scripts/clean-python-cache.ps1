<#
.SYNOPSIS
    Clean Python Cache Script - Removes all Python cache files and directories

.DESCRIPTION
    Recursively removes Python cache files and directories including:
    - __pycache__ directories
    - .pyc files (compiled Python)
    - .pyo files (optimized Python) 
    - .pytest_cache directories
    - .coverage files
    - htmlcov directories
    - .tox directories
    - .mypy_cache directories
    - .dmypy.json files

.PARAMETER Path
    The path to clean (default: current directory)

.PARAMETER Verbose
    Show detailed output of all files being processed

.PARAMETER WhatIf
    Show what would be deleted without actually deleting anything

.PARAMETER Force
    Force deletion of read-only files

.EXAMPLE
    .\clean-python-cache.ps1
    Clean cache files in current directory

.EXAMPLE
    .\clean-python-cache.ps1 -WhatIf
    Preview what would be cleaned without deleting anything

.EXAMPLE
    .\clean-python-cache.ps1 -Path "C:\MyProject" -Verbose
    Clean cache files in specific directory with detailed output
#>

param(
    [string]$Path = ".",
    [switch]$Verbose,
    [switch]$WhatIf,
    [switch]$Force
)

# Set colors for output
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"
$ErrorColor = "Red"

Write-Host "Python Cache Cleaner" -ForegroundColor $InfoColor
Write-Host "=====================" -ForegroundColor $InfoColor
Write-Host ""

if ($WhatIf) {
    Write-Host "Running in WHAT-IF mode (no files will be deleted)" -ForegroundColor $WarningColor
    Write-Host ""
}

# Convert path to absolute path
$CleanPath = Resolve-Path $Path -ErrorAction SilentlyContinue
if (-not $CleanPath) {
    Write-Host "ERROR: Path '$Path' not found!" -ForegroundColor $ErrorColor
    exit 1
}

Write-Host "Cleaning path: $CleanPath" -ForegroundColor $InfoColor
Write-Host ""

# Initialize counters
$TotalFilesRemoved = 0
$TotalDirsRemoved = 0
$TotalSizeFreed = 0

function Get-FolderSize {
    param([string]$FolderPath)
    try {
        $size = (Get-ChildItem -Path $FolderPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        return [math]::Round($size / 1MB, 2)
    }
    catch {
        return 0
    }
}

function Remove-Items {
    param(
        [string]$Pattern,
        [string]$Description,
        [string]$Type = "File"
    )
    
    Write-Host "Searching for $Description..." -ForegroundColor $InfoColor
    
    if ($Type -eq "Directory") {
        $items = Get-ChildItem -Path $CleanPath -Recurse -Directory -Filter $Pattern -ErrorAction SilentlyContinue
    } else {
        $items = Get-ChildItem -Path $CleanPath -Recurse -File -Filter $Pattern -ErrorAction SilentlyContinue
    }
    
    $count = 0
    $sizeFreed = 0
    
    foreach ($item in $items) {
        $fullPath = $item.FullName
        
        if ($Type -eq "Directory") {
            $itemSize = Get-FolderSize -FolderPath $fullPath
            $displaySize = "${itemSize} MB"
        } else {
            $itemSize = [math]::Round($item.Length / 1MB, 2)
            $displaySize = "${itemSize} MB"
        }
        
        if ($Verbose -or $WhatIf) {
            $relativePath = $fullPath.Replace($CleanPath.Path, ".")
            Write-Host "  -> $relativePath ($displaySize)" -ForegroundColor White
        }
        
        if (-not $WhatIf) {
            try {
                if ($Type -eq "Directory") {
                    Remove-Item -Path $fullPath -Recurse -Force:$Force -ErrorAction Stop
                    $script:TotalDirsRemoved++
                } else {
                    Remove-Item -Path $fullPath -Force:$Force -ErrorAction Stop
                    $script:TotalFilesRemoved++
                }
                $sizeFreed += $itemSize
                $count++
            }
            catch {
                Write-Host "  ERROR: Failed to remove: $fullPath" -ForegroundColor $ErrorColor
                if ($Verbose) {
                    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor $ErrorColor
                }
            }
        } else {
            $count++
            $sizeFreed += $itemSize
        }
    }
    
    $script:TotalSizeFreed += $sizeFreed
    
    if ($count -gt 0) {
        $action = if ($WhatIf) { "Would remove" } else { "Removed" }
        Write-Host "  SUCCESS: $action $count $Description ($sizeFreed MB)" -ForegroundColor $SuccessColor
    } else {
        Write-Host "  INFO: No $Description found" -ForegroundColor $WarningColor
    }
    Write-Host ""
}

# Clean different types of Python cache files and directories
Write-Host "Starting Python cache cleanup..." -ForegroundColor $InfoColor
Write-Host ""

# 1. Remove __pycache__ directories
Remove-Items -Pattern "__pycache__" -Description "__pycache__ directories" -Type "Directory"

# 2. Remove .pyc files
Remove-Items -Pattern "*.pyc" -Description ".pyc files (compiled Python)"

# 3. Remove .pyo files
Remove-Items -Pattern "*.pyo" -Description ".pyo files (optimized Python)"

# 4. Remove .pytest_cache directory
Remove-Items -Pattern ".pytest_cache" -Description ".pytest_cache directories" -Type "Directory"

# 5. Remove .coverage files
Remove-Items -Pattern ".coverage" -Description ".coverage files"

# 6. Remove .coverage.* files
Remove-Items -Pattern ".coverage.*" -Description ".coverage.* files"

# 7. Remove htmlcov directories (coverage reports)
Remove-Items -Pattern "htmlcov" -Description "htmlcov directories (coverage reports)" -Type "Directory"

# 8. Remove .tox directories
Remove-Items -Pattern ".tox" -Description ".tox directories" -Type "Directory"

# 9. Remove .mypy_cache directories
Remove-Items -Pattern ".mypy_cache" -Description ".mypy_cache directories" -Type "Directory"

# 10. Remove .dmypy.json files
Remove-Items -Pattern ".dmypy.json" -Description ".dmypy.json files"

# 11. Remove dmypy.json files
Remove-Items -Pattern "dmypy.json" -Description "dmypy.json files"

# Summary
Write-Host "CLEANUP SUMMARY" -ForegroundColor $InfoColor
Write-Host "===============" -ForegroundColor $InfoColor

if ($WhatIf) {
    Write-Host "Would remove:" -ForegroundColor $WarningColor
    Write-Host "  Directories: $TotalDirsRemoved" -ForegroundColor White
    Write-Host "  Files: $TotalFilesRemoved" -ForegroundColor White
    Write-Host "  Total size: $TotalSizeFreed MB" -ForegroundColor White
} else {
    Write-Host "Successfully removed:" -ForegroundColor $SuccessColor
    Write-Host "  Directories: $TotalDirsRemoved" -ForegroundColor White
    Write-Host "  Files: $TotalFilesRemoved" -ForegroundColor White
    Write-Host "  Disk space freed: $TotalSizeFreed MB" -ForegroundColor White
}

Write-Host ""
if ($WhatIf) {
    Write-Host "Dry run completed! Use without -WhatIf to actually clean files." -ForegroundColor $WarningColor
} else {
    Write-Host "Python cache cleanup completed!" -ForegroundColor $SuccessColor
} 