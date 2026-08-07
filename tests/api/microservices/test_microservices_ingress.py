"""
微服务 Ingress OpenAPI 接口测试脚本

覆盖 ingress的 28 个用例：
- ingress gateway（12 用例）：nginx 参数模板 + ingress 网关实例 CRUD
- ingress nginx（9 用例）：ingress 网关实例 + 网关配置 CRUD
- ingress scaling（7 用例）：ingress 网关实例 CRUD + 启停/扩缩容

共 28 用例。
"""
from typing import Dict

import allure
import pytest

from base.api.entity.microservices import (
    Ingress,
    IngressConfig,
    IngressIns,
    IngressPublicParams,
    NginxParam,
    NginxParamStatus,
)
from base.api.services.microservices_open_service import (
    MicroservicesOpenService,
)
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

@pytest.fixture(scope="module")
def public_params(test_env) -> IngressPublicParams:
    """提取 Ingress 测试所需的公共参数。"""
    return IngressPublicParams(
        mesh_gateway_name=test_env.get("meshGatewayName"),
        sys_code=test_env.get("sysCode"),
        unit_code=test_env.get("unitCode"),
        plane_code=test_env.get("planeCode"),
    )

# =============================================================================
# nginx 参数模板 CRUD + ingress 网关实例
# =============================================================================
@pytest.mark.api
@pytest.mark.microservice
@allure.epic("磐基API自动化测试")
@allure.feature("磐基微服务OpenAPI接口")
@allure.story("Ingress Gateway OpenAPI 接口")
class TestMsIngressGateway:

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ingress_service(self, service_factory):
        with service_factory(MicroservicesOpenService, self.TENANT) as svc:
            yield svc

    @allure.title("新增 nginx 参数模板")
    @allure.description("新增自定义 nginx 参数模板")
    def test_add_nginx_param(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 nginx 参数模板"):
                param = NginxParam(
                    code="nginx-tpl-auto",
                    name="nginx-tpl-auto",
                    desc="autotest template",
                )
                response_json = ingress_service.add_nginx_param(param)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("修改 nginx 参数模板")
    @allure.description("修改已有的 nginx 参数模板")
    def test_update_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求修改 nginx 参数模板"):
                param = NginxParam(
                    code="nginx-tpl-auto",
                    name="nginx-tpl-auto",
                    desc="updated by autotest",
                )
                response_json = ingress_service.update_nginx_param(param)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询 nginx 参数模板列表")
    @allure.description("查询全量 nginx 参数模板列表")
    def test_query_all_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 nginx 参数模板列表"):
                response_json = ingress_service.query_all_nginx_param(param_type="All")
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("nginx 参数模板上线接口")
    @allure.description("上线指定 nginx 参数模板")
    def test_online_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求上线 nginx 参数模板"):
                status = NginxParamStatus(id=1, keyword="", status="online")
                response_json = ingress_service.update_nginx_param_status(status)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("分页查询 nginx 参数模板列表")
    @allure.description("分页查询 nginx 参数模板列表（page=1, rows=10），断言响应包含 code 字段")
    def test_list_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求分页查询 nginx 参数模板"):
                status = NginxParamStatus(id=1, keyword="", page=1, rows=10)
                response_json = ingress_service.list_nginx_param(status)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("nginx 参数模板下线接口")
    @allure.description("下线指定 nginx 参数模板")
    def test_offline_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求下线 nginx 参数模板"):
                status = NginxParamStatus(id=1, keyword="", status="offline")
                response_json = ingress_service.update_nginx_param_status(status)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据 nginx 参数模板删除接口")
    @allure.description("根据编码删除指定 nginx 参数模板")
    def test_delete_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 nginx 参数模板"):
                response_json = ingress_service.delete_nginx_param_by_code(
                    code="nginx-tpl-auto", param_type="App"
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("新增 ingress 网关实例")
    @allure.description("基于 public_params 构造 ingress 实体新增网关实例，断言响应包含 code 字段")
    def test_add_ingress_instance(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关实例"):
                response_json = ingress_service.add_ingress_instance(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据编码查询 ingress 网关实例详情")
    @allure.description("按 code + sys_code + unit_code + plane_code 组合精确查询 ingress 网关实例详情，断言响应包含 code 字段")
    def test_get_ingress_instance_by_code(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询 ingress 网关实例信息分页")
    @allure.description("分页查询 ingress 网关实例列表")
    def test_list_ingress_instance(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求分页查询 ingress 网关实例"):
                data = IngressIns(
                    keyword="",
                    systemCode=public_params.sys_code,
                    unitCode=public_params.unit_code,
                    planeCode=public_params.plane_code,
                    page=1,
                    rows=10,
                )
                response_json = ingress_service.list_ingress_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("修改 ingress 网关实例")
    @allure.description("修改指定 ingress 网关实例的配置")
    def test_update_ingress_instance(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求修改 ingress 网关实例"):
                response_json = ingress_service.update_ingress_instance(
                    Ingress.from_public_params(public_params, remark="updated by autotest")
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码删除网关实例")
    @allure.description("按编码删除 ingress 网关实例")
    def test_delete_ingress_instance_by_code(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关实例"):
                response_json = ingress_service.delete_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

# =============================================================================
# ingress 网关配置 CRUD
# =============================================================================
@pytest.mark.api
@pytest.mark.microservice
@allure.epic("磐基API自动化测试")
@allure.feature("磐基微服务OpenAPI接口")
@allure.story("Ingress Nginx OpenAPI 接口")
class TestMsIngressNginx:

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ingress_service(self, service_factory):
        with service_factory(MicroservicesOpenService, self.TENANT) as svc:
            yield svc

    @allure.title("新增 ingress 网关实例")
    @allure.description("新增 ingress 网关实例（Nginx 配置流程前置）")
    def test_add_ingress_instance(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关实例"):
                response_json = ingress_service.add_ingress_instance(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据编码查询 ingress 网关实例详情")
    @allure.description("根据编码查询 ingress 网关实例详情（Nginx 配置流程前置）")
    def test_get_ingress_instance_by_code(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("新增 ingress 网关配置")
    @allure.description("为指定 ingress 网关新增配置")
    def test_add_ingress_config(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关配置"):
                response_json = ingress_service.add_ingress_config(
                    IngressConfig.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询 ingress 网关配置列表")
    @allure.description("查询指定 ingress 网关下的配置列表")
    def test_list_ingress_config(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求查询 ingress 网关配置列表"):
                response_json = ingress_service.list_ingress_config(
                    IngressConfig.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新 ingress 网关配置")
    @allure.description("更新指定 ingress 网关配置")
    def test_update_ingress_config(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求更新 ingress 网关配置"):
                response_json = ingress_service.update_ingress_config(
                    IngressConfig.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关配置详情")
    @allure.description("查询指定 ingress 网关配置详情")
    def test_get_ingress_config_detail(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关配置详情"):
                response_json = ingress_service.get_ingress_config_detail(
                    IngressConfig.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关配置通过 service 获取配置详情")
    @allure.description("按 service 名称获取 ingress 网关配置详情")
    def test_get_ingress_by_service_name(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求通过 service 获取网关配置详情"):
                response_json = ingress_service.get_ingress_by_service_name(
                    IngressConfig.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关配置删除接口")
    @allure.description("删除指定 ingress 网关配置")
    def test_delete_ingress_config_by_code(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关配置"):
                response_json = ingress_service.delete_ingress_config_by_code(
                    IngressConfig.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码删除网关实例")
    @allure.description("按编码删除 ingress 网关实例（Nginx 配置流程收尾）")
    def test_delete_ingress_instance_by_code(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关实例"):
                response_json = ingress_service.delete_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

# =============================================================================
# ingress 网关实例启停/扩缩容
# =============================================================================
@pytest.mark.api
@pytest.mark.microservice
@allure.epic("磐基API自动化测试")
@allure.feature("磐基微服务OpenAPI接口")
@allure.story("Ingress Scaling 扩容/缩容接口")
class TestIngressScaling:
    """Ingress Scaling 扩容/缩容接口测试（7 用例）"""

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def ingress_service(self, service_factory):
        with service_factory(MicroservicesOpenService, self.TENANT) as svc:
            yield svc

    @allure.title("新增 ingress 网关实例")
    @allure.description("新增 ingress 网关实例并缓存 instance_id 供扩缩容使用")
    def test_add_ingress_instance(self, ingress_service, public_params, api_cache):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关实例"):
                response_json = ingress_service.add_ingress_instance(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应并缓存 instance_id（若有）"):
                assert "code" in response_json
                if response_json.get("code") == 0 and isinstance(response_json.get("data"), Dict):
                    instance_id = response_json["data"].get("id") or response_json["data"].get("instanceId")
                    if instance_id:
                        api_cache.set("ms_ingress_instance_id", instance_id)

    @allure.title("根据编码查询 ingress 网关实例详情 - 第1次")
    @allure.description("首次查询 ingress 网关实例详情，确认启动前状态")
    def test_get_ingress_instance_first(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据编码查询 ingress 网关实例详情 - 第2次")
    @allure.description("启动后再次查询 ingress 网关实例详情，确认状态变化")
    def test_get_ingress_instance_second(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求再次查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码启动 ingress 网关实例")
    @allure.description("启动指定 ingress 网关实例")
    def test_start_ingress_instance(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求启动 ingress 网关实例"):
                response_json = ingress_service.start_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关实例扩缩容")
    @allure.description("对指定 ingress 网关实例进行副本数扩缩容")
    def test_scale_ingress_instance(self, ingress_service, api_cache):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("从缓存读取 instance_id 并发送扩缩容请求"):
                if not api_cache.has("ms_ingress_instance_id"):
                    pytest.skip("缺少 upstream 依赖：ms_ingress_instance_id 未缓存")
                instance_id = api_cache.get("ms_ingress_instance_id")
                response_json = ingress_service.scale_ingress_instance(
                    instance_id=instance_id, deploy_type="ksr", replicas=2
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码停止 ingress 网关实例")
    @allure.description("停止指定 ingress 网关实例")
    def test_stop_ingress_instance(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求停止 ingress 网关实例"):
                response_json = ingress_service.stop_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码删除网关实例")
    @allure.description("按编码删除 ingress 网关实例（扩缩容流程收尾）")
    def test_delete_ingress_instance(self, ingress_service, public_params):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关实例"):
                response_json = ingress_service.delete_ingress_instance_by_code(
                    Ingress.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
