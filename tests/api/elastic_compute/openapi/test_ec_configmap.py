"""
弹性计算 OpenAPI ConfigMap 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/ConfigMap.jmx
线程组: Thread Group - configmap
测试内容：ConfigMap 完整生命周期（查询/删除/创建/列表/全集群列表/PUT 更新/PATCH 增量更新/删除）
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
@allure.story("ConfigMap 生命周期接口")
class TestEcOpenapiConfigmap:
    """
    对应 JMeter 脚本: ConfigMap.jmx
    线程组: Thread Group - configmap

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询 → 清理已存在 → 创建 → 列表查询 → 全集群列表查询 → PUT更新 → PATCH更新 → 删除清理
    """

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 yaml 显式传入（camelCase key）。"""
        service = ElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 ConfigMap 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode"),
            "sys_code": api_env.get("sysCode"),
            "cm_name": "auto-test-probe-cm-test-0001",
        }

    # ---------------- Body helpers（对应 JMX POST/PUT/PATCH 请求体，从 XML 实体还原） ----------------

    @staticmethod
    def _build_configmap_create_payload(name: str) -> Dict[str, Any]:
        """
        构造创建 ConfigMap 请求体。

        源自 JMX ConfigMap.jmx 中"创建cm请求" sampler 的 postBodyRaw。
        """
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": name,
            },
            "data": {
                "test": "test",
            },
        }

    @staticmethod
    def _build_configmap_put_payload(name: str) -> Dict[str, Any]:
        """
        构造 PUT 全量更新 ConfigMap 请求体。

        源自 JMX ConfigMap.jmx 中"更新指定 configmap" sampler 的 postBodyRaw。
        """
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": name,
            },
            "data": {
                "test": "testput",
            },
        }

    @staticmethod
    def _build_configmap_patch_payload() -> Dict[str, Any]:
        """
        构造 PATCH 增量更新 ConfigMap 请求体（strategic merge patch）。

        源自 JMX ConfigMap.jmx 中"增量更新指定 configmap" sampler 的 postBodyRaw。
        """
        return {
            "metadata": {
                "labels": {
                    "test": "test2",
                },
            },
            "data": {
                "test": "test2",
            },
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 ConfigMap")
    @allure.description("查询指定 ConfigMap 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="configmap_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_configmap_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 ConfigMap，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            # 查询指定 ConfigMap
            get_resp = ec_service.get_configmap(
                cell_code=cell_code, sys_code=sys_code, name=cm_name,
            )
            ec_get_code = get_resp.get("code")

            # 断言：接口返回正常（code 为 2000 表示存在，4004 表示不存在，两者均为正常）
            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 ConfigMap 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            # 若已存在，先删除以保证幂等
            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_configmap(
                    cell_code=cell_code, sys_code=sys_code, name=cm_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"删除已存在的 ConfigMap 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_configmap_created", False)

    @allure.title("创建 ConfigMap")
    @allure.description("创建 ConfigMap 资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="configmap_create", depends=["configmap_query_and_cleanup"])
    @pytest.mark.order(2)
    def test_create_configmap(self, ec_service, public_params, api_cache):
        """创建 ConfigMap，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_configmap_create_payload(cm_name)
            create_resp = ec_service.create_configmap(
                cell_code=cell_code, sys_code=sys_code, payload=create_payload,
            )

            # 断言：业务码为成功
            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 ConfigMap 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )
            # 断言：返回数据中包含 ConfigMap 名称
            resp_str = json.dumps(create_resp, ensure_ascii=False)
            assert cm_name in resp_str, (
                f"创建 ConfigMap 响应中未包含资源名称 {cm_name}, 响应: {create_resp}"
            )

            api_cache.set("ec_configmap_created", True)

    @allure.title("查询 Namespace 下 ConfigMap 列表")
    @allure.description("查询指定命名空间下的 ConfigMap 列表，验证包含新创建的 ConfigMap")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="configmap_list_ns", depends=["configmap_create"])
    @pytest.mark.order(3)
    def test_list_configmaps_by_namespace(self, ec_service, public_params):
        """查询 Namespace 下 ConfigMap 列表，断言包含目标 cm。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_configmaps_by_ns(
                cell_code=cell_code, sys_code=sys_code,
            )

            # 断言：业务码为成功
            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Namespace ConfigMap 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            # 断言：列表中包含目标 ConfigMap
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert cm_name in resp_str, (
                f"Namespace 下 ConfigMap 列表未找到 {cm_name}, 响应: {list_resp}"
            )

    @allure.title("查询全集群 ConfigMap 列表")
    @allure.description("查询全集群所有 ConfigMap 列表，验证包含新创建的 ConfigMap")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="configmap_list_cell", depends=["configmap_create"])
    @pytest.mark.order(4)
    def test_list_configmaps_by_cell(self, ec_service, public_params):
        """查询全集群 ConfigMap 列表，断言包含目标 cm。"""
        cell_code = public_params["cell_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            all_list_resp = ec_service.list_configmaps_by_cell(cell_code=cell_code)

            # 断言：业务码为成功
            assert all_list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询全集群 ConfigMap 列表失败, code: {all_list_resp.get('code')}, 响应: {all_list_resp}"
            )
            # 断言：列表中包含目标 ConfigMap
            resp_str = json.dumps(all_list_resp, ensure_ascii=False)
            assert cm_name in resp_str, (
                f"全集群 ConfigMap 列表未找到 {cm_name}, 响应: {all_list_resp}"
            )

    @allure.title("PUT 全量更新 ConfigMap")
    @allure.description("使用 PUT 方法全量更新 ConfigMap 的 data 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="configmap_put", depends=["configmap_create"])
    @pytest.mark.order(5)
    def test_put_update_configmap(self, ec_service, public_params):
        """PUT 全量更新 ConfigMap，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            put_payload = self._build_configmap_put_payload(cm_name)
            put_resp = ec_service.update_configmap(
                cell_code=cell_code, sys_code=sys_code, name=cm_name,
                payload=put_payload,
            )

            # 断言：业务码为成功
            assert put_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PUT 更新 ConfigMap 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )
            # 断言：响应中包含更新后的数据值
            resp_str = json.dumps(put_resp, ensure_ascii=False)
            assert "testput" in resp_str, (
                f"PUT 更新后响应中未包含预期数据 'testput', 响应: {put_resp}"
            )

    @allure.title("PATCH 增量更新 ConfigMap")
    @allure.description("使用 PATCH 方法增量更新 ConfigMap 的 labels 和 data 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="configmap_patch", depends=["configmap_put"])
    @pytest.mark.order(6)
    def test_patch_update_configmap(self, ec_service, public_params):
        """PATCH 增量更新 ConfigMap，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_configmap_patch_payload()
            patch_resp = ec_service.patch_configmap(
                cell_code=cell_code, sys_code=sys_code, name=cm_name,
                payload=patch_payload,
            )

            # 断言：业务码为成功
            assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PATCH 增量更新 ConfigMap 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )
            # 断言：响应中包含增量更新后的数据值
            resp_str = json.dumps(patch_resp, ensure_ascii=False)
            assert "test2" in resp_str, (
                f"PATCH 更新后响应中未包含预期数据 'test2', 响应: {patch_resp}"
            )

    @allure.title("删除 ConfigMap")
    @allure.description("删除创建的 ConfigMap 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="configmap_delete", depends=["configmap_patch"])
    @pytest.mark.order(7)
    def test_delete_configmap(self, ec_service, public_params, api_cache):
        """删除 ConfigMap，断言删除成功并清理缓存标记。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_configmap(
                cell_code=cell_code, sys_code=sys_code, name=cm_name,
            )

            # 断言：业务码为成功
            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 ConfigMap 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_configmap_created", False)

    @allure.title("验证 ConfigMap 删除后不存在")
    @allure.description("删除后再次查询 ConfigMap，验证返回资源不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(depends=["configmap_delete"])
    @pytest.mark.order(8)
    def test_verify_configmap_deleted(self, ec_service, public_params):
        """删除后验证 ConfigMap 已不存在。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        cm_name = public_params["cm_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_configmap(
                cell_code=cell_code, sys_code=sys_code, name=cm_name,
            )

            # 断言：业务码为资源不存在
            assert get_resp.get("code") == RESOURCE_NOT_FOUND_CODE, (
                f"ConfigMap 删除后仍能查询到, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
