
import os
import yaml
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class WorkspaceConfig:
    name: str
    path: str
    description: str = ""
    is_active: bool = False


@dataclass
class ModelConfig:
    name: str
    codename: str
    model: str
    provider: str
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.7
    system_prompt: str = ""
    triggers: List[str] = field(default_factory=list)


@dataclass
class BrowserConfig:
    engine: str = "selenium"  # selenium or playwright
    browser_type: str = "chrome"  # chrome, firefox, edge, safari
    headless: bool = False
    window_width: int = 1920
    window_height: int = 1080
    user_data_dir: str = ""
    proxy: str = ""
    user_agent: str = ""
    extensions: List[str] = field(default_factory=list)
    arguments: List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    version: str = "2.0.0"
    app_name: str = "赛博印钞机 Pro Ultra"
    workspaces: List[WorkspaceConfig] = field(default_factory=list)
    models: List[ModelConfig] = field(default_factory=list)
    current_workspace: str = "default"
    theme: str = "dark"
    browser: BrowserConfig = field(default_factory=BrowserConfig)


class ConfigManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.config_path = self.base_path / "configs" / "app_config.yaml"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    # Convert dict workspaces to WorkspaceConfig objects
                    if 'workspaces' in data:
                        data['workspaces'] = [WorkspaceConfig(**ws) for ws in data['workspaces']]
                    # Convert dict models to ModelConfig objects
                    if 'models' in data:
                        data['models'] = [ModelConfig(**m) for m in data['models']]
                    # Convert dict browser to BrowserConfig object
                    if 'browser' in data and isinstance(data['browser'], dict):
                        data['browser'] = BrowserConfig(**data['browser'])
                    else:
                        data['browser'] = BrowserConfig()
                    return AppConfig(**data)
            except Exception as e:
                print(f"配置加载失败，使用默认配置: {e}")
        return self._create_default_config()

    def _create_default_config(self) -> AppConfig:
        default_workspace = WorkspaceConfig(
            name="default",
            path=str(self.base_path / "workspaces" / "default"),
            description="默认工作区",
            is_active=True
        )
        return AppConfig(workspaces=[default_workspace])

    def save_config(self):
        data = {
            "version": self.config.version,
            "app_name": self.config.app_name,
            "workspaces": [ws.__dict__ for ws in self.config.workspaces],
            "models": [m.__dict__ for m in self.config.models],
            "current_workspace": self.config.current_workspace,
            "theme": self.config.theme,
            "browser": self.config.browser.__dict__
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)

    def get_active_workspace(self) -> Optional[WorkspaceConfig]:
        for ws in self.config.workspaces:
            if ws.is_active:
                return ws
        return None

    def set_active_workspace(self, name: str):
        for ws in self.config.workspaces:
            ws.is_active = (ws.name == name)
        self.config.current_workspace = name
        self.save_config()

    def add_workspace(self, name: str, path: str, description: str = ""):
        ws = WorkspaceConfig(
            name=name,
            path=path,
            description=description,
            is_active=False
        )
        self.config.workspaces.append(ws)
        self.save_config()

    def add_model(self, model_config: ModelConfig):
        self.config.models.append(model_config)
        self.save_config()

    def get_model(self, name: str) -> Optional[ModelConfig]:
        for m in self.config.models:
            if m.name == name:
                return m
        return None

    def get_browser_config(self) -> BrowserConfig:
        return self.config.browser

    def update_browser_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config.browser, key):
                setattr(self.config.browser, key, value)
        self.save_config()

