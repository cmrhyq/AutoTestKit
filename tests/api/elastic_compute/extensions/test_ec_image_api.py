"""
镜像接口测试

转换自 JMeter 脚本: image-api.jmx
测试内容：获取镜像 tag 列表
"""

import allure
import pytest

from base.api.entity.elastic_compute import ImageApiPublicParams
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.constants.business import ApiCode
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("镜像管理接口")
class TestEcExtensionsImageApi:
    """
    对应 JMeter 脚本: image-api.jmx
    线程组: Thread Group - 镜像tag
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
    def public_params(self, api_env) -> ImageApiPublicParams:
        """提取镜像接口测试所需的公共参数。"""
        return ImageApiPublicParams(
            repo_name=api_env.get("nginxRepoName", "kube_system/nfs/provisioner/v1"),
            project_name=api_env.get("nginxProjectName", "kube_system"),
        )

    @pytest.mark.order(1)
    @allure.title("获取镜像 Tag 列表")
    @allure.description("根据镜像仓库名和项目名查询镜像 Tag 列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_image_tags(self, ec_ext_service, public_params):
        """获取镜像 tag 列表，断言业务码为 2000。"""
        repo_name = public_params.repo_name
        project_name = public_params.project_name

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.get_image_tags(
                repo_name=repo_name,
                project_name=project_name,
            )

            assert response_json.get("code") == ApiCode.SUCCESS, (
                f"获取镜像 Tag 列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
