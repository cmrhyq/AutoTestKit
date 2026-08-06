# Elastic Compute Extensions 测试重构 SOP

> 将 `tests/api/elastic_compute/extensions/` 下的测试文件按 `tests/api/portal/` 的分层模式进行改造：
> 测试层不再手写 payload dict，公共参数与业务实体统一放到 `base/api/entity/`，
> 请求体构造与字段映射统一收敛到 `base/api/services/*_service.py` 的方法内部。

**适用范围**：`tests/api/elastic_compute/extensions/*.py`（共 20 个测试文件）
**已完成 Pilot**：`test_ec_workload.py`（作为标准范式）
**待改造**：其余 18 个文件（`test_ec_application.py` 已合规，无需改）

---

## 目录

1. [背景与设计目标](#1-背景与设计目标)
2. [分层职责](#2-分层职责)
3. [重构标准流程（每个测试文件 3 步走）](#3-重构标准流程每个测试文件-3-步走)
4. [代码规范与命名约定](#4-代码规范与命名约定)
5. [Pilot 参考实现（test_ec_workload.py）](#5-pilot-参考实现test_ec_workloadpy)
6. [Checklist：单文件完成质量验证](#6-checklist单文件完成质量验证)
7. [剩余待改造文件清单与建议顺序](#7-剩余待改造文件清单与建议顺序)
8. [常见陷阱与解决方案](#8-常见陷阱与解决方案)

---

## 1. 背景与设计目标

### 1.1 问题

改造前，`tests/api/elastic_compute/extensions/` 下的测试文件普遍存在以下问题：

- 测试文件里散落着 `_build_xxx_payload()` / `_build_labels()` 等 **payload 构造 helper**
- `public_params` fixture 返回**无类型 `dict`**，包含 `int` 和 `str` 混合值 → 所有 `public_params["kind"]` 被推断为 `str | int | Any` → IDE 大量 "Expected type 'str', got 'str | int | Any' instead" 警告
- service 层方法签名普遍是 `payload: Dict[str, Any]` → 调用方要自己构造 JSON dict，字段名（camelCase / kebab-case）散落各处

### 1.2 目标（对齐 `tests/api/portal` 的分层模式）

- **测试层**只做：参数收集 → 构造 Entity → 调用 service → 断言业务码
- **`base/api/entity/`**：承载"公共参数集合"与"业务实体 DTO"，全部使用 `@dataclass`，字段类型精确
- **`base/api/services/`**：方法签名接收 Entity 对象，**payload 构造代码直接内联在方法体内**（不使用私有 helper 方法转换）

---

## 2. 分层职责

```
┌──────────────────────────────────────────────────────────────────┐
│  tests/api/elastic_compute/extensions/test_ec_*.py               │
│  ------------------------------------------------------------    │
│  • 只做：public_params fixture、构造 Entity、调用 service、断言 │
│  • 禁止：任何 payload dict、任何 _build_* helper、字典下标访问  │
└──────────────┬───────────────────────────────────────────────────┘
               │ 传入 Entity 对象
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  base/api/services/elastic_compute_ext_service.py                │
│  ------------------------------------------------------------    │
│  • 每个方法内联构造 payload dict（camelCase 字段名）             │
│  • 方法签名接收 Entity / List[Entity]                            │
│  • 禁止：私有 _xxx_to_payload helper（payload 构造要直接内联）  │
└──────────────┬───────────────────────────────────────────────────┘
               │ import
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  base/api/entity/elastic_compute.py                              │
│  ------------------------------------------------------------    │
│  • @dataclass 定义所有 Entity + PublicParams                     │
│  • 字段使用 snake_case，字段类型精确（str / int / List / Dict） │
│  • 提供便捷 classmethod（如 from_public_params）用于跨 Entity   │
│    组合场景                                                       │
│  • 全部导出到 __all__                                             │
└──────────────────────────────────────────────────────────────────┘
```

**关键分工**：
- 字段的 **snake_case ↔ camelCase 转换** 只发生在 service 方法体内
- 测试层永远不知道也不关心 API 契约字段名

---

## 3. 重构标准流程（每个测试文件 3 步走）

针对每个待改造的 `test_ec_xxx.py`，严格按以下顺序执行：

### Step A：盘点原文件

先执行盘点，梳理清楚要改什么：

```
# 1. 找到所有 payload 构造 helper
grep -n "def _build_\|payload\s*=\s*{" tests/api/elastic_compute/extensions/test_ec_xxx.py

# 2. 找到所有 public_params 字典下标访问
grep -n "public_params\[" tests/api/elastic_compute/extensions/test_ec_xxx.py

# 3. 找到所有调用 service 的地方（看现在 payload 参数是什么形状）
grep -n "ec_ext_service\." tests/api/elastic_compute/extensions/test_ec_xxx.py
```

产出一张**改造清单**：
- 需要新增几个 `Entity` dataclass（对应几种不同的 payload 结构）
- 需要新增一个 `XxxPublicParams` dataclass（对应 public_params fixture）
- 需要修改哪些 service 方法签名

### Step B：改 `base/api/entity/elastic_compute.py`（Entity 层）

按盘点结果新增 dataclass：

1. **`XxxPublicParams`**：承载测试公共参数
   - 必填字段（无默认值）：`cluster_id / namespace / name / kind / image / ...` 这类 fixture 必须传的
   - 可选字段（带默认值）：`app_code / paas_env_code / ...` 这类可从 api_env 兜底

2. **`XxxEntity`**：承载业务实体
   - 必填字段：`name / kind / image ...`
   - 可选字段：`replicas: Optional[int] = 1 / labels: Dict[str, str] = field(default_factory=dict)`
   - 如需从 `PublicParams` 快捷构造，加一个 `@classmethod from_public_params(cls, params)` 便捷方法

3. 全部新 Entity 追加进 `__all__`

**dataclass 命名约定**：
- Python 字段一律 `snake_case`（如 `app_code`、`target_port`）
- 不要在 dataclass 里做字段名映射（那是 service 的活）

### Step C：改 `base/api/services/elastic_compute_ext_service.py`（Service 层）

1. 顶部导入新增的 Entity 类：
   ```python
   from base.api.entity.elastic_compute import (
       XxxEntity,
       XxxPatchEntity,
       # ...
   )
   ```

2. 修改方法签名，把 `payload: Dict[str, Any]` 换成 Entity 对象或 `List[Entity]`

3. **在方法体内直接内联构造 payload**（**不要**再抽出 `_xxx_to_payload` 静态 helper！），例如：
   ```python
   def create_workload(
       self, cluster_id: str, namespace: str, kind: str, workload: WorkloadEntity
   ) -> Dict[str, Any]:
       logger.info(f"Create workload: name={workload.name}")
       url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications"
       payload: Dict[str, Any] = {
           "name": workload.name,
           "kind": workload.kind,
           "image": workload.image,
           "appCode": workload.app_code,        # snake_case → camelCase 转换点
           "labels": dict(workload.labels),
       }
       if workload.replicas is not None:
           payload["replicas"] = workload.replicas
       response = self.post(endpoint=url, json=payload, headers=_get_workload_headers())
       return response.json()
   ```

4. 如果多个 batch 方法（batch_create / batch_update）复用同一份 workload 转 dict 的逻辑，**接受轻度重复**，不要抽 helper —— 用户明确要求 payload 构造直接内联

### Step D：改 `tests/api/elastic_compute/extensions/test_ec_xxx.py`（测试层）

按顺序做：

1. **调整 import**：
   ```python
   from base.api.entity.elastic_compute import (
       XxxEntity,
       XxxPublicParams,
       # ...
   )
   ```

2. **删除所有 `_build_*` 静态方法**（整段删掉）

3. **改造 `public_params` fixture**：
   ```python
   @pytest.fixture(scope="class")
   def public_params(self, api_env) -> XxxPublicParams:
       return XxxPublicParams(
           cluster_id=str(api_env.get("clusterId", "1")),
           namespace=api_env.get("namespace", "test-ns"),
           # ...
       )
   ```

4. **批量替换 `public_params["xxx"]` → `public_params.xxx`**（用 StrReplace 的 `replace_all` 逐字段替换）

5. **改造所有 service 调用点**：把 `payload = self._build_xxx(public_params)` 换成构造 Entity：
   ```python
   # 改造前
   payload = self._build_workload_payload(public_params)
   response_json = ec_ext_service.create_workload(..., payload=payload)

   # 改造后
   workload = WorkloadEntity.from_public_params(public_params)
   response_json = ec_ext_service.create_workload(..., workload=workload)
   ```

### Step E：静态验证

```
# 1. 语法检查（3 个文件都要过）
python -c "import ast; ast.parse(open(r'base/api/entity/elastic_compute.py', encoding='utf-8').read())"
python -c "import ast; ast.parse(open(r'base/api/services/elastic_compute_ext_service.py', encoding='utf-8').read())"
python -c "import ast; ast.parse(open(r'tests/api/elastic_compute/extensions/test_ec_xxx.py', encoding='utf-8').read())"

# 2. 确认已无 helper / dict 下标残留
grep -n "_build_\|public_params\[\|payload\s*=\s*self\._build" tests/api/elastic_compute/extensions/test_ec_xxx.py
# 应该：No matches found

# 3. Entity 构造 smoke test（用 exec 绕过项目依赖）
python -c "src = open(r'base/api/entity/elastic_compute.py', encoding='utf-8').read(); ns = {}; exec(compile(src, 'e.py', 'exec'), ns); print(ns['XxxEntity'](name='x', ...))"

# 4. 有 pytest 环境时，做一次 collect-only
python -m pytest tests/api/elastic_compute/extensions/test_ec_xxx.py --collect-only -q
```

---

## 4. 代码规范与命名约定

### 4.1 Entity 命名

| 用途 | 命名规范 | 示例 |
|------|---------|------|
| 测试公共参数 | `<Feature>PublicParams` | `WorkloadPublicParams`、`HelmChartPublicParams` |
| 完整业务实体 | `<Resource>Entity` | `WorkloadEntity`、`HelmChartEntity` |
| 子结构（嵌套） | `<Resource><Field>Entity` | `WorkloadServicePortEntity` |
| PATCH 增量更新 | `<Resource>PatchEntity` | `WorkloadPatchEntity` |
| 操作型（仅 kind+name） | 复用完整 Entity，service 内部只挑字段 |

### 4.2 dataclass 编写规则

```python
@dataclass
class SomeEntity(object):
    """
    简明的一行 docstring 说明这个 Entity 对应什么 API。

    Attributes:
        name: xxx
        kind: xxx
        ...
    """

    # 必填字段（无默认值）优先声明
    name: str
    kind: str

    # 可选字段（带默认值）在后
    replicas: Optional[int] = 1
    labels: Dict[str, str] = field(default_factory=dict)

    # 便捷构造（可选）
    @classmethod
    def from_public_params(cls, params: "SomePublicParams") -> "SomeEntity":
        return cls(name=params.name, ...)
```

**要点**：
- 类型注解**精确**：`str` 就是 `str`，不写 `Any`；`Optional[int]` 表示允许 None
- **可变默认值**必须用 `field(default_factory=...)`（`dict / list`）
- **顺序**：必填字段（无 default）在前，可选字段在后（dataclass 语法强制要求）

### 4.3 Service 方法编写规则

```python
def create_xxx(
    self,
    # 路径 / 查询参数（str/int）保持不变
    cluster_id: str,
    namespace: str,
    # payload 参数改为 Entity 对象
    xxx: XxxEntity,
) -> Dict[str, Any]:
    """docstring。对应 JMX：xxx。POST /path"""
    logger.info(f"Create xxx: name={xxx.name}")
    url = f"/xxx/{cluster_id}/{namespace}"
    # payload 构造直接内联（严禁抽 _xxx_to_payload helper）
    payload: Dict[str, Any] = {
        "name": xxx.name,
        "appCode": xxx.app_code,  # snake_case → camelCase 就在这里转
    }
    response = self.post(endpoint=url, json=payload, headers=_get_xxx_headers())
    return response.json()
```

**要点**：
- payload 内联，**不抽 helper**
- 字段名映射（`app_code` → `appCode`、`target_port` → `targetPort`）在方法体内完成
- 条件字段用 `if xxx.field is not None: payload["field"] = xxx.field`

### 4.4 测试文件编写规则

```python
class TestEcExtensionsXxx:
    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env):
        service = ElasticComputeExtService(base_url=api_env.get("apiInnerBaseUrl"))
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> XxxPublicParams:
        return XxxPublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            # ...
        )

    def test_create_xxx(self, ec_ext_service, public_params):
        with AllureHelper.api_test(ec_ext_service):
            xxx = XxxEntity.from_public_params(public_params)
            response_json = ec_ext_service.create_xxx(
                cluster_id=public_params.cluster_id,
                namespace=public_params.namespace,
                xxx=xxx,
            )
            assert response_json.get("code") == ApiCode.SUCCESS
```

**禁止**：
- ❌ 测试文件里出现任何 `_build_` 前缀的方法
- ❌ 测试文件里出现任何 `payload = {...}` 字典字面量
- ❌ `public_params["xxx"]` 字典下标访问（必须用属性访问 `public_params.xxx`）
- ❌ 把 `dict` 直接传给 service 的 `xxx: XxxEntity` 参数

---

## 5. Pilot 参考实现（test_ec_workload.py）

已完成的 Pilot 涵盖了几乎所有常见场景，可作为**标准范式**参考。

### 5.1 涉及的 Entity（在 `base/api/entity/elastic_compute.py`）

| Entity | 用途 |
|--------|------|
| `WorkloadPublicParams` | Workload 测试的 15 个公共参数（cluster/namespace/name/kind/image + paas-* 标签字段） |
| `WorkloadEntity` | Workload create/update/batch payload 实体，含 `from_public_params()` 便捷方法 |
| `WorkloadServicePortEntity` | Service 端口子结构（port / target_port / protocol） |
| `WorkloadServiceEntity` | Workload 关联 Service payload 实体 |
| `WorkloadPatchEntity` | PATCH 增量更新 payload（labels-only） |

### 5.2 涉及的 Service 方法改造（`elastic_compute_ext_service.py`）

| 方法 | 参数改造前 | 参数改造后 |
|------|-----------|-----------|
| `create_workload` | `payload: Dict[str, Any]` | `workload: WorkloadEntity` |
| `update_workload` | `payload: Dict[str, Any]` | `workload: WorkloadEntity` |
| `patch_workload` | `payload: Dict[str, Any]` | `patch: WorkloadPatchEntity` |
| `update_workload_services` | `payload: Dict[str, Any]` | `services: List[WorkloadServiceEntity]` |
| `batch_create_workloads` | `payload: Dict[str, Any]` | `workloads: List[WorkloadEntity]` |
| `batch_update_workloads` | `payload: Dict[str, Any]` | `workloads: List[WorkloadEntity]` |
| `batch_delete_workloads` | `payload: Dict[str, Any]` | `workloads: List[WorkloadEntity]` |
| `batch_stop_workloads` | `payload: Dict[str, Any]` | `workloads: List[WorkloadEntity]` |
| `batch_start_workloads` | `payload: Dict[str, Any]` | `workloads: List[WorkloadEntity]` |

**注意**：service 内部 payload 全部**内联构造**，不使用私有 helper（曾经存在的 `_workload_to_full_payload / _workload_to_action_payload / _service_to_payload` 已在后续 iteration 里删掉）。

### 5.3 测试文件改造效果

改造前：567 行（含 5 个 `_build_*` helper 约 60 行）
改造后：503 行（无任何 helper，无任何 payload dict 字面量，无任何字典下标）

---

## 6. Checklist：单文件完成质量验证

每个测试文件改完后，逐项打勾确认：

### 6.1 Entity 层（`base/api/entity/elastic_compute.py`）
- [ ] 新增的 dataclass 全部加入 `__all__`
- [ ] 所有字段类型精确（无 `Any`，无裸 `dict`/`list`）
- [ ] 可变默认值使用 `field(default_factory=...)`
- [ ] 若跨 Entity 组合，提供 `@classmethod from_public_params(...)` 便捷方法
- [ ] 语法检查通过：`python -c "import ast; ast.parse(open(...).read())"`

### 6.2 Service 层（`base/api/services/elastic_compute_ext_service.py`）
- [ ] 顶部已从 entity 层导入所有用到的 Entity 类
- [ ] 所有 `payload: Dict[str, Any]` 签名已替换为 Entity 参数
- [ ] payload 构造代码**内联**在方法体内（未新增 `_xxx_to_payload` 私有 helper）
- [ ] snake_case → camelCase 字段映射准确（重点检查 `appCode / targetPort / etc.`）
- [ ] 条件字段（如 `replicas` 可 None）用 `if x is not None:` 分支保护
- [ ] 语法检查通过

### 6.3 测试层（`tests/api/elastic_compute/extensions/test_ec_xxx.py`）
- [ ] 所有 `_build_*` 静态方法已删除
- [ ] `public_params` fixture 返回 `XxxPublicParams` dataclass
- [ ] 所有 `public_params["xxx"]` 已替换为 `public_params.xxx`
  - 验证：`grep -n 'public_params\[' test_ec_xxx.py` 应该 no matches
- [ ] 所有 service 调用点不再传 `payload=dict`，而是传 Entity 对象
  - 验证：`grep -n 'payload\s*=' test_ec_xxx.py` 应该 no matches
- [ ] import 顺序：allure/pytest → base.api.entity → base.api.services → core
- [ ] 语法检查通过
- [ ] 有环境时，`pytest --collect-only` 通过

### 6.4 Entity 构造 smoke test（推荐）

用 exec 绕过项目依赖，快速验证 dataclass 构造不会崩：

```
python -c "src = open(r'base/api/entity/elastic_compute.py', encoding='utf-8').read(); ns = {}; exec(compile(src, 'e.py', 'exec'), ns); XxxEntity = ns['XxxEntity']; print(XxxEntity(name='test', ...))"
```

---

## 7. 剩余待改造文件清单与建议顺序

| # | 文件 | 行数 | 优先级 | 复杂度预估 |
|---|------|------|--------|-----------|
| 1 | `test_ec_workload.py` | 552 | ✅ 已完成（Pilot） | - |
| 2 | `test_ec_application.py` | 46 | ✅ 已合规（纯 GET） | - |
| 3 | `test_ec_helm_chart.py` | 555 | 🔴 高 | 大（Helm 完整生命周期） |
| 4 | `test_ec_partitions_api.py` | 291 | 🔴 高 | 中（ResourceQuota / LimitRange） |
| 5 | `test_ec_custom_resource_v1.py` | 226 | 🔴 高 | 中 |
| 6 | `test_ec_tenant_quota.py` | 175 | 🟡 中 | 中 |
| 7 | `test_ec_physical_host.py` | 168 | 🟡 中 | 中 |
| 8 | `test_ec_resource_collector.py` | 141 | 🟡 中 | 中 |
| 9 | `test_ec_namespace_quota.py` | 133 | 🟡 中 | 中 |
| 10 | `test_ec_nginx_rbac.py` | 125 | 🟡 中 | 中 |
| 11 | `test_ec_system_bind.py` | 103 | 🟢 低 | 小 |
| 12 | `test_ec_cluster_manager.py` | 95 | 🟢 低 | 小 |
| 13 | `test_ec_app_grant.py` | 86 | 🟢 低 | 小 |
| 14 | `test_ec_dashboard.py` | 73 | 🟢 低 | 小 |
| 15 | `test_ec_node.py` | 60 | 🟢 低 | 小 |
| 16 | `test_ec_harbor_bind_cluster.py` | 59 | 🟢 低 | 小 |
| 17 | `test_ec_image_api.py` | 54 | 🟢 低 | 小 |
| 18 | `test_ec_fuzzy_query.py` | 52 | 🟢 低 | 小 |
| 19 | `test_ec_endpoints.py` | 49 | 🟢 低 | 小 |
| 20 | `test_ec_host_bind.py` | 48 | 🟢 低 | 小 |

**推荐批次**：
- **批次 1（大文件优先）**：3, 4, 5
- **批次 2（中等文件）**：6, 7, 8, 9, 10
- **批次 3（收尾小文件）**：11–20

**并行执行提示**：如果条件允许，可以让多个 Subagent 并行处理不同的测试文件（每个 Subagent 只改自己那一个测试文件 + 增加自己需要的 Entity），最后由主 Agent 统一合并 `elastic_compute.py` 的 `__all__` 与 service 层的 import。

---

## 8. 常见陷阱与解决方案

### 8.1 陷阱：dataclass 字段顺序

**错误示例**：
```python
@dataclass
class Foo:
    replicas: int = 1
    name: str          # ❌ SyntaxError: non-default argument follows default argument
```

**正确写法**：无默认值的字段全部放前面：
```python
@dataclass
class Foo:
    name: str
    replicas: int = 1
```

### 8.2 陷阱：可变默认值

**错误示例**：
```python
@dataclass
class Foo:
    labels: Dict[str, str] = {}    # ❌ ValueError: mutable default
    ports: List[int] = []
```

**正确写法**：
```python
@dataclass
class Foo:
    labels: Dict[str, str] = field(default_factory=dict)
    ports: List[int] = field(default_factory=list)
```

### 8.3 陷阱：`public_params["kind"]` 中的 f-string 双引号冲突

改造前测试文件里可能存在：
```python
api_cache.set(f"workload_pod_name_{public_params["kind"]}", pod_name)
                                                 ^^^^^^^^ f-string 内部同名双引号
```

改造后必须变成属性访问，问题自动消失：
```python
api_cache.set(f"workload_pod_name_{public_params.kind}", pod_name)
```

### 8.4 陷阱：Entity `from_public_params()` 里丢字段

写完 `from_public_params()` 一定要**逐字段对比**原来的 `_build_xxx_payload()`，确保字段完全一致。可以通过 Entity smoke test 打印 `labels.keys()` 与原 `_build_labels()` 输出对拍：

```
# 改造前：_build_workload_labels 产出 14 个 key
# 改造后：WorkloadEntity.from_public_params 应产出同样 14 个 key
python -c "src = open(r'base/api/entity/elastic_compute.py', encoding='utf-8').read(); ns = {}; exec(compile(src, 'e.py', 'exec'), ns); WP=ns['WorkloadPublicParams']; WE=ns['WorkloadEntity']; p=WP(cluster_id='1', namespace='ns', cell_code='c', sys_code='s', name='n', kind='Deployment', image='i'); w=WE.from_public_params(p); print(sorted(w.labels.keys()), len(w.labels))"
```

### 8.5 陷阱：service 里内联的 payload dict 忘做字段名映射

因为 Python 侧是 `snake_case`（`app_code`），K8s / API 侧是 `camelCase`（`appCode`）。**内联时容易写成 `"app_code": xxx.app_code`**，请对照 JMX 原始 body 逐字段核对。

常见字段名映射：
| Python (Entity) | JSON payload |
|-----------------|--------------|
| `app_code` | `appCode` |
| `target_port` | `targetPort` |
| `paas_owner` | `paas-owner` (kebab-case, K8s labels 场景) |
| `role_code` | `roleCode` |
| `system_id` | `systemId` |

### 8.6 陷阱：批量方法 payload 结构差异

同一批量方法内 `workloads` 可能有两种 payload 形态：
- **完整**（`batch_create / batch_update`）：需要 name / kind / image / appCode / labels / replicas
- **精简**（`batch_stop / batch_start / batch_delete`）：只要 kind / name

用户明确要求 payload 内联，两种形态各自在方法体内写自己的 dict 字面量，**接受少量重复代码**：

```python
# batch_create
workload_list = []
for w in workloads:
    item = {"name": w.name, "kind": w.kind, "image": w.image, "appCode": w.app_code, "labels": dict(w.labels)}
    if w.replicas is not None:
        item["replicas"] = w.replicas
    workload_list.append(item)
payload = {"workloadList": workload_list}

# batch_stop（精简）
payload = {"workloadList": [{"kind": w.kind, "name": w.name} for w in workloads]}
```

### 8.7 陷阱：`from typing import TypedDict` 遗留

如果之前用过 TypedDict，改成 dataclass 后要把顶部的 `from typing import TypedDict` 一并删掉，否则会有 unused import lint 警告。

### 8.8 陷阱：service 层新增 Entity 导入后未添加 `List`

如果 service 方法签名新用到 `List[XxxEntity]`，记得 `from typing import ..., List`。

---

## 附录 A：openapi 系补充（与 extensions 系并存）

本 SOP 最初为 `tests/api/elastic_compute/extensions/` 编写，`tests/api/elastic_compute/openapi/`
后续按同样的分层原则完成了完整改造，但由于 API 契约差异，登记了以下三条补充约定：

### A.1 Entity 模块物理隔离

- openapi 系 Entity **不再**加入 `base/api/entity/elastic_compute.py`，改为独立文件
  `base/api/entity/elastic_compute_openapi.py`。
- 理由：openapi 侧接口使用 K8s 原生 spec 风格（`apiVersion` / `metadata` / `spec` / ...），
  而 extensions 侧是磐基自定义扁平结构；同名的 `WorkloadPublicParams` / `WorkloadEntity`
  在两个 module 中含义完全不同。物理隔离可避免同名冲突，也让 Entity 语义清晰对齐所属域。

### A.2 命名前缀约定

- 承载 K8s 原生 spec 的实体统一带 `K8s` 前缀：`K8sConfigMapEntity`、`K8sPodEntity`、
  `K8sServiceEntity`、`K8sLimitRangeEntity` …
- 无 K8s spec 语义、纯 openapi 业务的实体保持普通命名：`HarborProjectEntity`、
  `HelmInstallEntity`、`TenantQuotaAllocationEntity`、`WorkloadCreateEntity` …
- 每个测试类 `public_params` fixture 的强类型返回体统一命名为 `XxxPublicParams`，即使
  该测试文件的接口无入参也保留占位 dataclass（如 `ClusterPublicParams` / `NamespacePublicParams`
  / `OidcHarborInitPublicParams` / `ResourceCollectionPublicParams`）以保持 SOP 契约一致。

### A.3 Service 层单文件与内联 payload

- `base/api/services/elastic_compute_open_service.py` 保持**单文件**（当前 ~4000 行），
  各资源域通过顶层注释块 `# ==================== XxxV2 ====================` 分区。
- 每个改造后的方法签名接收 Entity（或必要时接收 `List[XxxEntity]`），并在方法体内内联完成
  snake_case → camelCase 的 payload 构造；测试层禁止再引用 `payload=...` 显式字典入参。
- 对 K8s spec 中的固定字段（如 `apiVersion: apps/v1`、`containerName: container0`、
  `containerPort: 8080/8090/8010/8020` 等 JMX 硬编码值）由 service 层内联写死，Entity
  只承载业务可变字段。

### A.4 完成状态

- 完成时间：2026-08-06
- 覆盖：32 个测试文件（openapi 目录全量）
- 静态验证：`python -m py_compile` 全部通过；
  `rg 'def _build_|self\._build_|public_params\['` 结果为 0。
- Entity 总数：72（含 extensions + openapi）。

---

**最后**：改完每个文件后，请把改动记录追加到 git commit message，格式建议：

```
refactor(ec-ext): migrate test_ec_xxx.py to entity-based service signature

- Add XxxEntity / XxxPublicParams to base/api/entity/elastic_compute.py
- Inline payload construction into elastic_compute_ext_service.py methods
  (create_xxx / update_xxx / batch_xxx)
- Remove _build_* helpers and public_params dict-subscript access from
  tests/api/elastic_compute/extensions/test_ec_xxx.py

Aligns test_ec_xxx.py with the api/portal layering pattern.
See ELASTIC_COMPUTE_EXTENSIONS_REFACTOR_SOP.md.
```




