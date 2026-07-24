# JMX 转 Python 实操 SOP（以 pvc-pv.jmx 为例）

本文档是 `JMX_TO_PYTHON_SOP.md`（规范文档）的实操补充，以 `pvc-pv.jmx` 真实转换过程为例，展示完整的转换步骤和决策过程。

---

## 第一阶段：信息收集与分析

### Step 1：读取 JMX 源文件

打开目标 JMX 文件，识别以下关键信息：

| 提取项 | 在 JMX 中的位置 | pvc-pv.jmx 实例 |
|--------|----------------|-----------------|
| 测试计划名称 | `<TestPlan testname="...">` | PVC(PersistentVolumeClaim) API完成生命周期测试 |
| 用户定义变量 | `<Arguments>` → `<elementProp>` | cellCode, sysCode, name, pvName, storageClassName |
| HTTP 默认值 | `<ConfigTestElement>` | host=${host}, port=${port}, protocol=http |
| 认证方式 | `<HeaderManager>` → Authorization | Bearer ${token} |
| 线程组名称 | `<ThreadGroup testname="...">` | Thread Group - pvc |
| HTTP 请求列表 | `<HTTPSamplerProxy>` | 7个请求（含条件分支中重复的） |
| 条件分支 | `<IfController>` | ec_get_code==2000 / ec_get_code==4004 |
| JSON 提取器 | `<JSONPostProcessor>` | $.code → ec_get_code, ec_create_code |
| 断言 | `<JSONPathAssertion>` / `<ResponseAssertion>` | code==2000, 响应包含 name |

### Step 2：梳理接口清单

从 JMX 中提取去重后的 HTTP 接口列表：

| 序号 | 接口名称 | 方法 | 路径 | 请求体 |
|------|---------|------|------|--------|
| 1 | 查询指定PVC | GET | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}` | 无 |
| 2 | 创建PVC | POST | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc` | K8s PVC 对象 |
| 3 | 删除指定PVC | DELETE | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}` | 无 |
| 4 | 查询PVC列表 | GET | `/openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc` | 无 |
| 5 | 查询全集群PVC列表 | GET | `/openapi/elastic-compute/v2/cells/{cellCode}/pvc` | 无 |
| 6 | 查询指定PV | GET | `/openapi/elastic-compute/v2/cells/{cellCode}/pv/{pvName}` | 无 |
| 7 | 查询StorageClass | GET | `/openapi/elastic-compute/v2/cells/{cellCode}/storageClass/{storageClassName}` | 无 |

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

检查现有 `config/env_*.yaml` 中是否已有对应参数：

| JMX 变量 | YAML 参数名 | 是否已存在 | 值（示例） |
|----------|-----------|-----------|-----------|
| cellCode | `ec_cell_code` | 已存在 | TEST |
| sysCode | `ec_sys_code` | 已存在 | test-admin |
| name | `ec_pvc_name` | 已存在 | test-hpa-001 |
| pvName | `ec_pv_name` | 已存在 | test-pv-001 |
| storageClassName | `ec_storage_class_name` | 已存在 | test-sc-001 |

如果有新参数，需同步写入**所有** `env_*.yaml` 文件（硬约束）。

---

## 第二阶段：Service 层编写

### Step 5：确认目标 Service 文件

| 决策点 | 结果 |
|--------|------|
| 属于哪个业务域？ | elastic-compute OpenAPI |
| 已有 Service 文件？ | `elastic_compute_open_service.py` ✔ |
| 需要新建还是追加？ | 追加方法 |

**决策树：**

```
JMX 文件归属哪个 domain？
├── 已有 Service → 检查已有方法是否覆盖接口
│   ├── 已覆盖 → 直接使用，跳到 Step 8
│   └── 未覆盖 → 在已有 Service 中追加方法
└── 没有 Service → 创建新的 Service 类继承 BaseService
```

### Step 6：编写 Service 方法

遵循以下模式为每个接口添加方法：

```python
def method_name(self, param1: str, ...) -> Dict[str, Any]:
    """
    中文功能描述。

    对应 JMX：弹性计算_openapi_pvc-pv_{接口中文名}
    {HTTP方法} {路径模板}

    Args:
        param1: 参数说明
    """
    self.logger.info(f"操作描述: {param1}")
    url = f"/openapi/elastic-compute/v2/..."
    response = self.get(endpoint=url, headers=_get_default_headers())
    return response.json()
```

**关键规范：**

- 方法名 `snake_case`，动词前缀（get/create/delete/list/update/patch）
- 带 `_get_default_headers()` 做鉴权（免鉴权接口除外）
- 返回 `response.json()` 的 `Dict[str, Any]`
- POST 请求体由调用方传入（`payload: Dict[str, Any]`），不在 Service 中写死
- 路径参数用 f-string 插值
- 不修改已有方法签名，只新增方法

### Step 7：处理 POST 请求体

JMX 中的请求体使用 XML 实体编码，需要还原：

| JMX 原始 | 还原后 |
|---------|--------|
| `&quot;` | `"` |
| `&apos;` | `'` |
| `&amp;` | `&` |
| `&lt;` | `<` |
| `&gt;` | `>` |
| `&#xd;` | 忽略（\r） |
| `&#xa;` | 忽略（\n） |
| `${name}` | 由调用方传参 |

