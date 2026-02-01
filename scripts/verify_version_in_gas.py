#!/usr/bin/env python3
"""
檢查 gas/ 目錄是否包含版本顯示相關程式，用來確認「code 沒更新」還是「code 有問題」。
在專案根目錄執行：python scripts/verify_version_in_gas.py
"""
import os
import sys

GAS_DIR = os.path.join(os.path.dirname(__file__), "..", "gas")


def check_file_contains(path: str, *needles: str) -> list[str]:
    """檢查檔案是否存在且包含所有 needles，回傳缺少的 needle 清單。"""
    missing = []
    if not os.path.isfile(path):
        return [f"檔案不存在: {path}"]
    try:
        text = open(path, "r", encoding="utf-8").read()
    except Exception as e:
        return [f"無法讀取 {path}: {e}"]
    for n in needles:
        if n not in text:
            missing.append(f"缺少: {n!r}")
    return missing


def main() -> int:
    gas_abs = os.path.abspath(GAS_DIR)
    if not os.path.isdir(gas_abs):
        print(f"錯誤: gas 目錄不存在: {gas_abs}")
        return 1

    failed = 0

    # Main.js: 首頁卡片版本
    main_js = os.path.join(gas_abs, "Main.js")
    missing = check_file_contains(
        main_js,
        "getVersion",
        "版本：v",
    )
    if missing:
        print(f"[FAIL] {main_js}")
        for m in missing:
            print(f"  - {m}")
        failed += 1
    else:
        print(f"[OK] Main.js 有版本相關程式（首頁卡片）")

    # web_app.js: getVersion + BACKEND_VERSION
    web_app_js = os.path.join(gas_abs, "web_app.js")
    missing = check_file_contains(
        web_app_js,
        "BACKEND_VERSION",
        "function getVersion()",
    )
    if missing:
        print(f"[FAIL] {web_app_js}")
        for m in missing:
            print(f"  - {m}")
        failed += 1
    else:
        print(f"[OK] web_app.js 有 getVersion 與 BACKEND_VERSION")

    # sidebar.html: 側邊欄版本顯示
    sidebar_html = os.path.join(gas_abs, "sidebar.html")
    missing = check_file_contains(
        sidebar_html,
        "sidebar-version",
        "getVersion()",
    )
    if missing:
        print(f"[FAIL] {sidebar_html}")
        for m in missing:
            print(f"  - {m}")
        failed += 1
    else:
        print(f"[OK] sidebar.html 有側邊欄版本顯示與 getVersion() 呼叫")

    if failed:
        print()
        print("→ 本機 gas/ 有缺少版本相關程式，請先補齊或還原再執行 clasp push。")
        return 1

    print()
    print("→ 本機 gas/ 版本相關程式齊全。若畫面上仍沒版號，請依 docs/VERSION_DISPLAY_DEBUG.md 做「二、確認 GAS 專案已收到最新 code」與「三、確認執行到的是最新版」。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
