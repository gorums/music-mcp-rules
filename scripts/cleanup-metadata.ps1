# PowerShell script to cleanup metadata files from any music collection folder

param(
    [Parameter(Mandatory=$false)]
    [string]$MusicCollectionPath = "test_music_collection",
    [switch]$WhatIf,
    [switch]$Recursive = $true
)

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Remove-FilesWithPattern {
    param([string]$Path, [string]$Pattern, [string]$Description)
    
    $searchParams = @{
        Path = $Path
        Filter = $Pattern
        Force = $true
        ErrorAction = 'SilentlyContinue'
    }
    
    if ($Recursive) {
        $searchParams.Recurse = $true
    }
    
    $files = Get-ChildItem @searchParams
    
    if ($files.Count -eq 0) {
        Write-ColorOutput "  No $Description found" "Cyan"
        return 0
    }
    
    $deletedCount = 0
    foreach ($file in $files) {
        if ($WhatIf) {
            Write-ColorOutput "  Would delete: $($file.FullName)" "Yellow"
        } else {
            try {
                Remove-Item $file.FullName -Force
                Write-ColorOutput "  Deleted: $($file.Name) from $($file.Directory.Name)" "Green"
                $deletedCount++
            }
            catch {
                Write-ColorOutput "  Failed to delete: $($file.Name) - $($_.Exception.Message)" "Red"
            }
        }
    }
    
    return $deletedCount
}

# Main execution
try {
    Write-ColorOutput "" "White"
    Write-ColorOutput "=== Music Collection Metadata Cleanup ===" "Cyan"
    Write-ColorOutput "Target folder: $MusicCollectionPath" "Cyan"
    Write-ColorOutput "Recursive search: $Recursive" "Cyan"
    if ($WhatIf) {
        Write-ColorOutput "*** DRY RUN MODE - No files will be deleted ***" "Yellow"
    }
    Write-ColorOutput "" "White"
    
    # Check if collection folder exists
    if (-not (Test-Path $MusicCollectionPath)) {
        Write-ColorOutput "Error: Collection folder '$MusicCollectionPath' not found!" "Red"
        Write-ColorOutput "Current directory: $(Get-Location)" "Cyan"
        Write-ColorOutput "Available folders:" "Cyan"
        Get-ChildItem -Directory | ForEach-Object { Write-ColorOutput "  $($_.Name)" "Gray" }
        exit 1
    }
    
    $totalDeleted = 0
    
    # 1. Remove band metadata files
    Write-ColorOutput "1. Removing band metadata files (.band_metadata.json)..." "Cyan"
    $count = Remove-FilesWithPattern -Path $MusicCollectionPath -Pattern ".band_metadata.json" -Description "band metadata files"
    $totalDeleted += $count
    
    # 2. Remove band metadata backup files  
    Write-ColorOutput "" "White"
    Write-ColorOutput "2. Removing band metadata backup files (.band_metadata.json.backup*)..." "Cyan"
    $count = Remove-FilesWithPattern -Path $MusicCollectionPath -Pattern ".band_metadata.json.backup*" -Description "band metadata backup files"
    $totalDeleted += $count
    
    # 3. Remove collection index file
    Write-ColorOutput "" "White"
    Write-ColorOutput "3. Removing collection index file (.collection_index.json)..." "Cyan"
    $count = Remove-FilesWithPattern -Path $MusicCollectionPath -Pattern ".collection_index.json" -Description "collection index file"
    $totalDeleted += $count
    
    # 4. Remove collection index backup files
    Write-ColorOutput "" "White"
    Write-ColorOutput "4. Removing collection index backup files (.collection_index.json.backup*)..." "Cyan"
    $count = Remove-FilesWithPattern -Path $MusicCollectionPath -Pattern ".collection_index.json.backup*" -Description "collection index backup files"
    $totalDeleted += $count
    
    # Summary
    Write-ColorOutput "" "White"
    Write-ColorOutput "=== Cleanup Summary ===" "Cyan"
    if ($WhatIf) {
        Write-ColorOutput "DRY RUN: Would delete $totalDeleted files" "Yellow"
    } elseif ($totalDeleted -eq 0) {
        Write-ColorOutput "No metadata files found to delete." "Cyan"
    } else {
        Write-ColorOutput "Total files deleted: $totalDeleted" "Green"
    }
    
    Write-ColorOutput "" "White"
    if ($WhatIf) {
        Write-ColorOutput "To actually delete files, run: .\cleanup-metadata.ps1 -MusicCollectionPath '$MusicCollectionPath'" "Yellow"
    } else {
        Write-ColorOutput "Cleanup completed successfully!" "Green"
    }
    
}
catch {
    Write-ColorOutput "" "White"
    Write-ColorOutput "Error during cleanup: $($_.Exception.Message)" "Red"
    exit 1
} 