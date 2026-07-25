"""Backup service for MongoDB database export/import with media support."""

import os
import json
import zipfile
import shutil
from typing import Dict, List, Optional
from datetime import datetime

from app.config import settings
from app.utils.logger import logger
from app.utils.jdatetime_helper import get_jalali_date, get_jalali_time

# All MongoDB collections to backup (including counters for ID continuity)
BACKUP_COLLECTIONS = [
    "users",
    "transactions",
    "payments",
    "customers",
    "card_info",
    "reminders",
    "backups",
    "counters",
]

# Data-only collections (no backups/metadata records)
DATA_COLLECTIONS = [
    "users",
    "transactions",
    "payments",
    "customers",
    "card_info",
    "reminders",
    "counters",
]


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB documents."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _ensure_backup_dir():
    """Ensure backup directory exists."""
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)


def _generate_backup_filename(backup_type: str = "full") -> str:
    """Generate a backup filename with timestamp."""
    date_str = get_jalali_date().replace("/", "-")
    time_str = get_jalali_time().replace(":", "-")
    return f"hesab_{backup_type}_backup_{date_str}_{time_str}.zip"


def _get_upload_dirs() -> List[str]:
    """Get all upload directories that exist."""
    dirs = []
    # Main uploads dir from config
    if os.path.isdir(settings.UPLOAD_DIR):
        dirs.append(settings.UPLOAD_DIR)
    # Inner hesab/uploads/ dir
    inner_dir = os.path.join(os.path.dirname(settings.UPLOAD_DIR), "hesab", "uploads")
    if os.path.isdir(inner_dir) and inner_dir != settings.UPLOAD_DIR:
        dirs.append(inner_dir)
    return dirs


def _collect_db_data(db, collections: List[str]) -> Dict:
    """Export collections from MongoDB to dict."""
    collections_data = {}
    total_docs = 0
    for coll_name in collections:
        try:
            docs = list(db[coll_name].find())
            for doc in docs:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            collections_data[coll_name] = docs
            total_docs += len(docs)
        except Exception as e:
            logger.warning(f"Failed to backup collection {coll_name}: {e}")
            collections_data[coll_name] = []
    return collections_data, total_docs


def _add_media_to_zip(zf: zipfile.ZipFile) -> int:
    """Add all upload directories to the ZIP file.
    Deduplicates files with the same name (first occurrence wins).
    
    Returns:
        Number of media files added.
    """
    media_count = 0
    upload_dirs = _get_upload_dirs()
    added_names = set()
    
    for upload_dir in upload_dirs:
        for root, dirs, files in os.walk(upload_dir):
            for fname in files:
                # Skip Windows Zone.Identifier files
                if fname.endswith(":Zone.Identifier"):
                    continue
                # Deduplicate by filename
                if fname in added_names:
                    continue
                added_names.add(fname)
                fpath = os.path.join(root, fname)
                arcname = os.path.join("media", fname)
                try:
                    zf.write(fpath, arcname)
                    media_count += 1
                except Exception as e:
                    logger.warning(f"Failed to add media file {fpath}: {e}")
    
    return media_count


def _extract_media_from_zip(zf: zipfile.ZipFile, base_dir: str) -> int:
    """Extract media files from ZIP to the uploads directory.
    
    Returns:
        Number of media files restored.
    """
    restored = 0
    upload_dir = settings.UPLOAD_DIR
    
    for name in zf.namelist():
        if not name.startswith("media/"):
            continue
        # Extract to the uploads directory
        rel_path = name[len("media/"):]
        if not rel_path:
            continue
        dest_path = os.path.join(upload_dir, rel_path)
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with zf.open(name) as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            restored += 1
        except Exception as e:
            logger.warning(f"Failed to restore media file {name}: {e}")
    
    return restored


def create_full_backup() -> Dict:
    """Create a full backup: all MongoDB collections + all media files.
    
    Returns:
        dict with keys: filename, filepath, file_size, collections, total_docs, media_files
    """
    from app.database.models import get_database

    _ensure_backup_dir()
    db = get_database()
    filename = _generate_backup_filename("full")
    filepath = os.path.join(settings.BACKUP_DIR, filename)

    collections_data, total_docs = _collect_db_data(db, BACKUP_COLLECTIONS)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write metadata
        metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "jalali_date": get_jalali_date(),
            "jalali_time": get_jalali_time(),
            "database": settings.MONGO_DB_NAME,
            "backup_type": "full",
            "collections": list(collections_data.keys()),
            "total_documents": total_docs,
            "has_media": True,
            "version": "2.0",
        }
        zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2, cls=JSONEncoder))

        # Write each collection as a separate JSON file
        for coll_name, docs in collections_data.items():
            zf.writestr(f"db/{coll_name}.json", json.dumps(docs, ensure_ascii=False, indent=2, cls=JSONEncoder))

        # Add media files
        media_count = _add_media_to_zip(zf)

    file_size = os.path.getsize(filepath)
    logger.info(f"Full backup created: {filename} ({file_size} bytes, {total_docs} docs, {media_count} media)")

    return {
        "filename": filename,
        "filepath": filepath,
        "file_size": file_size,
        "collections": len(collections_data),
        "total_docs": total_docs,
        "media_files": media_count,
    }


