#!/bin/bash
# Wrapper - calls block-tricks.py
# stdin (hook JSON) is forwarded to python script
exec python "$(dirname "$0")/block-tricks.py"
