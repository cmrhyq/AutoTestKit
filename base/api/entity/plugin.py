"""
Plugin（插件中心）相关实体模型。

- McpValidatePayload: 插件中心 MCP 校验接口（validate/task、validate/feature）
  统一使用的请求体结构。
  用于 plugin_open_service.verify_task_config() / verify_task_feature()。
"""

from dataclasses import dataclass
from typing import Any, Dict


DEFAULT_TASK_CONTENT = (
    "apiVersion: v1\n"
    "kind: ConfigMap\n"
    "metadata:\n"
    "  name: example-config\n"
    "data:\n"
    "  config.yaml: |\n"
    "    key: value"
)

DEFAULT_FEATURE_CONTENT = (
    "name: example-feature\n"
    "description: 示例特性\n"
    "type: menu\n"
    "position: /admin/plugins"
)


@dataclass
class McpValidatePayload(object):
    """
    MCP 校验请求体。

    type: 校验类型，例如 "kubernetes"、"feature"
    content: 待校验的原始文本（YAML 或其它 DSL）
    """
    type: str
    content: str

    def to_payload(self) -> Dict[str, Any]:
        """转换为接口请求所需的字典结构。"""
        return {
            "type": self.type,
            "content": self.content,
        }

    @classmethod
    def default_task(cls) -> "McpValidatePayload":
        """任务配置校验的默认实体（对应 validate/task 接口）。"""
        return cls(type="kubernetes", content=DEFAULT_TASK_CONTENT)

    @classmethod
    def default_feature(cls) -> "McpValidatePayload":
        """Feature 校验的默认实体（对应 validate/feature 接口）。"""
        return cls(type="feature", content=DEFAULT_FEATURE_CONTENT)


__all__ = [
    "McpValidatePayload",
    "DEFAULT_TASK_CONTENT",
    "DEFAULT_FEATURE_CONTENT",
]
