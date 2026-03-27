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
    "step10_case_split_report.md",
    "step10_ui_cases_final.md",
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
        r"服务器池组",
        r"启用 LB",
        r"LB 实例",
        r"LB 实例组",
    ],
    "vpc": [
        r"\bVPC\b",
        r"子网",
        r"边缘网关",
        r"边缘网关组",
        r"浮动 IP",
        r"对等连接",
        r"路由表",
        r"安全服务",
        r"VPC 网络",
        r"VPC 子网",
        r"外部子网",
        r"TEP IP",
    ],
    "ops": [
        r"运维",
        r"部署 Everoute 服务",
        r"ER 设置",
        r"\bER\b",
        r"Controller",
        r"controller",
        r"集群",
        r"节点",
        r"仲裁",
        r"系统服务",
        r"管理网络",
        r"工作节点",
    ],
    "dfw": [
        r"\bDFW\b",
        r"分布式防火墙",
        r"安全组",
        r"隔离策略",
        r"安全策略",
        r"放行策略",
        r"拒绝策略",
        r"命中计数",
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

PRODUCT_KNOWLEDGE_FILES = {
    "lb": ("负载均衡", "everoute_lb_product_knowledge.md"),
    "vpc": ("虚拟专有云网络", "everoute_vpc_product_knowledge.md"),
    "ops": ("Everoute 服务运维", "everoute_ops_product_knowledge.md"),
    "dfw": ("分布式防火墙", "everoute_dfw_product_knowledge.md"),
}

SHARED_DOCS = {
    "glossary": "*术语表*",
    "release": "*发布说明*",
    "install": "*安装与升级指南*",
}

OPS_SIGNAL_PATTERNS = {
    "controller": r"Controller|controller|工作节点|仲裁节点|替换节点",
    "cluster": r"跨集群|双活|所属集群|可用域|节点数量",
    "license": r"许可|物理 CPU|CPU 插槽|socket|扩容|额度",
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
    if "ops" in product_names and ("版本资源" in seen or "环境资源" in seen or "许可资源" in seen):
        hints.append(
            {
                "resource_type": "运维版本与部署资源",
                "scope": "ops",
                "reason": "运维场景下应同时保留 ER/Tower 版本、集群类型、节点关系和许可结果。",
            }
        )

    return hints


def build_product_knowledge_candidates(product_candidates: list[dict], everoute_root: Path) -> list[dict]:
    candidates: list[dict] = []
    for candidate in product_candidates:
        product = candidate["product"]
        config = PRODUCT_KNOWLEDGE_FILES.get(product)
        if config is None:
            continue
        directory_name, filename = config
        path = everoute_root / directory_name / filename
        if not path.is_file():
            continue
        candidates.append(
            convert_doc_info(
                path,
                "product-knowledge",
                f"{product} 候选产品优先读取产品知识摘要，用于对象树、固定块和高优先级拆分轴校准。",
                20,
            )
        )
    return candidates


def select_focus_products(product_candidates: list[dict]) -> list[dict]:
    if not product_candidates:
        return []
    top_score = product_candidates[0]["score"]
    threshold = max(18, int(top_score * 0.35))
    selected: list[dict] = []
    for index, candidate in enumerate(product_candidates):
        if index == 0 or candidate["score"] >= threshold:
            selected.append(candidate)
    return selected


def append_product_doc_candidates(
    smartx_doc_candidates: list[dict],
    product_candidates: list[dict],
    smartx_docs: list[Path],
    needs_version_notes: bool,
    needs_install_guide: bool,
    aggregate_text: str,
) -> None:
    for candidate in product_candidates:
        product = candidate["product"]
        if product in PRODUCT_DOC_RULES:
            rule = PRODUCT_DOC_RULES[product]
            management = first_matching_doc(smartx_docs, rule["management"])
            whitepaper = first_matching_doc(smartx_docs, rule["whitepaper"])
            if management is not None:
                smartx_doc_candidates.append(
                    convert_doc_info(management, "management-guide", f"{product} 候选产品优先读取同产品管理指南", 10)
                )
            if whitepaper is not None:
                smartx_doc_candidates.append(
                    convert_doc_info(whitepaper, "whitepaper", f"{product} 候选产品优先读取同产品技术白皮书", 9)
                )
            continue

        if product != "ops":
            continue

        install = first_matching_doc(smartx_docs, SHARED_DOCS["install"])
        release = first_matching_doc(smartx_docs, SHARED_DOCS["release"])
        glossary = first_matching_doc(smartx_docs, SHARED_DOCS["glossary"])
        priority_boost = 0
        if re.search(OPS_SIGNAL_PATTERNS["controller"], aggregate_text, flags=re.IGNORECASE):
            priority_boost += 2
        if re.search(OPS_SIGNAL_PATTERNS["cluster"], aggregate_text, flags=re.IGNORECASE):
            priority_boost += 1
        if re.search(OPS_SIGNAL_PATTERNS["license"], aggregate_text, flags=re.IGNORECASE):
            priority_boost += 1

        if install is not None and (needs_install_guide or priority_boost > 0):
            smartx_doc_candidates.append(
                convert_doc_info(
                    install,
                    "install-upgrade-guide",
                    "运维候选产品优先读取安装与升级指南，用于部署、跨集群、仲裁、节点替换和系统服务能力边界。",
                    12 + priority_boost,
                )
            )
        if release is not None and (needs_version_notes or priority_boost > 0):
            smartx_doc_candidates.append(
                convert_doc_info(
                    release,
                    "release-note",
                    "运维候选产品优先读取发布说明，用于校准 ER/Tower 版本、双活限制和功能边界。",
                    11 + priority_boost,
                )
            )
        if glossary is not None:
            smartx_doc_candidates.append(
                convert_doc_info(
                    glossary,
                    "glossary",
                    "运维候选产品优先读取术语表，用于统一 Controller、仲裁节点、许可等术语。",
                    8 + priority_boost,
                )
            )


def deduplicate_candidates(candidates: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen_paths: set[str] = set()
    for item in sorted(candidates, key=lambda doc: (-doc["priority"], doc["name"])):
        if item["path"] in seen_paths:
            continue
        seen_paths.add(item["path"])
        unique.append(item)
    return unique


def build_golden_reference_candidates(text: str, product_candidates: list[dict], skill_root: Path) -> list[dict]:
    product_names = {item["product"] for item in product_candidates}
    candidate_configs = [
        {
            "name": "LBG & LB 支持 VPC",
            "required_products": {"lb", "vpc"},
            "path_parts": ["负载均衡", "LBG & LB 支持 VPC", "测试用例-LBG & LB 支持 VPC.md"],
            "required_signal_labels": {"出现支持 VPC"},
            "signals": [
                ("主产品包含 LB", r"\bLB\b|负载均衡|LBI|LBG|虚拟服务"),
                ("补充产品包含 VPC", r"\bVPC\b|子网|网络组|所属 VPC"),
                ("出现支持 VPC", r"支持 VPC"),
                ("出现网络类型分支", r"VLAN|FullNAT|DNAT|vpc-vpc|vlan-vpc"),
                ("出现通信方向", r"与客户端通信|与服务端通信|与服务器池通信"),
                ("出现主备关系", r"主备|主实例|备实例"),
                ("出现对象簇", r"部署 Everoute 服务|启用 LB|LBI|LBG|虚拟服务"),
            ],
            "min_signal_count": 4,
            "reason": "当前材料同时命中 LB、VPC、支持 VPC、网络类型、通信方向和主备关系等高相似信号。",
        },
        {
            "name": "VPC 对等连接",
            "required_products": {"vpc"},
            "path_parts": ["虚拟专有云网络", "VPC 对等连接", "测试用例-VPC对等连接.md"],
            "required_signal_labels": {"出现对等连接对象"},
            "signals": [
                ("出现对等连接对象", r"对等连接"),
                ("出现路由表或下一跳", r"路由表|下一跳"),
                ("出现 VPC 详情或跳转", r"VPC 详情|VPC 链接|详情页"),
                ("出现创建编辑删除动作", r"创建|编辑|删除"),
            ],
            "min_signal_count": 3,
            "reason": "当前材料命中 VPC 对等连接、路由表/下一跳和详情跳转等高相似信号。",
        },
        {
            "name": "VPC 多网关",
            "required_products": {"vpc"},
            "path_parts": ["虚拟专有云网络", "VPC 多网关集群", "测试用例-VPC 多网关.md"],
            "required_signal_labels": {"出现边缘网关组", "出现外部子网组"},
            "signals": [
                ("出现边缘网关组", r"边缘网关组"),
                ("出现外部子网组", r"外部子网组"),
                ("出现多 CIDR", r"多个 CIDR|多 CIDR|CIDR"),
                ("出现浮动 IP", r"浮动 IP|浮动ip"),
                ("出现主备结构", r"主备|活动网关"),
            ],
            "min_signal_count": 4,
            "reason": "当前材料命中边缘网关组、外部子网组、多 CIDR、浮动 IP 和主备结构等多网关高相似信号。",
        },
        {
            "name": "Controller 跨集群",
            "required_products": {"ops"},
            "path_parts": ["Everoute 服务运维", "Controller 跨集群", "测试用例-controller 跨集群.md"],
            "required_signal_labels": {"出现 Controller 或工作节点", "出现跨集群或双活"},
            "signals": [
                ("出现 Controller 或工作节点", r"Controller|controller|工作节点"),
                ("出现仲裁节点", r"仲裁节点|仲裁"),
                ("出现跨集群或双活", r"跨集群|双活|可用域"),
                ("出现所属集群/节点数量", r"所属集群|节点数量|添加工作节点"),
                ("出现替换或 ER 设置", r"替换|ER 设置|部署 Everoute 服务"),
            ],
            "min_signal_count": 4,
            "reason": "当前材料命中 Controller、仲裁节点、跨集群/双活、所属集群和替换节点等运维高相似信号。",
        },
        {
            "name": "LB 支持物理 CPU 许可",
            "required_products": {"ops", "lb"},
            "path_parts": ["Everoute 服务运维", "LB 支持物理 CPU 许可", "测试用例-er340 + tower470 LB 支持物理 CPU 许可.md"],
            "required_signal_labels": {"出现物理 CPU 或插槽许可"},
            "signals": [
                ("出现物理 CPU 或插槽许可", r"物理 CPU|CPU 插槽|socket"),
                ("出现许可额度", r"许可|额度|已使用|可用"),
                ("出现扩容或部署启用", r"扩容|部署|启用 LB|创建 LBI"),
                ("出现 LB 相关对象", r"LBI|LB 虚拟机|LB"),
                ("出现跨产品文案", r"DFW|VPC|文案"),
            ],
            "min_signal_count": 4,
            "reason": "当前材料命中物理 CPU/插槽许可、额度状态、LB 对象与跨产品文案等高相似信号。",
        },
    ]

    candidates: list[dict] = []
    base_root = skill_root / "references" / "UI-former-testcase-analyse" / "Everoute"
    for config in candidate_configs:
        if not config["required_products"].issubset(product_names):
            continue
        matched_signals = [label for label, pattern in config["signals"] if re.search(pattern, text, flags=re.IGNORECASE)]
        required_signal_labels = config.get("required_signal_labels", set())
        if not required_signal_labels.issubset(set(matched_signals)):
            continue
        if len(matched_signals) < config["min_signal_count"]:
            continue
        golden_path = base_root.joinpath(*config["path_parts"])
        if not golden_path.is_file():
            continue
        candidates.append(
            {
                "name": config["name"],
                "path": str(golden_path.resolve()),
                "recommended": True,
                "reason": config["reason"],
                "similarity_signals": matched_signals,
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
    focus_product_candidates = select_focus_products(product_candidates)
    product_knowledge_candidates = deduplicate_candidates(build_product_knowledge_candidates(focus_product_candidates, everoute_root))

    smartx_doc_candidates: list[dict] = []
    append_product_doc_candidates(
        smartx_doc_candidates,
        focus_product_candidates,
        smartx_docs,
        needs_version_notes,
        needs_install_guide,
        aggregate_text,
    )

    glossary = first_matching_doc(smartx_docs, SHARED_DOCS["glossary"])
    if glossary is not None:
        smartx_doc_candidates.append(
            convert_doc_info(glossary, "glossary", "术语表用于统一需求文档、设计稿和历史用例中的产品名词", 6)
        )

    if needs_version_notes:
        release = first_matching_doc(smartx_docs, SHARED_DOCS["release"])
        if release is not None:
            smartx_doc_candidates.append(
                convert_doc_info(release, "release-note", "材料中出现版本、发布或兼容差异，需要读取发布说明校准版本边界", 7)
            )

    if needs_install_guide:
        install = first_matching_doc(smartx_docs, SHARED_DOCS["install"])
        if install is not None:
            smartx_doc_candidates.append(
                convert_doc_info(install, "install-upgrade-guide", "材料中出现部署、启用、安装或升级语义，需要读取安装与升级指南辅助理解", 5)
            )

    unique_doc_candidates = deduplicate_candidates(smartx_doc_candidates)

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

    resource_type_hints = build_resource_type_hints(aggregate_text, focus_product_candidates)
    golden_reference_candidates = build_golden_reference_candidates(aggregate_text, focus_product_candidates, skill_root)

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
        "focus_product_candidates": focus_product_candidates,
        "product_knowledge_candidates": product_knowledge_candidates,
        "product_knowledge_selection_hints": [
            "先读取主产品与补充产品的产品知识摘要，用于对象树、固定块和高优先级拆分轴校准。",
            "若历史样本中存在复合 case 写法，只能将其视为继续拆分的信号，不能直接继承为最终用例。",
        ],
        "smartx_doc_candidates": unique_doc_candidates,
        "smartx_doc_selection_hints": [
            "优先选择与主产品一致的产品知识摘要、管理指南和技术白皮书。",
            "术语表默认可用，用于统一产品对象、网络模式和命名。",
            "运维场景优先安装与升级指南、发布说明和术语表，再结合其他产品资料理解具体功能边界。",
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
