#!/data/data/com.termux/files/usr/bin/python3

"""
OpenHands Termux Installer
Installer Python untuk OpenHands di Termux
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Jalankan command dengan error handling"""
    print(f"📦 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Berhasil")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Gagal: {e.stderr}")
        return False

def check_termux():
    """Cek apakah berjalan di Termux"""
    return os.path.exists("/data/data/com.termux")

def install_packages():
    """Install packages yang diperlukan"""
    packages = [
        "python", "python-pip", "git", "nodejs", "npm", 
        "rust", "binutils", "clang", "make", "cmake", 
        "pkg-config", "libffi", "openssl", "zlib"
    ]
    
    print("📦 Updating Termux packages...")
    if not run_command("pkg update -y && pkg upgrade -y", "Update packages"):
        return False
    
    print("📦 Installing required packages...")
    package_list = " ".join(packages)
    return run_command(f"pkg install -y {package_list}", "Install packages")

def install_python_deps():
    """Install Python dependencies"""
    print("🐍 Installing Python dependencies...")
    
    # Upgrade pip
    if not run_command("pip install --upgrade pip setuptools wheel", "Upgrade pip"):
        return False
    
    # Install requirements
    requirements = [
        "litellm>=1.60.0",
        "aiohttp>=3.9.0",
        "fastapi",
        "uvicorn",
        "toml",
        "python-dotenv",
        "termcolor",
        "jinja2>=3.1.3",
        "tenacity>=8.5",
        "pyjwt>=2.9.0",
        "requests",
        "prompt-toolkit>=3.0.50",
        "json-repair",
        "pathspec>=0.12.1",
        "whatthepatch>=1.0.6"
    ]
    
    for req in requirements:
        if not run_command(f"pip install '{req}'", f"Install {req}"):
            print(f"⚠️ Warning: Failed to install {req}, continuing...")
    
    return True

def setup_directories():
    """Setup direktori yang diperlukan"""
    print("📁 Creating directories...")
    
    dirs = [
        Path.home() / ".openhands",
        Path.home() / ".openhands" / "config",
        Path.home() / ".openhands" / "workspace",
        Path.home() / ".openhands" / "cache",
        Path.home() / ".openhands" / "trajectories",
        Path.home() / ".openhands" / "file_store"
    ]
    
    for dir_path in dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_path}")
        except Exception as e:
            print(f"❌ Failed to create {dir_path}: {e}")
            return False
    
    return True

def setup_config():
    """Setup konfigurasi default"""
    print("⚙️ Setting up configuration...")
    
    config_file = Path.home() / ".openhands" / "config" / "config.toml"
    
    if config_file.exists():
        print("⚠️ Config file already exists, skipping...")
        return True
    
    try:
        # Copy config template
        if Path("termux_config.toml").exists():
            shutil.copy("termux_config.toml", config_file)
            print(f"✅ Config copied to {config_file}")
        else:
            print("⚠️ Config template not found, will create default")
            # Create minimal config
            config_content = """[llm]
api_key = ""
base_url = "https://api.openai.com/v1"
model = "gpt-3.5-turbo"
temperature = 0.7

[core]
workspace_base = "~/.openhands/workspace"
debug = false
"""
            with open(config_file, 'w') as f:
                f.write(config_content)
            print(f"✅ Default config created at {config_file}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to setup config: {e}")
        return False

def setup_cli():
    """Setup CLI executable"""
    print("🔧 Setting up CLI...")
    
    try:
        # Make CLI executable
        cli_file = Path("termux_cli.py")
        if cli_file.exists():
            os.chmod(cli_file, 0o755)
            
            # Create symlink
            bin_dir = Path.home() / ".openhands"
            bin_file = bin_dir / "openhands"
            
            if bin_file.exists():
                bin_file.unlink()
            
            bin_file.symlink_to(cli_file.absolute())
            print(f"✅ CLI linked to {bin_file}")
            
            # Copy agent file
            agent_file = Path("termux_agent.py")
            if agent_file.exists():
                shutil.copy(agent_file, bin_dir / "termux_agent.py")
                print("✅ Agent file copied")
            
            return True
        else:
            print("❌ CLI file not found")
            return False
            
    except Exception as e:
        print(f"❌ Failed to setup CLI: {e}")
        return False

def setup_path():
    """Setup PATH environment"""
    print("🔗 Setting up PATH...")
    
    try:
        bashrc = Path.home() / ".bashrc"
        path_line = 'export PATH="$HOME/.openhands:$PATH"'
        
        # Check if already in bashrc
        if bashrc.exists():
            with open(bashrc, 'r') as f:
                content = f.read()
                if path_line in content:
                    print("✅ PATH already configured")
                    return True
        
        # Add to bashrc
        with open(bashrc, 'a') as f:
            f.write(f"\n# OpenHands Termux\n{path_line}\n")
        
        print("✅ PATH added to .bashrc")
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup PATH: {e}")
        return False

def main():
    """Main installer function"""
    print("🚀 OpenHands Termux Installer")
    print("=" * 30)
    
    # Check if running in Termux
    if not check_termux():
        print("❌ This installer is designed for Termux only!")
        sys.exit(1)
    
    print("✅ Running in Termux environment")
    
    # Installation steps
    steps = [
        ("Installing packages", install_packages),
        ("Installing Python dependencies", install_python_deps),
        ("Setting up directories", setup_directories),
        ("Setting up configuration", setup_config),
        ("Setting up CLI", setup_cli),
        ("Setting up PATH", setup_path)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ {step_name} failed!")
        else:
            print(f"✅ {step_name} completed!")
    
    print("\n" + "=" * 50)
    
    if failed_steps:
        print("⚠️ Installation completed with some errors:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nYou may need to fix these issues manually.")
    else:
        print("🎉 Installation completed successfully!")
    
    print("\n📋 Next steps:")
    print("1. Restart Termux or run: source ~/.bashrc")
    print("2. Configure your API key: openhands config")
    print("3. Start using: openhands chat")
    print("\n📖 For help: openhands --help")

if __name__ == "__main__":
    main()