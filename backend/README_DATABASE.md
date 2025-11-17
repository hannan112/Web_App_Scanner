# 🗄️ Database & Scripts Organization

## 📁 Directory Structure

```
backend/
├── db.sqlite3                    # Active database (current)
├── database/                     # Database storage directory
│   ├── db_ml_training.sqlite3   # ML training database
│   ├── db_production.sqlite3    # Production database (when created)
│   └── database_backups/        # All backups stored here
│       ├── README.md
│       ├── db_original_20251111_121456.sqlite3 (562.9 MB)
│       └── db_before_switch_*.sqlite3
├── scripts/                      # All utility scripts
│   ├── db_manager.py            # Main database manager
│   ├── db_status.sh             # Check database status
│   ├── db_backup.sh             # Backup current database
│   ├── db_switch_ml_training.sh # Switch to ML training DB
│   ├── db_switch_original.sh    # Switch to original DB
│   ├── db_create_ml_training.sh # Create fresh ML training DB
│   ├── verify_setup.sh          # Pre-start verification script
│   ├── analyze_db.py            # Database analysis
│   ├── analyze_scans_detailed.py # Scan pattern analysis
│   └── analyze_data_diversity.py # Data diversity analysis
├── docs/                         # Documentation
│   ├── DATABASE_GUIDE.md        # Complete database guide
│   ├── SCANNING_SITES_LIST.md   # Sites to scan for ML
│   ├── SETUP_COMPLETE.md        # Setup summary
│   ├── ORGANIZATION_COMPLETE.md # Organization summary
│   └── PRE_START_CHECKLIST.md   # Pre-start verification checklist
├── db_status.sh                  # Convenience wrapper scripts
├── db_backup.sh                  # (These call scripts/ versions)
├── db_switch_ml_training.sh
└── db_switch_original.sh
```

## 🚀 Quick Start

### ⚠️ Before Starting: Verify Setup
```bash
# Run verification script to check everything is ready
python scripts/verify_setup.sh

# Or manually check:
python manage.py migrate          # Apply migrations
python manage.py createsuperuser  # Create admin user (optional)
```

### Check Database Status
```bash
./db_status.sh
```

### Switch Databases
```bash
# Switch to ML training database
./db_switch_ml_training.sh

# Switch back to original
./db_switch_original.sh
```

### Backup Database
```bash
./db_backup.sh
```

### Advanced Operations
```bash
# Direct access to database manager
python scripts/db_manager.py status
python scripts/db_manager.py list
python scripts/db_manager.py backup --name "my_backup"
```

## 📖 Documentation

All detailed documentation is in the `docs/` directory:

- **docs/DATABASE_GUIDE.md** - Complete database management guide
- **docs/SCANNING_SITES_LIST.md** - 25 sites to scan with checklist
- **docs/SETUP_COMPLETE.md** - Setup summary and next steps
- **docs/ORGANIZATION_COMPLETE.md** - Code organization summary
- **docs/PRE_START_CHECKLIST.md** - Pre-start verification checklist ⚠️ **READ THIS FIRST**
- **database/database_backups/README.md** - Backup strategy

## 🔧 Analysis Scripts

Located in `scripts/` directory:

```bash
# Analyze current database
python scripts/analyze_db.py

# Analyze scan patterns
python scripts/analyze_scans_detailed.py

# Check data diversity
python scripts/analyze_data_diversity.py
```

## 📊 Current Status

- **Original Database**: Backed up (562.9 MB, 127 scans, 23,517 vulnerabilities)
- **ML Training Database**: Active and ready (0 scans, 0 vulnerabilities)
- **Backups**: 2 automatic backups created
- **Scripts**: All working and tested ✅

## 💡 Why This Structure?

### Benefits:
- ✅ **Clean separation**: Database files in `database/`, scripts in `scripts/`, docs in `docs/`
- ✅ **Easy access**: Convenience scripts in root for quick commands
- ✅ **Organized backups**: All backups in one location
- ✅ **Better maintainability**: Clear structure for FYP project
- ✅ **Documentation**: Everything documented and easy to find

### Usage:
- **Root level**: Quick access convenience scripts
- **scripts/**: Full functionality and analysis tools
- **docs/**: All documentation and guides
- **database/**: All database files and backups

## 🎯 Next Steps

1. **⚠️ Verify setup** - Run `python scripts/verify_setup.sh` or check `docs/PRE_START_CHECKLIST.md`
2. **Apply migrations** - Run `python manage.py migrate` if needed
3. **Create superuser** (optional) - Run `python manage.py createsuperuser`
4. **Start scanning** - Begin scanning diverse sites (see `docs/SCANNING_SITES_LIST.md`)
5. **Monitor progress** - Use `./db_status.sh` to track your data collection
6. **Train ML model** - When you have 70-80+ scans
7. **Compare results** - Compare with original database

## 📞 Need Help?

- Quick help: `./db_status.sh`
- Full guide: `docs/DATABASE_GUIDE.md`
- Scan list: `docs/SCANNING_SITES_LIST.md`
- Manager help: `python scripts/db_manager.py --help`

---

**Status**: ✅ Organized and ready for ML training phase
**Last Updated**: November 11, 2025
