# ✅ Pre-Start Checklist

## Before Starting the Project After Creating New Database

This checklist ensures everything is set up correctly before you start using the project with your new ML training database.

---

## 🔍 Step 1: Verify Database Status

Check which database is currently active:

```bash
cd backend
./db_status.sh
# OR
python scripts/db_manager.py status
```

**Expected Output:**
- Current active database should show ML Training database
- Database should have 0 scans (fresh database)
- Size should be small (~400 KB)

---

## 🔄 Step 2: Verify Migrations Are Applied

**Important:** Even though `db_manager.py` runs migrations when creating a database, it's good practice to verify:

```bash
# Check migration status
python manage.py showmigrations

# Apply any pending migrations (if any)
python manage.py migrate
```

**What to look for:**
- All migrations should show `[X]` (applied)
- If any show `[ ]` (not applied), run `migrate` command
- No errors should occur

---

## 👤 Step 3: Create Superuser (If Needed)

If you need admin access, create a superuser:

```bash
python manage.py createsuperuser
```

**Note:** This is optional but recommended for:
- Accessing Django admin panel (`/admin/`)
- Managing users and projects through admin interface
- Testing authentication features

---

## 🧪 Step 4: Verify Database Connection

Test that Django can connect to the database:

```bash
# This will show any database errors
python manage.py check --database default
```

**Expected:** No errors should appear.

---

## 📊 Step 5: Verify Database Schema

Check that all tables are created correctly:

```bash
# List all tables in the database
python manage.py dbshell <<EOF
.tables
.quit
EOF
```

**Expected tables include:**
- `auth_*` (authentication tables)
- `scanning_*` (scanning app tables)
- `projects_*` (project management tables)
- `django_*` (Django system tables)

---

## 🚀 Step 6: Start the Development Server

Once everything is verified, start the server:

```bash
python manage.py runserver
```

**Expected:**
- Server starts without errors
- No database-related errors in console
- Can access `http://localhost:8000`

---

## ⚠️ Common Issues & Solutions

### Issue: "No such table" errors

**Solution:**
```bash
# Run migrations again
python manage.py migrate
```

### Issue: Database locked errors

**Solution:**
```bash
# Make sure no other process is using the database
# Check if server is running: ps aux | grep runserver
# Stop any running instances, then retry
```

### Issue: Migration conflicts

**Solution:**
```bash
# Check for conflicts
python manage.py showmigrations

# If needed, create new migrations
python manage.py makemigrations

# Then apply
python manage.py migrate
```

### Issue: Database file not found

**Solution:**
```bash
# Check if database exists
ls -lh db.sqlite3 database/db_ml_training.sqlite3

# If ML training DB doesn't exist, create it
python scripts/db_manager.py create ml-training

# Then switch to it
./db_switch_ml_training.sh
```

---

## ✅ Quick Verification Script

Run this to check everything at once:

```bash
#!/bin/bash
echo "🔍 Checking database status..."
python scripts/db_manager.py status

echo -e "\n🔄 Checking migrations..."
python manage.py showmigrations | grep -E "\[ \]|\[X\]" | tail -5

echo -e "\n✅ Database check..."
python manage.py check --database default

echo -e "\n📊 Database tables..."
python manage.py dbshell <<EOF 2>/dev/null | grep -E "^[a-z_]+"
.tables
.quit
EOF

echo -e "\n✅ Pre-start checks complete!"
```

---

## 📝 Summary

**Before starting the project, ensure:**

1. ✅ Database is switched to ML training database
2. ✅ All migrations are applied (`python manage.py migrate`)
3. ✅ Superuser is created (optional but recommended)
4. ✅ Database connection works (`python manage.py check`)
5. ✅ No errors when starting server

**Quick Commands:**
```bash
# 1. Check status
./db_status.sh

# 2. Apply migrations
python manage.py migrate

# 3. Create superuser (optional)
python manage.py createsuperuser

# 4. Start server
python manage.py runserver
```

---

## 🎯 After Setup

Once everything is verified:

1. **Start scanning sites** (see `docs/SCANNING_SITES_LIST.md`)
2. **Monitor progress** with `./db_status.sh`
3. **Collect data** for ML training (target: 70-80+ scans)
4. **Train ML model** when you have enough data

---

**Status**: Ready to use after completing checklist ✅
**Last Updated**: November 11, 2025













