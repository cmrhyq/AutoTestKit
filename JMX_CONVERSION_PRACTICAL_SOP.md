# JMX 转 Python 实操 SOP（以 pvc-pv.jmx 为例）

本文档以 `pvc-pv.jmx` 真实转换过程为例，展示 JMeter 脚本 → Pytest + Allure 用例的完整转换步骤、目录/命名约定与决策过程。所有示例均与仓库现存代码（`base/api/services/*.py`、`tests/api/**/test_*.py`、`config/env_*.yaml`）保持一致。

> 项目栈：Python 3.10+ / pytest 9 / requests / allure-pytest / pytest-xdist / ruff。
> 目标框架：`AutoTestKit`（本仓库）。

---

## 第一阶段：信息收集与分析

### Step 1：读取 JMX 源文件

打开目标 JMX 文件，识别以下关键信息：


| 提取项       | 在 JMX 中的位置                                    | pvc-pv.jmx 实例                                     |
| --------- | --------------------------------------------- | ------------------------------------------------- |
| 测试计划名称    | `<TestPlan testname="...">`                   | PVC(PersistentVolumeClaim) API完成生命周期测试            |
| 用户定义变量    | `<Arguments>` → `<elementProp>`               | cellCode, sysCode, name, pvName, storageClassName |
| HTTP 默认值  | `<ConfigTestElement>`                         | host=${host}, port=${port}, protocol=http         |
| 认证方式      | `<HeaderManager>` → Authorization             | Bearer ${token}                                   |
| 线程组名称     | `<ThreadGroup testname="...">`                | Thread Group - pvc                                |
| HTTP 请求列表 | `<HTTPSamplerProxy>`                          | 7个请求（含条件分支中重复的）                                   |
| 条件分支      | `<IfController>`                              | ec_get_code==2000 / ec_get_code==4004             |
| JSON 提取器  | `<JSONPostProcessor>`                         | $.code → ec_get_code, ec_create_code              |
| 断言        | `<JSONPathAssertion>` / `<ResponseAssertion>` | code==2000, 响应包含 name                             |


### Step 2：梳理接口清单

从 JMX 中提取去重后的 HTTP 接口列表：


| 序号  | 接口名称           | 方法     | 路径                                                                             | 请求体        |
| --- | -------------- | ------ | ------------------------------------------------------------------------------ | ---------- |
| 1   | 查询指定PVC        | GET    | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}`    | 无          |
| 2   | 创建PVC          | POST   | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc`           | K8s PVC 对象 |
| 3   | 删除指定PVC        | DELETE | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}`    | 无          |
| 4   | 查询PVC列表        | GET    | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc`           | 无          |
| 5   | 查询全集群PVC列表     | GET    | `/openapi/elastic-compute/v2/cells/{cellCode}/pvc`                             | 无          |
| 6   | 查询指定PV         | GET    | `/openapi/elastic-compute/v2/cells/{cellCode}/pv/{pvName}`                     | 无          |
| 7   | 查询StorageClass | GET    | `/openapi/elastic-compute/v2/cells/{cellCode}/storageClass/{storageClassName}` | 无          |


### Step 3：分析执行逻辑流

绘制 JMX 条件分支的执行逻辑：

```
查询指定PVC → 提取 code
  ├── code==2000（已存在）: 删除 → 创建 → 等3s → 查列表 → 查全集群列表 → 如创建成功则删除
  └── code==4004（不存在）: 创建 → 等3s → 查列表 → 查全集群列表 → 如创建成功则删除
查询指定PV
查询StorageClass
```

**合并策略**：两个分支的区别仅在于"是否先删除"，合并为：查询 → 若存在先删除 → 创建 → 验证 → 清理。

### Step 4：识别参数并映射到 YAML

检查现有 `config/env_*.yaml` 中是否已有对应参数。**本仓库统一使用 camelCase 作为 yaml key**（与 `env_test.yaml` / `env_bcv25_arm.yaml` 保持一致）。


| JMX 变量           | YAML 参数名           | 是否已存在 | 值（示例）         |
| ---------------- | ------------------ | ----- | ------------- |
| cellCode         | `cellCode`         | 已存在   | test          |
| sysCode          | `sysCode`          | 已存在   | test-sys      |
| name             | `pvcName`          | 已存在   | test-pvc-0001 |
| pvName           | `pvName`           | 已存在   | test-pv-0001  |
| storageClassName | `storageClassName` | 已存在   | nfs-test      |


**硬约束：**

- 所有新增 key 必须**同步写入**每一份 `config/env_*.yaml`（当前至少 `env_test.yaml` / `env_bcv25_arm.yaml`），否则切换环境时会读到 `None`，导致鉴权 / 请求失败。
- 命名统一 **camelCase**（如 `apiBaseUrl`、`nativeXApiKey`、`pvcName`），禁止 snake_case / kebab-case。
- 租户账号信息集中在 yaml 的 `tenants` 字典下：`tenants.<tenant_code>.username / password`。
- 忽略 threads, rampup, duration, testCases, intervalTime 这些参数，不要放入`config/env_*.yaml`

---

## 第二阶段：Service 层编写

### Step 5：确认目标 Service 文件


| 决策点            | 结果                                                    |
| -------------- | ----------------------------------------------------- |
| 属于哪个业务域？       | elastic-compute OpenAPI（Bearer 鉴权）                    |
| 已有 Service 文件？ | `base/api/services/elastic_compute_open_service.py` ✔ |
| 已有 Service 类？  | `ElasticComputeOpenService` ✔                         |
| 需要新建还是追加？      | 在已有类中**追加**方法                                         |


