from typing import Any, Dict, Optional

class SettingsStoreImpl:
    def __init__(self):
        self._settings: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        return self._settings.get(key)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def delete(self, key: str) -> None:
        if key in self._settings:
            del self._settings[key]