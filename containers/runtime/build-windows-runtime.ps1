# build-windows-runtime.ps1
# Script to build the OpenHands Windows Runtime Docker image

param(
    [string]$ImageName = "openhands-windows-runtime",
    [string]$Tag = "latest",
    [string]$BuildContext = ".",
    [switch]$NoCache = $false
)

Write-Host "Building OpenHands Windows Runtime Docker image..." -ForegroundColor Green

# Check whether Docker is running
try {
    docker version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running"
    }
} catch {
    Write-Error "Docker is not running or not installed. Please start Docker Desktop and try again."
    exit 1
}

# Validate script is run from the correct directory
if (-not (Test-Path "Dockerfile.windows")) {
    Write-Error "Dockerfile.windows not found. Please run this script from the OpenHands/containers/runtime/ directory."
    exit 1
}

# Ensure we found the OpenHands project root
$openhandsRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $openhandsRoot "pyproject.toml"))) {
    Write-Error "OpenHands project root not found. Please ensure you're running this from the correct directory."
    exit 1
}

Write-Host "OpenHands project root: $openhandsRoot" -ForegroundColor Yellow

# Build arguments
$buildArgs = @(
    "build",
    "-f", "Dockerfile.windows",
    "-t", "${ImageName}:${Tag}"
)

if ($NoCache) {
    $buildArgs += "--no-cache"
}

# Set build context to OpenHands project root
$buildArgs += $openhandsRoot

Write-Host "Building with command: docker $($buildArgs -join ' ')" -ForegroundColor Yellow

# Execute build
try {
    & docker $buildArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully built ${ImageName}:${Tag}" -ForegroundColor Green
        Write-Host ""
        Write-Host "To use this Windows runtime image, set the following environment variables:" -ForegroundColor Cyan
        Write-Host "`$env:RUNTIME = 'windows-docker'" -ForegroundColor White
        Write-Host "`$env:SANDBOX_RUNTIME_CONTAINER_IMAGE = '${ImageName}:${Tag}'" -ForegroundColor White
        Write-Host ""
        Write-Host "Then start OpenHands with:" -ForegroundColor Cyan
        Write-Host "poetry run uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000 --reload --reload-exclude './workspace'" -ForegroundColor White
    } else {
        Write-Error "Docker build failed with exit code $LASTEXITCODE"
        exit 1
    }
} catch {
    Write-Error "Failed to build Docker image: $_"
    exit 1
}
