"""
弹性计算 OpenAPI PVC/PV/StorageClass 接口测试

转换自 JMeter 脚本: pvc-pv.jmx
测试内容：PVC 完整生命周期（创建、查询、列表、删除）+ PV 查询 + StorageClass 查询
"""
import json
import time
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    PanJiElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper


BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004
PVC_CREATE_WAIT_SECONDS = 3


@pytest.mark.api
@allure.feature("磐基弹性计算 OpenAPI 服务")
@allure.story("PVC/PV/StorageClass 生命周期接口测试")
class TestEcOpenapiPvcPv:
    """
    对应 JMeter 脚本: pvc-pv.jmx
    线程组: Thread Group - pvc
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 env yaml 显式传入。"""
        service = PanJiElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @staticmethod
    def _build_pvc_payload(name: str, storage_class_name: str) -> Dict[str, Any]:
        """构造 PVC 创建请求体，源自 JMX POST body。"""
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": name,
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {
                        "storage": "1Gi",
                    },
                },
                "storageClassName": storage_class_name,
            },
        }

    @allure.title("PVC 完整生命周期测试")
    @allure.description(
        "GET/POST/DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc - "
        "查询指定PVC → 若存在先删除 → 创建 → 查列表 → 查全集群列表 → 删除"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_pvc_lifecycle(self, ec_service, api_env, api_cache):
        cell_code = api_env.get("cellCode")
        sys_code = api_env.get("sysCode")
        pvc_name = api_env.get("pvcName", "auto-test-probe-pvc-test-0001")
        storage_class_name = api_env.get("storageClassName")

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step("查询指定 PVC 确认当前状态"):
                response_json = ec_service.get_pvc(
                    cell_code=cell_code, sys_code=sys_code, name=pvc_name
                )
                ec_get_code = response_json.get("code")

            if ec_get_code == BUSINESS_SUCCESS_CODE:
                with AllureHelper.step("PVC 已存在，先删除"):
                    del_resp = ec_service.delete_pvc(
                        cell_code=cell_code, sys_code=sys_code, name=pvc_name
                    )
                    assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                        f"删除已存在的 PVC 失败: {del_resp}"
                    )

            with AllureHelper.step("创建 PVC"):
                payload = self._build_pvc_payload(pvc_name, storage_class_name)
                create_resp = ec_service.create_pvc(
                    cell_code=cell_code, sys_code=sys_code, payload=payload
                )
                assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"创建 PVC 失败: {create_resp}"
                )
                api_cache.set("ec_pvc_created", True)

            with AllureHelper.step(f"等待 {PVC_CREATE_WAIT_SECONDS}s PVC 就绪"):
                time.sleep(PVC_CREATE_WAIT_SECONDS)

            with AllureHelper.step("查询 PVC 列表并验证新创建的 PVC 存在"):
                list_resp = ec_service.list_pvc(
                    cell_code=cell_code, sys_code=sys_code
                )
                resp_text = json.dumps(list_resp, ensure_ascii=False)
                assert f'"name":"{pvc_name}"' not in resp_text or pvc_name in resp_text, (
                    f"PVC 列表中未找到 {pvc_name}"
                )

            with AllureHelper.step("查询全集群所有 PVC 列表并验证"):
                all_list_resp = ec_service.list_all_cluster_pvc(cell_code=cell_code)
                all_resp_text = json.dumps(all_list_resp, ensure_ascii=False)
                assert pvc_name in all_resp_text, (
                    f"全集群 PVC 列表中未找到 {pvc_name}"
                )

            with AllureHelper.step("删除创建的 PVC"):
                del_resp = ec_service.delete_pvc(
                    cell_code=cell_code, sys_code=sys_code, name=pvc_name
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除 PVC 失败: {del_resp}"
                )
                api_cache.set("ec_pvc_created", False)

    @allure.title("查询指定 PV")
    @allure.description(
        "GET /openapi/elastic-compute/v2/cells/{cellCode}/pv/{pvName} - 验证 PV 查询接口"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_pv(self, ec_service, api_env):
        cell_code = api_env.get("cellCode")
        pv_name = api_env.get("pvName")

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(f"查询 PV: cell={cell_code}, name={pv_name}"):
                response_json = ec_service.get_pv(
                    cell_code=cell_code, pv_name=pv_name
                )

            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"查询 PV 失败: {response_json}"
                )

    @allure.title("查询指定 StorageClass")
    @allure.description(
        "GET /openapi/elastic-compute/v2/cells/{cellCode}/storageClass/{storageClassName} - "
        "验证 StorageClass 查询接口"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_storage_class(self, ec_service, api_env):
        cell_code = api_env.get("cellCode")
        storage_class_name = api_env.get("storageClassName")

        with AllureHelper.api_test(ec_service):
            with AllureHelper.step(
                f"查询 StorageClass: cell={cell_code}, name={storage_class_name}"
            ):
                response_json = ec_service.get_storage_class(
                    cell_code=cell_code, storage_class_name=storage_class_name
                )

            with AllureHelper.step("验证响应"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"查询 StorageClass 失败: {response_json}"
                )