**决策树：**

```
JMX 文件归属哪个 domain？
├── 已有 Service → 检查已有方法是否覆盖接口
│   ├── 已覆盖 → 直接使用，跳到 Step 8
│   └── 未覆盖 → 在已有 Service 中追加方法
└── 没有 Service → 新建 `{Domain}{Type}Service` 类继承 `BaseService`
```

**当前仓库已有 Service 一览（`base/api/services/`）：**


| 文件                                                   | 类                             | 鉴权方式                       |
| ---------------------------------------------------- | ----------------------------- | -------------------------- |
| `portal_open_service.py`                             | `PortalOpenService`           | 登录换 token / Bearer         |
| `portal_inner_service.py`                            | `PortalInnerService`          | X-API-KEY                  |
| `elastic_compute_open_service.py`                    | `ElasticComputeOpenService`   | Bearer（`cache["token"]`）   |
| `elastic_compute_ext_service.py`                     | `ElasticComputeExtService`    | Bearer                     |
| `elastic_compute_native_service.py`                  | `ElasticComputeNativeService` | X-API-KEY（`nativeXApiKey`） |
| `microservices_open_service.py`                      | `MicroservicesOpenService`    | Bearer                     |
| `microservices_inner_service.py`                     | `MicroservicesInnerService`   | X-API-KEY                  |
| `observable_open_service.py`                         | `ObservableOpenService`       | Bearer                     |
| `operation_open_service.py`                          | `OperationOpenService`        | Bearer                     |
| `plugin_open_service.py` / `plugin_inner_service.py` | `Plugin*Service`              | Bearer / X-API-KEY         |


### Step 6：编写 Service 方法

遵循以下模式为每个接口添加方法（与 `elastic_compute_open_service.py` 现有方法风格保持一致）：

```python
from typing import Any, Dict

from base import BaseService
from core import DataCache
from core.log import get_logger

logger = get_logger(__name__)


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头（走 Portal 登录得到的 Bearer Token）。"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class ElasticComputeOpenService(BaseService):

    def get_pvc(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 PVC。

        对应 JMX：弹性计算_openapi_pvc-pv_查询指定pvc
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}

        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: PVC 名称
        """
        logger.info(f"Get PVC: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc/{name}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()
```

**关键规范：**

- 类命名 `{Domain}{Type}Service`（例 `ElasticComputeOpenService`）。
- 方法名 `snake_case`，动词前缀：`get_/list_/create_/update_/patch_/delete_`。
- 每个方法首行 `logger.info(...)` 描述业务动作；docstring 必须包含**对应 JMX 名称**和 **HTTP 方法+路径**，方便与源脚本对照。
- 需要鉴权的接口：`headers=_get_default_headers()`；Native / Inner 接口改用对应的 `_get_default_headers()`（读 `nativeXApiKey` 等）。
- 返回 `response.json()`，类型标注 `Dict[str, Any]`（响应可能是列表时用 `Any`）。
- POST/PUT/PATCH 请求体由调用方传入 `payload: Dict[str, Any]`，**不在 Service 中写死**。
- 路径参数用 f-string 插值：`f"/openapi/.../cells/{cell_code}/..."`。
- 只新增方法，不修改已有方法签名，避免破坏其他用例。
- Service 类顶端建议保留 `DEFAULT_BASE_URL` 常量，构造函数签名统一 `(self, base_url: str = None)`。

### Step 7：处理 POST 请求体

JMX 中的请求体使用 XML 实体编码，需要还原：


| JMX 原始    | 还原后    |
| --------- | ------ |
| `"`       | `"`    |
| `'`       | `'`    |
| `&`       | `&`    |
| `<`       | `<`    |
| `>`       | `>`    |
| `         |        |
| `         | 忽略（\r） |
| `         |        |
| `         | 忽略（\n） |
| `${name}` | 由调用方传参 |


还原后的 JSON 结构提取为测试文件中的 **helper 方法**（如 `_build_pvc_payload`），而非 Service 方法内硬编码。

**实例：**

JMX 原始：

```xml
{

    "apiVersion": "v1",

    "kind": "PersistentVolumeClaim",

    "metadata": {

        "name": "${name}"

    },

    ...
}
```

还原后（写在测试类中）：

```python
@staticmethod
def _build_pvc_payload(name: str, storage_class_name: str) -> Dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": name},
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": "1Gi"}},
            "storageClassName": storage_class_name,
        },
    }
```

---

## 第三阶段：测试层编写

### Step 8：创建测试文件

文件路径规则：`tests/api/{domain}/{api_type?}/test_{模块名}.py`。elastic-compute 领域按 API 类型再分子目录（`openapi/` / `native/` / `extensions/`），其它领域直接放 `{domain}/` 下。


| JMX 路径                                       | 测试文件路径                                                        |
| -------------------------------------------- | ------------------------------------------------------------- |
| `elastic-compute/openapi/pvc-pv.jmx`         | `tests/api/elastic_compute/openapi/test_ec_pvc_pv.py`         |
| `elastic-compute/openapi/Node.jmx`           | `tests/api/elastic_compute/openapi/test_ec_node.py`           |
| `elastic-compute/native/ServiceAccount.jmx`  | `tests/api/elastic_compute/native/test_ec_serviceaccount.py`  |
| `elastic-compute/extensions/application.jmx` | `tests/api/elastic_compute/extensions/test_ec_application.py` |
| `portal/openapi/portal-openapi.jmx`          | `tests/api/portal/test_portal_openapi.py`                     |
| `portal/inner/portal-innerapi.jmx`           | `tests/api/portal/test_portal_innerapi.py`                    |
| `microservices/openapi/istio.jmx`            | `tests/api/microservices/test_microservices_istio.py`         |
| `observable/openapi/log.jmx`                 | `tests/api/observable/test_observable_log.py`                 |
| `operations/openapi/task.jmx`                | `tests/api/operations/test_operations_task.py`                |
| `plugin/openapi/info.jmx`                    | `tests/api/plugin/test_plugin_info.py`                        |


