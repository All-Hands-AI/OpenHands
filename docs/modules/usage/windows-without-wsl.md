# Running OpenHands GUI on Windows Without WSL

This guide provides step-by-step instructions for running OpenHands on a Windows machine without using WSL or Docker.

## Prerequisites

1. **Windows 10/11** - A modern Windows operating system
2. **PowerShell 7+** - While Windows PowerShell comes pre-installed on Windows 10/11, PowerShell 7+ is strongly recommended to avoid compatibility issues (see Troubleshooting section for "System.Management.Automation" errors)
3. **.NET Core Runtime** - Required for the PowerShell integration via pythonnet
4. **Python 3.12** - Python 3.12 is required (Python 3.14 is not supported due to pythonnet compatibility)
5. **Git** - For cloning the repository and version control
6. **Node.js and npm** - For running the frontend

## Step 1: Install Required Software

1. **Install Python 3.12**
   - Download Python 3.12.x from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation by opening PowerShell and running:
     ```powershell
     python --version
     ```

2. **Install PowerShell 7**
   - Download and install PowerShell 7 from the [official PowerShell GitHub repository](https://github.com/PowerShell/PowerShell/releases)
   - Choose the MSI installer appropriate for your system (x64 for most modern computers)
   - Run the installer with default options
   - Verify installation by opening a new terminal and running:
     ```powershell
     pwsh --version
     ```
   - Using PowerShell 7 (pwsh) instead of Windows PowerShell will help avoid "System.Management.Automation" errors

3. **Install .NET Core Runtime**
   - Download and install the .NET Core Runtime from [Microsoft's .NET download page](https://dotnet.microsoft.com/download)
   - Choose the latest .NET Core Runtime (not SDK)
   - Verify installation by opening PowerShell and running:
     ```powershell
     dotnet --info
     ```
   - This step is required for the PowerShell integration via pythonnet. Without it, OpenHands will fall back to a more limited PowerShell implementation.

4. **Install Git**
   - Download Git from [git-scm.com](https://git-scm.com/download/win)
   - Use default installation options
   - Verify installation:
     ```powershell
     git --version
     ```

5. **Install Node.js and npm**
   - Download Node.js from [nodejs.org](https://nodejs.org/) (LTS version recommended)
   - During installation, accept the default options which will install npm as well
   - Verify installation:
     ```powershell
     node --version
     npm --version
     ```

6. **Install Poetry**
   - Open PowerShell as Administrator and run:
     ```powershell
     (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
     ```
   - Add Poetry to your PATH:
     ```powershell
     $env:Path += ";$env:APPDATA\Python\Scripts"
     ```
   - Verify installation:
     ```powershell
     poetry --version
     ```

## Step 2: Clone and Set Up OpenHands

1. **Clone the Repository**
   ```powershell
   git clone https://github.com/All-Hands-AI/OpenHands.git
   cd OpenHands
   ```

2. **Install Dependencies**
   ```powershell
   poetry install
   ```
   
   This will install all required dependencies, including:
   - pythonnet - Required for Windows PowerShell integration
   - All other OpenHands dependencies

## Step 3: Run OpenHands

1. **Build the Frontend**
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

   This will build the frontend files that the backend will serve.

2. **Start the Backend**
   ```powershell
   # Make sure to use PowerShell 7 (pwsh) instead of Windows PowerShell
   pwsh
   $env:RUNTIME="local"; poetry run uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000 --reload --reload-exclude "./workspace"
   ```

   This will start the OpenHands backend using the local runtime with PowerShell integration.

   > **Note**: If you encounter a `RuntimeError: Directory './frontend/build' does not exist` error, make sure you've built the frontend first using the command above.
   
   > **Important**: Using PowerShell 7 (pwsh) instead of Windows PowerShell is recommended to avoid "System.Management.Automation" errors. If you encounter this error, see the Troubleshooting section below.

3. **Alternatively, Run the Frontend in Development Mode (in a separate PowerShell window)**
   ```powershell
   cd frontend
   npm run dev
   ```

4. **Access the OpenHands GUI**
   
   Open your browser and navigate to:
   ```
   http://localhost:3001
   ```

## Limitations on Windows

When running OpenHands on Windows without WSL or Docker, be aware of the following limitations:

1. **Browser Tool Not Supported**: The browser tool is not currently supported on Windows.

2. **.NET Core Requirement**: The PowerShell integration requires .NET Core Runtime to be installed. If .NET Core is not available, OpenHands will automatically fall back to a more limited PowerShell implementation with reduced functionality.

3. **Interactive Shell Commands**: Some interactive shell commands may not work as expected. The PowerShell session implementation has limitations compared to the bash session used on Linux/macOS.

4. **Path Handling**: Windows uses backslashes (`\`) in paths, which may require adjustments when working with code examples designed for Unix-like systems.

5. **Performance**: Some operations may be slower on Windows compared to Linux/macOS.

## Troubleshooting

### "System.Management.Automation" Not Found Error

If you encounter an error message stating that "System.Management.Automation" was not found, this typically indicates that you have a minimal version of PowerShell installed or that the .NET components required for PowerShell integration are missing.

To resolve this issue:

1. **Install the latest version of PowerShell** (PowerShell 7 or later) from the official Microsoft repository:
   - Visit [https://github.com/PowerShell/PowerShell/releases](https://github.com/PowerShell/PowerShell/releases)
   - Download and install the latest MSI package for your system architecture (x64 for most systems)
   - During installation, make sure to select the option to "Add to PATH"

2. **Restart your terminal or command prompt** to ensure the new PowerShell is available

3. **Verify the installation** by running:
   ```powershell
   pwsh --version
   ```

4. **Run OpenHands using PowerShell 7** instead of Windows PowerShell:
   ```powershell
   pwsh -c "cd path\to\openhands && poetry run openhands"
   ```

5. **If the issue persists**, ensure that you have the .NET Runtime installed:
   - Download and install the latest .NET Runtime from [Microsoft's .NET download page](https://dotnet.microsoft.com/download)
   - Restart your computer after installation
   - Try running OpenHands again

6. **Ensure that the .NET Framework is properly installed** on your system:
   - Go to Control Panel > Programs > Programs and Features > Turn Windows features on or off
   - Make sure ".NET Framework" features are enabled

This error occurs because OpenHands uses the pythonnet package to interact with PowerShell, which requires the System.Management.Automation assembly from the .NET framework. A minimal PowerShell installation might not include all the necessary components for this integration.

### Environment Variable Errors

If you encounter errors related to environment variables, such as:

```
The term 'export' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

This is likely because you're using an older version of OpenHands that doesn't properly handle PowerShell environment variables. Update to the latest version of OpenHands, which includes Windows-specific handling for environment variables.

## Additional Resources

- [OpenHands Documentation](https://docs.all-hands.dev/)
- [PowerShell Documentation](https://learn.microsoft.com/en-us/powershell/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [PowerShell GitHub Repository](https://github.com/PowerShell/PowerShell)