#!/bin/bash
# Quick verification script to check if everything is ready before starting

echo "🔍 Pre-Start Verification Checklist"
echo "===================================="
echo ""

# Check 1: Database files exist
echo "1️⃣ Checking database files..."
if [ -f "db.sqlite3" ]; then
    DB_SIZE=$(du -h db.sqlite3 | cut -f1)
    echo "   ✅ Active database exists: db.sqlite3 ($DB_SIZE)"
else
    echo "   ❌ Active database not found: db.sqlite3"
fi

if [ -f "database/db_ml_training.sqlite3" ]; then
    ML_SIZE=$(du -h database/db_ml_training.sqlite3 | cut -f1)
    echo "   ✅ ML training database exists: database/db_ml_training.sqlite3 ($ML_SIZE)"
else
    echo "   ⚠️  ML training database not found"
fi

echo ""

# Check 2: Migrations
echo "2️⃣ Checking migrations..."
MIGRATIONS=$(python manage.py showmigrations 2>&1 | grep -c "\[ \]")
if [ "$MIGRATIONS" -eq 0 ]; then
    echo "   ✅ All migrations applied"
else
    echo "   ⚠️  $MIGRATIONS pending migration(s) - run: python manage.py migrate"
fi

echo ""

# Check 3: Django check
echo "3️⃣ Running Django system check..."
python manage.py check --database default 2>&1 | grep -q "System check identified"
if [ $? -eq 0 ]; then
    echo "   ⚠️  Django found some issues - check output above"
else
    echo "   ✅ Django system check passed"
fi

echo ""

# Check 4: Database status
echo "4️⃣ Database status:"
python scripts/db_manager.py status 2>&1 | head -20

echo ""
echo "===================================="
echo "✅ Verification complete!"
echo ""
echo "Next steps:"
echo "  1. If migrations pending: python manage.py migrate"
echo "  2. Create superuser (optional): python manage.py createsuperuser"
echo "  3. Start server: python manage.py runserver"
echo ""