def create_db_backup() -> Dict:
    """Create a database-only backup (no media, no backup records).
    
    Returns:
        dict with keys: filename, filepath, file_size, collections, total_docs
    """
    from app.database.models import get_database

    _ensure_backup_dir()
    db = get_database()
    filename = _generate_backup_filename("db")
    filepath = os.path.join(settings.BACKUP_DIR, filename)

    collections_data, total_docs = _collect_db_data(db, DATA_COLLECTIONS)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "jalali_date": get_jalali_date(),
            "jalali_time": get_jalali_time(),
            "database": settings.MONGO_DB_NAME,
            "backup_type": "database",
            "collections": list(collections_data.keys()),
            "total_documents": total_docs,
            "has_media": False,
            "version": "2.0",
        }
        zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2, cls=JSONEncoder))

        for coll_name, docs in collections_data.items():
            zf.writestr(f"db/{coll_name}.json", json.dumps(docs, ensure_ascii=False, indent=2, cls=JSONEncoder))

    file_size = os.path.getsize(filepath)
    logger.info(f"DB backup created: {filename} ({file_size} bytes, {total_docs} documents)")

    return {
        "filename": filename,
        "filepath": filepath,
        "file_size": file_size,
        "collections": len(collections_data),
        "total_docs": total_docs,
    }


def create_media_backup() -> Dict:
    """Create a media-only backup (just uploads/ directories).
    
    Returns:
        dict with keys: filename, filepath, file_size, media_files
    """
    _ensure_backup_dir()
    filename = _generate_backup_filename("media")
    filepath = os.path.join(settings.BACKUP_DIR, filename)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "jalali_date": get_jalali_date(),
            "jalali_time": get_jalali_time(),
            "backup_type": "media",
            "has_media": True,
            "version": "2.0",
        }
        zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2, cls=JSONEncoder))
        media_count = _add_media_to_zip(zf)

    file_size = os.path.getsize(filepath)
    logger.info(f"Media backup created: {filename} ({file_size} bytes, {media_count} files)")

    return {
        "filename": filename,
        "filepath": filepath,
        "file_size": file_size,
        "media_files": media_count,
    }


def get_backup_metadata(filepath: str) -> Optional[Dict]:
    """Read metadata from a backup ZIP file."""
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            if "metadata.json" in zf.namelist():
                return json.loads(zf.read("metadata.json"))
    except Exception as e:
        logger.error(f"Failed to read backup metadata: {e}")
    return None


def verify_backup_integrity(filepath: str) -> Dict:
    """Verify that a backup file is valid and complete.
    
    Returns:
        dict with keys: valid, collections, total_docs, media_files, errors
    """
    result = {"valid": False, "collections": 0, "total_docs": 0, "media_files": 0, "errors": []}

    if not os.path.exists(filepath):
        result["errors"].append("فایل پشتیبان یافت نشد")
        return result

    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            # Check ZIP integrity
            bad_file = zf.testzip()
            if bad_file:
                result["errors"].append(f"فایل خراب: {bad_file}")
                return result

            # Check for metadata
            if "metadata.json" not in zf.namelist():
                result["errors"].append("فایل metadata.json یافت نشد")
                return result

            metadata = json.loads(zf.read("metadata.json"))
            namelist = zf.namelist()

            # Verify each collection file exists and is valid JSON
            total_docs = 0
            for coll_name in metadata.get("collections", []):
                # Support both old format (coll.json) and new format (db/coll.json)
                coll_file = f"db/{coll_name}.json"
                if coll_file not in namelist:
                    coll_file = f"{coll_name}.json"
                if coll_file not in namelist:
                    result["errors"].append(f"فایل {coll_file} یافت نشد")
                    continue

                try:
                    docs = json.loads(zf.read(coll_file))
                    if not isinstance(docs, list):
                        result["errors"].append(f"{coll_file}: فرمت نامعتبر")
                        continue
                    total_docs += len(docs)
                except json.JSONDecodeError:
                    result["errors"].append(f"{coll_file}: JSON نامعتبر")

            # Count media files
            media_files = len([n for n in namelist if n.startswith("media/") and not n.endswith("/")])

            result["valid"] = len(result["errors"]) == 0
            result["collections"] = len(metadata.get("collections", []))
            result["total_docs"] = total_docs
            result["media_files"] = media_files

    except zipfile.BadZipFile:
        result["errors"].append("فایل ZIP نامعتبر")
    except Exception as e:
        result["errors"].append(f"خطای غیرمنتظره: {str(e)}")

    return result


