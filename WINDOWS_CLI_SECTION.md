## Installing and Running the CLI

To install and run the OpenHands CLI on Windows without WSL, follow these steps:

### 1. Install uv (Python Package Manager)

Open PowerShell as Administrator and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install .NET SDK

The OpenHands CLI requires the .NET Core runtime for PowerShell integration. Install the .NET SDK which includes the runtime:

```powershell
winget install Microsoft.DotNet.SDK.8
```

Alternatively, you can download and install the .NET SDK from the [official Microsoft website](https://dotnet.microsoft.com/download).

### 3. Install and Run OpenHands

After installing the prerequisites, you can install and run OpenHands with:

```powershell
uvx --python 3.12 --from openhands-ai openhands
```

### Troubleshooting

If you encounter a `coreclr` error when running OpenHands, ensure that:

1. The .NET SDK is properly installed
2. Your system PATH includes the .NET SDK directories
3. You've restarted your PowerShell session after installing the .NET SDK

To verify your .NET installation, run:

```powershell
dotnet --info
```

This should display information about your installed .NET SDKs and runtimes.