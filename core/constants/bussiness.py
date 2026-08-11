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
    """自定义模板的构建/发布状态文案枚举。

    枚举值直接与前端展示文本对齐，可通过 ``value`` 与 DOM 中的
    ``text_content()`` 结果直接比较：

        >>> SandboxTemplateStatus.SUCCESS.value == "成功"
        True

    使用场景：
        - **判定构建终态**：模板创建后需要轮询等待
          "成功" / "失败" 之一出现，此时应使用 :meth:`terminal_values`；
        - **读取当前状态**：从表格单元格中匹配已知状态文本，
          此时应使用 :meth:`all_values` 做 ``in`` 判断。

    .. Note::
        - :attr:`SUCCESS` / :attr:`FAILED` 为轮询终态，出现后应终止轮询；
        - 其它枚举值仅用于状态展示读取，不作为终态判定依据。
    """

    #: 构建中（非终态，轮询时应继续等待）
    BUILDING = "构建中"
    #: 构建成功（终态）
    SUCCESS = "成功"
    #: 构建失败（终态）
    FAILED = "失败"
    #: 已构建、可用
    AVAILABLE = "可用"
    #: 已发布至运行时
    PUBLISHED = "已发布"
    #: 未发布
    UNPUBLISHED = "未发布"
    #: 通用正常状态
    NORMAL = "正常"

    @classmethod
    def terminal_values(cls) -> tuple:
        """返回轮询构建结果时的**终态**文本集合。

        Returns:
            tuple[str, ...]: ``("成功", "失败")``。任一出现即应停止轮询。
        """
        return (cls.SUCCESS.value, cls.FAILED.value)

    @classmethod
    def all_values(cls) -> tuple:
        """返回枚举中所有状态的文本集合。

        Returns:
            tuple[str, ...]: 所有状态文本，用于在表格 ``<td>`` 中做
            ``txt in valid_values`` 的成员判断。
        """
        return tuple(item.value for item in cls)
