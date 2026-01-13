import logging
from dataclasses import dataclass
from typing import Dict, Any

from base.api.services.base_service import BaseService
from core import DataCache


@dataclass
class PortalUserEntity(object):
    """
    用户相关的实体类
    user_id: 用户编号
    username: 登陆用户名
    password: 登陆密码
    tenant_code: 租户编码
    phone: DES加密后的手机号
    email: DES加密后的邮箱
    expire_time: token过期时间，默认18000000
    """
    user_id: str = None
    username: str = None
    password: str = None
    tenant_code: str = None
    phone: str = None
    email: str = None
    expire_time: int = 18000000

@dataclass
class ClusterPlaneEntity(object):
    """
    集群平面相关的实体类
    instance_id: 实例id
    prod_inst_name: pord实例名称
    """
    instance_id: str = None
    prod_inst_name: str = None

@dataclass
class OpenSystemEntity(object):
    """
    创建 or 更新系统需要的参数实体
    system_id: 系统编号
    system_name: 系统名称
    system_code: 系统编码
    system_desc: 系统描述
    field_one: 一级域编号
    field_two: 二级域编号
    create_id: 创建者编号
    username: 创建者用户名
    """
    system_id: str = None
    system_name: str = None
    system_code: str = None
    system_desc: str = None
    field_one: str = None
    field_two: str = None
    create_id: str = None
    username: str = None

