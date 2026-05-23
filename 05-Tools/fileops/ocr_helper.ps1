# OCR Helper Script
# Check Tesseract installation

Write-Host "=== ContextStack OCR Helper ===" -ForegroundColor Cyan
Write-Host ""

$tesseractPaths = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
)

$installed = $false
$installedPath = $null

foreach ($path in $tesseractPaths) {
    if (Test-Path $path) {
        $installed = $true
        $installedPath = $path
        break
    }
}

if ($installed) {
    Write-Host "Tesseract found at: $installedPath" -ForegroundColor Green
    Write-Host ""
    & $installedPath --version
} else {
    Write-Host "Tesseract NOT installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download from: https://github.com/UB-Mannheim/tesseract/wiki"
    Write-Host "Install and select Chinese language packs during setup."
}

Write-Host ""
Write-Host "Usage after installation:" -ForegroundColor Yellow
Write-Host "  tesseract 'image.jpg' 'output' -l chi_sim+eng"
Write-Host "  Get-Content 'output.txt'"