每个新目录需存在 `__init__.py`（当前所有子目录均已就位，直接放文件即可）。

### Step 9：搭建测试类骨架

对齐仓库现有测试类（如 `tests/api/elastic_compute/openapi/test_ec_pvc_pv.py`）：

```python
"""
{模块中文名} 接口测试

转换自 JMeter 脚本: {filename}.jmx
测试内容：{功能点描述}
"""
import json
import time
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper


# 顶部常量抽取（禁止在方法内使用魔法数字）
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004
PVC_CREATE_WAIT_SECONDS = 3


@pytest.mark.api
@pytest.mark.openapi                       # 按业务模块选择：openapi/portal/extension/native/microservice/observable/operation/plugin
@allure.epic("磐基API自动化测试")            # 项目级 epic，所有 API 用例统一
@allure.feature("磐基弹性计算OpenAPI接口")   # 一级业务域
@allure.story("PVC/PV/StorageClass 生命周期接口")  # 二级故事
class TestEcOpenapiPvcPv:
    """
    对应 JMeter 脚本: pvc-pv.jmx
    线程组: Thread Group - pvc
    """

    TENANT = "monitor-group"                # 显式声明本类使用的租户，值必须存在于 yaml.tenants

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env):
        """创建服务实例，base_url 从 yaml 显式传入（camelCase key）。"""
        service = ElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
        )
        yield service
        service.close()
```

**必须项（缺一不可）：**

- 类装饰器四件套：`@pytest.mark.api` + `@pytest.mark.<module>` + `@allure.epic` + `@allure.feature` + `@allure.story`
- `TENANT` 类属性 + `autouse` 的 `_login` fixture（调用 `get_token(self.TENANT)`）
- Service fixture 使用 `yield` + `service.close()`（scope 建议 `class`，全类共用一个 session）
- `base_url=api_env.get("apiBaseUrl")`（**camelCase key**，不要写 `api_base_url`）
- 顶部常量抽取：业务码（`BUSINESS_SUCCESS_CODE = 2000`）、等待时长（`XXX_WAIT_SECONDS`）等

**可用的项目级 fixtures（由 `base/api/fixtures.py` + `tests/api/conftest.py` 提供）：**


| Fixture                  | Scope   | 说明                         |
| ------------------------ | ------- | -------------------------- |
| `api_env`                | session | 当前环境 yaml 全量字典             |
| `api_cache`              | session | `DataCache` 单例，跨用例数据传递     |
| `get_token(tenant_code)` | session | 多租户 token 懒加载工厂，切租户只需再调用一次 |


### Step 10：拆分接口为独立测试函数

**核心原则：每个接口对应一个独立的测试函数**，通过 `@pytest.mark.dependency` 声明依赖关系、`@pytest.mark.order` 保证执行顺序。

JMX 中的 IfController 转换策略：


| JMX 模式        | Python 转换策略                                          | 适用场景          |
| ------------- | ---------------------------------------------------- | ------------- |
| 两分支仅区别"是否先删除" | 第一个测试函数内 if 处理（查询+条件删除）                              | 资源 CRUD 幂等性处理 |
| 独立无依赖的接口      | 拆为独立测试方法                                             | 查询类接口         |
| 创建后验证的等待      | `time.sleep(N)`                                      | 对应 JMX `ConstantTimer` |
| 条件判断后续操作是否执行  | `@pytest.mark.dependency(depends=[...])` 声明前置依赖      | 创建成功才执行后续操作   |


**拆分实例（ConfigMap.jmx，对齐 `test_ec_configmap.py`）：**

首先定义公共参数 fixture，将多个测试函数共用的参数集中提取，避免每个函数重复获取：

```python
@pytest.fixture(scope="class")
def public_params(self, api_env):
    """提取 ConfigMap 测试所需的公共参数。"""
    return {
        "cell_code": api_env.get("cellCode"),
        "sys_code": api_env.get("sysCode"),
        "cm_name": api_env.get("configmapName", "auto-test-probe-cm-test-0001"),
    }
```

然后每个接口对应一个独立测试函数，通过 `public_params` fixture 获取参数：

