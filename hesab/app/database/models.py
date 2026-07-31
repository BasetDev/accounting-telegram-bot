"""MongoDB database connection and document schemas for the accounting bot."""

from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

from pymongo import MongoClient, ReturnDocument
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings, IS_SERVERLESS
from app.utils.logger import logger


# ==============================
# MongoDB Connection Manager
# ==============================
# Uses lazy singleton pattern for connection reuse across serverless invocations.

_client: Optional[MongoClient] = None
_db: Optional[Database] = None
_indexes_created: bool = False


def get_database() -> Database:
    """Get the MongoDB database instance. Initializes connection if needed.

    In serverless environments, reuses existing connections when possible
    to avoid connection overhead on each invocation.
    """
    global _client, _db
    if _db is not None:
        # Verify the connection is still alive
        try:
            _client.admin.command('ping')
            return _db
        except Exception:
            # Connection died, reset and reinitialize
            _client = None
            _db = None

    init_database()
    return _db


def get_collection(name: str) -> Collection:
    """Get a MongoDB collection by name."""
    return get_database()[name]


def init_database():
    """Initialize MongoDB connection and create indexes.

    Connection pool sizes are optimized for serverless:
    - maxPoolSize=10 (reduced from 50 for serverless)
    - minPoolSize=0 (no idle connections in serverless)
    - maxIdleTimeMS=30000 (close idle connections faster)
    """
    global _client, _db, _indexes_created

    if not settings.MONGO_URI:
        raise ValueError("MONGO_URI is not configured. Please set it in .env file.")

    # Serverless-optimized connection settings
    pool_size = 10 if IS_SERVERLESS else 50
    min_pool = 0 if IS_SERVERLESS else 2
    idle_time = 30000 if IS_SERVERLESS else 60000

    max_retries = 3
    for attempt in range(max_retries):
        try:
            _client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=15000,
                socketTimeoutMS=30000,
                maxPoolSize=pool_size,
                minPoolSize=min_pool,
                maxIdleTimeMS=idle_time,
                retryWrites=True,
                retryReads=True,
                w='majority',
                directConnection=False,
            )
            _db = _client[settings.MONGO_DB_NAME]

            # Verify connection
            _client.admin.command('ping')
            logger.info(f"Connected to MongoDB Atlas: {settings.MONGO_DB_NAME}")

            # Create indexes only once per process lifecycle
            if not _indexes_created:
                _create_indexes()
                _indexes_created = True
            return  # Success

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(3)
                continue
            raise
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(3)
                continue
            raise


def _create_indexes():
    """Create database indexes for optimal query performance."""
    try:
        # Users collection
        _db.users.create_index("telegram_id", unique=True)
        _db.users.create_index("id", unique=True)

        # Transactions collection
        _db.transactions.create_index("user_id")
        _db.transactions.create_index("transaction_type")
        _db.transactions.create_index([("user_id", 1), ("transaction_type", 1)])
        _db.transactions.create_index([("user_id", 1), ("is_settled", 1)])
        _db.transactions.create_index("customer_id")
        _db.transactions.create_index("id", unique=True)

        # Customers collection
        _db.customers.create_index("user_id")
        _db.customers.create_index("id", unique=True)

        # Card info collection
        _db.card_info.create_index("user_id")
        _db.card_info.create_index("id", unique=True)

        # Reminders collection
        _db.reminders.create_index("user_id")
        _db.reminders.create_index([("is_sent", 1), ("reminder_jalali_date", 1)])
        _db.reminders.create_index("id", unique=True)

        # Backups collection
        _db.backups.create_index("user_id")
        _db.backups.create_index("id", unique=True)

        # Payments collection
        _db.payments.create_index("transaction_id")
        _db.payments.create_index("user_id")
        _db.payments.create_index("id", unique=True)

        # Counters collection (for auto-increment IDs)
        # _id index is created automatically, no need to create it explicitly

        logger.info("Database indexes created successfully.")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


def close_database():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


def get_next_sequence(name: str) -> int:
    """Get the next auto-increment ID for a collection."""
    counters = _db.counters
    counter = counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return counter["seq"]


# ==============================
# Document Schema Helpers
# ==============================

def _utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def document_to_dict(doc: Optional[Dict]) -> Optional[Dict]:
    """Convert MongoDB document to dict, removing _id."""
    if doc is None:
        return None
    result = dict(doc)
    result.pop("_id", None)
    return result


