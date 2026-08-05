"""一次性迁移脚本：将散落的公共常量集中到 core.constants。

覆盖：
1. HTTP 状态码本地常量：
   - HTTP_OK = 200 / HTTP_CREATED = 201 / HTTP_NOT_FOUND = 404 / HTTP_STATUS_OK = 200
   → HttpStatus.OK / HttpStatus.CREATED / HttpStatus.NOT_FOUND / HttpStatus.OK
2. 类内租户字符串：
   - TENANT = "tenant_admin" → TENANT = Tenant.ADMIN
   - TENANT = "monitor-group" → TENANT = Tenant.MONITOR_GROUP
   （模块级 TENANT = "..." 也一并处理）
3. 各类等待秒数常量：
   - POD_CREATE_WAIT_SECONDS / POD_WAIT_SECONDS / WORKLOAD_WAIT_SECONDS
   - PVC_CREATE_WAIT_SECONDS / IMAGEPULLSECRET_WAIT_SECONDS
   - CR_CREATE_WAIT_SECONDS / DS_CREATE_WAIT_SECONDS
   → Timing.<XXX>
4. Harbor / Helm / Cluster / Secret 域内常量：
   - HARBOR_DEFAULT_PAGE / HARBOR_DEFAULT_PAGE_SIZE / HARBOR_REPLICATION_SPEED_UNLIMITED
     → HarborConst.DEFAULT_PAGE / DEFAULT_PAGE_SIZE / REPLICATION_SPEED_UNLIMITED
   - DEFAULT_ROLLBACK_REVISION / RESOURCE_CONFLICT_MSG
     → HelmConst.DEFAULT_ROLLBACK_REVISION / RESOURCE_CONFLICT_MSG
   - STANDARD_CLUSTER_FLAG / HOST_CLUSTER_FLAG → ClusterFlag.STANDARD / HOST
   - DEFAULT_SECRET_NAME → SecretConst.DEFAULT_IMAGE_PULL_SECRET_NAME

策略：
- 使用 regex 逐行处理；行首缩进敏感（避免误伤字符串内容）。
- 完成后自动补齐 import；已有导入则合并（避免重复）。
- 删除孤立的分组注释（对应常量被删后剩下的行首中文注释）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
TESTS_ROOT = ROOT / "tests" / "api"


HTTP_MAP = {
    "HTTP_OK": "HttpStatus.OK",
    "HTTP_CREATED": "HttpStatus.CREATED",
    "HTTP_NOT_FOUND": "HttpStatus.NOT_FOUND",
    "HTTP_STATUS_OK": "HttpStatus.OK",
}
TIMING_MAP = {
    "POD_CREATE_WAIT_SECONDS": "Timing.POD_CREATE_WAIT_SECONDS",
    "POD_WAIT_SECONDS": "Timing.POD_WAIT_SECONDS",
    "WORKLOAD_WAIT_SECONDS": "Timing.WORKLOAD_WAIT_SECONDS",
    "PVC_CREATE_WAIT_SECONDS": "Timing.PVC_CREATE_WAIT_SECONDS",
    "IMAGEPULLSECRET_WAIT_SECONDS": "Timing.IMAGEPULLSECRET_WAIT_SECONDS",
    "CR_CREATE_WAIT_SECONDS": "Timing.CR_CREATE_WAIT_SECONDS",
    "DS_CREATE_WAIT_SECONDS": "Timing.DS_CREATE_WAIT_SECONDS",
}
HARBOR_MAP = {
    "HARBOR_DEFAULT_PAGE": "HarborConst.DEFAULT_PAGE",
    "HARBOR_DEFAULT_PAGE_SIZE": "HarborConst.DEFAULT_PAGE_SIZE",
    "HARBOR_REPLICATION_SPEED_UNLIMITED": "HarborConst.REPLICATION_SPEED_UNLIMITED",
}
HELM_MAP = {
    "DEFAULT_ROLLBACK_REVISION": "HelmConst.DEFAULT_ROLLBACK_REVISION",
    "RESOURCE_CONFLICT_MSG": "HelmConst.RESOURCE_CONFLICT_MSG",
}
CLUSTER_MAP = {
    "STANDARD_CLUSTER_FLAG": "ClusterFlag.STANDARD",
    "HOST_CLUSTER_FLAG": "ClusterFlag.HOST",
}
SECRET_MAP = {
    "DEFAULT_SECRET_NAME": "SecretConst.DEFAULT_IMAGE_PULL_SECRET_NAME",
}

# 所有会被删除声明的常量名（用于识别本地声明行）
ALL_NAMES = (
    list(HTTP_MAP.keys())
    + list(TIMING_MAP.keys())
    + list(HARBOR_MAP.keys())
    + list(HELM_MAP.keys())
    + list(CLUSTER_MAP.keys())
    + list(SECRET_MAP.keys())
)

# 匹配 “模块级”常量声明（无缩进 + NAME = 数字/字符串）
DECL_RE = re.compile(
    r"^(?P<name>" + "|".join(re.escape(n) for n in ALL_NAMES) + r")\s*=\s*.+$"
)

# 匹配注释行（用于清理孤立分组注释）
COMMENT_RE = re.compile(r"^\s*#")

# 类内 TENANT 属性行
TENANT_LINE_RE = re.compile(
    r'^(?P<indent>\s+)TENANT\s*=\s*"(?P<val>tenant_admin|monitor-group)"\s*$'
)
# 模块级 TENANT 常量（如果有）
TENANT_MOD_RE = re.compile(
    r'^TENANT\s*=\s*"(?P<val>tenant_admin|monitor-group)"\s*$'
)

TENANT_TO_ENUM = {
    "tenant_admin": "Tenant.ADMIN",
    "monitor-group": "Tenant.MONITOR_GROUP",
}


def replace_references(line: str, mapping: dict[str, str]) -> str:
    """在同一行中，用 \b 边界安全地把 old_name 替换成 new_name。"""
    for old, new in mapping.items():
        line = re.sub(rf"\b{re.escape(old)}\b", new, line)
    return line


def process_file(path: Path) -> bool:  # noqa: C901 - migration script, complexity acceptable
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=False)

    used_http = False
    used_timing = False
    used_harbor = False
    used_helm = False
    used_cluster = False
    used_secret = False
    used_tenant = False

    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        m_decl = DECL_RE.match(line)
        if m_decl:
            # 丢弃这一整行；如果紧邻的下一行是空行，则一并丢弃（避免留下双空行）；
            # 若前一行是孤立分组注释（且再前一行是空行/文件头），也把该注释删除。
            if out and COMMENT_RE.match(out[-1] or ""):
                # 只有当上一行是紧贴的注释块首（且不是代码行）时才删
                # 简化处理：如果上一行是注释且再上一行是空行或文件开头，就删
                if len(out) <= 1 or (out[-2].strip() == ""):
                    out.pop()
            i += 1
            # 跳过紧邻的空行
            while i < len(lines) and lines[i].strip() == "":
                # 只跳一个空行以保留段落
                out_next_nonempty = next(
                    (ln for ln in lines[i + 1:] if ln.strip() != ""),
                    None,
                )
                # 如果再下面还有声明，则不留空行；否则保留一个
                if out_next_nonempty and DECL_RE.match(out_next_nonempty):
                    i += 1
                    continue
                break
            continue

        # 类内 TENANT
        m_tenant_cls = TENANT_LINE_RE.match(line)
        if m_tenant_cls:
            enum_ref = TENANT_TO_ENUM[m_tenant_cls.group("val")]
            line = f'{m_tenant_cls.group("indent")}TENANT = {enum_ref}'
            used_tenant = True
            out.append(line)
            i += 1
            continue

        # 模块级 TENANT
        m_tenant_mod = TENANT_MOD_RE.match(line)
        if m_tenant_mod:
            enum_ref = TENANT_TO_ENUM[m_tenant_mod.group("val")]
            line = f"TENANT = {enum_ref}"
            used_tenant = True
            out.append(line)
            i += 1
            continue

        # 引用替换（记录用到了哪些常量）
        new_line = line
        for name in HTTP_MAP:
            if re.search(rf"\b{re.escape(name)}\b", new_line):
                used_http = True
        new_line = replace_references(new_line, HTTP_MAP)

        for name in TIMING_MAP:
            if re.search(rf"\b{re.escape(name)}\b", new_line):
                used_timing = True
        new_line = replace_references(new_line, TIMING_MAP)

        for name in HARBOR_MAP:
            if re.search(rf"\b{re.escape(name)}\b", new_line):
                used_harbor = True
        new_line = replace_references(new_line, HARBOR_MAP)

        for name in HELM_MAP:
            if re.search(rf"\b{re.escape(name)}\b", new_line):
                used_helm = True
        new_line = replace_references(new_line, HELM_MAP)

        for name in CLUSTER_MAP:
            if re.search(rf"\b{re.escape(name)}\b", new_line):
                used_cluster = True
        new_line = replace_references(new_line, CLUSTER_MAP)

        for name in SECRET_MAP:
            if re.search(rf"\b{re.escape(name)}\b", new_line):
                used_secret = True
        new_line = replace_references(new_line, SECRET_MAP)

        out.append(new_line)
        i += 1

    # 决定要导入的名字
    to_import: list[str] = []
    if used_http:
        to_import.append("HttpStatus")
    if used_timing:
        to_import.append("Timing")
    if used_harbor:
        to_import.append("HarborConst")
    if used_helm:
        to_import.append("HelmConst")
    if used_cluster:
        to_import.append("ClusterFlag")
    if used_secret:
        to_import.append("SecretConst")
    if used_tenant:
        to_import.append("Tenant")

    if not to_import:
        # 检查是否有 TENANT 类属性用到了 Tenant 枚举但没被上面识别（保险）
        # 若无变化则不改文件
        if "\n".join(out) == original.rstrip("\n"):
            return False

    if to_import:
        out = _ensure_import(out, to_import)

    new_text = "\n".join(out)
    if not new_text.endswith("\n"):
        new_text += "\n"

    if new_text == original:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def _ensure_import(lines: list[str], to_import: Iterable[str]) -> list[str]:
    """在 lines 中确保存在 `from core.constants import ...` 且包含所需名字。

    - 若已存在 ``from core.constants import ...`` 行，合并名字并按字母序排序。
    - 同时归并旧写法 ``from core.constants.api_codes import ApiCode``
      为统一的 ``from core.constants import ApiCode, ...``（保持单点风格）。
    - 否则在最合适位置（文件顶部注释/docstring 之后、其他 import 之后）插入一行。
    """
    to_import_set = set(to_import)
    existing_idx: int | None = None
    existing_names: set[str] = set()
    api_codes_idx: int | None = None

    import_re = re.compile(r"^from core\.constants import (?P<names>[^#\n]+?)\s*$")
    api_codes_re = re.compile(r"^from core\.constants\.api_codes import ApiCode\s*$")

    for idx, line in enumerate(lines):
        m = import_re.match(line)
        if m and existing_idx is None:
            existing_idx = idx
            existing_names = {n.strip() for n in m.group("names").split(",") if n.strip()}
            continue
        if api_codes_re.match(line) and api_codes_idx is None:
            api_codes_idx = idx

    if api_codes_idx is not None:
        to_import_set.add("ApiCode")

    merged = sorted(existing_names | to_import_set)
    new_import_line = f"from core.constants import {', '.join(merged)}"

    if existing_idx is not None:
        lines[existing_idx] = new_import_line
        if api_codes_idx is not None and api_codes_idx != existing_idx:
            # 删除旧的 api_codes 独立导入
            del lines[api_codes_idx]
        return lines

    if api_codes_idx is not None:
        lines[api_codes_idx] = new_import_line
        return lines

    # 插入位置：找到最后一个 import / from ... import 行，插到其后
    last_import_idx = -1
    for idx, line in enumerate(lines):
        if re.match(r"^\s*(import\s+\S|from\s+\S+\s+import\s+\S)", line):
            last_import_idx = idx

    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, new_import_line)
    else:
        insert_at = 0
        if lines and (lines[0].startswith('"""') or lines[0].startswith("'''")):
            quote = lines[0][:3]
            if lines[0].count(quote) >= 2:
                insert_at = 1
            else:
                for j in range(1, len(lines)):
                    if quote in lines[j]:
                        insert_at = j + 1
                        break
        lines.insert(insert_at, new_import_line)
        if insert_at + 1 < len(lines) and lines[insert_at + 1].strip():
            lines.insert(insert_at + 1, "")
    return lines


def main() -> None:
    targets: list[Path] = sorted(TESTS_ROOT.rglob("*.py"))
    changed_files: list[Path] = []
    for p in targets:
        if p.name == "__init__.py":
            continue
        if process_file(p):
            changed_files.append(p)

    print(f"changed {len(changed_files)} files")
    for p in changed_files:
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
