"""
微服务 Ingress OpenAPI 接口测试脚本

基于以下 3 个 JMeter 脚本转换合并（同属 ms-ingress 域，路径前缀相同，有明显数据依赖）：
- msingressgw.jmx（12 用例）：nginx 参数模板 + ingress 网关实例 CRUD
- ingressnginx.jmx（9 用例）：ingress 网关实例 + 网关配置 CRUD
- msingressksr.jmx（7 用例）：ingress 网关实例 CRUD + 启停/扩缩容

共 28 用例。
"""
from typing import Dict

import allure
import pytest

from base.api.services.microservices_open_service import (
    PanJiMicroservicesOpenService,
    Ingress,
    IngressConfig,
    NginxParam,
    NginxParamStatus,
    IngressIns,
)
from core.reporting.allure_helper import AllureHelper


@pytest.fixture(scope="module")
def ingress_service(api_env, api_logger):
    """模块级 Ingress OpenAPI 服务实例"""
    service = PanJiMicroservicesOpenService(
        base_url=api_env.get("apiBaseUrl"),
        logger=api_logger,
    )
    yield service
    service.close()


def _build_ingress(api_env) -> Ingress:
    return Ingress(
        name=api_env.get("meshGatewayName"),
        code=api_env.get("meshGatewayName"),
        sysCode=api_env.get("sysCode"),
        unitCode=api_env.get("unitCode"),
        planeCode=api_env.get("planeCode"),
    )


def _build_ingress_config(api_env, soft_load_code: str = None) -> IngressConfig:
    return IngressConfig(
        name=api_env.get("meshGatewayName"),
        code=api_env.get("meshGatewayName"),
        sysCode=api_env.get("sysCode"),
        unitCode=api_env.get("unitCode"),
        planeCode=api_env.get("planeCode"),
        serviceName=api_env.get("meshGatewayName"),
        softLoadCode=soft_load_code or api_env.get("meshGatewayName"),
    )


