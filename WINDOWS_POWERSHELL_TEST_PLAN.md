# Windows PowerShell Support Test Plan

## Overview
This document outlines a comprehensive test plan for validating the Windows PowerShell support in OpenHands CLI runtime.

## Test Environment Setup

### Cloud Windows VM Options

1. **Azure Windows VM**
   - Create a Windows Server 2019/2022 or Windows 11 VM
   - Ensure PowerShell 5.1+ is installed (default on modern Windows)
   - Install Python 3.8+ and Git
   - Configure RDP access for testing

2. **AWS EC2 Windows Instance**
   - Launch a Windows Server 2019/2022 AMI
   - Use t3.medium or larger for adequate performance
   - Enable RDP access via security groups
   - Install required dependencies

3. **Google Cloud Windows VM**
   - Create a Windows Server instance
   - Configure firewall rules for RDP
   - Install development tools

### VM Configuration Steps

1. **Install Dependencies**
   ```powershell
   # Install Python (if not already installed)
   winget install Python.Python.3.12

   # Install Git
   winget install Git.Git

   # Install Visual Studio Build Tools (for Python packages)
   winget install Microsoft.VisualStudio.2022.BuildTools
   ```

2. **Clone and Setup OpenHands**
   ```powershell
   git clone https://github.com/All-Hands-AI/OpenHands.git
   cd OpenHands

   # Install OpenHands
   pip install -e .
   ```

## Test Cases

### 1. Basic PowerShell Detection
**Objective**: Verify that OpenHands correctly detects Windows and enables PowerShell support.

**Test Steps**:
1. Run OpenHands CLI on Windows
2. Check logs for PowerShell initialization messages
3. Verify no fallback to subprocess warnings

**Expected Results**:
- Log message: "Windows detected. PowerShell support will be used for command execution."
- Log message: "PowerShell session initialized successfully."
- No subprocess fallback warnings

### 2. Basic Command Execution
**Objective**: Test basic PowerShell command execution through OpenHands.

**Test Commands**:
```powershell
# Test basic commands
Get-Location
Get-ChildItem
echo "Hello from PowerShell"
$PSVersionTable.PSVersion
```

**Expected Results**:
- Commands execute successfully
- Output is captured and returned correctly
- Working directory is maintained

### 3. File Operations
**Objective**: Test file operations using PowerShell commands.

**Test Commands**:
```powershell
# Create a test file
New-Item -Path "test.txt" -ItemType File -Value "Test content"

# Read file content
Get-Content "test.txt"

# Modify file
Add-Content -Path "test.txt" -Value "Additional content"

# List files
Get-ChildItem -Name "*.txt"

# Remove file
Remove-Item "test.txt"
```

**Expected Results**:
- All file operations complete successfully
- File content is correctly read and modified
- File cleanup works properly

### 4. Directory Navigation
**Objective**: Test directory navigation and path handling.

**Test Commands**:
```powershell
# Create test directory structure
New-Item -Path "testdir" -ItemType Directory
Set-Location "testdir"
Get-Location
New-Item -Path "subdir" -ItemType Directory
Set-Location "subdir"
Get-Location
Set-Location ".."
Set-Location ".."
Remove-Item -Recurse "testdir"
```

**Expected Results**:
- Directory creation and navigation work correctly
- Path changes are reflected in subsequent commands
- Cleanup removes directories properly

### 5. Environment Variables
**Objective**: Test environment variable access and modification.

**Test Commands**:
```powershell
# Read environment variables
$env:PATH
$env:USERNAME
$env:COMPUTERNAME

# Set temporary environment variable
$env:TEST_VAR = "test_value"
echo $env:TEST_VAR

# Remove environment variable
Remove-Item Env:TEST_VAR
```

**Expected Results**:
- Environment variables are accessible
- Temporary variables can be set and retrieved
- Variable cleanup works

### 6. Error Handling
**Objective**: Test error handling for invalid commands and operations.

**Test Commands**:
```powershell
# Invalid command
Get-NonExistentCommand

# Access non-existent file
Get-Content "nonexistent.txt"

# Invalid syntax
This-Is-Not-Valid-PowerShell
```

**Expected Results**:
- Errors are captured and returned as ErrorObservation
- Error messages are informative
- Runtime remains stable after errors

