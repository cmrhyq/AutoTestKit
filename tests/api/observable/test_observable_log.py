"""
可观测 OpenAPI 日志接口测试

转换自 JMeter 脚本: observable-log.jmx
测试内容：
- 根据四元组检索日志
- 根据日志检索requestId轮询拉取日志列表
- 查询日志上下文
- 根据上下文检索requestId获取上下文日志列表
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.observable_open_service import (
    PanJiObservableOpenService,
    Log,
    LogContext,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("可观测OpenAPI服务")
@allure.story("observable-log 日志接口")
class TestObservableLog:
    """
    对应 JMeter 脚本: observable-log.jmx
    线程组: 可观测接口调用
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def observable_service(self, api_env, api_logger):
        """创建 Observable OpenAPI 服务实例"""
        service = PanJiObservableOpenService(
            base_url=api_env.get("apiBaseUrl"), logger=api_logger
        )
        yield service
        service.close()

    @allure.title("根据四元组检索日志")
    @allure.description(
        "GET /openapi/monitor-o11y/webgate-log-console/3rd/log/query - "
        "通过 namespace/cluster/pod/container 四元组检索日志"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_log_by_quadruple(self, observable_service, api_env, api_cache):
        log = Log(
            namespace=api_env.get("obsNamespace", "paas-monitor"),
            cluster_name=api_env.get("obsClusterName", "kzm-101"),
            pod_name=api_env.get("obsPodName", "monitor-cmdb-confs-deploy-6ff6c6669b-nsz4r"),
            container_name=api_env.get("obsContainerName", "monitor-amdb-confs"),
            start_time=int(api_env.get("obsStartTime", 176145907000)),
            end_time=int(api_env.get("obsEndTime", 176145908000)),
            component_type=api_env.get("obsComponentType", "app"),
            sync=False,
            size=int(api_env.get("obsSize", 1)),
        )

        with AllureHelper.step("发送 GET 请求根据四元组检索日志"):
            response_json = observable_service.query_log_by_quadruple(log=log)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("statusCode") == 200, \
                f"statusCode 应为 200，实际为 {response_json.get('statusCode')}"

        with AllureHelper.step("提取 requestId 供后续接口使用"):
            data = response_json.get("data", {})
            request_id = data.get("requestId")
            api_cache.set("log_request_id", request_id)

    @allure.title("根据日志检索requestId轮询拉取日志列表")
    @allure.description(
        "GET /openapi/monitor-o11y/webgate-log-console/3rd/log/pull - "
        "通过requestId轮询获取日志数据"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_pull_log_by_request_id(self, observable_service, api_cache):
        request_id = api_cache.get("log_request_id")
        if not request_id:
            pytest.skip("未获取到 log_request_id，跳过轮询日志列表")

        with AllureHelper.step(f"发送 GET 请求轮询拉取日志列表，requestId={request_id}"):
            response_json = observable_service.pull_log_by_request_id(request_id=request_id)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("statusCode") == 200, \
                f"statusCode 应为 200，实际为 {response_json.get('statusCode')}"

    @allure.title("查询日志上下文")
    @allure.description(
        "GET /openapi/monitor-o11y/webgate-log-console/3rd/log/context - "
        "根据日志ID查询上下文信息"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_log_context(self, observable_service, api_env, api_cache):
        context = LogContext(
            log_id=api_env.get("obsId", "2cNV25kBX1NeH2CondPI"),
            timestamp=int(api_env.get("obsTimestamp", 1760321444470)),
            offset=int(api_env.get("obsOffset", 100016405)),
            log_file_path=api_env.get(
                "obsLogFilePath",
                "/apps/monitor/oblogs/ns/paas-compmgmt/pod/monitor-cmdb-confs-deploy-6ff6c6669b-nsz4r/monitor-amdb-confs/stdout.log"
            ),
            host_ip=api_env.get("obsHostIp", "100.10.32.101"),
            namespace=api_env.get("obsNamespace", "paas-monitor"),
            cluster_name=api_env.get("obsClusterName", "kzm-101"),
            pod_name=api_env.get("obsPodName", "monitor-cmdb-confs-deploy-6ff6c6669b-nsz4r"),
            container_name=api_env.get("obsContainerName", "monitor-amdb-confs"),
            sync=False,
            size=int(api_env.get("obsSize", 1)),
        )

        with AllureHelper.step("发送 GET 请求查询日志上下文"):
            response_json = observable_service.query_log_context(context=context)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("statusCode") == 200, \
                f"statusCode 应为 200，实际为 {response_json.get('statusCode')}"

        with AllureHelper.step("提取 contextRequestId 供后续接口使用"):
            data = response_json.get("data", {})
            context_request_id = data.get("requestId")
            api_cache.set("context_request_id", context_request_id)

    @allure.title("根据上下文检索requestId获取上下文日志列表")
    @allure.description(
        "GET /openapi/monitor-o11y/webgate-log-console/3rd/log/context/pull - "
        "通过上下文requestId拉取上下文日志"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_pull_log_context_by_request_id(self, observable_service, api_cache):
        context_request_id = api_cache.get("context_request_id")
        if not context_request_id:
            pytest.skip("未获取到 context_request_id，跳过上下文日志列表")

        with AllureHelper.step(f"发送 GET 请求获取上下文日志列表，requestId={context_request_id}"):
            response_json = observable_service.pull_log_context_by_request_id(
                request_id=context_request_id
            )

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("statusCode") == 200, \
                f"statusCode 应为 200，实际为 {response_json.get('statusCode')}"
