from typing import List, Dict, Any
import json

class PlanningSystem:
    """
    計画立案と実行を管理するシステム。
    
    このクラスは以下の機能を提供します：
    1. タスクを小さなステップに分割する計画を生成
    2. 計画の実行状態を追跡
    3. 実行結果に基づいて計画を適応
    """
    
    def __init__(self, max_steps: int = 10):
        """
        PlanningSystemを初期化します。
        
        Parameters:
        - max_steps (int): 計画の最大ステップ数
        """
        self.max_steps = max_steps
        self.current_plan = []
        self.current_step_index = 0
        self.step_results = {}
        
    def create_plan(self, task: str, plan_steps: List[str]) -> List[str]:
        """
        タスクに基づいて計画を作成します。
        
        Parameters:
        - task (str): 実行するタスク
        - plan_steps (List[str]): LLMから生成された計画ステップ
        
        Returns:
        - List[str]: 作成された計画
        """
        # 計画ステップ数を制限
        self.current_plan = plan_steps[:self.max_steps]
        self.current_step_index = 0
        self.step_results = {}
        
        return self.current_plan
        
    def get_current_step(self) -> str:
        """
        現在のステップを取得します。
        
        Returns:
        - str: 現在のステップ
        """
        if self.current_step_index < len(self.current_plan):
            return self.current_plan[self.current_step_index]
        return ""
        
    def record_step_result(self, result: Dict[str, Any]) -> None:
        """
        ステップの実行結果を記録します。
        
        Parameters:
        - result (Dict[str, Any]): ステップの実行結果
        """
        self.step_results[self.current_step_index] = result
        
    def advance_to_next_step(self) -> bool:
        """
        次のステップに進みます。
        
        Returns:
        - bool: 次のステップが存在する場合はTrue、そうでない場合はFalse
        """
        self.current_step_index += 1
        return self.current_step_index < len(self.current_plan)
        
    def is_plan_complete(self) -> bool:
        """
        計画が完了したかどうかを確認します。
        
        Returns:
        - bool: 計画が完了した場合はTrue、そうでない場合はFalse
        """
        return self.current_step_index >= len(self.current_plan)
        
    def adapt_plan(self, feedback: str, remaining_steps: List[str]) -> List[str]:
        """
        フィードバックに基づいて計画を適応させます。
        
        Parameters:
        - feedback (str): ユーザーからのフィードバック
        - remaining_steps (List[str]): LLMから生成された残りのステップ
        
        Returns:
        - List[str]: 適応された計画
        """
        # 現在のステップまでの計画を保持
        adapted_plan = self.current_plan[:self.current_step_index]
        
        # 残りのステップを更新
        adapted_plan.extend(remaining_steps)
        
        # 計画を更新
        self.current_plan = adapted_plan
        
        return self.current_plan
        
    def get_plan_summary(self) -> Dict[str, Any]:
        """
        計画の要約を取得します。
        
        Returns:
        - Dict[str, Any]: 計画の要約
        """
        return {
            "total_steps": len(self.current_plan),
            "completed_steps": self.current_step_index,
            "current_step": self.get_current_step(),
            "is_complete": self.is_plan_complete(),
            "steps": self.current_plan,
            "results": self.step_results
        }
        
    def to_json(self) -> str:
        """
        計画をJSON形式に変換します。
        
        Returns:
        - str: JSON形式の計画
        """
        return json.dumps(self.get_plan_summary())
