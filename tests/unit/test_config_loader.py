"""ConfigLoader 單元測試：驗證 local / production 模式下配置取得。"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.clients.config_loader import ConfigLoader


@pytest.fixture
def local_mode_env():
    """設定 ENV_MODE=local 並清理其他可能干擾的 env。"""
    with patch.dict(os.environ, {"ENV_MODE": "local"}, clear=False):
        yield


@pytest.fixture
def production_mode_env():
    """設定 ENV_MODE=production 與 PROJECT_ID。"""
    with patch.dict(
        os.environ,
        {"ENV_MODE": "production", "PROJECT_ID": "test-project"},
        clear=False,
    ):
        yield


@pytest.fixture
def mock_dotenv():
    """Mock load_dotenv，並可控制 os.environ 內容。"""
    with patch("src.clients.config_loader.load_dotenv") as m:
        yield m


@pytest.fixture
def mock_secret_manager():
    """Mock Secret Manager 客戶端與 access_secret_version 回傳值。"""
    with patch("src.clients.config_loader.secretmanager", create=True) as mock_sm:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.payload.data = b"secret-value-from-gcp"
        mock_client.access_secret_version.return_value = mock_response
        mock_sm.SecretManagerServiceClient.return_value = mock_client
        yield mock_client


def test_local_mode_default_env_mode():
    """未設定 ENV_MODE 時，預設為 local。"""
    with patch.dict(os.environ, {}, clear=False):
        # 移除 ENV_MODE 若存在
        os.environ.pop("ENV_MODE", None)
    with patch("src.clients.config_loader.load_dotenv"):
        loader = ConfigLoader(env_mode=None)
    assert loader.env_mode == ConfigLoader.ENV_MODE_LOCAL


def test_local_mode_get_secret_from_env(local_mode_env, mock_dotenv):
    """local 模式下，get_secret 從 os.environ 讀取。"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"}, clear=False):
        loader = ConfigLoader(env_mode="local")
        value = loader.get_secret("GEMINI_API_KEY")
    assert value == "test-key-123"
    mock_dotenv.assert_called()


def test_local_mode_get_secret_missing_returns_none(local_mode_env, mock_dotenv):
    """local 模式下，不存在的 key 回傳 None。"""
    with patch.dict(os.environ, {}, clear=False):
        for k in ("GEMINI_API_KEY", "PROJECT_ID"):
            os.environ.pop(k, None)
    loader = ConfigLoader(env_mode="local")
    assert loader.get_secret("GEMINI_API_KEY") is None
    assert loader.get_secret("MISSING_KEY") is None


def test_production_mode_get_secret_from_secret_manager(production_mode_env, mock_secret_manager):
    """production 模式下，get_secret 從 Secret Manager 取得並解碼。"""
    with patch("google.cloud.secretmanager.SecretManagerServiceClient", return_value=mock_secret_manager):
        loader = ConfigLoader(env_mode="production")
        value = loader.get_secret("GEMINI_API_KEY")
    assert value == "secret-value-from-gcp"
    mock_secret_manager.access_secret_version.assert_called_once()
    call_args = mock_secret_manager.access_secret_version.call_args
    assert "request" in call_args.kwargs
    assert call_args.kwargs["request"]["name"] == "projects/test-project/secrets/GEMINI_API_KEY/versions/latest"


def test_production_mode_no_project_id_returns_none():
    """production 模式下若無 PROJECT_ID，get_secret 回傳 None。"""
    with patch.dict(os.environ, {"ENV_MODE": "production"}, clear=False):
        os.environ.pop("PROJECT_ID", None)
        os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
    with patch("google.cloud.secretmanager.SecretManagerServiceClient"):
        loader = ConfigLoader(env_mode="production")
        value = loader.get_secret("GEMINI_API_KEY")
    assert value is None


def test_production_mode_secret_manager_exception_returns_none(production_mode_env):
    """production 模式下 Secret Manager 拋錯時，get_secret 回傳 None。"""
    mock_client = MagicMock()
    mock_client.access_secret_version.side_effect = Exception("Permission denied")
    with patch("google.cloud.secretmanager.SecretManagerServiceClient", return_value=mock_client):
        loader = ConfigLoader(env_mode="production")
        value = loader.get_secret("GEMINI_API_KEY")
    assert value is None


def test_env_mode_property():
    """env_mode 屬性回傳目前模式。"""
    assert ConfigLoader(env_mode="local").env_mode == "local"
    assert ConfigLoader(env_mode="production").env_mode == "production"
