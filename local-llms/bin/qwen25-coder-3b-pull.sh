set -euo pipefail

echo "Pulling qwen2.5-coder:3b"
echo "OLLAMA_HOST=${OLLAMA_HOST:-127.0.0.1:11434}"
echo "OLLAMA_MODELS=${OLLAMA_MODELS:?OLLAMA_MODELS must be set}"

exec ollama pull qwen2.5-coder:3b
