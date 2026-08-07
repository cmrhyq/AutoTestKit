"""
可观测 OpenAPI 日志接口测试

测试内容：
- 根据四元组检索日志
- 根据日志检索requestId轮询拉取日志列表
- 查询日志上下文
- 根据上下文检索requestId获取上下文日志列表
"""

import allure
import pytest

from base.api.entity.observable import ObservableLogPublicParams
from base.api.services.observable_open_service import (
    Log,
    LogContext,
    ObservableOpenService,
)
from core.reporting.allure_helper import AllureHelper
from core.constants import HttpStatus, Tenant

@pytest.mark.api
@pytest.mark.observable
@allure.epic("磐基API自动化测试")
@allure.feature("磐基可观测OpenAPI接口")
@allure.story("observable Log 日志接口")
class TestObservableLog:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def observable_service(self, service_factory):
        with service_factory(ObservableOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> ObservableLogPublicParams:
        """提取可观测日志测试所需的公共参数。"""
        return ObservableLogPublicParams(
            obs_namespace=test_env.get("obsNamespace", "paas-monitor"),
            obs_cluster_name=test_env.get("obsClusterName", "kzm-101"),
            obs_pod_name=test_env.get("obsPodName", "monitor-cmdb-confs-deploy-6ff6c6669b-nsz4r"),
            obs_container_name=test_env.get("obsContainerName", "monitor-amdb-confs"),
            obs_start_time=int(test_env.get("obsStartTime", 176145907000)),
            obs_end_time=int(test_env.get("obsEndTime", 176145908000)),
            obs_component_type=test_env.get("obsComponentType", "app"),
            obs_size=int(test_env.get("obsSize", 1)),
            obs_id=test_env.get("obsId", "2cNV25kBX1NeH2CondPI"),
            obs_timestamp=int(test_env.get("obsTimestamp", 1760321444470)),
            obs_offset=int(test_env.get("obsOffset", 100016405)),
            obs_log_file_path=test_env.get(
                "obsLogFilePath",
                "/stdout.log"
            ),
            obs_host_ip=test_env.get("obsHostIp", "100.10.32.101"),
        )

    @allure.title("根据四元组检索日志")
    @allure.description("按 namespace/cluster/pod/container 四元组检索日志并缓存 requestId")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_log_by_quadruple(self, observable_service, public_params, api_cache):
        with AllureHelper.api_test(observable_service):
            log = Log(
                namespace=public_params.obs_namespace,
                cluster_name=public_params.obs_cluster_name,
                pod_name=public_params.obs_pod_name,
                container_name=public_params.obs_container_name,
                start_time=public_params.obs_start_time,
                end_time=public_params.obs_end_time,
                component_type=public_params.obs_component_type,
                sync=False,
                size=public_params.obs_size,
            )

            with AllureHelper.step("发送 GET 请求根据四元组检索日志"):
                response_json = observable_service.query_log_by_quadruple(log=log)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("statusCode") == HttpStatus.OK, \
                    f"statusCode 应为 {int(HttpStatus.OK)}，实际为 {response_json.get('statusCode')}"

            with AllureHelper.step("提取 requestId 供后续接口使用"):
                data = response_json.get("data", {})
                request_id = data.get("requestId")
                api_cache.set("log_request_id", request_id)

    @allure.title("根据日志检索requestId轮询拉取日志列表")
    @allure.description("按 requestId 轮询拉取日志列表数据")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_pull_log_by_request_id(self, observable_service, api_cache):
        with AllureHelper.api_test(observable_service):
            request_id = api_cache.get("log_request_id")
            if not request_id:
                pytest.skip("未获取到 log_request_id，跳过轮询日志列表")

            with AllureHelper.step(f"发送 GET 请求轮询拉取日志列表，requestId={request_id}"):
                response_json = observable_service.pull_log_by_request_id(request_id=request_id)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("statusCode") == HttpStatus.OK, \
                    f"statusCode 应为 {int(HttpStatus.OK)}，实际为 {response_json.get('statusCode')}"

    @allure.title("查询日志上下文")
    @allure.description("按日志 ID 查询上下文信息并缓存 contextRequestId")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_log_context(self, observable_service, public_params, api_cache):
        with AllureHelper.api_test(observable_service):
            context = LogContext(
                log_id=public_params.obs_id,
                timestamp=public_params.obs_timestamp,
                offset=public_params.obs_offset,
                log_file_path=public_params.obs_log_file_path,
                host_ip=public_params.obs_host_ip,
                namespace=public_params.obs_namespace,
                cluster_name=public_params.obs_cluster_name,
                pod_name=public_params.obs_pod_name,
                container_name=public_params.obs_container_name,
                sync=False,
                size=public_params.obs_size,
            )

            with AllureHelper.step("发送 GET 请求查询日志上下文"):
                response_json = observable_service.query_log_context(context=context)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("statusCode") == HttpStatus.OK, \
                    f"statusCode 应为 {int(HttpStatus.OK)}，实际为 {response_json.get('statusCode')}"

            with AllureHelper.step("提取 contextRequestId 供后续接口使用"):
                data = response_json.get("data", {})
                context_request_id = data.get("requestId")
                api_cache.set("context_request_id", context_request_id)

    @allure.title("根据上下文检索requestId获取上下文日志列表")
    @allure.description("按上下文 requestId 拉取上下文日志列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_pull_log_context_by_request_id(self, observable_service, api_cache):
        with AllureHelper.api_test(observable_service):
            context_request_id = api_cache.get("context_request_id")
            if not context_request_id:
                pytest.skip("未获取到 context_request_id，跳过上下文日志列表")

            with AllureHelper.step(f"发送 GET 请求获取上下文日志列表，requestId={context_request_id}"):
                response_json = observable_service.pull_log_context_by_request_id(
                    request_id=context_request_id
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("statusCode") == HttpStatus.OK, \
                    f"statusCode 应为 {int(HttpStatus.OK)}，实际为 {response_json.get('statusCode')}"
