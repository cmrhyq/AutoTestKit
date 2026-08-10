from enum import Enum

from attr import dataclass


@dataclass
class SystemMenu(str, Enum):
    """
    首页/沙箱/AI可观测
    """
    INDEX = "首页"
    SANDBOX = "沙箱"
    OBSERVABLE = "AI可观测"

@dataclass
class SandboxMenu(str, Enum):
    """
    沙箱管理：
        - 沙箱管理
        - 运维看板
    沙箱集群：
        - 集群管理
        - 节点管理
    镜像管理：
        - 镜像库管理
    模板管理：
        - 模板管理
        - 构建记录
    SDK使用示例：
        - SDK使用示例
    """
    SANDBOX_MANAGER = "沙箱管理"
    MAINTENANCE_DASHBOARD = "运维看板"
    SANDBOX_CLUSTER = "沙箱集群"
    CLUSTER_MANAGER = "集群管理"
    NODE_MANAGER = "节点管理"
    IMAGE_MANAGER = "镜像管理"
    IMAGE_LIBRARY_MANAGER = "镜像库管理"
    TEMPLATE_MANAGER = "模板管理"
    BUILD_RECORD = "构建记录"
    SDK_EXAMPLE = "SDK使用示例"