# =============================================================================
# msingressgw.jmx — nginx 参数模板 CRUD + ingress 网关实例
# =============================================================================
@pytest.mark.api
@allure.feature("磐基微服务 Ingress OpenAPI 服务")
@allure.story("msingressgw - nginx 参数模板与网关实例")
class TestMsIngressGw:
    """msingressgw.jmx 转换（12 用例）"""

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        get_token(self.TENANT)

    @allure.title("新增 nginx 参数模板")
    def test_add_nginx_param(self, ingress_service, api_env):
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
    def test_query_all_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 nginx 参数模板列表"):
                response_json = ingress_service.query_all_nginx_param(param_type="All")
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("nginx 参数模板上线接口")
    def test_online_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求上线 nginx 参数模板"):
                status = NginxParamStatus(id=1, keyword="", status="online")
                response_json = ingress_service.update_nginx_param_status(status)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("分页查询 nginx 参数模板列表")
    def test_list_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求分页查询 nginx 参数模板"):
                status = NginxParamStatus(id=1, keyword="", page=1, rows=10)
                response_json = ingress_service.list_nginx_param(status)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("nginx 参数模板下线接口")
    def test_offline_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求下线 nginx 参数模板"):
                status = NginxParamStatus(id=1, keyword="", status="offline")
                response_json = ingress_service.update_nginx_param_status(status)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据 nginx 参数模板删除接口")
    def test_delete_nginx_param(self, ingress_service):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 nginx 参数模板"):
                response_json = ingress_service.delete_nginx_param_by_code(
                    code="nginx-tpl-auto", param_type="App"
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("新增 ingress 网关实例")
    def test_add_ingress_instance(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关实例"):
                response_json = ingress_service.add_ingress_instance(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据编码查询 ingress 网关实例详情")
    def test_get_ingress_instance_by_code(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询 ingress 网关实例信息分页")
    def test_list_ingress_instance(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求分页查询 ingress 网关实例"):
                data = IngressIns(
                    keyword="",
                    systemCode=api_env.get("sysCode"),
                    unitCode=api_env.get("unitCode"),
                    planeCode=api_env.get("planeCode"),
                    page=1,
                    rows=10,
                )
                response_json = ingress_service.list_ingress_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("修改 ingress 网关实例")
    def test_update_ingress_instance(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求修改 ingress 网关实例"):
                data = {
                    "name": api_env.get("meshGatewayName"),
                    "code": api_env.get("meshGatewayName"),
                    "sysCode": api_env.get("sysCode"),
                    "unitCode": api_env.get("unitCode"),
                    "planeCode": api_env.get("planeCode"),
                    "remark": "updated by autotest",
                }
                response_json = ingress_service.update_ingress_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码删除网关实例")
    def test_delete_ingress_instance_by_code(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关实例"):
                response_json = ingress_service.delete_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json


# =============================================================================
# ingressnginx.jmx — ingress 网关配置 CRUD
# =============================================================================
@pytest.mark.api
@allure.feature("磐基微服务 Ingress OpenAPI 服务")
@allure.story("ingressnginx - ingress 网关实例和配置")
class TestIngressNginx:
    """ingressnginx.jmx 转换（9 用例）"""

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        get_token(self.TENANT)

    @allure.title("新增 ingress 网关实例")
    def test_add_ingress_instance(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关实例"):
                response_json = ingress_service.add_ingress_instance(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据编码查询 ingress 网关实例详情")
    def test_get_ingress_instance_by_code(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("新增 ingress 网关配置")
    def test_add_ingress_config(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关配置"):
                response_json = ingress_service.add_ingress_config(_build_ingress_config(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询 ingress 网关配置列表")
    def test_list_ingress_config(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求查询 ingress 网关配置列表"):
                response_json = ingress_service.list_ingress_config(_build_ingress_config(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新 ingress 网关配置")
    def test_update_ingress_config(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求更新 ingress 网关配置"):
                response_json = ingress_service.update_ingress_config(_build_ingress_config(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关配置详情")
    def test_get_ingress_config_detail(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关配置详情"):
                response_json = ingress_service.get_ingress_config_detail(_build_ingress_config(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关配置通过 service 获取配置详情")
    def test_get_ingress_by_service_name(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求通过 service 获取网关配置详情"):
                response_json = ingress_service.get_ingress_by_service_name(_build_ingress_config(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关配置删除接口")
    def test_delete_ingress_config_by_code(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关配置"):
                response_json = ingress_service.delete_ingress_config_by_code(_build_ingress_config(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码删除网关实例")
    def test_delete_ingress_instance_by_code(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关实例"):
                response_json = ingress_service.delete_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json


# =============================================================================
# msingressksr.jmx — ingress 网关实例启停/扩缩容
# =============================================================================
@pytest.mark.api
@allure.feature("磐基微服务 Ingress OpenAPI 服务")
@allure.story("msingressksr - ingress 实例启停扩缩容")
class TestMsIngressKsr:
    """msingressksr.jmx 转换（7 用例）"""

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        get_token(self.TENANT)

    @allure.title("新增 ingress 网关实例")
    def test_add_ingress_instance(self, ingress_service, api_env, api_cache):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求新增 ingress 网关实例"):
                response_json = ingress_service.add_ingress_instance(_build_ingress(api_env))
            with AllureHelper.step("验证响应并缓存 instance_id（若有）"):
                assert "code" in response_json
                if response_json.get("code") == 0 and isinstance(response_json.get("data"), Dict):
                    instance_id = response_json["data"].get("id") or response_json["data"].get("instanceId")
                    if instance_id:
                        api_cache.set("ms_ingress_instance_id", instance_id)

    @allure.title("根据编码查询 ingress 网关实例详情 - 第1次")
    def test_get_ingress_instance_first(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据编码查询 ingress 网关实例详情 - 第2次")
    def test_get_ingress_instance_second(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 GET 请求再次查询 ingress 网关实例详情"):
                response_json = ingress_service.get_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码启动 ingress 网关实例")
    def test_start_ingress_instance(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求启动 ingress 网关实例"):
                response_json = ingress_service.start_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("ingress 网关实例扩缩容")
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
    def test_stop_ingress_instance(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 POST 请求停止 ingress 网关实例"):
                response_json = ingress_service.stop_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关实例编码删除网关实例")
    def test_delete_ingress_instance(self, ingress_service, api_env):
        with AllureHelper.api_test(ingress_service):
            with AllureHelper.step("发送 DELETE 请求删除 ingress 网关实例"):
                response_json = ingress_service.delete_ingress_instance_by_code(_build_ingress(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
