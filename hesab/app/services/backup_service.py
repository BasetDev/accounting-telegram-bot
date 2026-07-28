"""Backup service for MongoDB database export/import with media support.

The backup format is versioned and tied to the current bot version.
Only the current backup format (v3.0) is supported — legacy format
compatibility has been removed.
"""

import os
import re
import json
import uuid
import zipfile
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from app.config import settings
from app.utils.logger import logger
from app.utils.jdatetime_helper import get_jalali_date, get_jalali_time
from app.database.models import create_user_doc

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

# Collections that may contain photo_path fields
PHOTO_PATH_COLLECTIONS = {
    "transactions": ["photo_path"],
    "payments": ["photo_path"],
}

BACKUP_VERSION = "3.0"


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB documents."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        fallback = str(obj)
        try:
            return super().default(obj)
        except TypeError:
            return fallback


def _ensure_backup_dir():
    """Ensure backup directory exists."""
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)


def _generate_backup_filename(backup_type: str = "full") -> str:
    """Generate a backup filename with timestamp and unique ID."""
    date_str = get_jalali_date().replace("/", "-")
    time_str = get_jalali_time().replace(":", "-")
    unique_id = uuid.uuid4().hex[:6]
    return f"hesab_{backup_type}_backup_{date_str}_{time_str}_{unique_id}.zip"


def _get_upload_dirs() -> List[str]:
    """Get all upload directories that exist."""
    dirs = []
    if os.path.isdir(settings.UPLOAD_DIR):
        dirs.append(settings.UPLOAD_DIR)
    inner_dir = os.path.join(os.path.dirname(settings.UPLOAD_DIR), "hesab", "uploads")
    if os.path.isdir(inner_dir) and inner_dir != settings.UPLOAD_DIR:
        dirs.append(inner_dir)
    return dirs


def _normalize_photo_path(photo_path: str) -> str:
    """Convert an absolute photo path to a relative path (just the filename).
    
    Example:
        /home/bac/New folder/New/hesab/uploads/your_telegram_user_id_here_14050503_162525.jpg
        -> your_telegram_user_id_here_14050503_162525.jpg
    """
    if not photo_path:
        return photo_path
    # Extract just the filename
    return os.path.basename(photo_path)


def _resolve_photo_path(relative_path: str) -> str:
    """Resolve a relative photo path to the current installation's absolute path.
    
    Example:
        your_telegram_user_id_here_14050503_162525.jpg
        -> /home/bac/New folder/New/hesab/uploads/your_telegram_user_id_here_14050503_162525.jpg
    """
    if not relative_path:
        return relative_path
    # If already absolute, return as-is
    if os.path.isabs(relative_path):
        return relative_path
    return os.path.join(settings.UPLOAD_DIR, relative_path)


def _normalize_doc_paths(doc: dict, collection_name: str) -> dict:
    """Normalize photo_path fields in a document from absolute to relative."""
    if collection_name not in PHOTO_PATH_COLLECTIONS:
        return doc
    for field in PHOTO_PATH_COLLECTIONS[collection_name]:
        if field in doc and doc[field]:
            doc[field] = _normalize_photo_path(doc[field])
    return doc


def _remap_doc_paths(doc: dict, collection_name: str) -> dict:
    """Remap relative photo_path fields to the current installation's absolute paths."""
    if collection_name not in PHOTO_PATH_COLLECTIONS:
        return doc
    for field in PHOTO_PATH_COLLECTIONS[collection_name]:
        if field in doc and doc[field]:
            doc[field] = _resolve_photo_path(doc[field])
    return doc


def _collect_db_data(db, collections: List[str], normalize_paths: bool = True) -> Tuple[Dict, int]:
    """Export collections from MongoDB to dict.
    
    Args:
        db: MongoDB database instance
        collections: List of collection names to export
        normalize_paths: If True, convert absolute photo paths to relative
    
    Returns:
        Tuple of (collections_data dict, total document count)
    """
    collections_data = {}
    total_docs = 0
    for coll_name in collections:
        try:
            docs = list(db[coll_name].find())
            for doc in docs:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if normalize_paths:
                    doc = _normalize_doc_paths(doc, coll_name)
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
                if fname.endswith(":Zone.Identifier"):
                    continue
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


