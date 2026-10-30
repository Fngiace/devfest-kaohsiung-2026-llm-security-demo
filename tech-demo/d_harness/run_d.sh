#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
exec venv/bin/python tech-demo/d_harness/run_d.py