def restore_from_backup(filepath: str, drop_existing: bool = False) -> Dict:
    """Restore database and media from a backup ZIP file.
    
    Args:
        filepath: Path to the backup ZIP file
        drop_existing: If True, drop existing collections before restore
    
    Returns:
        dict with keys: success, collections_restored, total_docs, media_restored, errors
    """
    from app.database.models import get_database

    result = {
        "success": False,
        "collections_restored": 0,
        "total_docs": 0,
        "media_restored": 0,
        "errors": []
    }

    if not os.path.exists(filepath):
        result["errors"].append("فایل پشتیبان یافت نشد")
        return result

    try:
        db = get_database()

        with zipfile.ZipFile(filepath, "r") as zf:
            if "metadata.json" not in zf.namelist():
                result["errors"].append("فایل metadata.json یافت نشد")
                return result

            metadata = json.loads(zf.read("metadata.json"))
            collections = metadata.get("collections", [])
            namelist = zf.namelist()

            # Restore database collections
            for coll_name in collections:
                # Support both old and new format
                coll_file = f"db/{coll_name}.json"
                if coll_file not in namelist:
                    coll_file = f"{coll_name}.json"
                if coll_file not in namelist:
                    result["errors"].append(f"فایل {coll_file} یافت نشد")
                    continue

                try:
                    docs = json.loads(zf.read(coll_file))
                    if not isinstance(docs, list):
                        result["errors"].append(f"{coll_file}: فرمت نامعتبر")
                        continue

                    if drop_existing:
                        db[coll_name].drop()

                    if docs:
                        # Remove _id to avoid conflicts on insert
                        for doc in docs:
                            if "_id" in doc:
                                del doc["_id"]
                        try:
                            db[coll_name].insert_many(docs, ordered=False)
                        except Exception as e:
                            # Some may fail due to duplicates on non-drop restore
                            if drop_existing:
                                raise
                            logger.warning(f"Partial restore of {coll_name}: {e}")

                    result["collections_restored"] += 1
                    result["total_docs"] += len(docs)
                    logger.info(f"Restored collection {coll_name}: {len(docs)} documents")

                except Exception as e:
                    result["errors"].append(f"خطا در بازیابی {coll_name}: {str(e)}")

            # Restore media files if present
            has_media = metadata.get("has_media", False) or any(n.startswith("media/") for n in namelist)
            if has_media:
                media_restored = _extract_media_from_zip(zf, settings.UPLOAD_DIR)
                result["media_restored"] = media_restored
                logger.info(f"Restored {media_restored} media files")

        result["success"] = result["collections_restored"] > 0

    except zipfile.BadZipFile:
        result["errors"].append("فایل ZIP نامعتبر")
    except Exception as e:
        result["errors"].append(f"خطای غیرمنتظره: {str(e)}")

    return result


def list_backup_files() -> List[Dict]:
    """List all backup files in the backup directory.
    
    Returns:
        list of dicts with keys: filename, filepath, file_size, jalali_date, backup_type, media_files
    """
    _ensure_backup_dir()
    backups = []

    for f in sorted(os.listdir(settings.BACKUP_DIR), reverse=True):
        if not f.endswith(".zip"):
            continue
        filepath = os.path.join(settings.BACKUP_DIR, f)
        file_size = os.path.getsize(filepath)

        metadata = get_backup_metadata(filepath)
        backup_type = metadata.get("backup_type", "unknown") if metadata else "unknown"
        jalali_date = metadata.get("jalali_date", "") if metadata else ""
        jalali_time = metadata.get("jalali_time", "") if metadata else ""
        total_docs = metadata.get("total_documents", 0) if metadata else 0
        has_media = metadata.get("has_media", False) if metadata else False

        backups.append({
            "filename": f,
            "filepath": filepath,
            "file_size": file_size,
            "jalali_date": jalali_date,
            "jalali_time": jalali_time,
            "backup_type": backup_type,
            "total_docs": total_docs,
            "has_media": has_media,
        })

    return backups


def delete_backup_file(filepath: str) -> bool:
    """Delete a backup file."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Backup deleted: {filepath}")
            return True
    except Exception as e:
        logger.error(f"Failed to delete backup: {e}")
    return False


def cleanup_old_backups(keep_count: int = 10) -> int:
    """Delete old backup files, keeping the most recent ones.
    
    Returns:
        Number of files deleted
    """
    backups = list_backup_files()
    if len(backups) <= keep_count:
        return 0

    to_delete = backups[keep_count:]
    deleted = 0
    for b in to_delete:
        if delete_backup_file(b["filepath"]):
            deleted += 1

    logger.info(f"Cleanup: deleted {deleted} old backups, kept {keep_count}")
    return deleted


def get_backup_stats() -> Dict:
    """Get backup statistics.
    
    Returns:
        dict with keys: total_backups, total_size, latest_backup, backup_types, total_media_size
    """
    backups = list_backup_files()
    total_size = sum(b["file_size"] for b in backups)
    backup_types = {}
    media_count = 0
    for b in backups:
        bt = b["backup_type"]
        backup_types[bt] = backup_types.get(bt, 0) + 1
        if b.get("has_media"):
            media_count += 1

    return {
        "total_backups": len(backups),
        "total_size": total_size,
        "latest_backup": backups[0] if backups else None,
        "backup_types": backup_types,
        "backups_with_media": media_count,
    }