def _extract_media_from_zip(zf: zipfile.ZipFile) -> Tuple[int, List[str]]:
    """Extract media files from ZIP to the uploads directory.
    
    Returns:
        Tuple of (number of media files restored, list of error messages)
    """
    restored = 0
    errors = []
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except Exception as e:
        errors.append(f"Failed to create upload directory: {e}")
        return restored, errors
    
    for name in zf.namelist():
        if not name.startswith("media/"):
            continue
        rel_path = name[len("media/"):]
        if not rel_path:
            continue
        dest_path = os.path.abspath(os.path.join(upload_dir, rel_path))
        if not dest_path.startswith(upload_dir + os.sep):
            error_msg = f"Skipped unsafe media path: {name}"
            logger.warning(error_msg)
            errors.append(error_msg)
            continue
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with zf.open(name) as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            restored += 1
        except Exception as e:
            error_msg = f"Failed to restore media file {name}: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)
    
    return restored, errors


def validate_uploaded_backup(filepath: str) -> Dict:
    """Validate an uploaded backup file for cross-bot restore.
    
    Returns:
        dict with keys: valid, metadata, collections, total_docs, media_files, errors, warnings
    """
    result = {
        "valid": False,
        "metadata": None,
        "collections": 0,
        "total_docs": 0,
        "media_files": 0,
        "errors": [],
        "warnings": [],
    }

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

            try:
                metadata = json.loads(zf.read("metadata.json"))
            except Exception as e:
                result["errors"].append(f"metadata.json قابل خواندن نیست: {str(e)}")
                return result

            result["metadata"] = metadata
            namelist = zf.namelist()

            # Version compatibility check
            backup_version = metadata.get("version", "unknown")
            if backup_version != BACKUP_VERSION:
                result["errors"].append(
                    f"نسخه پشتیبان ({backup_version}) با نسخه فعلی ({BACKUP_VERSION}) سازگار نیست"
                )
                return result

            # Verify each collection file
            total_docs = 0
            for coll_name in metadata.get("collections", []):
                coll_file = f"db/{coll_name}.json"
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

            # Validate media file references in transactions and payments
            media_filenames = set()
            for name in namelist:
                if name.startswith("media/") and not name.endswith("/"):
                    media_filenames.add(name[len("media/"):])
            
            # Check if photo_path references in transactions/payments exist in media/
            for coll_name in ["transactions", "payments"]:
                coll_file = f"db/{coll_name}.json"
                if coll_file in namelist:
                    try:
                        docs = json.loads(zf.read(coll_file))
                        for doc in docs:
                            photo_path = doc.get("photo_path")
                            if photo_path:
                                fname = os.path.basename(photo_path)
                                if fname not in media_filenames:
                                    result["warnings"].append(
                                        f"عکس {fname} در {coll_name} در فایل پشتیبان یافت نشد"
                                    )
                    except Exception:
                        pass  # Already validated above

            result["valid"] = len(result["errors"]) == 0
            result["collections"] = len(metadata.get("collections", []))
            result["total_docs"] = total_docs
            result["media_files"] = media_files

    except zipfile.BadZipFile:
        result["errors"].append("فایل ZIP نامعتبر")
    except Exception as e:
        result["errors"].append(f"خطای غیرمنتظره: {str(e)}")

    return result