还原后的 JSON 结构提取为测试文件中的 **helper 方法**（如 `_build_pvc_payload`），而非 Service 方法内硬编码。

**实例：**

JMX 原始：
```xml
{&#xd;
    &quot;apiVersion&quot;: &quot;v1&quot;,&#xd;
    &quot;kind&quot;: &quot;PersistentVolumeClaim&quot;,&#xd;
    &quot;metadata&quot;: {&#xd;
        &quot;name&quot;: &quot;${name}&quot;&#xd;
    },&#xd;
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

文件路径规则：`tests/api/{domain}/test_{jmx文件名去横线}.py`

| JMX 路径 | 测试文件路径 |
|---------|------------|
| `elastic-compute/openapi/pvc-pv.jmx` | `tests/api/elastic_compute/test_ec_openapi_pvc_pv.py` |
| `elastic-compute/openapi/Node.jmx` | `tests/api/elastic_compute/test_ec_openapi_node.py` |
| `portal/openapi/portal-openapi.jmx` | `tests/api/portal/test_portal_openapi.py` |

### Step 9：搭建测试类骨架

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

from base.api.services.xxx_service import XxxService
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("{模块名}")
@allure.story("{JMX 对应的测试故事}")
class TestXxx:
    """
    对应 JMeter 脚本: {filename}.jmx
    线程组: {线程组名称}
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 env yaml 显式传入。"""
        service = XxxService(
            base_url=api_env.get("api_base_url"),
            logger=api_logger,
        )
        yield service
        service.close()
```

**必须项（缺一不可）：**
- `TENANT` 类属性
- `_login` autouse fixture
- service fixture 使用 `yield` + `service.close()`

### Step 10：处理条件分支逻辑

JMX 中的 IfController 转换策略：

| JMX 模式 | Python 转换策略 | 适用场景 |
|----------|----------------|---------|
| 两分支仅区别"是否先删除" | 合并为一个方法内 if/else | 资源 CRUD 幂等性处理 |
| 独立无依赖的接口 | 拆为独立测试方法 | 查询类接口 |
| 创建后验证的等待 | `time.sleep(N)` | 对应 JMX `ConstantTimer` |
| 条件判断后续操作是否执行 | if 语句包裹后续调用 | 创建成功才删除 |

**合并实例（pvc-pv.jmx）：**

```python
def test_pvc_lifecycle(self, ec_service, api_env, api_cache):
    with AllureHelper.api_test(ec_service):
        # Step 1: 查询当前状态
        with AllureHelper.step("查询指定 PVC 确认当前状态"):
            response_json = ec_service.get_pvc(...)
            ec_get_code = response_json.get("code")

        # Step 2: 若已存在，先删除（对应 IfController code==2000）
        if ec_get_code == 2000:
            with AllureHelper.step("PVC 已存在，先删除"):
                ec_service.delete_pvc(...)

        # Step 3: 创建（两个分支共同操作）
        with AllureHelper.step("创建 PVC"):
            create_resp = ec_service.create_pvc(...)
            assert create_resp.get("code") == 2000

        # Step 4: 等待（对应 ConstantTimer 3000ms）
        time.sleep(3)

        # Step 5: 验证
        with AllureHelper.step("查询列表验证"):
            list_resp = ec_service.list_pvc(...)

        # Step 6: 清理（对应内层 IfController ec_create_code==2000）
        with AllureHelper.step("删除创建的 PVC"):
            ec_service.delete_pvc(...)
```

### Step 11：编写测试方法

每个测试方法遵循以下结构：

```python
@allure.title("中文标题")
@allure.description("HTTP方法 路径 - 验证描述")
@allure.severity(allure.severity_level.CRITICAL)  # 生命周期=CRITICAL，单查=NORMAL
def test_xxx(self, ec_service, api_env, api_cache):
    # 从 api_env 获取参数（禁止硬编码）
    param = api_env.get("param_name")

    with AllureHelper.api_test(ec_service):
        with AllureHelper.step("操作描述"):
            response_json = ec_service.some_method(param)

        with AllureHelper.step("验证响应"):
            assert response_json.get("code") == 2000, f"失败: {response_json}"

        with AllureHelper.step("缓存数据（如有下游依赖）"):
            api_cache.set("some_key", response_json["data"]["id"])
```

**severity 选择：**
- `CRITICAL`：完整生命周期测试（CRUD 全流程）
- `NORMAL`：单个查询接口

### Step 12：映射断言

| JMX 断言类型 | Python 断言 |
|-------------|------------|
| `JSONPathAssertion: $.code == 2000` | `assert resp.get("code") == 2000` |
| `ResponseAssertion: test_type=2 (contains)` | `assert expected in json.dumps(resp)` |
| `ResponseAssertion: test_type=16 (NOT contains)` | `assert expected not in json.dumps(resp)` |
| `ResponseAssertion: test_type=8 (equals)` | `assert value == expected` |
| `ResponseAssertion: response_code == 200` | 由 `raise_for_status()` 覆盖，无需断言 |

