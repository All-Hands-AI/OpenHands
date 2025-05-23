# Running OpenHands GUI on Windows Without WSL

This guide provides step-by-step instructions for running OpenHands on a Windows machine without using WSL or Docker.

## Prerequisites

1. **Windows 10/11** - A modern Windows operating system
2. **PowerShell 5.1 or PowerShell 7+** - Windows PowerShell comes pre-installed on Windows 10/11, but PowerShell 7+ is recommended for better compatibility
3. **Python 3.12** - Python 3.12 is required (Python 3.14 is not supported due to pythonnet compatibility)
4. **Git** - For cloning the repository and version control
5. **Node.js and npm** - For running the frontend

## Step 1: Install Required Software

1. **Install Python 3.12**
   - Download Python 3.12.x from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation by opening PowerShell and running:
     ```powershell
     python --version
     ```

2. **Install Git**
   - Download Git from [git-scm.com](https://git-scm.com/download/win)
   - Use default installation options
   - Verify installation:
     ```powershell
     git --version
     ```

3. **Install Node.js and npm**
   - Download Node.js from [nodejs.org](https://nodejs.org/) (LTS version recommended)
   - During installation, accept the default options which will install npm as well
   - Verify installation:
     ```powershell
     node --version
     npm --version
     ```

4. **Install Poetry**
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
   $env:LOCAL_RUNTIME_MODE=1; poetry run uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000 --reload --reload-exclude "./workspace"
   ```

   This will start the OpenHands backend using the local runtime with PowerShell integration.

   > **Note**: If you encounter a `RuntimeError: Directory './frontend/build' does not exist` error, make sure you've built the frontend first using the command above.

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

2. **Interactive Shell Commands**: Some interactive shell commands may not work as expected. The PowerShell session implementation has limitations compared to the bash session used on Linux/macOS.

3. **Path Handling**: Windows uses backslashes (`\`) in paths, which may require adjustments when working with code examples designed for Unix-like systems.

4. **Performance**: Some operations may be slower on Windows compared to Linux/macOS.

## Additional Resources

- [OpenHands Documentation](https://docs.all-hands.dev/)
- [PowerShell Documentation](https://learn.microsoft.com/en-us/powershell/)
- [Poetry Documentation](https://python-poetry.org/docs/)