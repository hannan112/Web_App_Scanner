#!/bin/bash
# Switch to ML training database

echo "🔄 Switching to ML Training database..."
echo "Current database will be backed up automatically."
echo ""

cd "$(dirname "$0")" && python db_manager.py switch ml-training

echo ""
echo "✅ Now using ML Training database!"
echo "Ready to scan diverse sites for ML training."
