set -euo pipefail

init_local_llm_env() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  if [ -z "${LOCAL_LLM_HOME:-}" ]; then
    export LOCAL_LLM_HOME="$(cd "$script_dir/.." && pwd)"
  fi

  export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
  export OLLAMA_MODELS="${OLLAMA_MODELS:-$LOCAL_LLM_HOME/.ollama/models}"

  mkdir -p "$OLLAMA_MODELS"
}
