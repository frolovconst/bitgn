#!/usr/bin/env bash
set -euo pipefail

# Quick check of latest BitGN SDK versions from Buf's Python index.
python -m pip index versions bitgn-api-connectrpc-python --index-url https://buf.build/gen/python
python -m pip index versions bitgn-api-protocolbuffers-python --index-url https://buf.build/gen/python

# Optional: narrow output to the first two lines per package.
# python -m pip index versions bitgn-api-connectrpc-python --index-url https://buf.build/gen/python | sed -n '1,2p'
# python -m pip index versions bitgn-api-protocolbuffers-python --index-url https://buf.build/gen/python | sed -n '1,2p'
