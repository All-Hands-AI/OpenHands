#!/usr/bin/env bash
set -euo pipefail

# --- Paths (edit if needed) ---
BASE="/home/ubuntu/OpenHands/evaluation/evaluation_outputs/outputs/swefficiency__swefficiency-test/CodeActAgent/deepseek-reasoner_maxiter_100_N_v0.51.1-no-hint-run_1"
LOG_DIR="$BASE/infer_logs_backup"
COMPL_DIR="$BASE/llm_completions"
PHRASE="Logging LLM completions"

ok_ids=()

# Iterate over instance IDs from llm_completions (top-level dirs only)
while IFS= read -r -d '' id_path; do
  id="$(basename "$id_path")"

  # Find the matching log file "instance_<id>.log" somewhere under LOG_DIR
  logpath="$(find "$LOG_DIR" -type f -name "instance_${id}.log" -print -quit || true)"
  [[ -z "${logpath:-}" ]] && continue

  # Check last line contains the phrase
  last_line="$(awk 'END{printf "%s", $0}' "$logpath" | tr -d '\r')"
  [[ "$last_line" == *"$PHRASE"* ]] && ok_ids+=("$id")
done < <(find "$COMPL_DIR" -mindepth 1 -maxdepth 1 -type d -print0)

# Print just a comma-separated, quoted list (matches your earlier style)
if ((${#ok_ids[@]})); then
  printf '%s\0' "${ok_ids[@]}" \
    | xargs -0 -n1 printf '"%s"\n' \
    | paste -sd, -
else
  echo ""
fi
