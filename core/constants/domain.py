"""
领域内特化常量。

集中收拢分散在单点使用的、语义与 Harbor / Helm / 集群 flag 等域相关的常量。
这些常量虽然目前每个只在 1-2 个文件里使用，但集中定义可避免语义漂移
（如集群 flag 的 ``"0"/"1"`` 含义、Harbor 分页默认值），也便于新测试直接引用。
"""


class HarborConst:
    """Harbor 相关默认值。"""

    #: Harbor 列表接口默认页码
    DEFAULT_PAGE: int = 1
    #: Harbor 列表接口默认每页数量
    DEFAULT_PAGE_SIZE: int = 10
    #: Harbor 复制策略不限速的取值
    REPLICATION_SPEED_UNLIMITED: int = -1


class HelmConst:
    """Helm 相关默认值。"""

    #: Helm 冲突场景下后端返回的错误消息
    RESOURCE_CONFLICT_MSG: str = "RESOURCE CONFLICT"


class ClusterFlag:
    """集群类型 flag（后端约定的字符串枚举）。"""

    #: 标准集群
    STANDARD: str = "0"
    #: 宿主集群
    HOST: str = "1"


class SecretConst:
    """Secret 相关默认值。"""

    #: 默认镜像拉取 Secret 名称（自动化探针使用）
    DEFAULT_IMAGE_PULL_SECRET_NAME: str = "container-image-registry-auto-test-probe"


__all__ = ["HarborConst", "HelmConst", "ClusterFlag", "SecretConst"]
