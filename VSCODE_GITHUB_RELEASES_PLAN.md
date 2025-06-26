# VSCode Extension GitHub Releases Installation Plan

## Overview
Implement GitHub releases download as the primary method for VSCode extension installation, with fallback to existing bundled and marketplace methods.

## Current Installation Flow
1. **Bundled .vsix** (from PyPI package)
2. **VS Code Marketplace** (fallback)

## New Installation Flow
1. **GitHub Releases** (new primary method)
2. **Bundled .vsix** (fallback 1)
3. **VS Code Marketplace** (fallback 2)

## Implementation Details

### 1. GitHub API Integration
- **Endpoint**: `GET https://api.github.com/repos/All-Hands-AI/OpenHands/releases/latest`
- **Asset Discovery**: Find `.vsix` file in `assets` array
- **Download URL**: Use `browser_download_url` from matching asset
- **Rate Limiting**: Handle 403 responses gracefully
- **Timeout**: 10-second timeout for API calls

### 2. Download Management
- **Temporary Storage**: Use `tempfile.NamedTemporaryFile` with `.vsix` suffix
- **Progress**: Silent download (no progress bar to keep CLI fast)
- **Validation**: Basic file size check (> 1KB, < 50MB)
- **Cleanup**: Automatic cleanup via context manager

### 3. Error Handling
- **Network Errors**: Catch `urllib.error.URLError`, `socket.timeout`
- **API Errors**: Handle 404 (no releases), 403 (rate limit), 500 (server error)
- **Download Errors**: Incomplete downloads, corrupted files
- **Installation Errors**: Same as existing logic
- **Logging**: Use existing logger for warnings, not errors (graceful degradation)

### 4. Security Considerations
- **HTTPS Only**: Verify SSL certificates
- **Asset Validation**: Only download `.vsix` files from official repo
- **File Type Check**: Verify downloaded file has `.vsix` extension
- **Size Limits**: Reasonable file size bounds

### 5. Performance Requirements
- **Fast Failure**: Quick timeout on network issues
- **Non-blocking**: Don't significantly delay CLI startup
- **Caching**: Consider basic caching with timestamp check (future enhancement)

## Code Structure

### New Function: `download_latest_vsix_from_github()`
```python
def download_latest_vsix_from_github() -> str | None:
    """Download latest .vsix from GitHub releases.
    
    Returns:
        Path to downloaded .vsix file, or None if failed
    """
```

### Modified Function: `attempt_vscode_extension_install()`
- Add GitHub download attempt as first step
- Preserve existing logic as fallbacks
- Update logging messages to reflect new flow

### Dependencies
- **urllib.request**: HTTP client (already available)
- **urllib.error**: Error handling (already available)
- **json**: Parse GitHub API response (already available)
- **tempfile**: Temporary file management (already available)
- **pathlib**: Path handling (already imported)

## Testing Strategy
- **Unit Tests**: Mock GitHub API responses
- **Integration Tests**: Test with real GitHub API (rate limit aware)
- **Error Scenarios**: Network failures, malformed responses, missing assets
- **Fallback Testing**: Ensure existing logic still works

## Rollout Plan
1. **Implementation**: Add new download logic
2. **Testing**: Comprehensive error scenario testing
3. **Documentation**: Update installation flow documentation
4. **Monitoring**: Watch for any installation issues in the wild

## Future Enhancements
- **Caching**: Cache downloaded .vsix with version check
- **Pre-releases**: Option to download pre-release versions
- **Progress Indicator**: For slow connections (optional)
- **Offline Detection**: Smart detection of network availability

## Success Criteria
- ✅ Users get latest extension version immediately
- ✅ No regression in installation success rate
- ✅ Graceful fallback when GitHub is unavailable
- ✅ Fast CLI startup time maintained
- ✅ Clear logging for troubleshooting