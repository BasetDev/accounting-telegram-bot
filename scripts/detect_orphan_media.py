#!/usr/bin/env python3
"""Detect and optionally clean up orphaned media files in the uploads directory.

Usage:
    python scripts/detect_orphan_media.py              # Report only
    python scripts/detect_orphan_media.py --delete     # Report and delete orphans
    python scripts/detect_orphan_media.py --dry-run    # Report only (explicit)

Requires a running MongoDB instance configured in .env.
"""

import os
import sys
import argparse

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "hesab"))

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app.config import settings
from app.database.models import get_database


def collect_db_photo_filenames(db) -> set:
    """Collect all photo filenames referenced in the database."""
    db_photos = set()

    # From transactions collection
    for txn in db.transactions.find(
        {"photo_path": {"$ne": None, "$exists": True}}, {"photo_path": 1}
    ):
        pp = txn.get("photo_path")
        if pp:
            db_photos.add(os.path.basename(pp))

    # From payments collection
    for pay in db.payments.find(
        {"photo_path": {"$ne": None, "$exists": True}}, {"photo_path": 1}
    ):
        pp = pay.get("photo_path")
        if pp:
            db_photos.add(os.path.basename(pp))

    return db_photos


def collect_disk_filenames(upload_dir: str) -> set:
    """Collect all filenames on disk in the uploads directory."""
    disk_files = set()
    if not os.path.isdir(upload_dir):
        return disk_files
    for f in os.listdir(upload_dir):
        fpath = os.path.join(upload_dir, f)
        if os.path.isfile(fpath) and not f.endswith(":Zone.Identifier"):
            disk_files.add(f)
    return disk_files


def find_broken_refs(db) -> list:
    """Find DB records whose photo_path points to a non-existent file."""
    broken = []

    for txn in db.transactions.find(
        {"photo_path": {"$ne": None, "$exists": True}},
        {"id": 1, "photo_path": 1, "transaction_type": 1},
    ):
        pp = txn.get("photo_path")
        if pp and not os.path.exists(pp):
            broken.append(
                {"collection": "transactions", "id": txn["id"], "photo_path": pp}
            )

    for pay in db.payments.find(
        {"photo_path": {"$ne": None, "$exists": True}},
        {"id": 1, "photo_path": 1},
    ):
        pp = pay.get("photo_path")
        if pp and not os.path.exists(pp):
            broken.append(
                {"collection": "payments", "id": pay["id"], "photo_path": pp}
            )

    return broken


def main():
    parser = argparse.ArgumentParser(description="Detect orphaned media files")
    parser.add_argument(
        "--delete", action="store_true", help="Delete orphaned files from disk"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Report only (default)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ORPHAN MEDIA DETECTION SCRIPT")
    print("=" * 60)

    try:
        db = get_database()
    except Exception as e:
        print(f"\nERROR: Could not connect to MongoDB: {e}")
        print("Ensure MongoDB is running and MONGO_URI is set in .env")
        sys.exit(1)

    upload_dir = settings.UPLOAD_DIR
    print(f"\nUpload directory: {upload_dir}")

    # Collect references
    db_photos = collect_db_photo_filenames(db)
    disk_files = collect_disk_filenames(upload_dir)

    print(f"Photos referenced in DB: {len(db_photos)}")
    print(f"Files on disk: {len(disk_files)}")

    # Orphans: on disk but not in DB
    orphans = sorted(disk_files - db_photos)
    print(f"\n--- ORPHANED FILES (on disk, not in DB): {len(orphans)} ---")
    total_orphan_bytes = 0
    for f in orphans:
        fpath = os.path.join(upload_dir, f)
        size = os.path.getsize(fpath)
        total_orphan_bytes += size
        print(f"  {f} ({size:,} bytes)")

    if orphans:
        print(f"\nTotal orphan size: {total_orphan_bytes:,} bytes ({total_orphan_bytes / 1024:.1f} KB)")

    # Missing: in DB but not on disk
    missing = sorted(db_photos - disk_files)
    print(f"\n--- MISSING FILES (in DB, not on disk): {len(missing)} ---")
    for f in missing:
        print(f"  {f}")

    # Broken references
    broken = find_broken_refs(db)
    print(f"\n--- BROKEN DB REFERENCES (photo_path points to missing file): {len(broken)} ---")
    for b in broken:
        print(f"  {b['collection']}#{b['id']}: {b['photo_path']}")

    # DB stats
    print(f"\n--- DATABASE COLLECTION STATS ---")
    for coll_name in ["users", "transactions", "payments", "customers",
                      "card_info", "reminders", "backups", "counters"]:
        count = db[coll_name].count_documents({})
        print(f"  {coll_name}: {count} documents")

    # Action
    if args.delete and orphans:
        print(f"\n--- DELETING {len(orphans)} ORPHANED FILES ---")
        deleted = 0
        for f in orphans:
            fpath = os.path.join(upload_dir, f)
            try:
                os.remove(fpath)
                deleted += 1
                print(f"  DELETED: {f}")
            except OSError as e:
                print(f"  FAILED:  {f} ({e})")
        print(f"\nDeleted {deleted}/{len(orphans)} orphaned files.")
    elif orphans:
        print(f"\nTo delete orphaned files, run: python {__file__} --delete")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"  Orphaned files: {len(orphans)}")
    print(f"  Missing files:  {len(missing)}")
    print(f"  Broken refs:    {len(broken)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
