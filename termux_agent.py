"""
TermuxAgent - Agent khusus untuk lingkungan Termux
"""

import os
import sys
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import litellm
    from litellm import completion
except ImportError:
    print("❌ Error: litellm tidak terinstall. Jalankan: pip install litellm")
    sys.exit(1)

class TermuxTools:
    """Tools khusus untuk Termux"""
    
    @staticmethod
    def execute_command(command: str) -> Dict[str, Any]:
        """Execute command di Termux"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timeout",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    @staticmethod
    def read_file(file_path: str) -> Dict[str, Any]:
        """Baca file"""
        try:
            path = Path(file_path).expanduser()
            if not path.exists():
                return {
                    "success": False,
                    "content": "",
                    "error": "File tidak ditemukan"
                }
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "error": str(e)
            }
    
    @staticmethod
    def write_file(file_path: str, content: str) -> Dict[str, Any]:
        """Tulis file"""
        try:
            path = Path(file_path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def list_directory(dir_path: str) -> Dict[str, Any]:
        """List isi direktori"""
        try:
            path = Path(dir_path).expanduser()
            if not path.exists():
                return {
                    "success": False,
                    "files": [],
                    "error": "Direktori tidak ditemukan"
                }
            
            files = []
            for item in path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {
                "success": True,
                "files": files,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "files": [],
                "error": str(e)
            }

class TermuxAgent:
    """Agent khusus untuk Termux dengan kemampuan tool calling"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config.get("llm", {})
        self.conversation_history = []
        self.tools = TermuxTools()
        
        # System prompt khusus untuk Termux
        self.system_prompt = """Anda adalah OpenHands AI Assistant yang berjalan di Termux (Android).

Anda memiliki akses ke tools berikut:
1. execute_command(command) - Menjalankan command di terminal Termux
2. read_file(file_path) - Membaca file
3. write_file(file_path, content) - Menulis file
4. list_directory(dir_path) - Melihat isi direktori

Anda dapat membantu dengan:
- Menjawab pertanyaan
- Menulis dan menjelaskan kode
- Menjalankan command di Termux
- Mengelola file dan direktori
- Membantu dengan tugas programming
- Memberikan saran dan solusi

Ketika diminta melakukan sesuatu yang memerlukan tool, gunakan format:
TOOL_CALL: nama_tool(parameter)

Contoh:
- Untuk menjalankan command: TOOL_CALL: execute_command("ls -la")
- Untuk membaca file: TOOL_CALL: read_file("/path/to/file.txt")
- Untuk menulis file: TOOL_CALL: write_file("/path/to/file.txt", "content")

Berikan jawaban yang jelas dan praktis untuk lingkungan Termux/Android."""
    
    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Parse tool calls dari respons AI"""
        tool_calls = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('TOOL_CALL:'):
                try:
                    tool_call = line[10:].strip()  # Remove 'TOOL_CALL:'
                    
                    # Parse function call
                    if '(' in tool_call and ')' in tool_call:
                        func_name = tool_call.split('(')[0].strip()
                        params_str = tool_call[tool_call.find('(')+1:tool_call.rfind(')')]
                        
                        # Simple parameter parsing
                        params = []
                        if params_str.strip():
                            # Handle quoted strings
                            if params_str.startswith('"') and params_str.endswith('"'):
                                params = [params_str[1:-1]]
                            elif params_str.startswith("'") and params_str.endswith("'"):
                                params = [params_str[1:-1]]
                            else:
                                # Split by comma for multiple params
                                params = [p.strip().strip('"\'') for p in params_str.split(',')]
                        
                        tool_calls.append({
                            "function": func_name,
                            "parameters": params
                        })
                except Exception as e:
                    print(f"Error parsing tool call: {e}")
        
        return tool_calls
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call"""
        func_name = tool_call["function"]
        params = tool_call["parameters"]
        
        try:
            if func_name == "execute_command" and len(params) >= 1:
                return self.tools.execute_command(params[0])
            elif func_name == "read_file" and len(params) >= 1:
                return self.tools.read_file(params[0])
            elif func_name == "write_file" and len(params) >= 2:
                return self.tools.write_file(params[0], params[1])
            elif func_name == "list_directory" and len(params) >= 1:
                return self.tools.list_directory(params[0])
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {func_name} or invalid parameters"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat(self, message: str) -> str:
        """Chat dengan AI dan execute tools jika diperlukan"""
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
                    "content": self.system_prompt
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
            
            # Parse dan execute tool calls
            tool_calls = self.parse_tool_calls(assistant_message)
            tool_results = []
            
            for tool_call in tool_calls:
                result = self.execute_tool_call(tool_call)
                tool_results.append({
                    "tool": tool_call["function"],
                    "result": result
                })
            
            # Jika ada tool calls, tambahkan hasil ke respons
            if tool_results:
                assistant_message += "\n\n📋 Tool Results:\n"
                for tr in tool_results:
                    if tr["result"]["success"]:
                        if "stdout" in tr["result"]:
                            assistant_message += f"\n✅ {tr['tool']}:\n```\n{tr['result']['stdout']}\n```"
                        elif "content" in tr["result"]:
                            assistant_message += f"\n✅ {tr['tool']}:\n```\n{tr['result']['content']}\n```"
                        elif "files" in tr["result"]:
                            files_info = "\n".join([f"  {f['type']}: {f['name']}" for f in tr['result']['files']])
                            assistant_message += f"\n✅ {tr['tool']}:\n```\n{files_info}\n```"
                        else:
                            assistant_message += f"\n✅ {tr['tool']}: Success"
                    else:
                        assistant_message += f"\n❌ {tr['tool']}: {tr['result']['error']}"
            
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