# 🗄️ Database Management Guide

## 📋 Quick Summary

### Current Setup:
✅ **Original Database**: Backed up (562.9 MB, 127 scans, 23,517 vulnerabilities)
✅ **ML Training Database**: Created fresh (ready for diverse scanning)
✅ **Management Tools**: Ready to use

---

## 🎯 Strategy Overview

### 1️⃣ Original Database (PRESERVED)
- **Location**: `database_backups/db_original_20251111_121456.sqlite3`
- **Purpose**: Your baseline data - kept for comparison
- **Contains**: 127 scans from 10 sites
- **Use for**: FYP "before ML" metrics

### 2️⃣ ML Training Database (ACTIVE FOR NEW SCANS)
- **Location**: `db_ml_training.sqlite3`
- **Purpose**: Clean, diverse dataset for ML training
- **Status**: Empty, ready for scanning
- **Target**: 180-200 scans from 25+ diverse sites
- **Use for**: Training your ML false positive classifier

### 3️⃣ Current Active Database
- **Location**: `db.sqlite3`
- **Status**: Currently using original data
- **Note**: Switch to ML training database before scanning new sites

---

## 🚀 Quick Start Commands

### Check Status
```bash
./db_status.sh
# OR
python db_manager.py status
```

### Switch to ML Training Database
```bash
./db_switch_ml_training.sh
# OR
python db_manager.py switch ml-training
```

### Switch Back to Original
```bash
./db_switch_original.sh
# OR
python db_manager.py switch original
```

### Backup Current Database
```bash
./db_backup.sh
# OR
python db_manager.py backup --name "my_backup"
```

---

## 📖 Detailed Usage

### Python Database Manager
The `db_manager.py` script provides comprehensive database management:

```bash
# Show help
python db_manager.py --help

# Check status
python db_manager.py status

# Create fresh database
python db_manager.py create ml-training
python db_manager.py create production

# Switch databases
python db_manager.py switch ml-training
python db_manager.py switch original
python db_manager.py switch production

# Backup current database
python db_manager.py backup
python db_manager.py backup --name "before_experiment"

# List all backups
python db_manager.py list

# Restore from backup
python db_manager.py restore db_backup_20251111_121456.sqlite3
```

---

## 🎓 Workflow for FYP

### Phase 1: Scan Diverse Sites (Week 1-2)
```bash
# 1. Switch to ML training database
./db_switch_ml_training.sh

# 2. Verify you're using the right database
./db_status.sh
# Should show: Scans: 0, Vulnerabilities: 0

# 3. Start scanning recommended sites
# Use your frontend or API to scan:
#   - testphp.vulnweb.com (5 scans)
#   - itsecgames.com (5 scans)
#   - zero.webappsecurity.com (5 scans)
#   - juice-shop.herokuapp.com (3 scans)
#   - demo.testfire.net (3 scans)
#   - github.com (3 scans)
#   - stackoverflow.com (3 scans)
#   - etc.

# 4. Monitor progress
./db_status.sh
# Watch scan and vulnerability counts increase
```

### Phase 2: Train ML Model (Week 2-3)
```bash
# Still using ML training database
# Run ML training scripts (to be created)
python train_fp_classifier.py

# Export model for integration
```

### Phase 3: Compare Results (For FYP Report)
```bash
# Switch to original database
./db_switch_original.sh

# Run analysis on original data (WITHOUT ML)
python analyze_db.py > results_without_ml.txt

# Switch to ML training database
./db_switch_ml_training.sh

# Run analysis with ML filtering
python analyze_with_ml.py > results_with_ml.txt

# Compare and show improvement in your thesis!
```

---

## 📊 Expected Results

### Original Database (Before ML)
- 127 scans, 10 sites
- 23,517 vulnerabilities
- ~54% false positives (missing headers)
- ~22% informational findings
- Only 0.03% critical/high

### ML Training Database (After Diverse Scanning)
- Target: 180-200 scans, 25+ sites
- Expected: 40,000-50,000 vulnerabilities
- Better balance:
  - 30% real vulnerabilities (injection, XSS, etc.)
  - 30% false positives (for training)
  - 40% medium/low findings

