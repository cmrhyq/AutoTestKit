"""
Portal（门户）相关实体模型。

包含内部 API 与开放 API 使用到的所有 DTO：
- InnerSystemEntity / ApplicationEntity / MenuEntity / RoleEntity /
  TenantEntity / InnerUserEntity: portal_inner_service 使用
- PortalUserEntity / ClusterPlaneEntity / OpenSystemEntity /
  BasicCodeEntity: portal_open_service 使用
"""

from dataclasses import dataclass, field
from typing import List

# ==================== Portal Inner API 实体 ====================

@dataclass
class PortalInnerPublicParams(object):
    """
    portal_user_id: 用户id
    portal_username: 用户名
    module_name: 测试用模块名称
    role_code: 测试用角色名称
    username: 测试用用户名
    tenant_code: 测试用租户名称
    menu_name: 测试用菜单名称
    source_code: 测试用来源码
    """
    portal_user_id: str
    portal_username: str
    module_name: str = "portal"
    role_code: str = "autotest260807"
    username: str = "test_user_260807"
    tenant_code: str = "auto_tenant_260807"
    menu_name: str = "新增测试菜单"
    source_code: str = "observability"


@dataclass
class InnerSystemEntity(object):
    """
    system_name: 系统名称
    system_code: 系统编码
    field_one: 一级域ID
    field_two: 二级域ID
    create_id: 创建人ID
    username: 创建人用户名
    system_section: 系统分区
    system_level: 系统级别
    system_desc: 系统描述
    system_environment: 系统环境
    tenant_id: 租户ID
    """
    system_name: str
    system_code: str
    field_one: str
    field_two: str
    create_id: str
    username: str
    system_section: str = "算力调度"
    system_level: str = "SYS_1"
    system_desc: str = "test"
    system_environment: str = "PROD"
    tenant_id: int = 1


@dataclass
class ApplicationEntity(object):
    """
    app_name: 应用名称
    app_code: 应用编码
    app_type: 应用类型，如 web_type
    system_id: 系统ID
    create_id: 创建人ID
    username: 创建人用户名
    workload_type: 工作负载类型
    environment: 环境
    tenant_id: 租户ID
    micro_service_code: 微服务编码
    """
    app_name: str
    app_code: str
    app_type: str
    system_id: str
    create_id: str
    username: str
    workload_type: str
    environment: str = "PROD"
    tenant_id: int = 1,
    micro_service_code: str = None


@dataclass
class MenuEntity(object):
    """
    menu_name: 菜单名称
    url_path: 菜单URL
    plugin_url: 插件URL
    source_code: 来源编码，例如 observability
    roles: 角色编码list，例如 ["tenant_admin","platform_manager"]
    view_type: 视图类型，默认1
    sort_no: 排序号，默认1
    status: 状态，默认0
    menu_type: 菜单类型，默认0
    menu_icon: 菜单图标，默认空
    permission_code: 权限编码，例如 observability
    parent_id: 父菜单ID，默认Null
    plugin_flag: 插件标识，例如 observability
    """
    menu_name: str
    url_path: str
    plugin_url: str
    source_code: str = "observability"
    roles: List[str] = field(default_factory=lambda: ["platform_manager"])
    view_type: str = "1"
    sort_no: int = 1
    status: int = 0
    menu_type: str = "D"
    menu_icon: str = ""
    permission_code: str = ""
    parent_id: str = None
    plugin_flag: str = "observability"


@dataclass
class RoleEntity(object):
    """
    role_name: 角色名称
    role_code: 角色编码
    role_desc: 角色描述，默认None
    role_type: 角色类型，默认1
    has_edit: 是否可编辑，默认1
    create_id: 创建用户id，默认None
    """
    role_name: str
    role_code: str
    role_desc: str = None
    role_type: int = 1
    has_edit: int = 1
    create_id: str = None


@dataclass
class TenantEntity(object):
    """
    tenant_name: 租户名称
    tenant_code: 租户编码
    tenant_lever: 租户等级
    tenant_parent_id: 父租户id
    tenant_area: 租户区域
    dept_code: 部门编码
    source_code: 来源编码，例如 plugin-center
    create_user_id: 创建者id
    """
    tenant_code: str = None
    tenant_name: str = None
    tenant_lever: int = None
    tenant_parent_id: int = None
    tenant_area: int = None
    dept_code: str = None
    source_code: str = "plugin-center"
    create_user_id: int = None


@dataclass
class InnerUserEntity(object):
    """
    username: 用户名，AES加密
    alias: 用户别名
    phone: 手机号，DES加密
    email: 邮箱，DES加密
    tenant_code: 租户编码
    role_code: 角色编码
    create_id: 创建者id
    """
    username: str = None
    alias: str = None
    phone: str = None
    email: str = None
    tenant_code: str = None
    role_code: str = None
    create_id: int = None


# ==================== Portal Open API 实体 ====================
@dataclass
class PortalOpenPublicParams(object):
    """
    portal_user_id: 用户id
    portal_username: 用户名
    cell_code: 系统的cell code
    tenant_code: 租户code
    prod_inst_name: name
    sync_phone: 同步的手机号，DES加密
    sync_email: 同步的邮箱，DES加密
    sync_username: 同步的用户名，AES加密
    """
    portal_username: str
    portal_user_id: str
    cell_code: str
    tenant_code: str
    prod_inst_name: str = "test-inst1210"
    sync_phone: str = "FZfAKlL4LhFOuegCAVR0cA=="
    sync_email: str = "/9VWlMdY7PShZj72q53jIQ=="
    sync_username: str = "YV9l97xXmCphM0kLY8IptQ=="


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


__all__ = [
    "InnerSystemEntity",
    "ApplicationEntity",
    "MenuEntity",
    "RoleEntity",
    "TenantEntity",
    "InnerUserEntity",
    "PortalUserEntity",
    "ClusterPlaneEntity",
    "OpenSystemEntity",
    "BasicCodeEntity",
]
