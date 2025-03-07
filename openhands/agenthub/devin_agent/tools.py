from typing import List, Dict, Any

def get_tools(
    enable_browsing: bool = True,
    enable_jupyter: bool = True,
    enable_llm_editor: bool = False,
) -> List[Dict[str, Any]]:
    """
    DevinAgentで使用するツールを取得します。
    
    Parameters:
    - enable_browsing (bool): ブラウジングツールを有効にするかどうか
    - enable_jupyter (bool): Jupyterツールを有効にするかどうか
    - enable_llm_editor (bool): LLMエディタツールを有効にするかどうか
    
    Returns:
    - List[Dict[str, Any]]: ツールのリスト
    """
    tools = []
    
    # シェルコマンド実行ツール
    tools.append({
        "name": "shell",
        "description": "シェルコマンドを実行します。",
        "parameters": {
            "command": {
                "type": "string",
                "description": "実行するシェルコマンド"
            }
        },
        "action_type": "CmdRunAction"
    })
    
    # ファイル読み込みツール
    tools.append({
        "name": "read_file",
        "description": "ファイルの内容を読み込みます。",
        "parameters": {
            "path": {
                "type": "string",
                "description": "読み込むファイルのパス"
            }
        },
        "action_type": "FileReadAction"
    })
    
    # ファイル書き込みツール
    tools.append({
        "name": "write_file",
        "description": "ファイルに内容を書き込みます。",
        "parameters": {
            "path": {
                "type": "string",
                "description": "書き込むファイルのパス"
            },
            "content": {
                "type": "string",
                "description": "書き込む内容"
            }
        },
        "action_type": "FileWriteAction"
    })
    
    # ブラウジングツール
    if enable_browsing:
        tools.append({
            "name": "browse",
            "description": "URLを開いてWebページを閲覧します。",
            "parameters": {
                "url": {
                    "type": "string",
                    "description": "開くURL"
                }
            },
            "action_type": "BrowseURLAction"
        })
    
    # Jupyterツール
    if enable_jupyter:
        tools.append({
            "name": "run_python",
            "description": "Pythonコードを実行します。",
            "parameters": {
                "code": {
                    "type": "string",
                    "description": "実行するPythonコード"
                }
            },
            "action_type": "IPythonRunCellAction"
        })
    
    # LLMエディタツール
    if enable_llm_editor:
        tools.append({
            "name": "edit_code",
            "description": "LLMを使用してコードを編集します。",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "編集するファイルのパス"
                },
                "instruction": {
                    "type": "string",
                    "description": "編集の指示"
                }
            },
            "action_type": "LLMEditorAction"
        })
    
    return tools
