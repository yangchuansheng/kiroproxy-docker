#!/usr/bin/env python3
"""Validate KiroProxy Opus model mapping patch."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

EXPECTED = {
    "claude-opus-4.6": "claude-opus-4.6",
    "claude-opus-4.7": "claude-opus-4.7",
    "opus-4.6": "claude-opus-4.6",
    "opus-4.7": "claude-opus-4.7",
    "opus": "claude-opus-4.7",
    "claude-4-opus": "claude-opus-4.7",
}


def load_config(root: Path):
    config_path = root / "kiro_proxy" / "config.py"
    spec = importlib.util.spec_from_file_location("kiro_proxy_config_under_test", config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {config_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    config = load_config(root)

    missing = {"claude-opus-4.6", "claude-opus-4.7"} - set(config.KIRO_MODELS)
    if missing:
        raise AssertionError(f"KIRO_MODELS missing: {sorted(missing)}")

    for source, expected in EXPECTED.items():
        actual = config.map_model_name(source)
        if actual != expected:
            raise AssertionError(f"{source} mapped to {actual}, expected {expected}")

    main_source = (root / "kiro_proxy" / "main.py").read_text(encoding="utf-8")
    for model in ("claude-opus-4.6", "claude-opus-4.7"):
        if model not in main_source:
            raise AssertionError(f"main.py static model list missing {model}")

    print("Model patch validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
