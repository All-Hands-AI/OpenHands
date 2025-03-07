from typing import List, Dict, Any
import json

class ContextManager:
    """
    長期的なコンテキストを管理するシステム。
    
    このクラスは以下の機能を提供します：
    1. タスク関連の情報を保存
    2. 過去の実行結果を記憶
    3. 関連するコンテキストを提供
    """
    
    def __init__(self, max_context_items: int = 100):
        """
        ContextManagerを初期化します。
        
        Parameters:
        - max_context_items (int): 保存する最大コンテキストアイテム数
        """
        self.max_context_items = max_context_items
        self.context_items = []
        self.task_info = {}
        
    def add_context_item(self, item_type: str, content: Any) -> None:
        """
        コンテキストアイテムを追加します。
        
        Parameters:
        - item_type (str): アイテムのタイプ
        - content (Any): アイテムの内容
        """
        # 最大数を超える場合は古いアイテムを削除
        if len(self.context_items) >= self.max_context_items:
            self.context_items.pop(0)
            
        self.context_items.append({
            "type": item_type,
            "content": content
        })
        
    def set_task_info(self, key: str, value: Any) -> None:
        """
        タスク情報を設定します。
        
        Parameters:
        - key (str): 情報のキー
        - value (Any): 情報の値
        """
        self.task_info[key] = value
        
    def get_task_info(self, key: str) -> Any:
        """
        タスク情報を取得します。
        
        Parameters:
        - key (str): 情報のキー
        
        Returns:
        - Any: 情報の値
        """
        return self.task_info.get(key)
        
    def get_context_items_by_type(self, item_type: str) -> List[Dict[str, Any]]:
        """
        指定されたタイプのコンテキストアイテムを取得します。
        
        Parameters:
        - item_type (str): アイテムのタイプ
        
        Returns:
        - List[Dict[str, Any]]: コンテキストアイテムのリスト
        """
        return [item for item in self.context_items if item["type"] == item_type]
        
    def get_recent_context_items(self, count: int) -> List[Dict[str, Any]]:
        """
        最近のコンテキストアイテムを取得します。
        
        Parameters:
        - count (int): 取得するアイテム数
        
        Returns:
        - List[Dict[str, Any]]: コンテキストアイテムのリスト
        """
        return self.context_items[-count:]
        
    def clear_context(self) -> None:
        """
        コンテキストをクリアします。
        """
        self.context_items = []
        self.task_info = {}
        
    def get_context_summary(self) -> Dict[str, Any]:
        """
        コンテキストの要約を取得します。
        
        Returns:
        - Dict[str, Any]: コンテキストの要約
        """
        return {
            "total_items": len(self.context_items),
            "task_info": self.task_info,
            "recent_items": self.get_recent_context_items(10)
        }
        
    def to_json(self) -> str:
        """
        コンテキストをJSON形式に変換します。
        
        Returns:
        - str: JSON形式のコンテキスト
        """
        return json.dumps(self.get_context_summary())