**注意：** JMX 的 `test_type` 字段含义：
- 2 = contains
- 8 = equals
- 16 = NOT（配合其他类型使用，如 2+16=18 表示 not contains）

实际项目中需看 `<intProp name="Assertion.test_type">` 的具体值。本例中 test_type=16 在 `<ResponseAssertion>` 上，结合 `Asserion.test_strings` 中的 `"name":"${name}"`，实际含义是**断言响应数据中不包含该字符串为失败**（即断言包含）。

---

## 第四阶段：验证与收尾

### Step 13：Linter 检查

```bash
ruff check base/api/services/elastic_compute_open_service.py
ruff check tests/api/elastic_compute/test_ec_pvc_pv.py
```

确保无错误。如有格式问题：

```bash
ruff format base/api/services/elastic_compute_open_service.py
ruff format tests/api/elastic_compute/test_ec_pvc_pv.py
```

### Step 14：核对检查清单

- [ ] 测试文件在 `tests/api/<domain>/` 目录下
- [ ] 文件名格式：`test_{模块名}.py`
- [ ] 所有参数在**每一份** `config/env_*.yaml` 中都有对应 key
- [ ] YAML 参数名全部是 snake_case
- [ ] import 路径正确（`from base.api.services.xxx import ...`）
- [ ] 类装饰器包含 `@pytest.mark.api`、`@allure.feature`、`@allure.story`
- [ ] 测试类顶部声明 `TENANT = "..."`，并有 `autouse` 的 `_login` fixture
- [ ] 每个测试方法有 `@allure.title`、`@allure.description`、`@allure.severity`
- [ ] 测试方法体最外层用 `AllureHelper.api_test(service)` 包裹
- [ ] 关键操作用 `AllureHelper.step()` 分段
- [ ] Service 方法调用带 `_get_default_headers()`
- [ ] 数据依赖通过 `api_cache` 传递
- [ ] 断言的是业务字段（`code`），不是 HTTP status
- [ ] 没有硬编码的 URL、账号、明文 token
- [ ] Service fixture 使用 `yield` + `service.close()`
- [ ] `@dataclass` 字段末尾无逗号（如果使用了 dataclass）
- [ ] JMX 中所有 `HTTPSamplerProxy` 都有对应的测试步骤
- [ ] JMX 中的 `JSONPostProcessor` 逻辑都有对应的数据提取和缓存
- [ ] 常量抽取到模块顶部（如 `BUSINESS_SUCCESS_CODE = 2000`）

---

## 快速参考

### 文件产出对照表

| JMX 元素 | Python 产出 | 存放位置 |
|----------|-----------|---------|
| 用户定义变量 | `env_*.yaml` 参数 | `config/` |
| HTTPSamplerProxy | Service 方法 | `base/api/services/` |
| ThreadGroup | 测试类 | `tests/api/{domain}/` |
| IfController | if/else 分支 | 测试方法内 |
| JSONPostProcessor | `api_cache.set()` | 测试方法内 |
| ResponseAssertion / JSONPathAssertion | `assert` 语句 | 测试方法内 |
| ConstantTimer | `time.sleep()` | 测试方法内 |
| HeaderManager + token | `_get_default_headers()` | Service 层自动处理 |
| POST body (raw JSON) | helper 方法构造 dict | 测试类的 `@staticmethod` |

### 命名约定速查

| 类型 | 格式 | 示例 |
|------|------|------|
| Service 文件 | `{domain}_{api_type}_service.py` | `elastic_compute_open_service.py` |
| Service 类 | `PanJi{Domain}{Type}Service` | `PanJiElasticComputeOpenService` |
| Service 方法 | `{verb}_{resource}` | `get_pvc`, `create_pvc`, `list_nodes` |
| 测试文件 | `test_{domain}_{api_type}_{module}.py` | `test_ec_openapi_pvc_pv.py` |
| 测试类 | `Test{Domain}{Module}` | `TestEcOpenapiPvcPv` |
| 测试方法 | `test_{功能描述}` | `test_pvc_lifecycle`, `test_get_pv` |
| YAML 参数 | `{domain_prefix}_{resource}_{field}` | `ec_pvc_name`, `ec_cell_code` |

### 常见陷阱

| 陷阱 | 后果 | 预防 |
|------|------|------|
| 遗漏 `_login` fixture | 全部请求 401 | 骨架模板强制包含 |
| 参数只加了一个 yaml | 切环境后 None → 401 | 同步所有 env_*.yaml |
| POST body 在 Service 中写死 | 无法参数化测试 | body 由调用方传入 |
| 断言 HTTP status 而非业务码 | raise_for_status 已覆盖 | 只断 response_json["code"] |
| dataclass 字段末尾加逗号 | 值变成 tuple | 严格禁止尾逗号 |
| 条件分支拆成独立测试方法 | 丢失上下文/顺序依赖 | CRUD 生命周期合并为一个方法 |
| JMX test_type 理解错误 | 断言方向反转 | 查表确认 test_type 含义 |
