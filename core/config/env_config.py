"""
环境适配配置模块

该模块提供基于配置文件的多环境配置管理。
根据环境名称自动加载对应的配置文件（如 config/env/env_dev.json, config/env/env_test.json）。
"""

import os
import re
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from jinja2 import Template, Environment, BaseLoader, UndefinedError
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

from core.config.system_config import system_manager


class EnvConfig:
    """环境配置类，支持字典式访问和属性访问"""
    
    def __init__(self, config_data: Dict[str, Any]):
        self._data = config_data
    
    def __getattr__(self, key: str) -> Any:
        """支持属性访问：config.apiBaseUrl"""
        if key.startswith('_'):
            return object.__getattribute__(self, key)
        return self._data.get(key)
    
    def __getitem__(self, key: str) -> Any:
        """支持字典访问：config['apiBaseUrl']"""
        return self._data.get(key)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持默认值"""
        return self._data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()
    
    def __repr__(self) -> str:
        return f"EnvConfig({self._data})"


class EnvironmentManager:
    """
    环境管理器
    
    根据环境名称从指定目录加载配置文件。
    支持 JSON 和 YAML 格式。
    
    配置文件命名规则：
    - env_{env_name}.json
    """
    
    def __init__(self, config_dir: str = None):
        """
        初始化环境管理器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = config_dir or Path(os.path.join(Path(__file__).parent.parent.parent, "config"))
        self._current_env: Optional[str] = None
        self._config: Optional[EnvConfig] = None
        
        # 从环境变量获取当前环境
        system = system_manager.get_config()
        env_name = system.get("test_env")
        self.load_env(env_name)
    
    def load_env(self, env_name: str) -> EnvConfig:
        """
        加载指定环境的配置
        
        Args:
            env_name: 环境名称（如 dev, test, staging, prod）
        
        Returns:
            EnvConfig: 配置对象
        
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        # 尝试加载 yaml 文件
        yaml_file = self.config_dir / f"env_{env_name}.yaml"
        
        config_data = None
        
        if yaml_file.exists():
            config_data = self._load_yaml(yaml_file)
        else:
            raise FileNotFoundError(
                f"配置文件不存在: {yaml_file}\n"
                f"请在 {self.config_dir} 目录下创建 env_{env_name}.yaml"
            )
        
        # 环境变量覆盖配置
        config_data = self._apply_env_overrides(config_data)
        
        self._current_env = env_name
        self._config = EnvConfig(config_data)
        
        return self._config
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """加载 YAML 配置文件，支持 jinja2 变量渲染"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # 如果安装了 jinja2，先进行变量渲染
            if HAS_JINJA2:
                raw_content = self._render_template(raw_content)
            
            return yaml.safe_load(raw_content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 格式错误 {file_path}: {e}")
        except ImportError:
            raise ImportError("需要安装 PyYAML: pip install pyyaml")
    
    def _render_template(self, content: str) -> str:
        """
        使用 jinja2 渲染配置模板中的变量
        
        支持两种变量语法：
        - jinja2 标准语法: {{ var_name }}
        - 简化语法: ${var_name}（自动转换为 jinja2 语法）
        
        变量来源（优先级从高到低）：
        1. 环境变量 CONFIG_<KEY>
        2. 系统环境变量
        3. system_config 中的配置项
        
        使用示例（在 YAML 配置文件中）：
            useraccount: auto${param}-user
            api_url: {{ api_host }}:{{ api_port }}
            
        对应的环境变量：
            CONFIG_PARAM=test → useraccount: autotest-user
        """
        # 将 ${var} 语法转换为 jinja2 的 {{ var }} 语法
        content = re.sub(r'\$\{(\w+)\}', r'{{ \1 }}', content)
        
        # 构建渲染上下文：合并 system_config + 环境变量
        context = {}
        
        # 1. 从 system_config 加载基础变量
        sys_config = system_manager.get_config()
        if hasattr(sys_config, 'config') and sys_config.config:
            context.update(sys_config.config)
        
        # 2. 从环境变量加载（优先级更高）
        for key, value in os.environ.items():
            if key.startswith("CONFIG_"):
                config_key = key[7:].lower()
                context[config_key] = value
            else:
                # 所有环境变量都可用，小写形式
                context[key.lower()] = value
        
        try:
            from jinja2 import DebugUndefined
            env = Environment(loader=BaseLoader(), undefined=DebugUndefined)
            template = env.from_string(content)
            rendered = template.render(**context)
            # 检查是否有未渲染的变量（DebugUndefined 会保留 {{ undefined }} 形式）
            if "{{ " in rendered:
                import logging
                logging.warning(
                    f"Configuration contains unresolved template variables. "
                    f"Check your environment variables or config files."
                )
            return rendered
        except Exception:
            # 渲染失败时返回原始内容，不中断流程
            return content
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用环境变量覆盖配置
        
        环境变量命名规则：CONFIG_<KEY> 会覆盖配置中的 key
        例如：CONFIG_API_BASE_URL 会覆盖 apiBaseUrl（大小写不敏感匹配 CONFIG_ 前缀部分）
        """
        result = config_data.copy()
        
        for key, value in os.environ.items():
            if key.startswith("CONFIG_"):
                config_key = key[7:].lower()  # 移除 CONFIG_ 前缀并转小写
                
                # 尝试转换类型
                if value.lower() in ("true", "false"):
                    result[config_key] = value.lower() == "true"
                elif value.isdigit():
                    result[config_key] = int(value)
                else:
                    try:
                        result[config_key] = float(value)
                    except ValueError:
                        result[config_key] = value
        
        return result
    
    def get_config(self) -> EnvConfig:
        """
        获取当前环境配置
        
        Returns:
            EnvConfig: 当前配置对象
        """
        if self._config is None:
            raise RuntimeError("配置未加载，请先调用 load_env()")
        return self._config
    
    def get_current_env(self) -> str:
        """获取当前环境名称"""
        return self._current_env or "unknown"
    
    def switch_env(self, env_name: str) -> EnvConfig:
        """
        切换到指定环境
        
        Args:
            env_name: 目标环境名称
        
        Returns:
            EnvConfig: 新环境的配置对象
        """
        return self.load_env(env_name)
    
    def list_available_envs(self) -> list[str]:
        """列出所有可用的环境配置"""
        if not self.config_dir.exists():
            return []
        
        envs = []
        for file in self.config_dir.glob("*"):
            if file.suffix in [".yaml"]:
                envs.append(file.stem)
        
        return sorted(envs)


# 创建全局环境管理器实例
env_manager = EnvironmentManager()

# 便捷函数
def get_env_config() -> EnvConfig:
    """获取当前环境配置"""
    return env_manager.get_config()


def get_current_env() -> str:
    """获取当前环境名称"""
    return env_manager.get_current_env()


def switch_env(env_name: str) -> EnvConfig:
    """切换环境"""
    return env_manager.switch_env(env_name)


def list_available_envs() -> list[str]:
    """列出所有可用环境"""
    return env_manager.list_available_envs()