def create_full_backup() -> Dict:
    """Create a full backup: all MongoDB collections + all media files.
    Photo paths are normalized to relative paths for portability.
    """
    from app.database.models import get_database

    _ensure_backup_dir()
    db = get_database()
    filename = _generate_backup_filename("full")
    filepath = os.path.join(settings.BACKUP_DIR, filename)

    collections_data, total_docs = _collect_db_data(db, BACKUP_COLLECTIONS, normalize_paths=True)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "jalali_date": get_jalali_date(),
            "jalali_time": get_jalali_time(),
            "database": settings.MONGO_DB_NAME,
            "backup_type": "full",
            "collections": list(collections_data.keys()),
            "total_documents": total_docs,
            "has_media": True,
            "version": BACKUP_VERSION,
        }
        zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2, cls=JSONEncoder))

        for coll_name, docs in collections_data.items():
            zf.writestr(f"db/{coll_name}.json", json.dumps(docs, ensure_ascii=False, indent=2, cls=JSONEncoder))

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
    """Create a database-only backup (no media, no backup records)."""
    from app.database.models import get_database

    _ensure_backup_dir()
    db = get_database()
    filename = _generate_backup_filename("db")
    filepath = os.path.join(settings.BACKUP_DIR, filename)

    collections_data, total_docs = _collect_db_data(db, DATA_COLLECTIONS, normalize_paths=True)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "jalali_date": get_jalali_date(),
            "jalali_time": get_jalali_time(),
            "database": settings.MONGO_DB_NAME,
            "backup_type": "database",
            "collections": list(collections_data.keys()),
            "total_documents": total_docs,
            "has_media": False,
            "version": BACKUP_VERSION,
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
    """Create a media-only backup (just uploads/ directories)."""
    _ensure_backup_dir()
    filename = _generate_backup_filename("media")
    filepath = os.path.join(settings.BACKUP_DIR, filename)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "jalali_date": get_jalali_date(),
            "jalali_time": get_jalali_time(),
            "backup_type": "media",
            "has_media": True,
            "version": BACKUP_VERSION,
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
    """Verify that a backup file is valid and complete."""
    result = {"valid": False, "collections": 0, "total_docs": 0, "media_files": 0, "errors": []}

    if not os.path.exists(filepath):
        result["errors"].append("فایل پشتیبان یافت نشد")
        return result

    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            bad_file = zf.testzip()
            if bad_file:
                result["errors"].append(f"فایل خراب: {bad_file}")
                return result

            if "metadata.json" not in zf.namelist():
                result["errors"].append("فایل metadata.json یافت نشد")
                return result

            try:
                metadata = json.loads(zf.read("metadata.json"))
            except Exception as e:
                result["errors"].append(f"metadata.json قابل خواندن نیست: {str(e)}")
                return result

            namelist = zf.namelist()

            total_docs = 0
            for coll_name in metadata.get("collections", []):
                coll_file = f"db/{coll_name}.json"
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


