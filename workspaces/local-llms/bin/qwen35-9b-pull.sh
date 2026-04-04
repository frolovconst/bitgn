set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common-env.sh"
init_local_llm_env

echo "Pulling qwen3.5:9b"
echo "OLLAMA_HOST=${OLLAMA_HOST:-127.0.0.1:11434}"
echo "OLLAMA_MODELS=${OLLAMA_MODELS}"

exec ollama pull qwen3.5:9b