```python
@pytest.mark.dependency(name="configmap_query_and_cleanup")
@pytest.mark.order(1)
@allure.title("查询指定 ConfigMap")
@allure.description("查询指定 ConfigMap 确认当前状态，若存在则先删除以保证后续创建的幂等性")
@allure.severity(allure.severity_level.CRITICAL)
def test_query_configmap_and_cleanup(self, ec_service, public_params, api_cache):
    """查询指定 ConfigMap，若已存在则删除，确保测试环境干净。"""
    cell_code = public_params["cell_code"]
    sys_code = public_params["sys_code"]
    cm_name = public_params["cm_name"]

    with AllureHelper.api_test(ec_service):
        get_resp = ec_service.get_configmap(
            cell_code=cell_code, sys_code=sys_code, name=cm_name,
        )
        ec_get_code = get_resp.get("code")

        # 断言：接口返回正常（2000=存在，4004=不存在，两者均为正常）
        assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
            f"查询 ConfigMap 返回异常 code: {ec_get_code}, 响应: {get_resp}"
        )

        # 若已存在，先删除以保证幂等
        if ec_get_code == BUSINESS_SUCCESS_CODE:
            del_resp = ec_service.delete_configmap(
                cell_code=cell_code, sys_code=sys_code, name=cm_name,
            )
            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除已存在的 ConfigMap 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

        api_cache.set("ec_configmap_created", False)


@pytest.mark.dependency(name="configmap_create", depends=["configmap_query_and_cleanup"])
@pytest.mark.order(2)
@allure.title("创建 ConfigMap")
@allure.description("创建 ConfigMap 资源，验证返回业务码为 2000")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_configmap(self, ec_service, public_params, api_cache):
    """创建 ConfigMap，断言创建成功。"""
    cell_code = public_params["cell_code"]
    sys_code = public_params["sys_code"]
    cm_name = public_params["cm_name"]

    with AllureHelper.api_test(ec_service):
        create_payload = self._build_configmap_create_payload(cm_name)
        create_resp = ec_service.create_configmap(
            cell_code=cell_code, sys_code=sys_code, payload=create_payload,
        )

        # 断言：业务码为成功
        assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
            f"创建 ConfigMap 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
        )
        # 断言：返回数据中包含 ConfigMap 名称
        resp_str = json.dumps(create_resp, ensure_ascii=False)
        assert cm_name in resp_str, (
            f"创建 ConfigMap 响应中未包含资源名称 {cm_name}, 响应: {create_resp}"
        )

        api_cache.set("ec_configmap_created", True)


@pytest.mark.dependency(name="configmap_list_ns", depends=["configmap_create"])
@pytest.mark.order(3)
@allure.title("查询 Namespace 下 ConfigMap 列表")
@allure.description("查询指定命名空间下的 ConfigMap 列表，验证包含新创建的 ConfigMap")
@allure.severity(allure.severity_level.NORMAL)
def test_list_configmaps_by_namespace(self, ec_service, public_params):
    """查询 Namespace 下 ConfigMap 列表，断言包含目标 cm。"""
    cell_code = public_params["cell_code"]
    sys_code = public_params["sys_code"]
    cm_name = public_params["cm_name"]

    with AllureHelper.api_test(ec_service):
        list_resp = ec_service.list_configmaps_by_ns(
            cell_code=cell_code, sys_code=sys_code,
        )

        # 断言：业务码为成功
        assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
            f"查询 Namespace ConfigMap 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
        )
        # 断言：列表中包含目标 ConfigMap
        resp_str = json.dumps(list_resp, ensure_ascii=False)
        assert cm_name in resp_str, (
            f"Namespace 下 ConfigMap 列表未找到 {cm_name}, 响应: {list_resp}"
        )


@pytest.mark.dependency(name="configmap_put", depends=["configmap_create"])
@pytest.mark.order(4)
@allure.title("PUT 全量更新 ConfigMap")
@allure.description("使用 PUT 方法全量更新 ConfigMap 的 data 字段，验证更新成功")
@allure.severity(allure.severity_level.CRITICAL)
def test_put_update_configmap(self, ec_service, public_params):
    """PUT 全量更新 ConfigMap，断言更新成功。"""
    cell_code = public_params["cell_code"]
    sys_code = public_params["sys_code"]
    cm_name = public_params["cm_name"]

    with AllureHelper.api_test(ec_service):
        put_payload = self._build_configmap_put_payload(cm_name)
        put_resp = ec_service.update_configmap(
            cell_code=cell_code, sys_code=sys_code, name=cm_name,
            payload=put_payload,
        )

        # 断言：业务码为成功
        assert put_resp.get("code") == BUSINESS_SUCCESS_CODE, (
            f"PUT 更新 ConfigMap 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
        )
        # 断言：响应中包含更新后的数据值
        resp_str = json.dumps(put_resp, ensure_ascii=False)
        assert "testput" in resp_str, (
            f"PUT 更新后响应中未包含预期数据 'testput', 响应: {put_resp}"
        )


@pytest.mark.dependency(name="configmap_patch", depends=["configmap_put"])
@pytest.mark.order(5)
@allure.title("PATCH 增量更新 ConfigMap")
@allure.description("使用 PATCH 方法增量更新 ConfigMap 的 labels 和 data 字段，验证更新成功")
@allure.severity(allure.severity_level.CRITICAL)
def test_patch_update_configmap(self, ec_service, public_params):
    """PATCH 增量更新 ConfigMap，断言更新成功。"""
    cell_code = public_params["cell_code"]
    sys_code = public_params["sys_code"]
    cm_name = public_params["cm_name"]

    with AllureHelper.api_test(ec_service):
        patch_payload = self._build_configmap_patch_payload()
        patch_resp = ec_service.patch_configmap(
            cell_code=cell_code, sys_code=sys_code, name=cm_name,
            payload=patch_payload,
        )

        # 断言：业务码为成功
        assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
            f"PATCH 增量更新 ConfigMap 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
        )
        # 断言：响应中包含增量更新后的数据值
        resp_str = json.dumps(patch_resp, ensure_ascii=False)
        assert "test2" in resp_str, (
            f"PATCH 更新后响应中未包含预期数据 'test2', 响应: {patch_resp}"
        )


@pytest.mark.dependency(name="configmap_delete", depends=["configmap_patch"])
@pytest.mark.order(6)
@allure.title("删除 ConfigMap")
@allure.description("删除创建的 ConfigMap 清理测试环境，验证删除成功")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_configmap(self, ec_service, public_params, api_cache):
    """删除 ConfigMap，断言删除成功并清理缓存标记。"""
    cell_code = public_params["cell_code"]
    sys_code = public_params["sys_code"]
    cm_name = public_params["cm_name"]

    with AllureHelper.api_test(ec_service):
        del_resp = ec_service.delete_configmap(
            cell_code=cell_code, sys_code=sys_code, name=cm_name,
        )

        # 断言：业务码为成功
        assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
            f"删除 ConfigMap 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
        )

        api_cache.set("ec_configmap_created", False)


@pytest.mark.dependency(depends=["configmap_delete"])
@pytest.mark.order(7)
@allure.title("验证 ConfigMap 删除后不存在")
@allure.description("删除后再次查询 ConfigMap，验证返回资源不存在")
@allure.severity(allure.severity_level.NORMAL)
def test_verify_configmap_deleted(self, ec_service, public_params):
    """删除后验证 ConfigMap 已不存在。"""
    cell_code = public_params["cell_code"]
    sys_code = public_params["sys_code"]
    cm_name = public_params["cm_name"]

    with AllureHelper.api_test(ec_service):
        get_resp = ec_service.get_configmap(
            cell_code=cell_code, sys_code=sys_code, name=cm_name,
        )

        # 断言：业务码为资源不存在
        assert get_resp.get("code") == RESOURCE_NOT_FOUND_CODE, (
            f"ConfigMap 删除后仍能查询到, code: {get_resp.get('code')}, 响应: {get_resp}"
        )
```

