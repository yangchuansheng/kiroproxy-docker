#!/usr/bin/env python3
"""Patch KiroProxy model mapping for additional Opus model IDs."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

OPUS_MODELS = ("claude-opus-4.6", "claude-opus-4.7")
ALIAS_MAPPING = {
    "claude-4-opus": "claude-opus-4.7",
    "opus": "claude-opus-4.7",
    "opus-4.6": "claude-opus-4.6",
    "opus-4.7": "claude-opus-4.7",
}


def find_assignment_span(source: str, name: str) -> tuple[int, int, ast.AST]:
    """Return the source span and node for a top-level assignment."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.lineno, node.end_lineno or node.lineno, node.value
    raise RuntimeError(f"Could not find assignment for {name}")


def replace_lines(source: str, start: int, end: int, replacement: str) -> str:
    lines = source.splitlines()
    lines[start - 1:end] = replacement.splitlines()
    return "\n".join(lines) + "\n"


def patch_kiro_models(source: str) -> str:
    start, end, value = find_assignment_span(source, "KIRO_MODELS")
    models = set(ast.literal_eval(value))
    models.update(OPUS_MODELS)
    body = ",\n".join(f'    "{model}"' for model in sorted(models))
    return replace_lines(source, start, end, f"KIRO_MODELS = {{\n{body},\n}}")


def patch_model_mapping(source: str) -> str:
    for alias, target in ALIAS_MAPPING.items():
        pattern = re.compile(rf'("{re.escape(alias)}"\s*:\s*)"[^"]+"')
        source, count = pattern.subn(rf'\1"{target}"', source, count=1)
        if count == 0:
            marker = "    # 别名\n"
            if marker not in source:
                raise RuntimeError(f"Could not insert alias mapping for {alias}")
            source = source.replace(marker, f'{marker}    "{alias}": "{target}",\n', 1)
    return source


def patch_opus_heuristic(source: str) -> str:
    old = '    if "opus" in model_lower:\n        return "claude-opus-4.5"\n'
    new = '''    if "opus" in model_lower:
        if "4.7" in model_lower:
            return "claude-opus-4.7"
        if "4.6" in model_lower:
            return "claude-opus-4.6"
        if "4.5" in model_lower:
            return "claude-opus-4.5"
        return "claude-opus-4.7"
'''
    if old not in source:
        if 'return "claude-opus-4.7"' in source:
            return source
        raise RuntimeError("Could not find Opus fallback heuristic")
    return source.replace(old, new, 1)


def patch_static_models(source: str) -> str:
    anchor = '        {"id": "claude-opus-4.5", "object": "model", "owned_by": "kiro", "name": "Claude Opus 4.5"},\n'
    additions = (
        '        {"id": "claude-opus-4.6", "object": "model", "owned_by": "kiro", "name": "Claude Opus 4.6"},\n'
        '        {"id": "claude-opus-4.7", "object": "model", "owned_by": "kiro", "name": "Claude Opus 4.7"},\n'
    )
    if additions in source:
        return source
    if anchor not in source:
        raise RuntimeError("Could not find static Opus model list anchor")
    return source.replace(anchor, anchor + additions, 1)


def patch_project(root: Path) -> None:
    config = root / "kiro_proxy" / "config.py"
    main = root / "kiro_proxy" / "main.py"

    config_source = config.read_text(encoding="utf-8")
    config_source = patch_kiro_models(config_source)
    config_source = patch_model_mapping(config_source)
    config_source = patch_opus_heuristic(config_source)
    config.write_text(config_source, encoding="utf-8")

    main_source = main.read_text(encoding="utf-8")
    main_source = patch_static_models(main_source)
    main.write_text(main_source, encoding="utf-8")


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    patch_project(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
