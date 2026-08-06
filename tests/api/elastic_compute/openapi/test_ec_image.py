"""
弹性计算 OpenAPI Image 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/image-api.jmx
线程组: Thread Group - image
测试内容：
- 获取镜像列表
- 获取镜像已部署应用服务列表
"""
import allure
import pytest

from base.api.entity.elastic_compute.openapi import ImagePublicParams
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Image 镜像查询接口")
class TestEcOpenapiImage:
    """
    对应 JMeter 脚本: image-api.jmx
    线程组: Thread Group - image

    覆盖 2 个接口：
      1) GET /openapi/elastic-compute/v1/images 镜像列表
      2) GET /openapi/elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/images/apps
         镜像已部署应用服务列表
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ImagePublicParams:
        """提取 Image 测试所需的公共参数。"""
        return ImagePublicParams(
            cluster_id=api_env.get("clusterId"),
            namespace=api_env.get("namespace"),
            project_name=api_env.get("copyProjectName"),
            image_name=api_env.get("copyRepName"),
            image_version=api_env.get("copyImageTag"),
        )

    @allure.title("获取镜像列表")
    @allure.description("查询弹性计算镜像列表，验证业务码为 2000")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="image_list")
    @pytest.mark.order(1)
    def test_list_images(self, ec_service):
        """查询镜像列表。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_images()
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"获取镜像列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("获取镜像已部署应用服务列表")
    @allure.description(
        "根据 clusterId + namespace + projectName + imageName + version "
        "查询镜像已部署应用服务列表，验证业务码为 2000"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="image_apps", depends=["image_list"])
    @pytest.mark.order(2)
    def test_list_image_apps(self, ec_service, public_params):
        """查询镜像已部署应用服务列表。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_image_apps(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                project_name=public_params.project_name,
                image_name=public_params.image_name,
                version=public_params.image_version,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"获取镜像已部署应用服务列表失败, code: {resp.get('code')}, 响应: {resp}"
            )