# ==============================
# Collection Names
# ==============================

COLLECTIONS = {
    "users": "users",
    "transactions": "transactions",
    "customers": "customers",
    "reminders": "reminders",
    "card_info": "card_info",
    "backups": "backups",
    "payments": "payments",
    "counters": "counters",
}


# ==============================
# Document Factory Functions
# ==============================

def create_user_doc(telegram_id: int, username: str = None,
                    first_name: str = None, last_name: str = None,
                    is_admin: bool = False, is_active: bool = True) -> Dict:
    """Create a user document."""
    now = _utcnow()
    return {
        "id": get_next_sequence("users"),
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "is_admin": is_admin,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now,
    }


def create_transaction_doc(user_id: int, transaction_type: str,
                           amount: float, jalali_date: str, jalali_time: str,
                           jalali_full: str, description: str = None,
                           category: str = None, subcategory: str = None,
                           party_name: str = None, customer_id: int = None,
                           due_jalali_date: str = None, due_jalali_time: str = None,
                           photo_path: str = None, card_number: str = None,
                           sheba: str = None, bank_name: str = None) -> Dict:
    """Create a transaction document."""
    return {
        "id": get_next_sequence("transactions"),
        "user_id": user_id,
        "transaction_type": transaction_type,
        "amount": amount,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "party_name": party_name,
        "customer_id": customer_id,
        "jalali_date": jalali_date,
        "jalali_time": jalali_time,
        "jalali_full": jalali_full,
        "due_jalali_date": due_jalali_date,
        "due_jalali_time": due_jalali_time,
        "photo_path": photo_path,
        "card_number": card_number,
        "sheba": sheba,
        "bank_name": bank_name,
        "created_at": _utcnow(),
        "is_settled": False,
        "settled_at": None,
    }


def create_customer_doc(user_id: int, full_name: str,
                        phone: str = None, address: str = None,
                        notes: str = None) -> Dict:
    """Create a customer document."""
    now = _utcnow()
    return {
        "id": get_next_sequence("customers"),
        "user_id": user_id,
        "full_name": full_name,
        "phone": phone,
        "address": address,
        "notes": notes,
        "total_debt": 0.0,
        "total_receivable": 0.0,
        "created_at": now,
        "updated_at": now,
    }


def create_reminder_doc(user_id: int, reminder_type: str, title: str,
                        reminder_jalali_date: str, message: str = None,
                        transaction_id: int = None,
                        reminder_time: str = None) -> Dict:
    """Create a reminder document."""
    return {
        "id": get_next_sequence("reminders"),
        "user_id": user_id,
        "transaction_id": transaction_id,
        "reminder_type": reminder_type,
        "title": title,
        "message": message,
        "reminder_jalali_date": reminder_jalali_date,
        "reminder_time": reminder_time,
        "is_sent": False,
        "sent_at": None,
        "created_at": _utcnow(),
    }


def create_card_info_doc(user_id: int, name: str, card_number: str = None,
                         sheba: str = None, customer_id: int = None,
                         bank_name: str = None) -> Dict:
    """Create a card info document."""
    now = _utcnow()
    return {
        "id": get_next_sequence("card_info"),
        "user_id": user_id,
        "name": name,
        "customer_id": customer_id,
        "card_number": card_number,
        "sheba": sheba,
        "bank_name": bank_name,
        "created_at": now,
        "updated_at": now,
    }


def create_backup_doc(user_id: int, filename: str, file_size: int,
                      jalali_date: str, jalali_time: str = None) -> Dict:
    """Create a backup document."""
    return {
        "id": get_next_sequence("backups"),
        "user_id": user_id,
        "filename": filename,
        "file_size": file_size,
        "jalali_date": jalali_date,
        "jalali_time": jalali_time,
        "created_at": _utcnow(),
    }


def create_payment_doc(transaction_id: int, user_id: int, amount: float,
                       payment_type: str, jalali_date: str, jalali_time: str,
                       jalali_full: str, description: str = None,
                       photo_path: str = None) -> Dict:
    """Create a payment document."""
    return {
        "id": get_next_sequence("payments"),
        "transaction_id": transaction_id,
        "user_id": user_id,
        "amount": amount,
        "payment_type": payment_type,
        "description": description,
        "photo_path": photo_path,
        "jalali_date": jalali_date,
        "jalali_time": jalali_time,
        "jalali_full": jalali_full,
        "created_at": _utcnow(),
    }
