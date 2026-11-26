#!/usr/bin/env python3
"""Validate representative fun-learning outputs against strict memory-hook rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> str:
    return "FAIL: " + message


def validate_case(case: dict) -> list[str]:
    errors: list[str] = []
    identifier = case.get("id", "<missing id>")
    mode = case.get("mode")
    response = case.get("response", "")
    strict_core = case.get("strict_core", [])
    source_symbols = case.get("source_symbols", [])
    hook = case.get("memory_hook", "")
    recall_prompt = case.get("recall_prompt", "")
    hidden_answers = case.get("hidden_answers", [])
    forbidden = case.get("forbidden_terms", [])

    if mode not in {"fun", "normal", "downgraded"}:
        errors.append(fail(identifier + ": invalid mode"))
    if not response:
        errors.append(fail(identifier + ": missing response"))
    for item in strict_core:
        if item not in response:
            errors.append(fail(identifier + ": missing strict core `" + item + "`"))
    for symbol in source_symbols:
        if symbol not in response:
            errors.append(fail(identifier + ": source symbol changed or missing `" + symbol + "`"))
    for answer in hidden_answers:
        if answer in response:
            errors.append(fail(identifier + ": retrieval answer leaked `" + answer + "`"))
    for term in forbidden:
        if term in response:
            errors.append(fail(identifier + ": forbidden term `" + term + "` found"))

    if mode == "fun":
        if not hook:
            errors.append(fail(identifier + ": fun mode needs one memory hook"))
        elif hook not in response:
            errors.append(fail(identifier + ": memory hook not embedded in response"))
        elif len(hook) > 52:
            errors.append(fail(identifier + ": memory hook is too long"))
        if not recall_prompt:
            errors.append(fail(identifier + ": missing retrieval question"))
        elif recall_prompt not in response:
            errors.append(fail(identifier + ": retrieval question not embedded in response"))
    elif hook:
        errors.append(fail(identifier + ": non-fun mode must not contain a memory hook"))

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_fun_learning_mode.py <cases.json>")
        return 2

    cases_path = Path(sys.argv[1])
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    all_errors = [error for case in cases for error in validate_case(case)]

    if all_errors:
        print("Fun-learning mode validation failed")
        print("\n".join(all_errors))
        return 1

    print("Fun-learning mode validation passed: " + str(len(cases)) + " representative cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