**拆分关键规范：**

- **公共参数 fixture**：定义 `scope="class"` 的参数 fixture（如 `public_params`），将多个函数共用的 `api_env.get(...)` 集中提取一次，各测试函数通过 fixture 注入获取参数，避免重复代码且参数变更只需改一处。
- **env默认值**：`api_env.get(...)`在get的时候需要填入默认值，默认值参考JMX文件
- **每个接口一个函数**：一个 `test_` 函数只调用一个 Service 方法（查询+条件清理可合并在第一个函数中）。
- **`@pytest.mark.order(N)`**：保证执行顺序，N 从 1 开始递增。
- **`@pytest.mark.dependency(name="xxx", depends=["yyy"])`**：声明依赖关系，前置用例失败时后续用例自动 SKIP（不会误报）。
- **完整断言**：每个函数至少断言业务码 `code`，有数据变更的还需断言响应内容（如包含资源名、更新后的值等）。
- **幂等处理**：第一个函数负责"查询 + 若存在则删除"，确保后续创建操作的幂等性。
- **收尾验证**：最后一个函数在删除后再次查询，断言资源确实不存在（`code == 4004`）。

**依赖链示意：**

```
test_query_and_cleanup (order=1)
    └── test_create (order=2, depends=["query_and_cleanup"])
            ├── test_list_by_ns (order=3, depends=["create"])
            ├── test_put_update (order=4, depends=["create"])
            │       └── test_patch_update (order=5, depends=["put"])
            │               └── test_delete (order=6, depends=["patch"])
            │                       └── test_verify_deleted (order=7, depends=["delete"])
```

**与旧方案（单函数）的对比：**

| 维度 | 旧方案（单函数 lifecycle） | 新方案（每接口一函数） |
| --- | --- | --- |
| 失败定位 | 需看 Allure step 才知道哪步失败 | 直接看函数名即知哪个接口失败 |
| 报告粒度 | Allure 只显示 1 条用例 | 每个接口独立显示，通过/失败一目了然 |
| 依赖控制 | 中间失败后续全部不执行（隐式） | `dependency` 显式声明，失败后续自动 SKIP |
| 可维护性 | 函数过长，逻辑嵌套深 | 每个函数职责单一，易读易改 |
| 并行安全 | 不可拆分并行 | 同类内顺序执行，不同类可并行 |

### Step 11：编写测试方法

每个测试方法遵循以下结构（对齐 `test_ec_pvc_pv.py::test_get_pv`）：

```python
@allure.title("中文标题")
@allure.description("一句业务动词描述，补场景/依赖/预期")
@allure.severity(allure.severity_level.CRITICAL)  # 生命周期=CRITICAL，单查=NORMAL
def test_xxx(self, ec_service, api_env, api_cache):
    # 从 api_env 获取参数（camelCase key，禁止硬编码）
    cell_code = api_env.get("cellCode")
    pv_name = api_env.get("pvName")

    with AllureHelper.api_test(ec_service):
        with AllureHelper.step("操作描述"):
            response_json = ec_service.get_pv(
                cell_code=cell_code, pv_name=pv_name,
            )

        with AllureHelper.step("验证响应"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 PV 失败: {response_json}"
            )

        with AllureHelper.step("缓存数据（如有下游依赖）"):
            api_cache.set("some_key", response_json["data"]["id"])
```

**severity 选择：**

- `CRITICAL`：完整生命周期测试（CRUD 全流程）、关键鉴权/数据入口
- `NORMAL`：单个查询、非关键路径接口
- `MINOR`：辅助工具类接口

**变量取值原则：**

- 一律从 `api_env.get("<camelCaseKey>")` 读取，禁止直接写字面量
- 下游依赖数据用 `api_cache.set(key, value)` 传递，另一个用例用 `api_cache.get(key)` 消费
- 断言业务码用顶部常量（`BUSINESS_SUCCESS_CODE` 等），不写魔法数字

