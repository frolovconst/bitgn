set -euo pipefail

echo "Starting Ollama server"
echo "OLLAMA_HOST=${OLLAMA_HOST:-127.0.0.1:11434}"
echo "OLLAMA_MODELS=${OLLAMA_MODELS:?OLLAMA_MODELS must be set}"

host_port="${OLLAMA_HOST#http://}"
host_port="${host_port#https://}"
host="${host_port%%:*}"
port="${host_port##*:}"

if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "An existing process is already listening on ${host}:${port}."
  echo "Stop that process first or point OLLAMA_HOST to a different port."
  exit 1
fi

exec ollama serve
