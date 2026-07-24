"""
可观测 OpenAPI 模型查询接口测试

转换自 JMeter 脚本: observable-query.jmx
测试内容：
- 查询模型列表
- 根据ID或名称获取模型
- 配置项结构化查询
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.observable_open_service import (
    PanJiObservableOpenService,
    QueryModelConf,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基可观测OpenAPI接口")
@allure.story("Observable Query 查询接口")
class TestObservableQuery:
    """
    对应 JMeter 脚本: observable-query.jmx
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

    @allure.title("查询模型列表")
    @allure.description(
        "GET /openapi/monitor-o11y/amdb-console/publish/v3/confs/models - "
        "验证能够分页查询模型列表"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_models(self, observable_service, api_cache):
        with AllureHelper.api_test(observable_service):
            config = QueryModelConf(
                page=1,
                per_page=1,
                with_logo=True,
                with_props=True,
                with_relations=True,
                with_graph=True,
                with_confs_count=True,
            )

            with AllureHelper.step("发送 GET 请求查询模型列表"):
                response_json = observable_service.query_models(config=config)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"

    @allure.title("根据ID或名称获取模型")
    @allure.description(
        "GET /openapi/monitor-o11y/amdb-console/publish/v3/confs/models/{modelsIdOrName} - "
        "验证能够根据模型ID或名称获取模型详情"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_model_by_id_or_name(self, observable_service, api_env, api_cache):
        with AllureHelper.api_test(observable_service):
            models_id_or_name = api_env.get(
                "modelsIdOrName", "c6869bc8-b527-4bff-bce7-6f39de1b06ab"
            )

            with AllureHelper.step(f"发送 GET 请求获取模型详情: {models_id_or_name}"):
                response_json = observable_service.get_model_by_id_or_name(
                    model_id_or_name=models_id_or_name
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"

    @allure.title("配置项结构化查询")
    @allure.description(
        "GET /openapi/monitor-o11y/amdb-console/publish/v3/confs/search/conf-items - "
        "验证配置项结构化查询接口"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_conf_items(self, observable_service, api_env, api_cache):
        with AllureHelper.api_test(observable_service):
            # 构造查询条件（对应 JMX 中的大 JSON body）
            query = {
                "uniques": [],
                "filters": [],
                "processors": [],
                "sort": [],
                "flatPrefix": "",
                "dataMode": "",
                "perPage": 10,
                "scopes": [],
                "page": 1,
                "keyword": "",
                "fields": [],
                "conditions": {
                    "condition": "and",
                    "rules": []
                },
                "forCount": False,
                "singleData": False
            }

            with AllureHelper.step("发送请求进行配置项结构化查询"):
                response_json = observable_service.search_conf_items(query=query)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
