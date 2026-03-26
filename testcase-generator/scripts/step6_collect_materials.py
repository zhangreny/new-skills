#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
from typing import Optional


MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mkd", ".mkdn", ".mdx"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".svg"}
IGNORED_FILE_NAMES = {"input_manifest.json"}
GENERATED_OUTPUT_FILE_NAMES = {
    "step6_product_context.md",
    "step7_test_blueprint.md",
    "step8_combination_expansion.md",
    "step9_rule_gate_report.md",
    "step9_ui_cases_review.md",
    "step9_ui_cases_final.md",
    "step6_dimension_breakdown.md",
    "step7_combination_expansion.md",
    "step8_rule_gate_report.md",
    "step8_ui_cases_review.md",
    "step8_ui_cases_final.md",
}

PRODUCT_PATTERNS = {
    "lb": [
        r"负载均衡",
        r"\bLB\b",
        r"\bLBI\b",
        r"\bLBG\b",
        r"虚拟服务",
        r"服务器池",
        r"部署 Everoute 服务",
        r"启用 LB",
        r"LB 实例",
    ],
    "vpc": [
        r"\bVPC\b",
        r"子网",
        r"边缘网关",
        r"浮动 IP",
        r"对等连接",
        r"路由表",
        r"安全服务",
        r"VPC 网络",
        r"VPC 子网",
    ],
    "ops": [
        r"运维",
        r"部署 Everoute 服务",
        r"启用 LB",
        r"\bER\b",
        r"集群",
        r"节点",
        r"仲裁",
        r"系统服务",
    ],
    "dfw": [
        r"\bDFW\b",
        r"分布式防火墙",
        r"安全组",
        r"隔离策略",
        r"安全策略",
    ],
}

PRODUCT_DOC_RULES = {
    "lb": {
        "management": "*网络负载均衡器管理指南*",
        "whitepaper": "*网络负载均衡器技术白皮书*",
    },
    "vpc": {
        "management": "*虚拟专有云网络管理指南*",
        "whitepaper": "*虚拟专有云网络技术白皮书*",
    },
    "dfw": {
        "management": "*分布式防火墙管理指南*",
        "whitepaper": "*分布式防火墙技术白皮书*",
    },
}

SHARED_DOCS = {
    "glossary": "*术语表*",
    "release": "*发布说明*",
    "install": "*安装与升级指南*",
}

RESOURCE_PATTERNS = [
    ("版本资源", [r"版本", r"发布", r"升级", r"兼容", r"\bER ?\d", r"CloudTower"]),
    ("环境资源", [r"集群", r"节点", r"双活", r"跨集群", r"仲裁", r"机房"]),
    ("对象资源", [r"详情", r"列表", r"创建", r"编辑", r"删除", r"tab", r"section"]),
    ("网络资源", [r"VPC", r"子网", r"VLAN", r"TEP", r"VIP", r"LIP", r"网络组", r"FullNAT", r"DNAT", r"通信"]),
    ("关联资源", [r"关联", r"解绑", r"过滤", r"删除限制", r"引用", r"下一跳"]),
    ("权限资源", [r"权限", r"只读", r"可编辑", r"可操作", r"不可操作"]),
    ("审计资源", [r"事件审计", r"任务", r"审计"]),
    ("文案资源", [r"文案", r"提示", r"报错", r"tooltip", r"note"]),
    ("许可资源", [r"许可", r"license", r"vCPU", r"CPU", r"socket", r"插槽", r"额度", r"过期"]),
]


def collect_files(root: Path, suffixes: set[str]) -> tuple[list[str], list[str]]:
    files: list[str] = []
    ignored_generated: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in GENERATED_OUTPUT_FILE_NAMES:
            ignored_generated.append(str(path.resolve()))
            continue
        if path.name in IGNORED_FILE_NAMES:
            continue
        if path.suffix.lower() not in suffixes:
            continue
        files.append(str(path.resolve()))
    return files, ignored_generated


def read_preview_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            lines = path.read_text(encoding=encoding).splitlines()[:200]
            return "\n".join(lines)
        except UnicodeDecodeError:
            continue
    return ""


def match_patterns(text: str, patterns: list[str]) -> list[str]:
    matched: list[str] = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE) and pattern not in matched:
            matched.append(pattern)
    return matched


def add_reason(bucket: dict[str, dict], name: str, weight: int, reason: str) -> None:
    info = bucket.setdefault(name, {"score": 0, "reasons": []})
    info["score"] += weight
    if reason not in info["reasons"]:
        info["reasons"].append(reason)


def convert_doc_info(path: Path, category: str, reason: str, priority: int) -> dict:
    return {
        "path": str(path.resolve()),
        "name": path.name,
        "category": category,
        "reason": reason,
        "priority": priority,
    }


