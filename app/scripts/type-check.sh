#!/usr/bin/env bash

set -e
set -x

echo "Running type checks..."
mypy src
