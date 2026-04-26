#!/bin/bash
cd "$(dirname "$0")/.."
export PYTHONPATH=".:$(dirname $(pwd)):$(dirname $(pwd))/insightbrowser-ahp"
python3 main.py
