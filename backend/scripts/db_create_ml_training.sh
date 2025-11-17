#!/bin/bash
# Create fresh ML training database

echo "🎯 Creating fresh ML Training database..."
echo "This will be used for scanning diverse sites and ML model training."
echo ""

cd "$(dirname "$0")" && python db_manager.py create ml-training

echo ""
echo "✅ ML Training database created!"
echo "Next steps:"
echo "  1. Run: ./db_switch_ml_training.sh"
echo "  2. Start scanning the recommended sites"
echo "  3. Train ML model on this clean, diverse dataset"