### 7. Long-Running Commands
**Objective**: Test handling of commands that take time to execute.

**Test Commands**:
```powershell
# Sleep command
Start-Sleep -Seconds 5

# Process listing (potentially slow)
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

**Expected Results**:
- Commands complete successfully
- Timeout handling works correctly
- Output is captured after completion

### 8. Special Characters and Encoding
**Objective**: Test handling of special characters and different encodings.

**Test Commands**:
```powershell
# Test special characters
echo "Special chars: àáâãäåæçèéêë"
echo "Symbols: !@#$%^&*()_+-={}[]|;:,.<>?"

# Test quotes
echo 'Single quotes'
echo "Double quotes with 'nested' quotes"
```

**Expected Results**:
- Special characters are preserved
- Different quote types are handled correctly
- Encoding issues don't occur

### 9. PowerShell-Specific Features
**Objective**: Test PowerShell-specific functionality.

**Test Commands**:
```powershell
# Object pipeline
Get-Process | Where-Object {$_.CPU -gt 0} | Select-Object Name, CPU | Sort-Object CPU -Descending

# PowerShell cmdlets
Get-Date
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion

# PowerShell variables and arrays
$array = @(1, 2, 3, 4, 5)
$array | ForEach-Object { $_ * 2 }
```

**Expected Results**:
- PowerShell pipelines work correctly
- Cmdlets execute and return structured data
- PowerShell-specific syntax is supported

### 10. Integration with OpenHands Features
**Objective**: Test PowerShell integration with OpenHands-specific features.

**Test Scenarios**:
1. File editing operations
2. Code execution and compilation
3. Package management (if applicable)
4. Git operations

**Expected Results**:
- All OpenHands features work with PowerShell backend
- No regression in functionality
- Performance is acceptable

## Performance Tests

### 1. Command Execution Speed
- Measure time for basic command execution
- Compare with subprocess fallback (if available)
- Ensure reasonable performance

### 2. Session Initialization Time
- Measure PowerShell session startup time
- Verify it doesn't significantly impact OpenHands startup

### 3. Memory Usage
- Monitor memory consumption during extended use
- Ensure no memory leaks in PowerShell session

## Regression Tests

### 1. Non-Windows Platforms
- Verify that non-Windows platforms still work correctly
- Ensure no PowerShell-related code affects Linux/macOS

### 2. Fallback Behavior
- Test behavior when PowerShell is not available
- Verify graceful fallback to subprocess

## Automated Testing

### Test Script Template
```powershell
# PowerShell test script for OpenHands
param(
    [string]$OpenHandsPath = ".",
    [string]$TestOutputPath = "test_results.txt"
)

# Test cases array
$TestCases = @(
    @{Name="Basic Command"; Command="Get-Location"; ExpectedPattern=".*"},
    @{Name="File Creation"; Command="New-Item -Path 'test.txt' -ItemType File"; ExpectedPattern=".*test.txt.*"},
    # Add more test cases...
)

# Execute tests
foreach ($Test in $TestCases) {
    Write-Host "Running test: $($Test.Name)"
    # Execute OpenHands with the test command
    # Capture and validate output
    # Log results
}
```

## Success Criteria

1. **Functionality**: All basic PowerShell commands execute correctly
2. **Stability**: No crashes or hangs during extended testing
3. **Performance**: Command execution time is reasonable (< 2x subprocess time)
4. **Compatibility**: Works on Windows Server 2019+, Windows 10+, Windows 11
5. **Error Handling**: Graceful handling of errors and edge cases
6. **Integration**: No regression in existing OpenHands functionality

## Test Execution Checklist

- [ ] Set up Windows VM with required dependencies
- [ ] Install OpenHands with PowerShell support
- [ ] Execute all basic functionality tests
- [ ] Run error handling tests
- [ ] Perform performance benchmarks
- [ ] Test integration with OpenHands features
- [ ] Verify fallback behavior
- [ ] Document any issues or limitations
- [ ] Create test report with results and recommendations

## Reporting

Create a comprehensive test report including:
- Test environment details
- Test results summary
- Performance metrics
- Issues encountered and resolutions
- Recommendations for improvements
- Screenshots/logs of key test scenarios

This test plan ensures thorough validation of the Windows PowerShell support implementation.
