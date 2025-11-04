# PRISM Project Packaging Script
# Usage: .\create_package.ps1

Write-Host "=== PRISM Package Creation ===" -ForegroundColor Green
Write-Host ""

# Create zip filename with timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipFileName = "PRISM_v2.0_$timestamp.zip"

# Folders and files to exclude
$excludeFolders = @(
    "node_modules",
    "__pycache__",
    ".git",
    ".vscode",
    ".idea",
    "data"
)

$excludeFiles = @(
    "*.log",
    ".env",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini"
)

Write-Host "[Step 1] Preparing files..." -ForegroundColor Yellow

# Create temporary folder
$tempFolder = "PRISM_temp"
if (Test-Path $tempFolder) {
    Remove-Item $tempFolder -Recurse -Force
}
New-Item -ItemType Directory -Path $tempFolder | Out-Null

# Copy required files and folders
Write-Host "[Step 2] Copying files..." -ForegroundColor Yellow

$itemsToCopy = @(
    "public",
    "config",
    "routes",
    "api_server.py",
    "app.js",
    "raspberry_pi_sensor.py",
    "package.json",
    "requirements.txt",
    "README.md",
    "INSTALLATION_GUIDE.md",
    "DEPLOYMENT.md",
    "vercel.json",
    "render.yaml",
    ".env.example",
    ".gitignore"
)

foreach ($item in $itemsToCopy) {
    if (Test-Path $item) {
        Write-Host "  [OK] $item" -ForegroundColor Gray
        Copy-Item $item -Destination $tempFolder -Recurse -Force
    }
}

# Create ZIP file
Write-Host "[Step 3] Creating ZIP archive..." -ForegroundColor Yellow
Compress-Archive -Path "$tempFolder\*" -DestinationPath $zipFileName -Force

# Clean up temporary folder
Remove-Item $tempFolder -Recurse -Force

Write-Host ""
Write-Host "=== Package Created Successfully ===" -ForegroundColor Green
Write-Host "Filename: $zipFileName" -ForegroundColor Cyan
Write-Host "Location: $(Get-Location)\$zipFileName" -ForegroundColor Cyan

# Check file size
$fileSize = (Get-Item $zipFileName).Length / 1MB
Write-Host "Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Yellow
Write-Host "1. Share the ZIP file with recipients" -ForegroundColor White
Write-Host "2. Recipients should extract and read INSTALLATION_GUIDE.md" -ForegroundColor White
Write-Host "3. Run 'npm install' and 'pip install -r requirements.txt'" -ForegroundColor White
Write-Host ""
