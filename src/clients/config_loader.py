"""配置管理模組：依 ENV_MODE 智慧切換 local（.env）與 production（Secret Manager）。"""

import os
from pathlib import Path

from dotenv import load_dotenv


class ConfigLoader:
    """
    統一配置載入：依 ENV_MODE 決定來源。
    - local：使用 python-dotenv 從專案根目錄 .env 讀取。
    - production：使用 Google Cloud Secret Manager 動態抓取金鑰。
    提供 get_secret(key_name) 供其他組件統一呼叫。
    """

    ENV_MODE_LOCAL = "local"
    ENV_MODE_PRODUCTION = "production"

    def __init__(self, env_mode: str | None = None, project_root: str | Path | None = None) -> None:
        self._env_mode = (env_mode or os.environ.get("ENV_MODE") or self.ENV_MODE_LOCAL).strip().lower()
        self._project_root = Path(project_root) if project_root else self._find_project_root()
        self._secret_client = None

        if self._env_mode == self.ENV_MODE_LOCAL:
            self._load_dotenv()
        elif self._env_mode == self.ENV_MODE_PRODUCTION:
            self._init_secret_client()

    def _find_project_root(self) -> Path:
        """尋找專案根目錄（含 .env 或 main.py 的目錄）。"""
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            if (parent / ".env").exists() or (parent / "main.py").exists():
                return parent
        return cwd

    def _load_dotenv(self) -> None:
        """local 模式：從根目錄 .env 載入環境變數。"""
        env_path = self._project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)

    def _init_secret_client(self) -> None:
        """production 模式：延遲初始化 Secret Manager 客戶端。"""
        try:
            from google.cloud.secretmanager import SecretManagerServiceClient
            self._secret_client = SecretManagerServiceClient()
        except Exception:
            self._secret_client = None

    def get_secret(self, key_name: str) -> str | None:
        """
        依目前模式取得金鑰／配置值。
        - local：從 os.environ 讀取（已由 dotenv 載入）。
        - production：從 Secret Manager 讀取，secret_id 使用 key_name。
        """
        if self._env_mode == self.ENV_MODE_LOCAL:
            return os.environ.get(key_name) or None

        if self._env_mode == self.ENV_MODE_PRODUCTION and self._secret_client:
            project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                return None
            try:
                name = f"projects/{project_id}/secrets/{key_name}/versions/latest"
                response = self._secret_client.access_secret_version(request={"name": name})
                return response.payload.data.decode("utf-8") if response.payload.data else None
            except Exception:
                return None

        return None

    @property
    def env_mode(self) -> str:
        """目前環境模式。"""
        return self._env_mode