#### Step 11.1：@allure.title 编写规范（强制）

**核心原则：一句话业务动词短语，让人 3 秒看懂测什么。**


| 规则  | 说明                                         |
| --- | ------------------------------------------ |
| 长度  | 中文 6–20 字，一句话                              |
| 视角  | 业务/场景（动词开头），不写实现细节                         |
| 内容  | 只写「做什么」，不塞 HTTP 方法、URL、断言细节、参数名            |
| 唯一性 | 同一 class 内 title 唯一；跨 class 允许重名（如生命周期各阶段） |
| 参数化 | 支持 `{param}` 占位符                           |


正例 vs 反例：


| ❌ 不推荐                          | ✅ 推荐            |
| ------------------------------ | --------------- |
| `test_get_user_list`           | `查询用户全量数据`      |
| `GET /portal/api/user/list 成功` | `查询用户全量数据`      |
| `获取用户全量数据接口测试`                 | `查询用户全量数据`      |
| `case_001`                     | `新增用户后可在列表中查询到` |
| `PVC测试`                        | `PVC 完整生命周期测试`  |


参数化用例写法：

```python
@pytest.mark.parametrize("role,expected_count", [
    ("admin", 100),
    ("user", 10),
])
@allure.title("角色为 {role} 的用户查询列表，返回 {expected_count} 条")
def test_query_user_list_by_role(role, expected_count):
    ...
```

#### Step 11.2：@allure.description 编写规范（强制）

**核心原则：一句业务动词描述，补充 title 未表达的场景/前置/预期。**


| 规则         | 说明                                  |
| ---------- | ----------------------------------- |
| 长度         | 中文 8–40 字，一句话；生命周期类可稍长              |
| 内容         | 只写「做什么/预期什么」；**禁止**再写 HTTP 方法 + URL |
| 与 title 关系 | 补充而非重复；不能是 title 的换句话说              |
| 多行         | 除生命周期串联流程外，禁用多行字符串；单行更清晰            |


正例 vs 反例：


| ❌ 不推荐（禁止风格）                                  | ✅ 推荐（本仓库标准风格）    |
| -------------------------------------------- | ---------------- |
| `GET /portal/api/user/list - 验证能够成功获取用户全量数据` | `查询用户全量数据`       |
| `验证接口能否成功`                                   | `查询平台版本信息`       |
| （与 title 完全一致）                               | 补充场景条件、缓存字段、串联步骤 |
| 多行 + HTTP 方法 + URL + 「验证 XXX」                | 一句业务动词描述         |


生命周期/复合流程类允许「箭头串联」描述：

```python
@allure.title("PVC 完整生命周期测试")
@allure.description("覆盖 PVC 的查询、创建、列表、删除完整生命周期")

@allure.title("角色管理（创建/修改/删除）")
@allure.description("完整测试角色CRUD流程：查询 -> 清理 -> 创建 -> 修改 -> 删除")
```

带缓存传递的用例，用 description 提示下游依赖：

```python
@allure.title("查询 Namespace 列表")
@allure.description("查询指定单元下的 Namespace 列表并缓存首条 sysCode")
```

#### Step 11.3：与其他 allure 装饰器的层次关系


| 装饰器                   | 位置  | 内容            | 示例                             |
| --------------------- | --- | ------------- | ------------------------------ |
| `@allure.feature`     | 类级  | 一级业务领域        | `"磐基弹性计算OpenAPI接口"`            |
| `@allure.story`       | 类级  | 二级功能故事        | `"PVC/PV/StorageClass 生命周期接口"` |
| `@allure.title`       | 方法级 | 用例做什么（业务动词）   | `"PVC 完整生命周期测试"`               |
| `@allure.description` | 方法级 | 一句业务描述，补场景/预期 | `"覆盖 PVC 的查询、创建、列表、删除完整生命周期"`  |
| `@allure.severity`    | 方法级 | 严重级别          | `CRITICAL` / `NORMAL`          |


**禁止的组合：**

- 只有 title 没有 description（或反之）
- title 与 description 内容完全一样
- description 里塞 HTTP 方法与 URL（信息重复且过时时维护成本高）
- description 只写「验证接口能否成功」这类空话

### Step 12：映射断言


| JMX 断言类型                                         | Python 断言                                 |
| ------------------------------------------------ | ----------------------------------------- |
| `JSONPathAssertion: $.code == 2000`              | `assert resp.get("code") == 2000`         |
| `ResponseAssertion: test_type=2 (contains)`      | `assert expected in json.dumps(resp)`     |
| `ResponseAssertion: test_type=16 (NOT contains)` | `assert expected not in json.dumps(resp)` |
| `ResponseAssertion: test_type=8 (equals)`        | `assert value == expected`                |
| `ResponseAssertion: response_code == 200`        | 由 `raise_for_status()` 覆盖，无需断言            |


**注意：** JMX 的 `test_type` 字段含义：

- 2 = contains
- 8 = equals
- 16 = NOT（配合其他类型使用，如 2+16=18 表示 not contains）

实际项目中需看 `<intProp name="Assertion.test_type">` 的具体值。本例中 test_type=16 在 `<ResponseAssertion>` 上，结合 `Asserion.test_strings` 中的 `"name":"${name}"`，实际含义是**断言响应数据中不包含该字符串为失败**（即断言包含）。

---

## 第四阶段：验证与收尾

### Step 13：Linter 检查

项目使用 `ruff`（配置在 `pyproject.toml`：`line-length=120`，`target-version=py310`，规则集 `E,F,W,I`）。

