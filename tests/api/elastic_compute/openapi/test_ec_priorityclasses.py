"""
PriorityClass 接口测试

转换自 JMeter 脚本: PriorityClassesV2.jmx
测试内容：PriorityClass 完整生命周期（查询、创建、列表、PUT更新、PATCH更新、删除）
"""
import json
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 顶部常量抽取
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("PriorityClass 生命周期接口")
class TestEcOpenapiPriorityClasses:
    """
    对应 JMeter 脚本: PriorityClassesV2.jmx
    线程组: PriorityClass
    """

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 yaml 显式传入。"""
        service = ElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 PriorityClass 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "TEST"),
            "pc_name": api_env.get("priorityClassName", "pc-test"),
        }

    # -------------------- Payload 构造 --------------------

    @staticmethod
    def _build_create_payload(name: str) -> Dict[str, Any]:
        """构造 PriorityClass 创建请求体。"""
        return {
            "apiVersion": "scheduling.k8s.io/v1",
            "description": "this is a test",
            "kind": "PriorityClass",
            "metadata": {"name": name},
            "value": 100000000,
        }

    @staticmethod
    def _build_update_payload(name: str) -> Dict[str, Any]:
        """构造 PriorityClass PUT 更新请求体。"""
        return {
            "apiVersion": "scheduling.k8s.io/v1",
            "description": "this is a test",
            "kind": "PriorityClass",
            "metadata": {"name": name},
            "value": 100000000,
        }

    @staticmethod
    def _build_patch_payload() -> Dict[str, Any]:
        """构造 PriorityClass PATCH 增量更新请求体。"""
        return {
            "description": "this is a patched description",
            "globalDefault": True,
            "metadata": {
                "labels": {
                    "environment": "production",
                    "app": "critical-service",
                },
                "annotations": {
                    "update-reason": "configuration change",
                    "updated-by": "system-admin",
                },
            },
        }

    # -------------------- 测试用例 --------------------

    @pytest.mark.dependency(name="pc_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 PriorityClass")
    @allure.description("查询指定 PriorityClass 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_priorityclass_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 PriorityClass，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        pc_name = public_params["pc_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_priority_class(
                cell_code=cell_code, name=pc_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 PriorityClass 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_priority_class(
                    cell_code=cell_code, name=pc_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的 PriorityClass 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_pc_created", False)

    @pytest.mark.dependency(name="pc_create", depends=["pc_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 PriorityClass")
    @allure.description("创建 PriorityClass 资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_priorityclass(self, ec_service, public_params, api_cache):
        """创建 PriorityClass，断言创建成功。"""
        cell_code = public_params["cell_code"]
        pc_name = public_params["pc_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_create_payload(pc_name)
            create_resp = ec_service.create_priority_class(
                cell_code=cell_code, payload=create_payload,
            )

            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 PriorityClass 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

            api_cache.set("ec_pc_created", True)

    @pytest.mark.dependency(name="pc_list", depends=["pc_create"])
    @pytest.mark.order(3)
    @allure.title("查询 PriorityClass 列表")
    @allure.description("查询 PriorityClass 列表，验证包含新创建的资源")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_priorityclasses(self, ec_service, public_params):
        """查询 PriorityClass 列表，断言包含目标资源。"""
        cell_code = public_params["cell_code"]
        pc_name = public_params["pc_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_priority_classes(cell_code=cell_code)

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 PriorityClass 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert pc_name in resp_str, (
                f"PriorityClass 列表未找到 {pc_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="pc_update", depends=["pc_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 PriorityClass")
    @allure.description("使用 PUT 方法全量更新 PriorityClass，验证响应包含资源名称")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_priorityclass(self, ec_service, public_params):
        """PUT 全量更新 PriorityClass，断言更新成功。"""
        cell_code = public_params["cell_code"]
        pc_name = public_params["pc_name"]

        with AllureHelper.api_test(ec_service):
            put_payload = self._build_update_payload(pc_name)
            put_resp = ec_service.update_priority_class(
                cell_code=cell_code, name=pc_name, payload=put_payload,
            )

            assert put_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PUT 更新 PriorityClass 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

            resp_str = json.dumps(put_resp, ensure_ascii=False)
            assert pc_name in resp_str, (
                f"PUT 更新后响应中未包含资源名称 {pc_name}, 响应: {put_resp}"
            )

    @pytest.mark.dependency(name="pc_patch", depends=["pc_update"])
    @pytest.mark.order(5)
    @allure.title("PATCH 增量更新 PriorityClass")
    @allure.description("使用 PATCH 方法增量更新 PriorityClass 的 description 和 metadata，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patch_priorityclass(self, ec_service, public_params):
        """PATCH 增量更新 PriorityClass，断言更新成功。"""
        cell_code = public_params["cell_code"]
        pc_name = public_params["pc_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_patch_payload()
            patch_resp = ec_service.patch_priority_class(
                cell_code=cell_code, name=pc_name, payload=patch_payload,
            )

            assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PATCH 增量更新 PriorityClass 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

            resp_str = json.dumps(patch_resp, ensure_ascii=False)
            assert pc_name in resp_str, (
                f"PATCH 更新后响应中未包含资源名称 {pc_name}, 响应: {patch_resp}"
            )

    @pytest.mark.dependency(name="pc_delete", depends=["pc_patch"])
    @pytest.mark.order(6)
    @allure.title("删除 PriorityClass")
    @allure.description("删除创建的 PriorityClass 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_priorityclass(self, ec_service, public_params, api_cache):
        """删除 PriorityClass，断言删除成功。"""
        cell_code = public_params["cell_code"]
        pc_name = public_params["pc_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_priority_class(
                cell_code=cell_code, name=pc_name,
            )

            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 PriorityClass 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_pc_created", False)
