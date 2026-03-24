set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common-env.sh"
init_local_llm_env

echo "Pulling qwen2.5-coder:3b"
echo "OLLAMA_HOST=${OLLAMA_HOST:-127.0.0.1:11434}"
echo "OLLAMA_MODELS=${OLLAMA_MODELS}"

exec ollama pull qwen2.5-coder:3b