```bash
# 静态检查
ruff check base/api/services/elastic_compute_open_service.py
ruff check tests/api/elastic_compute/openapi/test_ec_pvc_pv.py

# 全量检查（新增/修改文件推荐）
ruff check base tests
```

如有格式问题：

```bash
ruff format base/api/services/elastic_compute_open_service.py
ruff format tests/api/elastic_compute/openapi/test_ec_pvc_pv.py
```

### Step 13.5：本地运行验证

```bash
# 单文件运行（先跑一遍，确认能收集+能通过）
pytest tests/api/elastic_compute/openapi/test_ec_pvc_pv.py -v

# 只跑本次新增标记
pytest -m "api and openapi" -v

# 并行 + Allure
pytest tests/api/elastic_compute/openapi/test_ec_pvc_pv.py -n auto --alluredir=report/allure-results
```

期望：所有用例 `PASSED`，无 warning，Allure 报告结构完整（epic/feature/story/title/description 全部渲染）。

### Step 14：核对检查清单

- 测试文件在 `tests/api/<domain>/[<api_type>/]` 目录下，且父目录都有 `__init__.py`
- 文件名格式：`test_{domain_prefix}_{module}.py`（例 `test_ec_pvc_pv.py`）
- 所有参数在**每一份** `config/env_*.yaml` 中都有对应 key（同步！）
- YAML 参数名全部是 **camelCase**（不是 snake_case）
- Service 类为 `{Domain}{Type}Service`，方法名 `snake_case + 动词前缀`
- import 路径正确（`from base.api.services.xxx_service import ...Service`）
- 类装饰器齐全：`@pytest.mark.api` + `@pytest.mark.<module>` + `@allure.epic("磐基API自动化测试")` + `@allure.feature(...)` + `@allure.story(...)`
- 测试类顶部声明 `TENANT = "..."`，值存在于 `yaml.tenants`，并有 `autouse` 的 `_login` fixture
- Service fixture `scope="class"`，用 `yield` + `service.close()`
- Service 构造参数 `base_url=api_env.get("apiBaseUrl")`（**不是** `api_base_url`）
- 每个测试方法有 `@allure.title` + `@allure.description` + `@allure.severity`
- `@allure.title` 一句业务动词短语（6–20 字），不含 HTTP 方法/URL/断言细节
- `@allure.description` 一句业务描述，**不含** HTTP 方法+URL，且**不与 title 完全一致**
- title / description / `def test`_ 三者数量一致
- 测试方法体最外层用 `AllureHelper.api_test(service)` 包裹
- 关键操作用 `AllureHelper.step()` 分段
- Service 方法调用带 `_get_default_headers()`（Bearer / X-API-KEY 按业务域选择）
- 数据依赖通过 `api_cache` 传递
- 断言的是业务字段（`code`），不是 HTTP status（`raise_for_status` 已覆盖）
- 没有硬编码的 URL、账号、明文 token、魔法数字
- 业务码 / 等待时长抽取为**模块顶部常量**（如 `BUSINESS_SUCCESS_CODE = 2000`、`PVC_CREATE_WAIT_SECONDS = 3`）
- JMX 中所有 `HTTPSamplerProxy` 都有对应的测试步骤
- JMX 中的 `JSONPostProcessor` 都有对应的数据提取和缓存
- `@dataclass` 字段末尾无逗号（如果使用了 dataclass）
- `ruff check` 无错误、`pytest` 本地能通过

---

## 快速参考

### 文件产出对照表


| JMX 元素                                | Python 产出                   | 存放位置                                           |
| ------------------------------------- | --------------------------- | ---------------------------------------------- |
| 用户定义变量                                | `env_*.yaml` 参数（camelCase）  | `config/`                                      |
| HTTPSamplerProxy                      | Service 方法                  | `base/api/services/<domain>_<type>_service.py` |
| ThreadGroup                           | 测试类                         | `tests/api/{domain}/[{api_type}/]test_*.py`    |
| IfController                          | if/else 分支                  | 测试方法内                                          |
| JSONPostProcessor                     | `api_cache.set()`           | 测试方法内                                          |
| ResponseAssertion / JSONPathAssertion | `assert` 语句                 | 测试方法内                                          |
| ConstantTimer                         | `time.sleep(常量)`            | 测试方法内                                          |
| HeaderManager + token                 | `_get_default_headers()`    | Service 层自动处理                                  |
| POST body (raw JSON)                  | helper 方法构造 dict            | 测试类的 `@staticmethod`                           |
| Login Sampler                         | `get_token(TENANT)` fixture | `tests/api/conftest.py` 已提供                    |


### 命名约定速查


| 类型            | 格式                                     | 示例                                                                         |
| ------------- | -------------------------------------- | -------------------------------------------------------------------------- |
| Service 文件    | `{domain}_{api_type}_service.py`       | `elastic_compute_open_service.py`                                          |
| Service 类     | `{Domain}{Type}Service`                | `ElasticComputeOpenService`                                                |
| Service 方法    | `{verb}_{resource}`                    | `get_pvc`, `create_pvc`, `list_nodes`                                      |
| 测试目录          | `tests/api/{domain}/[{api_type}/]`     | `tests/api/elastic_compute/openapi/`                                       |
| 测试文件          | `test_{domain_prefix}_{module}.py`     | `test_ec_pvc_pv.py`                                                        |
| 测试类           | `Test{DomainPrefix}{ApiType?}{Module}` | `TestEcOpenapiPvcPv`                                                       |
| 测试方法          | `test_{功能描述}`                          | `test_pvc_lifecycle`, `test_get_pv`                                        |
| YAML 参数       | camelCase 名词短语                         | `pvcName`, `cellCode`, `apiBaseUrl`                                        |
| 顶部常量          | `UPPER_SNAKE_CASE`                     | `BUSINESS_SUCCESS_CODE`, `PVC_CREATE_WAIT_SECONDS`                         |
| pytest marker | `@pytest.mark.api` + 模块 marker         | `openapi/portal/extension/native/microservice/observable/operation/plugin` |


