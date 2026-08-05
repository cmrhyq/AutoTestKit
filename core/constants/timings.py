"""
测试等待时长常量（单位：秒）。

集中定义测试代码中针对不同 Kubernetes/业务资源创建/就绪所需的等待秒数，
避免各测试文件内散落 ``POD_CREATE_WAIT_SECONDS = 10`` 之类的重复魔法数字。

调整全局等待时长时只需修改此文件；如某个测试确实需要与全局不同的等待，
应在该测试内以命名良好的局部常量覆盖，并附注释说明原因。
"""


class Timing:
    """各类资源创建/就绪的等待秒数集合。"""

    #: Pod 创建后到就绪的等待秒数
    POD_CREATE_WAIT_SECONDS: int = 10
    #: Pod 相关操作的通用等待秒数（较长，用于批量创建/删除轮询）
    POD_WAIT_SECONDS: int = 20
    #: Workload（Deployment/StatefulSet 等）就绪等待秒数
    WORKLOAD_WAIT_SECONDS: int = 10
    #: PVC 创建后进入 Bound 状态的等待秒数
    PVC_CREATE_WAIT_SECONDS: int = 3
    #: ImagePullSecret 创建后的等待秒数
    IMAGEPULLSECRET_WAIT_SECONDS: int = 3
    #: CustomResource 创建后的等待秒数
    CR_CREATE_WAIT_SECONDS: int = 10
    #: DaemonSet 创建后的等待秒数
    DS_CREATE_WAIT_SECONDS: int = 3


__all__ = ["Timing"]