### After ML Filtering
- Same scans
- ~50% reduction in false positives
- 85-90% precision on real vulnerabilities
- Focus on actionable findings

---

## 🔒 Safety Features

### Automatic Backups
Every time you switch databases, the current one is backed up automatically.

### List Backups
```bash
python db_manager.py list
```

### Restore from Backup
```bash
python db_manager.py restore db_backup_20251111_121456.sqlite3
```

---

## 📁 File Structure

```
backend/
├── db.sqlite3                          # Current active database (symlink/target)
├── database/                           # Database storage directory
│   ├── db_ml_training.sqlite3         # ML training database
│   ├── db_production.sqlite3          # Production database (when created)
│   └── database_backups/              # All backups stored here
│       ├── README.md                   # Backup documentation
│       ├── db_original_20251111_121456.sqlite3  # Original backup
│       └── db_before_switch_*.sqlite3  # Automatic backups
├── scripts/                            # All utility scripts
│   ├── db_manager.py                  # Main database manager
│   ├── db_status.sh                   # Check database status
│   ├── db_backup.sh                   # Backup current database
│   ├── db_switch_ml_training.sh       # Switch to ML training DB
│   ├── db_switch_original.sh          # Switch to original DB
│   ├── db_create_ml_training.sh       # Create fresh ML training DB
│   ├── analyze_db.py                  # Database analysis
│   ├── analyze_scans_detailed.py      # Scan pattern analysis
│   └── analyze_data_diversity.py      # Data diversity analysis
├── docs/                               # Documentation
│   ├── DATABASE_GUIDE.md              # This file
│   ├── SCANNING_SITES_LIST.md         # Sites to scan for ML
│   ├── SETUP_COMPLETE.md              # Setup summary
│   └── ORGANIZATION_COMPLETE.md       # Organization summary
├── db_status.sh                        # Convenience wrapper scripts
├── db_backup.sh                        # (These call scripts/ versions)
├── db_switch_ml_training.sh
└── db_switch_original.sh
```

---

## 🎯 Next Steps

### Immediate:
1. ✅ Databases are set up and backed up
2. ⏭️ Switch to ML training database
3. ⏭️ Start scanning diverse sites
4. ⏭️ Build ML classifier

### For Scanning:
I can help you with:
- Automated scanning scripts for all recommended sites
- Monitoring scan progress
- Analyzing results as you go
- Preparing data for ML training

### For ML Implementation:
I can help you with:
- Feature extraction from vulnerabilities
- Auto-labeling based on consistency
- Training the classifier
- Integration into the scanning pipeline

---

## ❓ Common Questions

**Q: Can I still access my original data?**
A: Yes! Either switch back with `./db_switch_original.sh` or access the backup directly.

**Q: What if I mess up?**
A: All switches create automatic backups. Use `python db_manager.py list` and `restore` to recover.

**Q: How do I know which database I'm using?**
A: Run `./db_status.sh` anytime to see current database and stats.

**Q: Can I compare both databases?**
A: Yes! Switch between them and run analysis scripts on each.

**Q: Should I delete the old database?**
A: No! Keep it for "before ML" comparison in your FYP.

---

## 🎓 For Your FYP Thesis

### What to Document:

1. **Dataset Collection Strategy**
   - "Created separate database for controlled ML training"
   - "Preserved original dataset for baseline comparison"
   - "Scanned 25 diverse sites across 3 categories"

2. **Methodology**
   - "Baseline: 127 scans, 23,517 vulnerabilities"
   - "Training set: 180 scans, 40,000+ vulnerabilities"
   - "Used database versioning for reproducibility"

3. **Results Comparison**
   - Table showing before/after metrics
   - False positive reduction percentage
   - Precision/recall improvements

---

## 📞 Need Help?

If you encounter issues:
1. Check status: `./db_status.sh`
2. List backups: `python db_manager.py list`
3. Check this guide
4. Ask me for help!

---

**Created**: November 11, 2025
**Status**: Ready for ML training phase
**Next**: Switch to ML training DB and start scanning! 🚀
