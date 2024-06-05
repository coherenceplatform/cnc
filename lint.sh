#!/bin/bash

set -e

black --check .
ruff check --ignore F811 --exclude __init__.py .