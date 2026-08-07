"""
Nginx RBAC 模板管理接口测试（Extensions - apikey 鉴权）

测试内容：
    1) 前置清理：若目标 RBAC 已存在则先删除，若不存在则跳过
    2) 创建 Nginx RBAC 模板
    3) 删除 Nginx RBAC 模板

依赖：
    - config/env_*.yaml 需提供：apiInnerBaseUrl / clusterId / namespace / rbacCode
    - 按 code==2000 或 code==4004 判断资源是否存在，
      拍平为顺序 fixture-driven 流程（pre_cleanup → create → delete）。
"""

import allure
import pytest

from base.api.entity.elastic_compute import NginxRbacPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Nginx RBAC 模板管理接口")
class TestEcExtensionsNginxRbac:
    """
        pre_cleanup（GET，若 2000 则 DELETE；若 4004 则跳过）
        → create（POST）
        → delete（DELETE）
    """

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, test_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=test_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> NginxRbacPublicParams:
        """提取 Nginx RBAC 测试所需的公共参数。"""
        return NginxRbacPublicParams(
            cluster_id=str(test_env.get("clusterId", "1")),
            namespace=test_env.get("namespace", "test-ns"),
            code="test-rbac",
        )

    # ==================== 1) 前置清理：若已存在则删除 ====================

    @pytest.mark.dependency(name="nginx_rbac_pre_cleanup")
    @pytest.mark.order(0)
    @allure.title("查询 Nginx RBAC 并在存在时预删除")
    @allure.description("先查询 RBAC，若存在则预清理，不存在则跳过；确保后续 create 测试从干净状态开始")
    @allure.severity(allure.severity_level.NORMAL)
    def test_00_pre_cleanup_nginx_rbac(self, ec_ext_service, public_params):
        """前置清理：GET 查询，若存在则 DELETE，否则 skip 清理动作。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        code = public_params.code

        with AllureHelper.api_test(ec_ext_service):
            get_resp = ec_ext_service.get_nginx_rbac(
                cluster_id=cluster_id,
                namespace=namespace,
                code=code,
            )
            get_code = get_resp.get("code")

            if get_code == ApiCode.SUCCESS:
                delete_resp = ec_ext_service.delete_nginx_rbac(
                    cluster_id=cluster_id,
                    namespace=namespace,
                    code=code,
                )
                assert delete_resp.get("code") == ApiCode.SUCCESS, (
                    f"预清理阶段删除 Nginx RBAC 失败, 响应: {delete_resp}"
                )
            elif get_code == ApiCode.NOT_FOUND:
                pytest.skip(f"目标 RBAC 不存在 (code={ApiCode.NOT_FOUND})，无需预清理")
            else:
                pytest.fail(f"查询 Nginx RBAC 返回未知业务码 code={get_code}, 响应: {get_resp}")

    # ==================== 2) 创建 Nginx RBAC ====================

    @pytest.mark.dependency(name="nginx_rbac_create", depends=["nginx_rbac_pre_cleanup"])
    @pytest.mark.order(1)
    @allure.title("创建 Nginx RBAC 模板")
    @allure.description("创建指定 code 的 Nginx RBAC 模板，断言业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_nginx_rbac(self, ec_ext_service, public_params):
        """创建 Nginx RBAC，断言业务码为 2000。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        code = public_params.code

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.create_nginx_rbac(
                cluster_id=cluster_id,
                namespace=namespace,
                code=code,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"创建 Nginx RBAC 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 3) 删除 Nginx RBAC ====================

    @pytest.mark.dependency(name="nginx_rbac_delete", depends=["nginx_rbac_create"])
    @pytest.mark.order(2)
    @allure.title("删除 Nginx RBAC 模板")
    @allure.description("删除刚创建的 Nginx RBAC 模板，断言业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_nginx_rbac(self, ec_ext_service, public_params):
        """删除 Nginx RBAC，断言业务码为 2000。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        code = public_params.code

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.delete_nginx_rbac(
                cluster_id=cluster_id,
                namespace=namespace,
                code=code,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"删除 Nginx RBAC 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
