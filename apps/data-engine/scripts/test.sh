#!/bin/bash
# Convenient script to run all backend tests

# Ensure we are in the apps/data-engine directory
cd "$(dirname "$0")/.."

# Run pytest using the virtual environment
.venv/bin/pytest "$@"