def first_matching_doc(paths: list[Path], pattern: str) -> Optional[Path]:
    for path in paths:
        if path.match(pattern):
            return path
    return None


def build_resource_type_hints(text: str, product_candidates: list[dict]) -> list[dict]:
    hints: list[dict] = []
    seen: set[str] = set()

    for resource_name, patterns in RESOURCE_PATTERNS:
        matched = match_patterns(text, patterns)
        if not matched:
            continue
        seen.add(resource_name)
        hints.append(
            {
                "resource_type": resource_name,
                "scope": "common",
                "reason": f"材料命中资源关键词：{', '.join(matched[:4])}",
            }
        )

    product_names = {item["product"] for item in product_candidates}
    if "dfw" in product_names and "许可资源" in seen:
        hints.append(
            {
                "resource_type": "DFW 许可资源",
                "scope": "dfw",
                "reason": "DFW 场景下应区分关联集群许可与策略对象/VM 许可。",
            }
        )
    if "lb" in product_names and "许可资源" in seen:
        hints.append(
            {
                "resource_type": "LB 许可资源",
                "scope": "lb",
                "reason": "LB 场景下应区分按 vCPU 与按 CPU 插槽、许可类型、额度状态与消耗/归还动作。",
            }
        )
    if "vpc" in product_names and ("许可资源" in seen or "网络资源" in seen):
        hints.append(
            {
                "resource_type": "VPC 资源与许可资源",
                "scope": "vpc",
                "reason": "VPC 场景下应保留关联集群许可、对象资源、过滤范围、删除限制和引用状态。",
            }
        )

    return hints


