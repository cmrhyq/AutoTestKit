"""
弹性计算 OpenAPI HPA(HorizontalPodAutoscaler) 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/HPA.jmx
线程组: Thread Group - hpa
测试内容：HPA 完整生命周期（查询/条件清理/创建/命名空间列表/全集群列表/PUT 全量更新/PATCH 增量更新/删除/删除后验证）
"""
import json
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 业务码 / 常量（顶部集中定义，禁止方法内魔法数字）
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("HPA 生命周期接口")
class TestEcOpenapiHpa:
    """
    对应 JMeter 脚本: HPA.jmx
    线程组: Thread Group - hpa

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询 → 清理已存在 → 创建 → 命名空间列表 → 全集群列表 →
             PUT 更新 → PATCH 增量更新 → 删除 → 删除后验证。
    """

    TENANT = "monitor-group"

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 HPA 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode"),
            "sys_code": api_env.get("sysCode"),
            "api_version": "v1",
            "hpa_name": "auto-test-hpa-test-0001",
        }

    # ---------------- Body helpers（对应 JMX POST/PUT/PATCH 请求体，从 XML 实体还原） ----------------

    @staticmethod
    def _build_hpa_payload(
        name: str, api_version: str, max_replicas: int
    ) -> Dict[str, Any]:
        """
        构造 HPA 请求体。

        源自 JMX HPA.jmx 中"创建/更新 hpa"sampler 的 postBodyRaw。
        - apiVersion 使用 autoscaling/{apiVersion}
        - scaleTargetRef 固定绑定到 StatefulSet 'web'
        """
        return {
            "apiVersion": f"autoscaling/{api_version}",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": name,
            },
            "spec": {
                "scaleTargetRef": {
                    "kind": "StatefulSet",
                    "name": "web",
                    "apiVersion": "apps/v1",
                },
                "minReplicas": 1,
                "maxReplicas": max_replicas,
                "targetCPUUtilizationPercentage": 50,
            },
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 HPA")
    @allure.description("查询指定 HPA 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="hpa_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_hpa_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 HPA，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_hpa(
                cell_code=cell_code, sys_code=sys_code,
                api_version=api_version, name=hpa_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 HPA 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_hpa(
                    cell_code=cell_code, sys_code=sys_code,
                    api_version=api_version, name=hpa_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的 HPA 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_hpa_created", False)

    @allure.title("创建 HPA")
    @allure.description("创建 HPA 资源，验证返回业务码为 2000 且响应包含资源名")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="hpa_create", depends=["hpa_query_and_cleanup"])
    @pytest.mark.order(2)
    def test_create_hpa(self, ec_service, public_params, api_cache):
        """创建 HPA，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_hpa_payload(
                name=hpa_name,
                api_version=api_version,
                max_replicas=3,
            )
            create_resp = ec_service.create_hpa(
                cell_code=cell_code, sys_code=sys_code,
                api_version=api_version, payload=create_payload,
            )

            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 HPA 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )
            resp_str = json.dumps(create_resp, ensure_ascii=False)
            assert hpa_name in resp_str, (
                f"创建 HPA 响应中未包含资源名称 {hpa_name}, 响应: {create_resp}"
            )

            api_cache.set("ec_hpa_created", True)

    @allure.title("查询 Namespace 下 HPA 列表")
    @allure.description("查询指定命名空间下 HPA 列表，验证包含新创建的 HPA")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="hpa_list_ns", depends=["hpa_create"])
    @pytest.mark.order(3)
    def test_list_hpas_by_namespace(self, ec_service, public_params):
        """查询 Namespace 下 HPA 列表，断言包含目标 HPA。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_hpas_by_ns(
                cell_code=cell_code, sys_code=sys_code, api_version=api_version,
            )

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Namespace HPA 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert hpa_name in resp_str, (
                f"Namespace 下 HPA 列表未找到 {hpa_name}, 响应: {list_resp}"
            )

    @allure.title("查询全集群 HPA 列表")
    @allure.description("查询全集群所有 HPA 列表，验证包含新创建的 HPA")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="hpa_list_cell", depends=["hpa_create"])
    @pytest.mark.order(4)
    def test_list_hpas_by_cell(self, ec_service, public_params):
        """查询全集群 HPA 列表，断言包含目标 HPA。"""
        cell_code = public_params["cell_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_hpas_by_cell(
                cell_code=cell_code, api_version=api_version,
            )

            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询全集群 HPA 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert hpa_name in resp_str, (
                f"全集群 HPA 列表未找到 {hpa_name}, 响应: {list_resp}"
            )

    @allure.title("PUT 全量更新 HPA")
    @allure.description("使用 PUT 全量更新 HPA 的 maxReplicas，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="hpa_put", depends=["hpa_create"])
    @pytest.mark.order(5)
    def test_put_update_hpa(self, ec_service, public_params):
        """PUT 全量更新 HPA，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            put_payload = self._build_hpa_payload(
                name=hpa_name,
                api_version=api_version,
                max_replicas=2,
            )
            put_resp = ec_service.update_hpa(
                cell_code=cell_code, sys_code=sys_code,
                api_version=api_version, name=hpa_name, payload=put_payload,
            )

            assert put_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PUT 更新 HPA 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

    @allure.title("PATCH 增量更新 HPA")
    @allure.description("使用 PATCH 增量更新 HPA 的 maxReplicas，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="hpa_patch", depends=["hpa_put"])
    @pytest.mark.order(6)
    def test_patch_update_hpa(self, ec_service, public_params):
        """PATCH 增量更新 HPA，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_hpa_payload(
                name=hpa_name,
                api_version=api_version,
                max_replicas=3,
            )
            patch_resp = ec_service.patch_hpa(
                cell_code=cell_code, sys_code=sys_code,
                api_version=api_version, name=hpa_name, payload=patch_payload,
            )

            assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PATCH 增量更新 HPA 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

    @allure.title("删除 HPA")
    @allure.description("删除创建的 HPA 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="hpa_delete", depends=["hpa_patch"])
    @pytest.mark.order(7)
    def test_delete_hpa(self, ec_service, public_params, api_cache):
        """删除 HPA，断言删除成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_hpa(
                cell_code=cell_code, sys_code=sys_code,
                api_version=api_version, name=hpa_name,
            )

            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 HPA 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_hpa_created", False)

    @allure.title("验证 HPA 删除后不存在")
    @allure.description("删除后再次查询 HPA，验证返回资源不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(depends=["hpa_delete"])
    @pytest.mark.order(8)
    def test_verify_hpa_deleted(self, ec_service, public_params):
        """删除后验证 HPA 已不存在。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        api_version = public_params["api_version"]
        hpa_name = public_params["hpa_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_hpa(
                cell_code=cell_code, sys_code=sys_code,
                api_version=api_version, name=hpa_name,
            )

            assert get_resp.get("code") == RESOURCE_NOT_FOUND_CODE, (
                f"HPA 删除后仍能查询到, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
