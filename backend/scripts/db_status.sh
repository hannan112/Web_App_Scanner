#!/bin/bash
# Quick database status check

cd "$(dirname "$0")" && python db_manager.py status