### title / description 一键校验

CR 提交前建议本地跑一次校验，确保每个 `def test_` 都同时具备 `@allure.title` 与 `@allure.description`，且三者数量匹配（脚本会递归扫描 `tests/api/**/test_*.py`，包括 `openapi/native/extensions/` 子目录）：

```bash
python -c "
import os, re
mismatch = []
for r,_,fs in os.walk('tests/api'):
    for f in fs:
        if not f.startswith('test_') or not f.endswith('.py'):
            continue
        p = os.path.join(r, f)
        s = open(p, encoding='utf-8').read()
        n_t = len(re.findall(r'@allure\.title', s))
        n_d = len(re.findall(r'@allure\.description', s))
        n_c = len(re.findall(r'^    def test_', s, flags=re.M))
        if n_t != n_c or n_d != n_c:
            mismatch.append((p, n_c, n_t, n_d))
print('MISMATCH:', mismatch) if mismatch else print('MATCH_OK')
"
```

期望输出：`MATCH_OK`。若出现 `MISMATCH` 列表，按文件补齐缺失装饰器。

### YAML key 覆盖一键校验

新用例落地前，用下面的脚本核对所有 `api_env.get("<key>")` 是否在**每一份** `env_*.yaml` 中都存在：

```bash
python -c "
import os, re, yaml
tests_root = 'tests/api'
config_root = 'config'
used = set()
for r,_,fs in os.walk(tests_root):
    for f in fs:
        if not f.endswith('.py'): continue
        s = open(os.path.join(r,f), encoding='utf-8').read()
        used.update(re.findall(r'api_env\.get\([\"\\'](\w+)[\"\\']', s))
envs = {}
for f in os.listdir(config_root):
    if f.startswith('env_') and f.endswith('.yaml'):
        with open(os.path.join(config_root, f), encoding='utf-8') as fh:
            envs[f] = set((yaml.safe_load(fh) or {}).keys())
missing = {f: sorted(used - keys) for f, keys in envs.items() if used - keys}
print('MISSING:', missing) if missing else print('YAML_OK')
"
```

期望输出：`YAML_OK`。若有 `MISSING`，按文件补齐缺失 key（含默认值）。

### 常见陷阱


| 陷阱                                        | 后果                          | 预防                                      |
| ----------------------------------------- | --------------------------- | --------------------------------------- |
| 遗漏 `_login` fixture                       | 全部请求 401                    | 骨架模板强制包含                                |
| 参数只加了一个 yaml                              | 切环境后 `None` → 401 / 500     | 同步所有 `env_*.yaml`                       |
| YAML key 用 snake_case                     | `api_env.get()` 拿到 `None`   | 统一 camelCase（对齐现有 yaml）                 |
| Service 构造用 `api_env.get("api_base_url")` | base_url = `None`，请求全部失败    | 用 `apiBaseUrl`                          |
| 忘记 `@pytest.mark.<module>` marker         | `-m openapi` 收集不到用例         | 类装饰器 4 件套齐全                             |
| 缺 `@allure.epic`                          | Allure 报告归属层次断裂             | 项目统一 `@allure.epic("磐基API自动化测试")`       |
| POST body 在 Service 中写死                   | 无法参数化测试                     | body 由调用方传入                             |
| 断言 HTTP status 而非业务码                      | `raise_for_status` 已覆盖，冗余断言 | 只断 `response_json["code"]`              |
| 用魔法数字断言（`== 2000`）                        | 语义弱、无法搜索                    | 顶部常量 `BUSINESS_SUCCESS_CODE`            |
| dataclass 字段末尾加逗号                         | 值变成 `tuple`                 | 严格禁止尾逗号                                 |
| 拆分接口但未声明 dependency/order                  | 执行顺序不确定/前置失败后续误报            | 必须加 `@pytest.mark.dependency` + `@pytest.mark.order` |
| JMX `test_type` 理解错误                      | 断言方向反转                      | 查表确认 test_type 含义（2/8/16）               |
| description 塞 HTTP 方法+URL                 | 与 title 重复、URL 变更即失效        | 只写业务动词一句话                               |
| title 塞方法/断言/URL 细节                       | 报告可读性差、语义弱                  | 一句业务动词短语（6–20 字）                        |
| title 与 description 内容一致                  | 信息冗余、无增量                    | description 补场景/依赖/预期                   |
| 缺 title 或 缺 description                   | Allure 报告用例失去可读标题/说明        | 检查清单：三者数量必须相等                           |
| Service 直接调 `requests`，绕过 `BaseService`   | 丢失日志/重试/session 复用          | 一律走 `self.get/post/put/patch/delete`    |
| 测试文件放错目录（少 `openapi/` 子目录）                | 团队约定不一致，难查                  | 严格按 `tests/api/{domain}/{api_type}/`    |
| Service fixture `scope="function"`        | 每个用例重建 session，性能差          | 用 `scope="class"` + `yield` + `close()` |