def _convert_iso_strings_to_datetime(doc: dict, collection_name: str) -> dict:
    """Convert ISO date strings back to datetime objects for known date fields.
    
    Only converts fields that are actual UTC datetime objects (ISO format).
    Jalali date strings (due_date, reminder_date) are NOT converted.
    """
    from datetime import datetime as dt
    
    datetime_fields = {
        "created_at", "updated_at", "settled_at", "sent_at",
    }
    
    for field in datetime_fields:
        if field in doc and isinstance(doc[field], str):
            try:
                doc[field] = dt.fromisoformat(doc[field].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
    return doc


def _recreate_indexes(db):
    """Recreate database indexes after restore."""
    try:
        db.users.create_index("telegram_id", unique=True)
        db.transactions.create_index("user_id")
        db.transactions.create_index("transaction_type")
        db.transactions.create_index([("user_id", 1), ("transaction_type", 1)])
        db.transactions.create_index([("user_id", 1), ("is_settled", 1)])
        db.transactions.create_index("customer_id")
        db.customers.create_index("user_id")
        db.card_info.create_index("user_id")
        db.reminders.create_index("user_id")
        db.reminders.create_index([("is_sent", 1), ("reminder_jalali_date", 1)])
        db.backups.create_index("user_id")
        db.payments.create_index("transaction_id")
        db.payments.create_index("user_id")
        # Unique indexes on id fields to prevent duplicate records after restore
        for coll_name in ["users", "transactions", "payments", "customers", 
                          "card_info", "reminders", "backups"]:
            try:
                db[coll_name].create_index("id", unique=True)
            except Exception:
                pass
        logger.info("Database indexes recreated after restore.")
    except Exception as e:
        logger.warning(f"Index recreation warning: {e}")


def _update_counters_after_restore(db):
    """Rebuild counter sequences from max IDs in each collection.
    
    Drops the counters collection and recreates it with correct values.
    This prevents ID collisions after restore.
    """
    counter_collections = ["users", "transactions", "payments", "customers", 
                           "card_info", "reminders", "backups"]
    
    # Drop existing counters to start fresh
    db.counters.drop()
    
    for coll_name in counter_collections:
        try:
            coll = db[coll_name]
            # Find the max 'id' field in the collection
            pipeline = [
                {"$group": {"_id": None, "max_id": {"$max": "$id"}}}
            ]
            result = list(coll.aggregate(pipeline))
            max_id = result[0]["max_id"] if result and result[0]["max_id"] is not None else 0
            
            # Create counter document with string _id
            db.counters.insert_one({
                "_id": coll_name,
                "seq": max_id
            })
            logger.info(f"Counter for {coll_name} set to {max_id}")
        except Exception as e:
            logger.warning(f"Failed to create counter for {coll_name}: {e}")


def restore_from_backup(filepath: str, drop_existing: bool = False, 
                        remap_paths: bool = True, new_telegram_id: int = None) -> Dict:
    """Restore database and media from a backup ZIP file.
    
    Supports cross-bot restore:
    - Counters collection uses string _id (preserved correctly)
    - Photo paths are remapped from relative to the current installation's paths
    - User telegram_id can be remapped to the new installation's admin
    - ISO date strings are converted back to datetime objects
    - Indexes are recreated after restore
    - Counter sequences are updated to prevent ID collisions
    - Post-restore verification checks data integrity
    
    Args:
        filepath: Path to the backup ZIP file
        drop_existing: If True, drop existing collections before restore
        remap_paths: If True, remap relative photo paths to current installation
        new_telegram_id: If set, update user records with this telegram_id
    """
    from app.database.models import get_database

    result = {
        "success": False,
        "collections_restored": 0,
        "total_docs": 0,
        "media_restored": 0,
        "errors": [],
        "warnings": [],
        "verification": {}
    }

    if not os.path.exists(filepath):
        result["errors"].append("فایل پشتیبان یافت نشد")
        return result

    try:
        db = get_database()

        with zipfile.ZipFile(filepath, "r") as zf:
            # Check ZIP integrity first
            bad_file = zf.testzip()
            if bad_file:
                result["errors"].append(f"فایل ZIP خراب است: {bad_file}")
                return result

            if "metadata.json" not in zf.namelist():
                result["errors"].append("فایل metadata.json یافت نشد")
                return result

            metadata = json.loads(zf.read("metadata.json"))
            collections = metadata.get("collections", [])
            namelist = zf.namelist()
            is_cross_bot = new_telegram_id is not None

            # Version compatibility check
            backup_version = metadata.get("version", "unknown")
            if backup_version != BACKUP_VERSION:
                result["errors"].append(
                    f"نسخه پشتیبان ({backup_version}) با نسخه فعلی ({BACKUP_VERSION}) سازگار نیست"
                )
                return result
            
            # Validate collection names
            valid_collections = {"users", "transactions", "payments", "customers", 
                               "card_info", "reminders", "backups", "counters"}
            for coll_name in collections:
                if coll_name not in valid_collections:
                    result["warnings"].append(f"مجموعه ناشناخته: {coll_name}")

            # When dropping existing data, drop ALL application collections first
            if drop_existing:
                all_app_collections = ["users", "transactions", "payments", "customers",
                                       "card_info", "reminders", "backups", "counters"]
                for coll_name in all_app_collections:
                    try:
                        db[coll_name].drop()
                    except Exception:
                        pass
                logger.info("Dropped all existing collections for clean restore")
            
            restored_collections = {}
            
            for idx, coll_name in enumerate(collections):
                # Skip counters collection - will be rebuilt from max IDs after restore
                if coll_name == "counters":
                    continue
                
                coll_file = f"db/{coll_name}.json"
                if coll_file not in namelist:
                    result["errors"].append(f"فایل {coll_file} یافت نشد")
                    continue

                try:
                    docs = json.loads(zf.read(coll_file))
                    if not isinstance(docs, list):
                        result["errors"].append(f"{coll_file}: فرمت نامعتبر")
                        continue

                    actual_inserted = 0

                    if docs:
                        for doc in docs:
                            if "_id" in doc:
                                del doc["_id"]
                            
                            # Convert ISO date strings back to datetime objects
                            doc = _convert_iso_strings_to_datetime(doc, coll_name)
                            
                            # Remap photo paths to current installation's paths
                            if remap_paths:
                                doc = _remap_doc_paths(doc, coll_name)

                        try:
                            insert_result = db[coll_name].insert_many(docs, ordered=False)
                            actual_inserted = len(insert_result.inserted_ids)
                        except Exception as e:
                            # Track how many were actually inserted despite errors
                            actual_inserted = 0
                            if hasattr(e, 'details') and 'writeErrors' in e.details:
                                write_errors = len(e.details['writeErrors'])
                                actual_inserted = len(docs) - write_errors
                                if actual_inserted > 0:
                                    logger.warning(
                                        f"Partial restore of {coll_name}: {actual_inserted}/{len(docs)} inserted, "
                                        f"{write_errors} duplicates skipped"
                                    )
                                else:
                                    logger.warning(f"Partial restore of {coll_name}: {e}")
                            else:
                                logger.warning(f"Partial restore of {coll_name}: {e}")

                            if drop_existing and actual_inserted < len(docs):
                                # In drop_existing mode, partial restore is a problem
                                raise

                    if actual_inserted > 0:
                        restored_collections[coll_name] = actual_inserted
                        result["collections_restored"] += 1
                        result["total_docs"] += actual_inserted
                        logger.info(f"Restored collection {coll_name}: {actual_inserted} documents")

                except Exception as e:
                    result["errors"].append(f"خطا در بازیابی {coll_name}: {str(e)}")
                    logger.error(f"Failed to restore {coll_name}: {e}")

            # Restore media files
            has_media = metadata.get("has_media", False) or any(n.startswith("media/") for n in namelist)
            if has_media:
                media_restored, media_errors = _extract_media_from_zip(zf)
                result["media_restored"] = media_restored
                if media_errors:
                    result["warnings"].extend(media_errors)
                logger.info(f"Restored {media_restored} media files")

            # For cross-bot restore: merge all users into one and assign new telegram_id
            if new_telegram_id:
                actual_user_count = _merge_users_for_cross_bot(db, new_telegram_id)
                restored_collections["users"] = actual_user_count
                result["warnings"].append(f"همه کاربران به کاربر واحد (telegram_id={new_telegram_id}) ادغام شدند")

            # Recreate indexes after restore (AFTER user merge for cross-bot)
            _recreate_indexes(db)
            
            # Update counters to prevent ID collisions
            _update_counters_after_restore(db)

        # Post-restore verification
        verification = _verify_restore(db, restored_collections, result["media_restored"])
        result["verification"] = verification
        
        if not verification["valid"]:
            result["warnings"].append("اعتبارسنجی پس از بازیابی مشکلاتی را نشان داد")

        # Success = at least one collection restored AND verification passed
        result["success"] = (result["collections_restored"] > 0 or result["media_restored"] > 0) and verification["valid"]

    except zipfile.BadZipFile:
        result["errors"].append("فایل ZIP نامعتبر")
    except Exception as e:
        result["errors"].append(f"خطای غیرمنتظره: {str(e)}")

    return result


def _merge_users_for_cross_bot(db, new_telegram_id: int) -> int:
    """Merge all users into a single user for cross-bot restore.
    
    In a single-user bot, all data should belong to one user.
    This function:
    1. Cleans up any orphan user_ids (data with user_id not matching any user)
    2. Identifies the user with the most data (transactions, payments, customers, etc.) as primary
    3. Transfers all data references to the primary user
    4. Deletes all other users
    5. Sets the primary user's telegram_id to the new admin
    6. If no users exist, creates one and reassigns all orphan data
    
    Returns:
        Final user count (should be 1)
    """
    users = list(db.users.find({}))
    
    if not users:
        # No users in backup — create a new user and reassign all orphan data
        logger.warning("No users found in backup. Creating new user and reassigning orphan data.")
        new_user = create_user_doc(
            telegram_id=new_telegram_id,
            username="restored_user",
            first_name="Restored User"
        )
        new_user.pop("_id", None)
        try:
            db.users.insert_one(new_user)
        except Exception as e:
            logger.error(f"Failed to create new user during merge: {e}")
            return 0
        new_user_id = new_user["id"]
        
        # Reassign ALL orphan data to the new user
        for coll_name in ["transactions", "payments", "customers", "card_info", "reminders"]:
            try:
                result = db[coll_name].update_many(
                    {"user_id": {"$exists": True}},
                    {"$set": {"user_id": new_user_id}}
                )
                if result.modified_count > 0:
                    logger.info(f"Reassigned {result.modified_count} records in {coll_name} to new user {new_user_id}")
            except Exception as e:
                logger.warning(f"Failed to reassign {coll_name}: {e}")
        
        return 1
    
    # Clean up any orphan user_ids first
    all_user_ids = set(u["id"] for u in users)
    for coll_name in ["transactions", "payments", "customers", "card_info", "reminders"]:
        try:
            orphan_count = db[coll_name].count_documents({"user_id": {"$nin": list(all_user_ids)}})
            if orphan_count > 0:
                db[coll_name].update_many(
                    {"user_id": {"$nin": list(all_user_ids)}},
                    {"$set": {"user_id": users[0]["id"]}}
                )
                logger.info(f"Cleaned up {orphan_count} orphan records in {coll_name}")
        except Exception as e:
            logger.warning(f"Orphan cleanup in {coll_name} failed: {e}")
    
    if len(users) == 1:
        result = db.users.update_one(
            {"_id": users[0]["_id"]},
            {"$set": {"telegram_id": new_telegram_id}}
        )
        if result.matched_count == 1:
            logger.info(f"Single user (id={users[0]['id']}), telegram_id set to {new_telegram_id}")
            return 1
        else:
            # Update failed — user doc may have been deleted. Create new user.
            logger.warning(f"Single user update failed (matched={result.matched_count}). Creating new user.")
            new_user = create_user_doc(
                telegram_id=new_telegram_id,
                username="restored_user",
                first_name="Restored User"
            )
            new_user.pop("_id", None)
            try:
                db.users.insert_one(new_user)
            except Exception as e:
                logger.error(f"Failed to create replacement user: {e}")
                return 0
            new_user_id = new_user["id"]
            # Reassign data from the old user to the new one
            old_user_id = users[0]["id"]
            for coll_name in ["transactions", "payments", "customers", "card_info", "reminders"]:
                try:
                    db[coll_name].update_many(
                        {"user_id": old_user_id},
                        {"$set": {"user_id": new_user_id}}
                    )
                except Exception:
                    pass
            # Delete the old user
            db.users.delete_one({"_id": users[0]["_id"]})
            return 1
    
    # Score each user by amount of data they own
    user_scores = {}
    for user in users:
        uid = user["id"]
        score = 0
        score += db.transactions.count_documents({"user_id": uid})
        score += db.payments.count_documents({"user_id": uid})
        score += db.customers.count_documents({"user_id": uid})
        score += db.card_info.count_documents({"user_id": uid})
        score += db.reminders.count_documents({"user_id": uid})
        user_scores[uid] = score
    
    # Pick user with most data
    primary_id = max(user_scores, key=user_scores.get)
    primary_user = next(u for u in users if u["id"] == primary_id)
    other_user_ids = [u["id"] for u in users if u["id"] != primary_id]
    
    logger.info(f"Cross-bot merge: primary user id={primary_id} (score={user_scores[primary_id]}), "
               f"{len(other_user_ids)} other users to merge")
    
    # Transfer all data references to the primary user
    for other_id in other_user_ids:
        db.transactions.update_many(
            {"user_id": other_id}, {"$set": {"user_id": primary_id}})
        db.payments.update_many(
            {"user_id": other_id}, {"$set": {"user_id": primary_id}})
        db.customers.update_many(
            {"user_id": other_id}, {"$set": {"user_id": primary_id}})
        db.card_info.update_many(
            {"user_id": other_id}, {"$set": {"user_id": primary_id}})
        db.reminders.update_many(
            {"user_id": other_id}, {"$set": {"user_id": primary_id}})
    
    # Delete all non-primary users
    if other_user_ids:
        db.users.delete_many({"id": {"$in": other_user_ids}})
    
    # Clean up any orphan user_ids again (in case of race conditions)
    all_user_ids = set(u["id"] for u in db.users.find({}))
    for coll_name in ["transactions", "payments", "customers", "card_info", "reminders"]:
        try:
            orphan_count = db[coll_name].count_documents({"user_id": {"$nin": list(all_user_ids)}})
            if orphan_count > 0:
                db[coll_name].update_many(
                    {"user_id": {"$nin": list(all_user_ids)}},
                    {"$set": {"user_id": primary_id}}
                )
                logger.info(f"Cleaned up {orphan_count} orphan records in {coll_name}")
        except Exception as e:
            logger.warning(f"Orphan cleanup in {coll_name} failed: {e}")
    
    # Set primary user's telegram_id to the new admin
    update_result = db.users.update_one(
        {"_id": primary_user["_id"]},
        {"$set": {"telegram_id": new_telegram_id}}
    )
    
    if update_result.matched_count == 1:
        logger.info(f"Cross-bot merge complete: primary user id={primary_id}, "
                   f"telegram_id={new_telegram_id}, {len(other_user_ids)} users merged")
    else:
        logger.warning(f"Primary user update failed (matched={update_result.matched_count}). "
                      f"Primary user may have been deleted.")
    
    return 1


def _verify_restore(db, restored_collections: dict, media_count: int) -> Dict:
    """Verify data integrity after restore.
    
    Checks:
    - Each restored collection has the expected document count
    - Counter values match max IDs
    - Media files exist on disk
    - Referential integrity (foreign keys point to existing documents)
    
    Returns:
        dict with keys: valid, checks, errors
    """
    result = {"valid": True, "checks": [], "errors": []}
    
    for coll_name, expected_count in restored_collections.items():
        try:
            actual_count = db[coll_name].count_documents({})
            if actual_count == expected_count:
                result["checks"].append(f"✅ {coll_name}: {actual_count} docs")
            else:
                result["checks"].append(f"⚠️ {coll_name}: expected {expected_count}, got {actual_count}")
                result["errors"].append(f"{coll_name}: count mismatch")
                result["valid"] = False
        except Exception as e:
            result["errors"].append(f"{coll_name}: verification error: {e}")
            result["valid"] = False
    
    try:
        counter_collections = ["users", "transactions", "payments", "customers", 
                              "card_info", "reminders", "backups"]
        for coll_name in counter_collections:
            counter = db.counters.find_one({"_id": coll_name})
            if counter:
                result["checks"].append(f"✅ counter.{coll_name}: seq={counter['seq']}")
            else:
                result["checks"].append(f"⚠️ counter.{coll_name}: missing")
                result["valid"] = False
    except Exception as e:
        result["errors"].append(f"Counter verification error: {e}")
        result["valid"] = False
    
    if media_count > 0:
        upload_dir = settings.UPLOAD_DIR
        if os.path.isdir(upload_dir):
            actual_media = len([f for f in os.listdir(upload_dir) 
                              if os.path.isfile(os.path.join(upload_dir, f)) 
                              and not f.endswith(":Zone.Identifier")])
            if actual_media >= media_count:
                result["checks"].append(f"✅ Media files on disk: {actual_media}")
            else:
                result["checks"].append(f"⚠️ Media files: expected >= {media_count}, got {actual_media}")
                result["errors"].append("media count mismatch")
                result["valid"] = False
        else:
            result["checks"].append(f"⚠️ Upload directory not found")
            result["errors"].append("upload directory missing")
            result["valid"] = False
    
    if "transactions" in restored_collections and "payments" in restored_collections:
        try:
            txn_ids = set(db.transactions.distinct("id"))
            orphan_payments = db.payments.count_documents(
                {"transaction_id": {"$nin": list(txn_ids)}}
            )
            if orphan_payments == 0:
                result["checks"].append(f"✅ Payment references: all valid")
            else:
                result["checks"].append(f"⚠️ Orphan payments: {orphan_payments}")
                result["errors"].append(f"orphan payments")
                result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Integrity check error: {e}")
    
    if "transactions" in restored_collections and "customers" in restored_collections:
        try:
            cust_ids = set(db["customers"].distinct("id"))
            orphan_txns = db["transactions"].count_documents(
                {"customer_id": {"$ne": None, "$nin": list(cust_ids)}}
            )
            if orphan_txns == 0:
                result["checks"].append(f"✅ Transaction-customer references: all valid")
            else:
                result["checks"].append(f"⚠️ Orphan customer references: {orphan_txns}")
                result["errors"].append(f"orphan customer references in transactions")
                result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Integrity check error: {e}")
    
    return result


def list_backup_files() -> List[Dict]:
    """List all backup files in the backup directory."""
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


def cleanup_old_backups(keep_count: int = 5) -> int:
    """Delete old backup files, keeping the most recent ones.
    Also removes orphan DB records for deleted files."""
    from app.database.repository import BackupRepository

    backups = list_backup_files()
    if len(backups) <= keep_count:
        return 0

    to_delete = backups[keep_count:]
    deleted = 0
    deleted_filenames = []
    for b in to_delete:
        if delete_backup_file(b["filepath"]):
            deleted += 1
            deleted_filenames.append(b["filename"])

    # Clean up orphan DB records
    if deleted_filenames:
        try:
            db_backups = BackupRepository.get_all()
            for dbr in db_backups:
                if dbr.get("filename") in deleted_filenames:
                    BackupRepository.delete(dbr["id"])
        except Exception as e:
            logger.warning(f"Failed to clean up DB records: {e}")

    logger.info(f"Cleanup: deleted {deleted} old backups, kept {keep_count}")
    return deleted


def get_backup_stats() -> Dict:
    """Get backup statistics."""
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
