#!/usr/bin/env bash
# OBE-Project：commit + clasp push + git push 一鍵執行
# 用法: ./scripts/commit-push-and-clasp.sh ["commit message"]
# 若未給訊息則使用預設: "chore: sync repo and GAS"

set -e
cd "$(dirname "$0")/.."

MSG="${1:-chore: sync repo and GAS}"

if [[ -z "$(git status --short)" ]]; then
  echo "[略過] 無變更可提交。"
else
  git add -A
  git commit -m "$MSG"
fi

if [[ -f .clasp.json ]]; then
  echo "[GAS] 正在 clasp push..."
  npx @google/clasp push --force || true
else
  echo "[略過] 無 .clasp.json，不執行 clasp push。"
fi

echo "[Git] 正在 git push origin main..."
git push origin main
echo "[完成] commit + clasp + push 完成。"
