#!/usr/bin/env python3
"""
Database Manager for Security Scanner Project
Handles backup, restore, and switching between different database versions
"""

import os
import sys
import shutil
from datetime import datetime
import argparse

# Database paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # Parent directory (backend/)
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
BACKUP_DIR = os.path.join(DATABASE_DIR, 'database_backups')
CURRENT_DB = os.path.join(BASE_DIR, 'db.sqlite3')
ML_TRAINING_DB = os.path.join(DATABASE_DIR, 'db_ml_training.sqlite3')
PRODUCTION_DB = os.path.join(DATABASE_DIR, 'db_production.sqlite3')

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

def get_db_size(db_path):
    """Get human-readable database size"""
    if not os.path.exists(db_path):
        return "N/A"
    size_bytes = os.path.getsize(db_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def backup_database(db_path=CURRENT_DB, name_prefix="db_backup"):
    """Backup a database with timestamp"""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{name_prefix}_{timestamp}.sqlite3"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    print(f"📦 Backing up database...")
    print(f"   Source: {db_path}")
    print(f"   Size: {get_db_size(db_path)}")
    print(f"   Destination: {backup_path}")

    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created successfully!")
    return backup_path

def create_fresh_database(db_path):
    """Create a fresh database by removing existing and running migrations"""
    if os.path.exists(db_path):
        print(f"🗑️  Removing existing database: {db_path}")
        os.remove(db_path)

    print(f"🆕 Creating fresh database: {db_path}")

    # Temporarily rename current db if it exists
    temp_current = None
    if os.path.exists(CURRENT_DB) and db_path != CURRENT_DB:
        temp_current = CURRENT_DB + ".temp"
        shutil.move(CURRENT_DB, temp_current)

    # Create new database at target location
    if db_path != CURRENT_DB:
        # Create empty file at target location
        open(db_path, 'a').close()
        # Temporarily make it the current db for migrations
        if os.path.exists(CURRENT_DB):
            os.remove(CURRENT_DB)
        shutil.copy2(db_path, CURRENT_DB)

    # Run migrations
    print("🔄 Running migrations...")
    os.system(f"cd {BASE_DIR} && python manage.py migrate --noinput")

    # If we created a different db, copy back
    if db_path != CURRENT_DB:
        shutil.copy2(CURRENT_DB, db_path)
        os.remove(CURRENT_DB)

        # Restore original current db if it existed
        if temp_current:
            shutil.move(temp_current, CURRENT_DB)

    print(f"✅ Fresh database created: {db_path}")

def switch_database(target_db, backup_current=True):
    """Switch to a different database"""
    if not os.path.exists(target_db):
        print(f"❌ Target database not found: {target_db}")
        print(f"   Would you like to create it? (y/n)")
        response = input().strip().lower()
        if response == 'y':
            create_fresh_database(target_db)
        else:
            return False

    # Backup current database if it exists
    if backup_current and os.path.exists(CURRENT_DB):
        backup_database(CURRENT_DB, "db_before_switch")

    # Switch
    print(f"🔄 Switching database...")
    print(f"   From: {CURRENT_DB} ({get_db_size(CURRENT_DB)})")
    print(f"   To: {target_db} ({get_db_size(target_db)})")

    if os.path.exists(CURRENT_DB):
        os.remove(CURRENT_DB)

    shutil.copy2(target_db, CURRENT_DB)
    print(f"✅ Database switched successfully!")
    return True

def list_backups():
    """List all available backups"""
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.sqlite3')]
    backups.sort(reverse=True)

    print("\n📚 Available Backups:")
    print("-" * 80)
    for backup in backups:
        backup_path = os.path.join(BACKUP_DIR, backup)
        size = get_db_size(backup_path)
        timestamp = os.path.getmtime(backup_path)
        date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {backup:50s} | {size:>10s} | {date_str}")
    print("-" * 80)

def get_db_stats(db_path):
    """Get statistics from a database"""
    if not os.path.exists(db_path):
        return None

    # Temporarily switch to this db for stats
    temp_current = None
    needs_restore = False

    if db_path != CURRENT_DB:
        if os.path.exists(CURRENT_DB):
            temp_current = CURRENT_DB + ".temp_stats"
            shutil.move(CURRENT_DB, temp_current)
            needs_restore = True
        shutil.copy2(db_path, CURRENT_DB)

    # Get stats using Django
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

    from scanning.models import Scan, Vulnerability

    stats = {
        'scans': Scan.objects.count(),
        'vulnerabilities': Vulnerability.objects.count(),
        'size': get_db_size(db_path)
    }

    # Restore original db if needed
    if needs_restore:
        os.remove(CURRENT_DB)
        shutil.move(temp_current, CURRENT_DB)

    return stats

def show_status():
    """Show current database status"""
    print("\n" + "="*80)
    print("DATABASE STATUS")
    print("="*80)

    print("\n📊 Current Active Database:")
    if os.path.exists(CURRENT_DB):
        print(f"   Location: {CURRENT_DB}")
        print(f"   Size: {get_db_size(CURRENT_DB)}")
        try:
            stats = get_db_stats(CURRENT_DB)
            if stats:
                print(f"   Scans: {stats['scans']}")
                print(f"   Vulnerabilities: {stats['vulnerabilities']}")
        except:
            print("   Stats: Unable to fetch")
    else:
        print("   ❌ No active database")

    print("\n📦 Available Database Versions:")

    databases = {
        "ML Training": ML_TRAINING_DB,
        "Production": PRODUCTION_DB,
    }

    for name, path in databases.items():
        status = "✅ Exists" if os.path.exists(path) else "❌ Not created"
        size = get_db_size(path) if os.path.exists(path) else "N/A"
        print(f"   {name:15s}: {status:12s} | Size: {size:>10s}")

    print("\n💾 Recent Backups:")
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith('.sqlite3')],
        key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x)),
        reverse=True
    )[:5]

    if backups:
        for backup in backups:
            backup_path = os.path.join(BACKUP_DIR, backup)
            size = get_db_size(backup_path)
            timestamp = os.path.getmtime(backup_path)
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            print(f"   {backup:45s} | {size:>8s} | {date_str}")
    else:
        print("   No backups found")

    print("="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Database Manager for Security Scanner')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Backup command
    parser_backup = subparsers.add_parser('backup', help='Backup current database')
    parser_backup.add_argument('--name', default='db_backup', help='Backup name prefix')

    # Switch command
    parser_switch = subparsers.add_parser('switch', help='Switch to a different database')
    parser_switch.add_argument('target', choices=['ml-training', 'production', 'original'],
                              help='Target database to switch to')
    parser_switch.add_argument('--no-backup', action='store_true',
                              help='Do not backup current database before switching')

    # Create command
    parser_create = subparsers.add_parser('create', help='Create a fresh database')
    parser_create.add_argument('name', choices=['ml-training', 'production'],
                              help='Database to create')

    # List command
    subparsers.add_parser('list', help='List all backups')

    # Status command
    subparsers.add_parser('status', help='Show database status')

    # Restore command
    parser_restore = subparsers.add_parser('restore', help='Restore from backup')
    parser_restore.add_argument('backup_file', help='Backup file name')

    args = parser.parse_args()

    if args.command == 'backup':
        backup_database(name_prefix=args.name)

    elif args.command == 'switch':
        target_map = {
            'ml-training': ML_TRAINING_DB,
            'production': PRODUCTION_DB,
            'original': os.path.join(BACKUP_DIR, 'db_original_20251111_121456.sqlite3')
        }
        switch_database(target_map[args.target], backup_current=not args.no_backup)

    elif args.command == 'create':
        target_map = {
            'ml-training': ML_TRAINING_DB,
            'production': PRODUCTION_DB
        }
        create_fresh_database(target_map[args.name])

    elif args.command == 'list':
        list_backups()

    elif args.command == 'status':
        show_status()

    elif args.command == 'restore':
        backup_path = os.path.join(BACKUP_DIR, args.backup_file)
        if os.path.exists(backup_path):
            switch_database(backup_path)
        else:
            print(f"❌ Backup not found: {backup_path}")

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
