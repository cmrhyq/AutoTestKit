from enum import Enum

from attr import dataclass

# ================== 菜单枚举 ==================
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
        - 节点管理
    镜像管理：
        - 镜像库管理
    模板管理：
        - 模板管理
        - 构建记录
    SDK使用示例：
        - SDK使用示例
    """
    SANDBOX_MANAGE = "沙箱管理"
    MAINTENANCE_DASHBOARD = "运维看板"
    SANDBOX_CLUSTER = "沙箱集群"
    CLUSTER_MANAGE = "集群管理"
    NODE_MANAGE = "节点管理"
    IMAGE_MANAGE = "镜像管理"
    IMAGE_LIBRARY_MANAGE = "镜像库管理"
    TEMPLATE_MANAGE = "模板管理"
    BUILD_RECORD = "构建记录"
    SDK_EXAMPLE = "SDK使用示例"

# ================== 页面Frame 枚举 ==================
@dataclass
class SandboxFramePath(str, Enum):
    """
    沙箱访问Frame Path
    SANDBOX_MANAGE = 沙箱管理
    NODE_MANAGE = 节点管理
    IMAGE_LIBRARY_MANAGE = 镜像库管理
    TEMPLATE_MANAGE = 模板管理
    BUILD_RECORD = 构建记录
    SDK_EXAMPLE = SDK使用示例
    """
    SANDBOX_MANAGE = "/iframe/sandbox-web/admin/sandboxManage"
    NODE_MANAGE = "/iframe/sandbox-web/cluster/node"
    IMAGE_LIBRARY_MANAGE = "/iframe/sandbox-web/admin/imageManage"
    TEMPLATE_MANAGE = "/iframe/sandbox-web/admin/templateManage"
    BUILD_RECORD = "/iframe/sandbox-web/templates/builds1"
    SDK_EXAMPLE = "/iframe/sandbox-web/sdk/examples1"

# ================== 模板构建状态 枚举 ==================
@dataclass
class SandboxTemplateStatus(str, Enum):
    """
    自定义模板构建/发布状态文案。

    Note:
        - SUCCESS / FAILED 为轮询终态；
        - 其它值用于状态展示读取。
    """
    BUILDING = "构建中"
    SUCCESS = "成功"
    FAILED = "失败"
    AVAILABLE = "可用"
    PUBLISHED = "已发布"
    UNPUBLISHED = "未发布"
    NORMAL = "正常"

    @classmethod
    def terminal_values(cls) -> tuple:
        """轮询构建结果时的终态文本集合。"""
        return (cls.SUCCESS.value, cls.FAILED.value)

    @classmethod
    def all_values(cls) -> tuple:
        """全部状态文本集合。"""
        return tuple(item.value for item in cls)
