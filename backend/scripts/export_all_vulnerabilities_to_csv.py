#!/usr/bin/env python3
"""
Export vulnerabilities from ALL available SQLite databases into a single CSV.

This script is designed for ML dataset preparation. It scans:
- The current active database: backend/db.sqlite3
- The ML training database: backend/database/db_ml_training.sqlite3 (if exists)
- The production database: backend/database/db_production.sqlite3 (if exists)
- All backup databases under: backend/database/database_backups/*.sqlite3

Output:
- A single CSV file with ALL vulnerabilities combined:
  ML/dataset/all_vulnerabilities_from_all_dbs.csv

Each row includes a `source_db` column indicating which database it came from.
"""

import csv
import os
import glob
import sqlite3
from typing import List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # project root

CURRENT_DB = os.path.join(BASE_DIR, "db.sqlite3")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
ML_TRAINING_DB = os.path.join(DATABASE_DIR, "db_ml_training.sqlite3")
PRODUCTION_DB = os.path.join(DATABASE_DIR, "db_production.sqlite3")
BACKUP_DIR = os.path.join(DATABASE_DIR, "database_backups")

# Where to store the combined CSV for ML
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "ML", "dataset")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "all_vulnerabilities_from_all_dbs.csv")


def find_databases() -> List[Tuple[str, str]]:
    """
    Collect all database files we care about.

    Returns a list of (label, path).
    """
    dbs: List[Tuple[str, str]] = []

    if os.path.exists(CURRENT_DB):
        dbs.append(("current", CURRENT_DB))

    if os.path.exists(ML_TRAINING_DB):
        dbs.append(("ml_training", ML_TRAINING_DB))

    if os.path.exists(PRODUCTION_DB):
        dbs.append(("production", PRODUCTION_DB))

    if os.path.isdir(BACKUP_DIR):
        for path in sorted(glob.glob(os.path.join(BACKUP_DIR, "*.sqlite3"))):
            label = f"backup:{os.path.basename(path)}"
            dbs.append((label, path))

    return dbs


def export_vulnerabilities_from_db(label: str, db_path: str, writer: csv.DictWriter) -> int:
    """
    Export vulnerabilities from a single SQLite database.

    Returns the number of rows written.
    """
    if not os.path.exists(db_path):
        return 0

    rows_written = 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Join vulnerabilities with scans, configurations, and projects to match desired format
        # Table names follow Django defaults:
        # - scanning_vulnerability
        # - scanning_scan
        # - scanning_scanconfiguration
        # - projects_project
        query = """
        SELECT
            v.id AS vulnerability_id,
            p.id AS project_id,
            p.name AS project_name,
            s.id AS scan_id,
            s.uuid AS scan_uuid,
            sc.scan_type AS scan_type,
            COALESCE(s.target_url, p.target_url) AS target_url,
            v.name AS vulnerability_name,
            v.severity AS severity,
            v.description AS description,
            v.url AS url,
            v.parameter AS parameter,
            v.evidence AS evidence,
            v.confidence AS confidence,
            v.remediation AS remediation,
            v.created_at AS created_at
        FROM scanning_vulnerability v
        JOIN scanning_scan s ON v.scan_id = s.id
        JOIN scanning_scanconfiguration sc ON s.configuration_id = sc.id
        JOIN projects_project p ON sc.project_id = p.id
        """

        for row in cursor.execute(query):
            (
                vulnerability_id,
                project_id,
                project_name,
                scan_id,
                scan_uuid,
                scan_type,
                target_url,
                vulnerability_name,
                severity,
                description,
                url,
                parameter,
                evidence,
                confidence,
                remediation,
                created_at,
            ) = row

            # Normalize text fields to avoid newlines breaking CSV
            description_clean = (description or "").replace("\n", " ").replace("\r", "")
            evidence_clean = (evidence or "").replace("\n", " ").replace("\r", "")
            remediation_clean = (remediation or "").replace("\n", " ").replace("\r", "")

            writer.writerow(
                {
                    "vulnerability_id": vulnerability_id,
                    "project_id": project_id,
                    "project_name": project_name,
                    "scan_id": scan_id,
                    "scan_uuid": scan_uuid,
                    "scan_type": scan_type,
                    "target_url": target_url,
                    "vulnerability_name": vulnerability_name,
                    "severity": severity,
                    "description": description_clean,
                    "url": url,
                    "parameter": parameter,
                    "evidence": evidence_clean,
                    "confidence": confidence,
                    "remediation": remediation_clean,
                    "created_at": created_at,
                }
            )
            rows_written += 1

    except sqlite3.OperationalError as e:
        # Likely the table doesn't exist (very old DB or empty DB) – just skip it.
        print(f"[WARN] Skipping DB '{db_path}' ({label}): {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

    print(f"[INFO] Exported {rows_written} vulnerabilities from {label} ({db_path})")
    return rows_written


def main() -> None:
    databases = find_databases()

    if not databases:
        print("No databases found. Nothing to export.")
        return

    print("Found the following databases:")
    for label, path in databases:
        print(f"  - {label}: {path}")

    # Exact header format requested for ML:
    fieldnames = [
        "vulnerability_id",
        "project_id",
        "project_name",
        "scan_id",
        "scan_uuid",
        "scan_type",
        "target_url",
        "vulnerability_name",
        "severity",
        "description",
        "url",
        "parameter",
        "evidence",
        "confidence",
        "remediation",
        "created_at",
    ]

    total = 0
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for label, path in databases:
            total += export_vulnerabilities_from_db(label, path, writer)

    print(f"\n✅ Done. Exported {total} vulnerabilities into:")
    print(f"   {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

