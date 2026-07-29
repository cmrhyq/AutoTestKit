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

    JMX 逻辑还原：
        查询指定 cm → 提取 code
          ├── code==2000（已存在）: 先删除 → 创建 → 列表 → 全集群列表 → 若创建成功: PUT → PATCH → 删除
          └── code!=2000（不存在）:            创建 → 列表 → 全集群列表 → 若创建成功: PUT → PATCH → 删除
        合并策略：两个分支的区别仅在于"是否先删除"，合并为一个方法内 if 处理。
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

    @allure.title("ConfigMap 完整生命周期测试")
    @allure.description("覆盖 ConfigMap 的查询、（存在则删除）、创建、列表、PUT 更新、PATCH 增量更新、删除完整生命周期")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_configmap_lifecycle(self, ec_service, api_env, api_cache):
        cell_code = api_env.get("cellCode")
        sys_code = api_env.get("sysCode")
        cm_name = api_env.get("configmapName", "auto-test-probe-cm-test-0001")

        with AllureHelper.api_test(ec_service):
            # Step 1: 查询当前状态（对应 JMX 首个 GET + JSONPostProcessor -> ec_get_code）
            with AllureHelper.step("查询指定 ConfigMap 确认当前状态"):
                get_resp = ec_service.get_configmap(
                    cell_code=cell_code, sys_code=sys_code, name=cm_name,
                )
                ec_get_code = get_resp.get("code")

            # Step 2: 若已存在，先删除（对应外层 IfController ec_get_code==2000）
            if ec_get_code == BUSINESS_SUCCESS_CODE:
                with AllureHelper.step("ConfigMap 已存在，先删除以保证幂等"):
                    del_resp = ec_service.delete_configmap(
                        cell_code=cell_code, sys_code=sys_code, name=cm_name,
                    )
                    assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                        f"删除已存在的 ConfigMap 失败: {del_resp}"
                    )

            # Step 3: 创建 ConfigMap（对应 JMX "创建cm请求" + JSONPathAssertion code==2000）
            with AllureHelper.step("创建 ConfigMap"):
                create_payload = self._build_configmap_create_payload(cm_name)
                create_resp = ec_service.create_configmap(
                    cell_code=cell_code, sys_code=sys_code, payload=create_payload,
                )
                ec_create_code = create_resp.get("code")
                assert ec_create_code == BUSINESS_SUCCESS_CODE, (
                    f"创建 ConfigMap 失败: {create_resp}"
                )
                api_cache.set("ec_configmap_created", True)

            # Step 4: 查询 Namespace 级 cm 列表并验证包含目标 cm
            # 对应 JMX "查询cm列表请求" + ResponseAssertion test_type=16（不包含=失败，实为断言包含）
            with AllureHelper.step("查询 Namespace 下 ConfigMap 列表并验证包含新建 cm"):
                list_resp = ec_service.list_configmaps_by_ns(
                    cell_code=cell_code, sys_code=sys_code,
                )
                assert cm_name in json.dumps(list_resp, ensure_ascii=False), (
                    f"Namespace 下 ConfigMap 列表未找到 {cm_name}"
                )

            # Step 5: 查询全集群 cm 列表并验证包含目标 cm
            with AllureHelper.step("查询全集群 ConfigMap 列表并验证包含新建 cm"):
                all_list_resp = ec_service.list_configmaps_by_cell(cell_code=cell_code)
                assert cm_name in json.dumps(all_list_resp, ensure_ascii=False), (
                    f"全集群 ConfigMap 列表未找到 {cm_name}"
                )

            # Step 6: PUT 全量更新（对应内层 IfController ec_create_code==2000 下的第一个动作）
            if ec_create_code == BUSINESS_SUCCESS_CODE:
                with AllureHelper.step("PUT 全量更新 ConfigMap"):
                    put_payload = self._build_configmap_put_payload(cm_name)
                    put_resp = ec_service.update_configmap(
                        cell_code=cell_code, sys_code=sys_code, name=cm_name,
                        payload=put_payload,
                    )
                    assert put_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                        f"PUT 更新 ConfigMap 失败: {put_resp}"
                    )

                # Step 7: PATCH 增量更新
                with AllureHelper.step("PATCH 增量更新 ConfigMap"):
                    patch_payload = self._build_configmap_patch_payload()
                    patch_resp = ec_service.patch_configmap(
                        cell_code=cell_code, sys_code=sys_code, name=cm_name,
                        payload=patch_payload,
                    )
                    assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                        f"PATCH 增量更新 ConfigMap 失败: {patch_resp}"
                    )

                # Step 8: 清理（对应 JMX 生命周期末尾的删除 + JSONPathAssertion）
                with AllureHelper.step("删除创建的 ConfigMap 清理环境"):
                    final_del_resp = ec_service.delete_configmap(
                        cell_code=cell_code, sys_code=sys_code, name=cm_name,
                    )
                    assert final_del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                        f"清理 ConfigMap 失败: {final_del_resp}"
                    )
                    api_cache.set("ec_configmap_created", False)
