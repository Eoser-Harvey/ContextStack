# ContextStack Daily Backup Script
# This script performs daily backups of the ContextStack directory, keeping 7 days of backups.

param(
    [string]$BackupRoot = (Join-Path $PSScriptRoot "..\..\backups_daily"),
    [string]$SourceDir = (Join-Path $PSScriptRoot "..\.."),
    [int]$RetentionDays = 7
)

# Function to log messages
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

# Create backup root directory if it doesn't exist
if (-not (Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    Write-Log "Created backup root directory: $BackupRoot"
}

# Generate backup directory name with timestamp
$backupDate = Get-Date -Format "yyyyMMdd"
$backupDir = Join-Path $BackupRoot "ContextStack_$backupDate"

# Check if today's backup already exists
if (Test-Path $backupDir) {
    Write-Log "Today's backup already exists at $backupDir. Skipping backup."
    exit 0
}

Write-Log "Starting backup of $SourceDir to $backupDir"

# Create backup directory
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Exclude patterns: skip the backup directories and temporary files
$excludePatterns = @(
    "backups_daily",
    "backup_archive",
    "*.backup*",
    "*.tmp",
    "*.log"
)

# Copy files using Robocopy for better performance and control
$robocopyArgs = @(
    $SourceDir,
    $backupDir,
    "/E",          # Copy subdirectories, including empty ones
    "/COPY:DAT",   # Copy Data, Attributes, Timestamps
    "/R:3",        # Retry 3 times on failure
    "/W:5",        # Wait 5 seconds between retries
    "/NP",         # No progress display
    "/NDL",        # No directory list
    "/NJH",        # No job header
    "/NJS"         # No job summary
)

# Add exclude patterns
foreach ($pattern in $excludePatterns) {
    $robocopyArgs += "/XF"
    $robocopyArgs += $pattern
}

Write-Log "Running robocopy..."
& robocopy @robocopyArgs

if ($LASTEXITCODE -lt 8) {
    Write-Log "Backup completed successfully to $backupDir"
} else {
    Write-Log "Backup completed with errors (robocopy exit code: $LASTEXITCODE)"
}

# Clean up old backups (older than RetentionDays)
Write-Log "Cleaning up backups older than $RetentionDays days..."
$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
$backupFolders = Get-ChildItem -Path $BackupRoot -Directory | Where-Object { $_.Name -match 'ContextStack_\d{8}' }

foreach ($folder in $backupFolders) {
    # Extract date from folder name
    if ($folder.Name -match 'ContextStack_(\d{8})') {
        $folderDate = [datetime]::ParseExact($matches[1], 'yyyyMMdd', $null)
        if ($folderDate -lt $cutoffDate) {
            Write-Log "Removing old backup: $($folder.FullName)"
            Remove-Item -Path $folder.FullName -Recurse -Force
        }
    }
}

Write-Log "Backup and cleanup completed."

# Create a summary file
$summaryFile = Join-Path $backupDir "backup_summary.txt"
@"
Backup Summary
==============
Source: $SourceDir
Destination: $backupDir
Backup Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Retention Policy: $RetentionDays days
Backup Size: $(Get-ChildItem -Path $backupDir -Recurse | Measure-Object -Property Length -Sum | Select-Object -ExpandProperty Sum) bytes
"@ | Out-File -FilePath $summaryFile -Encoding UTF8

Write-Log "Backup summary saved to $summaryFile"