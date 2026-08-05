"""
托管集群主机绑定接口测试

转换自 JMeter 脚本: host-bind.jmx
测试内容：集群下的主机列表查询
"""

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("主机绑定接口")
class TestEcExtensionsHostBind:
    """
    对应 JMeter 脚本: host-bind.jmx
    线程组: Thread Group - 主机绑定
    """

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=api_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取主机绑定测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "PROD_PLANE1_CELL3"),
        }

    @pytest.mark.order(1)
    @allure.title("查询集群下主机列表")
    @allure.description("查询指定单元下集群的主机列表信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_hosts(self, ec_ext_service, public_params):
        """查询集群下主机列表，断言业务码为成功。"""
        cell_code = public_params["cell_code"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_hosts(cell_code=cell_code)

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"查询主机列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
