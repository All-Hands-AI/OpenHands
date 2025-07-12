#!/data/data/com.termux/files/usr/bin/python3

"""
OpenHands Termux CLI
CLI sederhana untuk menjalankan OpenHands di Termux
"""

import os
import sys
import json
import toml
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import litellm
    from litellm import completion
except ImportError:
    print("❌ Error: litellm tidak terinstall. Jalankan: pip install litellm")
    sys.exit(1)

# Import TermuxAgent
try:
    from termux_agent import TermuxAgent
except ImportError:
    # Fallback ke simple agent jika termux_agent tidak tersedia
    TermuxAgent = None

class TermuxConfig:
    """Kelas untuk mengelola konfigurasi Termux"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".openhands" / "config"
        self.config_file = self.config_dir / "config.toml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """Load konfigurasi dari file"""
        if not self.config_file.exists():
            return self.get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return toml.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self.get_default_config()
    
    def save_config(self, config: Dict[str, Any]):
        """Simpan konfigurasi ke file"""
        try:
            with open(self.config_file, 'w') as f:
                toml.dump(config, f)
            print(f"✅ Konfigurasi disimpan ke {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Konfigurasi default"""
        return {
            "llm": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "timeout": 60
            },
            "core": {
                "workspace_base": str(Path.home() / ".openhands" / "workspace"),
                "max_iterations": 100,
                "debug": False
            }
        }

class SimpleTermuxAgent:
    """Agent sederhana untuk Termux (fallback)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config.get("llm", {})
        self.conversation_history = []
        
    async def chat(self, message: str) -> str:
        """Chat dengan AI"""
        try:
            # Tambahkan pesan ke history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            
            # Siapkan messages untuk API
            messages = [
                {
                    "role": "system",
                    "content": """Anda adalah OpenHands AI Assistant yang berjalan di Termux. 
                    Anda dapat membantu dengan:
                    - Menjawab pertanyaan
                    - Menulis dan menjelaskan kode
                    - Membantu dengan tugas programming
                    - Memberikan saran dan solusi
                    
                    Berikan jawaban yang jelas dan praktis untuk lingkungan Termux/Android."""
                }
            ] + self.conversation_history[-10:]  # Ambil 10 pesan terakhir
            
            # Panggil API
            response = await completion(
                model=self.llm_config.get("model", "gpt-3.5-turbo"),
                messages=messages,
                api_key=self.llm_config.get("api_key"),
                base_url=self.llm_config.get("base_url"),
                temperature=self.llm_config.get("temperature", 0.7),
                max_tokens=self.llm_config.get("max_output_tokens", 2048),
                timeout=self.llm_config.get("timeout", 60)
            )
            
            assistant_message = response.choices[0].message.content
            
            # Tambahkan respons ke history
            self.conversation_history.append({
                "role": "assistant", 
                "content": assistant_message
            })
            
            return assistant_message
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

def setup_config():
    """Setup konfigurasi interaktif"""
    config_manager = TermuxConfig()
    config = config_manager.load_config()
    
    print("🔧 Setup Konfigurasi OpenHands")
    print("=" * 30)
    
    # API Key
    current_key = config["llm"].get("api_key", "")
    if current_key:
        print(f"API Key saat ini: {current_key[:10]}...")
    
    new_key = input("Masukkan API Key (kosongkan untuk tidak mengubah): ").strip()
    if new_key:
        config["llm"]["api_key"] = new_key
    
    # Base URL
    current_url = config["llm"].get("base_url", "https://api.openai.com/v1")
    print(f"Base URL saat ini: {current_url}")
    
    new_url = input("Masukkan Base URL (kosongkan untuk tidak mengubah): ").strip()
    if new_url:
        config["llm"]["base_url"] = new_url
    
    # Model
    current_model = config["llm"].get("model", "gpt-3.5-turbo")
    print(f"Model saat ini: {current_model}")
    
    new_model = input("Masukkan Model (kosongkan untuk tidak mengubah): ").strip()
    if new_model:
        config["llm"]["model"] = new_model
    
    # Temperature
    current_temp = config["llm"].get("temperature", 0.7)
    print(f"Temperature saat ini: {current_temp}")
    
    temp_input = input("Masukkan Temperature 0.0-1.0 (kosongkan untuk tidak mengubah): ").strip()
    if temp_input:
        try:
            config["llm"]["temperature"] = float(temp_input)
        except ValueError:
            print("❌ Temperature harus berupa angka")
    
    # Simpan konfigurasi
    config_manager.save_config(config)
    print("✅ Konfigurasi berhasil disimpan!")

def show_config():
    """Tampilkan konfigurasi saat ini"""
    config_manager = TermuxConfig()
    config = config_manager.load_config()
    
    print("📋 Konfigurasi OpenHands")
    print("=" * 25)
    
    llm_config = config.get("llm", {})
    
    api_key = llm_config.get("api_key", "")
    if api_key:
        print(f"API Key: {api_key[:10]}...")
    else:
        print("API Key: Tidak diset")
    
    print(f"Base URL: {llm_config.get('base_url', 'Tidak diset')}")
    print(f"Model: {llm_config.get('model', 'Tidak diset')}")
    print(f"Temperature: {llm_config.get('temperature', 'Tidak diset')}")
    print(f"Max Tokens: {llm_config.get('max_output_tokens', 'Tidak diset')}")

async def start_chat():
    """Mulai sesi chat interaktif"""
    config_manager = TermuxConfig()
    config = config_manager.load_config()
    
    # Cek API key
    if not config["llm"].get("api_key"):
        print("❌ API Key belum diset. Jalankan: openhands config")
        return
    
    # Gunakan TermuxAgent jika tersedia, jika tidak gunakan SimpleTermuxAgent
    if TermuxAgent is not None:
        agent = TermuxAgent(config)
        print("🔧 Menggunakan Advanced TermuxAgent dengan tool support")
    else:
        agent = SimpleTermuxAgent(config)
        print("🔧 Menggunakan Simple TermuxAgent")
    
    print("🤖 OpenHands Chat - Termux Edition")
    print("=" * 35)
    print("Ketik 'exit' atau 'quit' untuk keluar")
    print("Ketik 'clear' untuk membersihkan history")
    print()
    
    while True:
        try:
            user_input = input("👤 Anda: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Sampai jumpa!")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("🧹 History percakapan dibersihkan")
                continue
            
            if not user_input:
                continue
            
            print("🤖 OpenHands: ", end="", flush=True)
            response = await agent.chat(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Sampai jumpa!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="OpenHands Termux CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  openhands config          # Setup konfigurasi
  openhands chat           # Mulai chat interaktif
  openhands show-config    # Tampilkan konfigurasi
  openhands --help         # Tampilkan bantuan
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=["config", "chat", "show-config"],
        default="chat",
        help="Perintah yang akan dijalankan"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="OpenHands Termux v1.0.0"
    )
    
    args = parser.parse_args()
    
    if args.command == "config":
        setup_config()
    elif args.command == "show-config":
        show_config()
    elif args.command == "chat":
        asyncio.run(start_chat())

if __name__ == "__main__":
    main()