@dataclass
class BasicCodeEntity(object):
    """
    测试时会用到的一些code实体
    cell_code: 单元编号
    tenant_code: 租户编号
    system_code: 系统编号
    """
    cell_code: str = None
    tenant_code: str = None
    system_code: str = None


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class PanJiPortalOpenService(BaseService):
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Portal OpenAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
        )
        self.logger.info(f"Initializing PanJi Portal OpenAPI Service with base_url: {self.base_url}")

    def get_token(self, panji_sign: PortalUserEntity) -> Dict[str, Any]:
        """
        登陆获取Token

        Args:
            panji_sign: PortalSignEntity (
                username: str
                password: str
                tenant_code: str
                expire_time: int = 18000000
            )

        Returns:
            Dict[str, Any]
        """
        self.logger.info(f"Getting PanJi Token")
        url = "/apisix/plugin/jwt/sign"
        sign_info = {
            "userName": panji_sign.username,
            "password": panji_sign.password,
            "tenantCode": panji_sign.tenant_code,
            "expireTime": panji_sign.expire_time,
        }
        response = self.post(endpoint=url, json=sign_info)
        return response.json()

    def get_first_field_info(self) -> Dict[str, Any]:
        """
        获取一级域信息

        Returns:
            Dict[str, Any]
        """
        self.logger.info(f"Getting First Field Info")
        url = "/openapi/portal/restApi/firstFieldInfo/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_second_field_info(self) -> Dict[str, Any]:
        """
        获取二级域信息

        Returns:
            Dict[str, Any]
        """
        self.logger.info(f"Getting Second Field Info")
        url = "/openapi/portal/restApi/secondFieldInfo/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_cluster_plane(self, cluster_info: ClusterPlaneEntity) -> Dict[str, Any]:
        """
        新增集群平面单元
        """
        self.logger.info(f"Create cluster plane")
        url = "/openapi/portal/restApi/cluster/add"
        body = {
            "prodInstName": cluster_info.prod_inst_name,
            "prodInstCode": cluster_info.prod_inst_name,
            "prodInstType": "k8s",
            "caCert": None,
            "clientCert": None,
            "envCode": "生产环境",
            "planeCode": "a",
            "cellCode": "a",
            "endPoints": None,
            "context": None,
            "planeName": "a",
            "cellName": "a",
            "envName": "生产环境"
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def query_cluster_plane(self, cluster_info: ClusterPlaneEntity) -> Dict[str, Any]:
        """
        查询集群平面单元
        """
        self.logger.info(f"Query cluster plane")
        url = "/openapi/portal/restApi/cluster/list"
        params = {
            "prodInstName": cluster_info.prod_inst_name,
        }
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def update_cluster_plane(self, cluster_info: ClusterPlaneEntity) -> Dict[str, Any]:
        """
        修改集群平面单元
        """
        self.logger.info(f"Update cluster plane")
        url = "/openapi/portal/restApi/cluster/update"
        body = {
            "instanceId": cluster_info.instance_id,
            "prodInstCode": cluster_info.prod_inst_name,
            "prodInstName": cluster_info.prod_inst_name,
            "prodInstType": "k8s",
            "cellName": "multest",
            "cellCode": "multest",
            "envCode": "PORD",
            "planeCode": "multest",
            "planeName": "multest"
        }
        response = self.patch(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def delete_cluster_plane(self, cluster_info: ClusterPlaneEntity) -> Dict[str, Any]:
        """
        删除集群平面单元
        """
        self.logger.info(f"Delete cluster plane")
        url = "/openapi/portal/restApi/cluster/delete"
        params = {
            "instanceId": cluster_info.instance_id,
        }
        response = self.delete(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def query_bind_cluster_list(self) -> Dict[str, Any]:
        """
        根据租户、环境查询绑定集群信息
        """
        self.logger.info(f"Query bind cluster list")
        url = "/openapi/portal/restApi/bindCluster/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def tenant_bind_cluster(self) -> Dict[str, Any]:
        """
        租户绑定集群平面单元
        """
        self.logger.info(f"Tenant bind cluster plane cell")
        url = "/openapi/portal/restApi/tenantCluster/addBatch"
        body = [
            {
                "clusterInstanceId": "348",
                "envCode": "生产环境",
                "envName": "生产环境",
                "tenantId": "1"
            }
        ]
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def query_tenant_info_by_username(self, username: str) -> Dict[str, Any]:
        """
        根据用户名查询绑定的租户信息
        """
        self.logger.info(f"Query tenant info by username: {username}")
        url = f"/openapi/portal/restApi/v1/user/{username}/tenants"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_menu_permission_data(self) -> Dict[str, Any]:
        """
        获取菜单权限数据
        """
        self.logger.info(f"Get menu permission data")
        url = "/openapi/portal/restApi/menu/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def sync_user_api(self, user_info: PortalUserEntity) -> Dict[str, Any]:
        """
        同步用户
        """
        self.logger.info(f"Sync user information")
        url = "/openapi/portal/restApi/sync/user"
        body = {
            "sourceCode": "1",
            "phone": user_info.phone,
            "displayName": "shengsong",
            "expireDate": "2099-12-31 23:59:59",
            "userName": user_info.username,
            "locked": False,
            "email": user_info.email,
            "tenantRoleList": [
                {
                    "roles": [
                        "platform_manager"
                    ],
                    "tenantCode": "tenant_admin"
                }
            ]
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def user_bind_tenant(self, user_info: PortalUserEntity) -> Dict[str, Any]:
        """
        绑定租户
        """
        self.logger.info(f"Bind tenant")
        url = "/openapi/portal/restApi/addTenantUsers"
        body = {
            "tenantId": "1",
            "userIdJsonStr": [
                {
                    "userId": user_info.user_id,
                    "userName": user_info.username,
                    "status": 1
                }
            ]
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def user_bind_role(self, user_info: PortalUserEntity) -> Dict[str, Any]:
        """
        绑定角色
        """
        self.logger.info(f"Bind role")
        url = "/openapi/portal/restApi/addRoleMember"
        body = {
            "tenantId": "1",
            "roleId": "1",
            "userList": [
                {
                    "userId": user_info.user_id,
                    "userName": user_info.username
                }
            ]
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def query_system(self, system_code: str) -> Dict[str, Any]:
        """
        查询系统
        """
        self.logger.info(f"Query system")
        url = "/openapi/portal/restApi/system/list"
        body = {
            "systemEnvironment": "PROD",
            "systemName": system_code
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def create_system(self, system: OpenSystemEntity):
        """
        创建系统
        """
        self.logger.info(f"Create system")
        url = "/openapi/portal/restApi/system/add"
        body = {
            "systemName": system.system_name,
            "systemCode": system.system_code,
            "systemDesc": system.system_desc,
            "systemLevel": "SYS_2",
            "systemEnvironment": "PROD",
            "fieldOne": system.field_one,
            "fieldTwo": system.field_two,
            "systemSection": "平台能力中心",
            "tenantId": "1",
            "createId": system.create_id,
            "userName": system.username
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def system_resource_allocation(self, username: str, code_list: BasicCodeEntity):
        """
        系统资源配额分配
        """
        self.logger.info(f"System resource allocation")
        url = f"/openapi/elastic-compute/v2/cells/{code_list.cell_code}/tenants/{code_list.tenant_code}/systems/{code_list.system_code}/quota/allocate"
        body = {
            "memory": 1073741824,
            "cpu": 1,
            "storage": {
                "nfs": []
            },
            "username": username
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def system_resource_quota_detail(self, code_list: BasicCodeEntity):
        """
        系统资源配额详情
        """
        self.logger.info(f"System resource quota detail")
        url = f"/openapi/elastic-compute/v2/cells/{code_list.cell_code}/tenants/{code_list.tenant_code}/systems/{code_list.system_code}/quota/detail"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_application(self, app_code: str, app_name: str, app_type: str, workload_type: str, system_id: str):
        """
        创建应用
        app_code: 应用编号
        app_name: 应用名称
        app_type: 应用类型
        workload_type: 工作负载类型
        system_id: 所属系统编号
        """
        self.logger.info(f"Create application")
        url = "/openapi/portal/restApi/application/add"
        body = {
            "applicationSourceCode": app_code,
            "applicationSourceName": app_name,
            "environment": "PROD",
            "applicationSourceType": app_type,
            "workloadType": workload_type,
            "systemId": system_id,
            "microServiceCode": ""
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def update_system(self, system: OpenSystemEntity):
        """
        更新系统
        """
        self.logger.info(f"Update system")
        url = "/openapi/portal/restApi/system/update"
        body = {
            "systemId": system.system_id,
            "systemName": system.system_name,
            "systemCode": system.system_code,
            "systemDesc": "cesdsfdssddsfds",
            "systemType": None,
            "status": 1,
            "parentId": None,
            "tenantId": 1,
            "systemPlane": None,
            "systemArea": None,
            "systemRank": None,
            "systemLevel": "SYS_2",
            "systemSection": "算力调度",
            "createTime": "2024-12-12 14:47:44",
            "updateTime": None,
            "systemEnvironment": "PROD",
            "fieldOne": "b39a802ef7834b17b3cd9e76dd6f20230817",
            "fieldTwo": "b39a802ef7834b17b3cd9e76dd6g20230817",
            "fieldThree": None,
            "createId": system.create_id,
            "sysId": None,
            "userName": system.username,
            "ids": None,
            "alias": "shengsong",
            "currentUserId": None,
            "fieldOneName": "算力调度一级域",
            "fieldTwoName": "算力调度二级域",
            "tenantUserEntityId": 0,
            "isManager": "true",
            "tenantCode": "tenant_admin",
            "tenantName": "平台运营租户",
            "isAuthorized": "true"
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def user_system_authorization(self, user_id_list: list[str], system_id_list: list[str]):
        """
        用户系统授权接口，批量授权
        user_id_list: 授权的用户id列表，["200685","201214"]
        system_id_list: 授权的系统id列表
        """
        self.logger.info(f"User system authorization")
        url = "/openapi/portal/restApi/batchAuthorization"
        body = {
            "authorizedType": "1",
            "type": "1",
            "isManager": "0",
            "expireTime": "",
            "tenantId":"1",
            "objectIdList": user_id_list,
            "entityIdList": system_id_list
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def update_application(self, app_id: str, system_id: str):
        """
        更新应用
        app_id: 更新的应用编号
        system_id: 所属的系统
        """
        self.logger.info(f"Update application")
        url = "/openapi/portal/restApi/application/update"
        body = {
            "applicationSourceId": app_id,
            "applicationSourceCode": "cs20241212yy",
            "applicationSourceName": "cs20241212yyxiugai",
            "applicationSourceType": "web_type",
            "tenantId": 1,
            "systemId": system_id,
            "environment": "PROD",
            "workloadType": "Deployment"
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def user_application_authorization(self, user_id_list: list[str], application_id_list: list[str]):
        """
        用户应用授权接口，批量授权
        user_id_list: 授权的用户id列表，["200685","201214"]
        application_id_list: 授权的应用id列表
        """
        self.logger.info(f"User application authorization")
        url = "/openapi/portal/restApi/batchAuthorization"
        body = {
            "authorizedType": "1",
            "type": "2",
            "isManager": "1",
            "expireTime": "",
            "tenantId":"1",
            "objectIdList": user_id_list,
            "entityIdList": application_id_list
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def query_application_list(self, app_code: str):
        """
        查询应用列表
        app_code: 应用编号
        """
        self.logger.info(f"Query application list")
        url = "/openapi/portal/restApi/application/list"
        body = {
            "pageNum": "1",
            "pageSize": "1",
            "applicationSourceName": app_code,
            "applicationSourceType": "web_type"
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def query_application_detail(self, app_id: str):
        """
        查看应用详细信息
        app_id: 要查看的应用的编号
        """
        self.logger.info(f"Query application detail")
        url = f"/openapi/portal/restApi/application/detail"
        params = {
            "applicationSourceId", app_id
        }
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def system_resource_quota_remove(self, code_list: BasicCodeEntity):
        """
        系统资源配额释放/删除
        """
        self.logger.info(f"System resource quota remove")
        url = f"/openapi/elastic-compute/v2/cells/{code_list.cell_code}/tenants/{code_list.tenant_code}/systems/{code_list.system_code}/quota/delete"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def delete_application(self, app_id: str):
        """
        删除应用
        app_id: 要删除的应用的编号
        """
        self.logger.info(f"Delete application")
        url = "/openapi/portal/restApi/application/delete"
        body = {
            "ids": app_id
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def system_quota_delete(self, code: BasicCodeEntity):
        """
        系统配额释放/删除
        """
        self.logger.info(f"System quota release delete")
        url = f"/openapi/elastic-compute/v2/cells/{code.cell_code}/tenants/{code.tenant_code}/systems/{code.system_code}/quota/delete"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def delete_system(self, system_id: str, system_code: str):
        """
        删除系统
        app_id: 要删除的应用的编号
        system_id: 要删除的系统的id
        system_name: 要删除的系统的Code
        """
        self.logger.info(f"Delete application")
        url = "/openapi/portal/restApi/system/delete"
        body = {
            "ids": system_id,
            "systemCode": system_code,
            "tenantCode": "tenant_admin"
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()
