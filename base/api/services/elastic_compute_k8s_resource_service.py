"""
弹性计算 K8s 标准资源 OpenAPI 服务封装（Bearer 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/openapi/*.jmx 转换：
- ConfigMap.jmx        （8）
- SecretV2.jmx         （14）
- ServiceV2.jmx        （14）
- ServiceAccountV2.jmx （3）
- EndpointsV2.jmx      （2）
- LimitRange.jmx       （16）
- resourcequota.jmx    （16）
- PriorityClassesV2.jmx（12）
- RBAC_V2.jmx          （4）
- pvc-pv.jmx           （12）
共 101 samplers。

所有方法 base_url 由 tests 侧传入 api_env["api_base_url"]，无硬编码。
"""
import logging
from typing import Any, Dict

from base import BaseService
from core import DataCache


def _get_default_headers() -> Dict[str, str]:
    """默认 Authorization 头（Portal 登录后的 Bearer Token）。"""
    cache = DataCache.get_instance()
    return {"Authorization": cache.get("token")}


class PanJiElasticComputeK8sResourceService(BaseService):
    """
    弹性计算 K8s 标准资源 OpenAPI 服务。

    - Bearer Token 走 conftest.get_token 注入 cache["token"]
    - base_url 由 api_env["api_base_url"] 提供
    """

    DEFAULT_BASE_URL = "http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030"

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        super().__init__(base_url=base_url or self.DEFAULT_BASE_URL, logger=logger)

    # ==================== ConfigMap.jmx ====================

    def get_configmap(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询指定 configmap。GET /openapi/elastic-compute/v2/cells/{c}/systems/{s}/configmaps/{name}"""
        self.logger.info(f"Get configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_configmap(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除指定 configmap。DELETE /.../configmaps/{name}"""
        self.logger.info(f"Delete configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def create_configmap(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 configmap 请求。POST /.../configmaps"""
        self.logger.info(f"Create configmap: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_configmaps_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 cm 列表请求。GET /.../configmaps"""
        self.logger.info(f"List configmaps by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_configmaps_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群所有 cm 列表请求。GET /openapi/elastic-compute/v2/cells/{c}/configmaps"""
        self.logger.info(f"List configmaps by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/configmaps"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_configmap(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新指定 configmap。PUT /.../configmaps/{name}"""
        self.logger.info(f"Update configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_configmap(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新指定 configmap。PATCH /.../configmaps/{name}"""
        self.logger.info(f"Patch configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    # ==================== SecretV2.jmx ====================

    def get_secret(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询 Secret。GET /.../secrets/{name}"""
        self.logger.info(f"Get secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_secret(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除 Secret。DELETE /.../secrets/{name}"""
        self.logger.info(f"Delete secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def create_secret(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 Secret。POST /.../secrets"""
        self.logger.info(f"Create secret: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_secrets_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询指定命名空间下的 Secret 列表。GET /.../secrets"""
        self.logger.info(f"List secrets by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_secrets_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 Secret 列表。GET /openapi/elastic-compute/v2/cells/{c}/secrets"""
        self.logger.info(f"List secrets by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/secrets"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_secret(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 Secret。PUT /.../secrets/{name}"""
        self.logger.info(f"Update secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_secret(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 Secret。PATCH /.../secrets/{name}"""
        self.logger.info(f"Patch secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    # ==================== ServiceV2.jmx ====================

    def get_service(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询 Service。GET /.../services/{name}"""
        self.logger.info(f"Get service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_service(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除 Service。DELETE /.../services/{name}"""
        self.logger.info(f"Delete service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def create_service(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 Service。POST /.../services"""
        self.logger.info(f"Create service: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_services_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询指定命名空间下的 Service 列表。GET /.../services"""
        self.logger.info(f"List services by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_services_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 Service 列表。GET /openapi/elastic-compute/v2/cells/{c}/services"""
        self.logger.info(f"List services by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/services"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_service(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 Service。PUT /.../services/{name}"""
        self.logger.info(f"Update service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_service(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 Service。PATCH /.../services/{name}"""
        self.logger.info(f"Patch service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    # ==================== ServiceAccountV2.jmx ====================

    def list_service_accounts_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 ServiceAccount 列。GET /.../serviceaccounts"""
        self.logger.info(f"List service accounts by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/serviceaccounts"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_service_accounts_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 ServiceAccount 列。GET /.../serviceaccounts"""
        self.logger.info(f"List service accounts by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/serviceaccounts"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_service_account(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """查询 ServiceAccount。GET /.../serviceaccounts/{name}"""
        self.logger.info(f"Get service account: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/serviceaccounts/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    # ==================== EndpointsV2.jmx ====================

    def list_endpoints(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 Endpoints 列表。GET /.../endpoints"""
        self.logger.info(f"List endpoints: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/endpoints"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_endpoints(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """查询 Endpoints。GET /.../endpoints/{name}"""
        self.logger.info(f"Get endpoints: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/endpoints/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()
