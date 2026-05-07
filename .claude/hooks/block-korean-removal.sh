#!/bin/bash
# Wrapper - calls block-korean-removal.py
# stdin (hook JSON) is forwarded to python script
exec python "$(dirname "$0")/block-korean-removal.py"
