#!/bin/bash -e
# Regenerate the Python protobuf modules in app/proto from the proto submodule.
# Run after bumping the submodule: git submodule update --init

cd "$(dirname "$0")/.."

uv run --frozen python -m grpc_tools.protoc \
    -I proto \
    --python_out=app/proto \
    --pyi_out=app/proto \
    proto/kcsu/alerts/v1/alert.proto
