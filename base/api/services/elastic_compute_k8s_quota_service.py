"""
弹性计算 K8s 集群级资源 OpenAPI 服务封装（Bearer 鉴权）

基于 auto_test_pro 的 JMX：
- LimitRange.jmx        （16）
- resourcequota.jmx     （16）
- PriorityClassesV2.jmx （12）
- RBAC_V2.jmx           （4）
- pvc-pv.jmx            （12）
共 60 samplers。
"""
import logging
from typing import Any, Dict

from base import BaseService
from core import DataCache


def _get_default_headers() -> Dict[str, str]:
    """默认 Authorization 头。"""
    cache = DataCache.get_instance()
    return {"Authorization": cache.get("token")}


class PanJiElasticComputeK8sQuotaService(BaseService):
    """
    弹性计算 K8s 命名空间配额/优先级/RBAC/存储 OpenAPI 服务。
    """

    DEFAULT_BASE_URL = "http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030"

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        super().__init__(base_url=base_url or self.DEFAULT_BASE_URL, logger=logger)

    # ==================== LimitRange.jmx ====================

    def list_limitranges_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 LimitRange。GET /openapi/elastic-compute/v2/cells/{c}/limitranges"""
        self.logger.info(f"List limitranges by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/limitranges",
            headers=_get_default_headers(),
        ).json()

    def list_limitranges_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询命名空间下 LimitRange。GET /.../limitranges"""
        self.logger.info(f"List limitranges by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/limitranges"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_limitrange(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询 LimitRange。GET /.../limitranges/{name}"""
        self.logger.info(f"Get limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_limitrange(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 LimitRange。POST /.../limitranges"""
        self.logger.info(f"Create limitrange: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/limitranges"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_limitrange(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 LimitRange。PUT /.../limitranges/{name}"""
        self.logger.info(f"Update limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_limitrange(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 LimitRange。PATCH /.../limitranges/{name}"""
        self.logger.info(f"Patch limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_limitrange(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除 LimitRange。DELETE /.../limitranges/{name}"""
        self.logger.info(f"Delete limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== resourcequota.jmx ====================

    def list_resource_quotas_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 ResourceQuota。GET /.../resourcequotas"""
        self.logger.info(f"List resourcequotas by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/resourcequotas",
            headers=_get_default_headers(),
        ).json()

    def list_resource_quotas_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询命名空间 ResourceQuota。GET /.../resourcequotas"""
        self.logger.info(f"List resourcequotas by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourcequotas"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_resource_quota(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """查询 ResourceQuota。GET /.../resourcequotas/{name}"""
        self.logger.info(f"Get resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_resource_quota(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 ResourceQuota。POST /.../resourcequotas"""
        self.logger.info(f"Create resourcequota: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourcequotas"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_resource_quota(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 ResourceQuota。PUT /.../resourcequotas/{name}"""
        self.logger.info(f"Update resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_resource_quota(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 ResourceQuota。PATCH /.../resourcequotas/{name}"""
        self.logger.info(f"Patch resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_resource_quota(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """删除 ResourceQuota。DELETE /.../resourcequotas/{name}"""
        self.logger.info(f"Delete resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== PriorityClassesV2.jmx ====================

    def list_priority_classes(self, cell_code: str) -> Dict[str, Any]:
        """查询 PriorityClass 列表。GET /.../priorityclasses"""
        self.logger.info(f"List priority classes: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses",
            headers=_get_default_headers(),
        ).json()

    def get_priority_class(self, cell_code: str, name: str) -> Dict[str, Any]:
        """查询 PriorityClass。GET /.../priorityclasses/{name}"""
        self.logger.info(f"Get priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_priority_class(self, cell_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """创建 PriorityClass。POST /.../priorityclasses"""
        self.logger.info(f"Create priority class: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_priority_class(
        self, cell_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 PriorityClass。PUT /.../priorityclasses/{name}"""
        self.logger.info(f"Update priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_priority_class(
        self, cell_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 PriorityClass。PATCH /.../priorityclasses/{name}"""
        self.logger.info(f"Patch priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_priority_class(self, cell_code: str, name: str) -> Dict[str, Any]:
        """删除 PriorityClass。DELETE /.../priorityclasses/{name}"""
        self.logger.info(f"Delete priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== RBAC_V2.jmx ====================

    def list_rbac_roles(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 Role 列表。GET /.../roles"""
        self.logger.info(f"List rbac roles: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/roles"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_rbac_role_bindings(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 RoleBinding 列表。GET /.../rolebindings"""
        self.logger.info(f"List rbac rolebindings: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/rolebindings"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_rbac_cluster_roles(self, cell_code: str) -> Dict[str, Any]:
        """查询 ClusterRole 列表。GET /.../clusterroles"""
        self.logger.info(f"List rbac clusterroles: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/clusterroles",
            headers=_get_default_headers(),
        ).json()

    def list_rbac_cluster_role_bindings(self, cell_code: str) -> Dict[str, Any]:
        """查询 ClusterRoleBinding 列表。GET /.../clusterrolebindings"""
        self.logger.info(f"List rbac clusterrolebindings: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/clusterrolebindings",
            headers=_get_default_headers(),
        ).json()

    # ==================== pvc-pv.jmx ====================

    def list_pvcs_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 PVC。GET /.../persistentvolumeclaims"""
        self.logger.info(f"List pvcs by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumeclaims",
            headers=_get_default_headers(),
        ).json()

    def list_pvcs_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询命名空间 PVC。GET /.../persistentvolumeclaims"""
        self.logger.info(f"List pvcs by ns: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_pvc(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询 PVC。GET /.../persistentvolumeclaims/{name}"""
        self.logger.info(f"Get pvc: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_pvc(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 PVC。POST /.../persistentvolumeclaims"""
        self.logger.info(f"Create pvc: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims"
        )
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_pvc(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 PVC。PUT /.../persistentvolumeclaims/{name}"""
        self.logger.info(f"Update pvc: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_pvc(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 PVC。PATCH /.../persistentvolumeclaims/{name}"""
        self.logger.info(f"Patch pvc: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_pvc(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除 PVC。DELETE /.../persistentvolumeclaims/{name}"""
        self.logger.info(f"Delete pvc: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def list_pvs(self, cell_code: str) -> Dict[str, Any]:
        """查询 PV 列表。GET /.../persistentvolumes"""
        self.logger.info(f"List pvs: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes",
            headers=_get_default_headers(),
        ).json()

    def get_pv(self, cell_code: str, name: str) -> Dict[str, Any]:
        """查询 PV。GET /.../persistentvolumes/{name}"""
        self.logger.info(f"Get pv: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_pv(self, cell_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """创建 PV。POST /.../persistentvolumes"""
        self.logger.info(f"Create pv: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_pv(
        self, cell_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 PV。PUT /.../persistentvolumes/{name}"""
        self.logger.info(f"Update pv: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_pv(self, cell_code: str, name: str) -> Dict[str, Any]:
        """删除 PV。DELETE /.../persistentvolumes/{name}"""
        self.logger.info(f"Delete pv: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()
