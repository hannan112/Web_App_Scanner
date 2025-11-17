#!/bin/bash
# Quick backup current database

cd "$(dirname "$0")" && python db_manager.py backup --name "db_manual_backup"