def build_golden_reference_candidates(text: str, product_candidates: list[dict], skill_root: Path) -> list[dict]:
    product_names = {item["product"] for item in product_candidates}
    signals: list[str] = []
    signal_patterns = [
        ("主产品包含 LB", r"\bLB\b|负载均衡|LBI|LBG|虚拟服务"),
        ("补充产品包含 VPC", r"\bVPC\b|子网|网络组|所属 VPC"),
        ("出现支持 VPC", r"支持 VPC"),
        ("出现网络类型分支", r"VLAN|FullNAT|DNAT|vpc-vpc|vlan-vpc"),
        ("出现通信方向", r"与客户端通信|与服务端通信|与服务器池通信"),
        ("出现主备关系", r"主备|主实例|备实例"),
        ("出现对象簇", r"部署 Everoute 服务|启用 LB|LBI|LBG|虚拟服务"),
    ]
    for label, pattern in signal_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            signals.append(label)

    candidates: list[dict] = []
    if "lb" in product_names and "vpc" in product_names and len(signals) >= 4:
        golden_path = (
            skill_root
            / "references"
            / "UI-former-testcase-analyse"
            / "Everoute"
            / "负载均衡"
            / "LBG & LB 支持 VPC"
            / "测试用例-LBG & LB 支持 VPC.md"
        )
        candidates.append(
            {
                "name": "LBG & LB 支持 VPC",
                "path": str(golden_path.resolve()),
                "recommended": True,
                "reason": "当前材料同时命中 LB、VPC、支持 VPC、网络类型、通信方向和主备关系等高相似信号。",
                "similarity_signals": signals,
                "default_relative_range": "0.8x-1.2x",
            }
        )
    return candidates


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/step6_collect_materials.py <workdir>")
        sys.exit(1)

    workdir = Path(sys.argv[1]).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print(json.dumps({"ok": False, "error": f"workdir not found: {workdir}"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    script_root = Path(__file__).resolve().parent
    skill_root = script_root.parent
    references_root = skill_root / "references"
    smartx_root = references_root / "UI-former-testcase-analyse" / "Everoute-SmartX-docs"
    everoute_root = references_root / "UI-former-testcase-analyse" / "Everoute"

    markdown_files, ignored_markdown = collect_files(workdir, MARKDOWN_SUFFIXES)
    image_files, ignored_images = collect_files(workdir, IMAGE_SUFFIXES)

    product_scores: dict[str, dict] = {}
    aggregate_chunks: list[str] = []

    for raw_path in markdown_files:
        path = Path(raw_path)
        preview = read_preview_text(path)
        text = f"{path}\n{preview}"
        aggregate_chunks.append(text)
        for product, patterns in PRODUCT_PATTERNS.items():
            matched = match_patterns(text, patterns)
            if matched:
                add_reason(product_scores, product, len(matched) * 3, f"markdown 命中 {product}: {path.name}")

    for raw_path in image_files:
        path = Path(raw_path)
        text = str(path)
        aggregate_chunks.append(text)
        for product, patterns in PRODUCT_PATTERNS.items():
            matched = match_patterns(text, patterns)
            if matched:
                add_reason(product_scores, product, len(matched), f"图片文件名命中 {product}: {path.name}")

    product_candidates = [
        {"product": product, "score": info["score"], "reasons": info["reasons"]}
        for product, info in sorted(product_scores.items(), key=lambda item: item[1]["score"], reverse=True)
    ]

    aggregate_text = "\n".join(aggregate_chunks)
    needs_version_notes = bool(re.search(r"版本|发布|升级|兼容|3\.\d|4\.\d|5\.\d|6\.\d", aggregate_text))
    needs_install_guide = bool(re.search(r"部署|启用|安装|升级|迁移", aggregate_text))

    smartx_docs = sorted(smartx_root.glob("*.md")) if smartx_root.is_dir() else []
    smartx_doc_candidates: list[dict] = []
    for candidate in product_candidates:
        product = candidate["product"]
        if product not in PRODUCT_DOC_RULES:
            continue
        rule = PRODUCT_DOC_RULES[product]
        management = first_matching_doc(smartx_docs, rule["management"])
        whitepaper = first_matching_doc(smartx_docs, rule["whitepaper"])
        if management is not None:
            smartx_doc_candidates.append(convert_doc_info(management, "management-guide", f"{product} 候选产品优先读取同产品管理指南", 10))
        if whitepaper is not None:
            smartx_doc_candidates.append(convert_doc_info(whitepaper, "whitepaper", f"{product} 候选产品优先读取同产品技术白皮书", 9))

    glossary = first_matching_doc(smartx_docs, SHARED_DOCS["glossary"])
    if glossary is not None:
        smartx_doc_candidates.append(convert_doc_info(glossary, "glossary", "术语表用于统一需求文档、设计稿和历史用例中的产品名词", 6))

    if needs_version_notes:
        release = first_matching_doc(smartx_docs, SHARED_DOCS["release"])
        if release is not None:
            smartx_doc_candidates.append(convert_doc_info(release, "release-note", "材料中出现版本、发布或兼容差异，需要读取发布说明校准版本边界", 7))

    if needs_install_guide:
        install = first_matching_doc(smartx_docs, SHARED_DOCS["install"])
        if install is not None:
            smartx_doc_candidates.append(convert_doc_info(install, "install-upgrade-guide", "材料中出现部署、启用、安装或升级语义，需要读取安装与升级指南辅助理解", 5))

    unique_doc_candidates: list[dict] = []
    seen_doc_paths: set[str] = set()
    for item in sorted(smartx_doc_candidates, key=lambda doc: (-doc["priority"], doc["name"])):
        if item["path"] in seen_doc_paths:
            continue
        seen_doc_paths.add(item["path"])
        unique_doc_candidates.append(item)

    effective_rule_files = {
        "common": [],
        "products": {},
    }
    common_rule = everoute_root / "everoute_common_testcase_rules.md"
    if common_rule.is_file():
        effective_rule_files["common"].append(str(common_rule.resolve()))
    product_rule_candidates = {
        "ops": everoute_root / "Everoute 服务运维" / "everoute_ops_testcase_rules.md",
        "dfw": everoute_root / "分布式防火墙" / "everoute_dfw_testcase_rules.md",
        "vpc": everoute_root / "虚拟专有云网络" / "everoute_vpc_testcase_rules.md",
        "lb": everoute_root / "负载均衡" / "everoute_lb_testcase_rules.md",
    }
    for name, path in product_rule_candidates.items():
        if path.is_file():
            effective_rule_files["products"][name] = str(path.resolve())

    resource_type_hints = build_resource_type_hints(aggregate_text, product_candidates)
    golden_reference_candidates = build_golden_reference_candidates(aggregate_text, product_candidates, skill_root)

    result = {
        "workdir": str(workdir),
        "markdown_files": markdown_files,
        "image_files": image_files,
        "ignored_generated_files": sorted(set(ignored_markdown + ignored_images)),
        "markdown_count": len(markdown_files),
        "image_count": len(image_files),
        "total_material_count": len(markdown_files) + len(image_files),
        "should_generate_product_context": bool(markdown_files or image_files),
        "product_candidates": product_candidates,
        "smartx_doc_candidates": unique_doc_candidates,
        "smartx_doc_selection_hints": [
            "优先选择与主产品一致的管理指南和技术白皮书。",
            "术语表默认可用，用于统一产品对象、网络模式和命名。",
            "只有在材料出现版本、发布或兼容差异时，才将发布说明纳入 Step6。",
            "只有在材料出现部署、启用、安装或升级语义时，才将安装与升级指南纳入 Step6。",
        ],
        "effective_rule_files": effective_rule_files,
        "resource_type_hints": resource_type_hints,
        "golden_reference_candidates": golden_reference_candidates,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
