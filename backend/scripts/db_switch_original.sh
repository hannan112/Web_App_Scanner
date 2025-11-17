#!/bin/bash
# Switch back to original database

echo "🔄 Switching to Original database..."
echo "Current database will be backed up automatically."
echo ""

cd "$(dirname "$0")" && python db_manager.py switch original

echo ""
echo "✅ Now using Original database!"
echo "Back to your original 127 scans and 23,517 vulnerabilities."
