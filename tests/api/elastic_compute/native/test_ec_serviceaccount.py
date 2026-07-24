"""
弹性计算 Native ServiceAccount 接口测试

转换自 JMeter 脚本: serviceaccount.jmx
测试内容：ServiceAccount 原生接口-特权接口，针对 ServiceAccount 增删改查进行测试
- 查询指定 ServiceAccount
- 创建 ServiceAccount
- 删除指定 ServiceAccount
"""
import time
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_native_service import (
    PanJiElasticComputeNativeService,
)
from core.reporting.allure_helper import AllureHelper

# Native K8s API 使用 HTTP 状态码，非业务 code
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NOT_FOUND = 404


@pytest.mark.api
@allure.feature("磐基弹性计算Native接口")
@allure.story("ServiceAccount 原生接口")
class TestEcNativeServiceAccount:
    """
    对应 JMeter 脚本: serviceaccount.jmx
    线程组: Thread Group - ServiceAccount
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def native_service(self, api_env, api_logger):
        """创建 Native API 服务实例，base_url 从 env yaml 显式传入。"""
        service = PanJiElasticComputeNativeService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @staticmethod
    def _build_service_account_payload(name: str) -> Dict[str, Any]:
        """
        构建 ServiceAccount 创建请求体。

        对应 JMX 中的 POST body（XML 实体还原后）：
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "${name}"}
        }
        """
        return {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": name
            },
        }

    # ==================== 生命周期测试 ====================

    @allure.title("ServiceAccount 完整生命周期（查询→清理→创建→删除）")
    @allure.description(
        "完整测试 ServiceAccount CRUD 流程：\n"
        "1. 查询指定 SA 确认当前状态\n"
        "2. 若已存在则先删除（幂等处理）\n"
        "3. 创建 SA\n"
        "4. 创建成功后删除（清理）"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_service_account_lifecycle(self, native_service, api_env, api_cache, api_logger):
        cluster_id = str(api_env.get("clusterId"))
        namespace = api_env.get("namespace")
        sa_name = api_env.get("nativeSaName", "test-sa")

        api_logger.info(
            f"开始测试: ServiceAccount 生命周期, cluster={cluster_id}, "
            f"ns={namespace}, name={sa_name}"
        )

        with AllureHelper.api_test(native_service):
            # Step 1: 查询指定 ServiceAccount 确认当前状态
            # 对应 JMX: 弹性计算_native_serviceaccount_查询指定ServiceAccount请求
            # 对应 JMX RegexExtractor: get_http_code
            with AllureHelper.step("查询指定 ServiceAccount 确认当前状态"):
                get_http_code, get_resp = native_service.get_service_account(
                    cluster_id=cluster_id,
                    namespace=namespace,
                    name=sa_name,
                )
                api_logger.info(f"查询 SA 状态码: {get_http_code}")
                assert get_http_code in (HTTP_OK, HTTP_NOT_FOUND), (
                    f"查询应返回200或404, 实际: {get_http_code}"
                )

            # Step 2: 若已存在则先删除（对应 JMX IfController: get_http_code==200）
            if get_http_code == HTTP_OK:
                with AllureHelper.step("ServiceAccount 已存在，先删除"):
                    del_resp = native_service.delete_service_account(
                        cluster_id=cluster_id,
                        namespace=namespace,
                        name=sa_name,
                    )
                    assert native_service.last_response.status_code == HTTP_OK, (
                        f"删除失败, status={native_service.last_response.status_code}"
                    )
                    api_logger.info(f"删除已存在的 SA 成功: {sa_name}")

            # Step 3: 创建 ServiceAccount
            # 对应 JMX: 弹性计算_native_serviceaccount_创建ServiceAccount请求
            # 对应 JMX RegexExtractor: create_http_code
            with AllureHelper.step("创建 ServiceAccount"):
                payload = self._build_service_account_payload(sa_name)
                create_resp = native_service.create_service_account(
                    cluster_id=cluster_id,
                    namespace=namespace,
                    payload=payload,
                )
                create_http_code = native_service.last_response.status_code
                assert create_http_code == HTTP_CREATED, (
                    f"创建失败, 期望201, 实际: {create_http_code}, resp: {create_resp}"
                )
                api_logger.info(f"创建 SA 成功: {sa_name}, status={create_http_code}")

            # Step 4: 等待（对应 JMX ConstantTimer: intervalTime=10000ms）
            time.sleep(3)

            # Step 5: 创建成功后删除（对应内层 IfController: create_http_code==201）
            if create_http_code == HTTP_CREATED:
                with AllureHelper.step("删除创建的 ServiceAccount（清理）"):
                    cleanup_resp = native_service.delete_service_account(
                        cluster_id=cluster_id,
                        namespace=namespace,
                        name=sa_name,
                    )
                    assert native_service.last_response.status_code == HTTP_OK, (
                        f"清理删除失败, status={native_service.last_response.status_code}"
                    )
                    api_logger.info(f"清理删除 SA 成功: {sa_name}")
