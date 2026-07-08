"""Database models for the accounting bot."""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, BigInteger, Float, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.config import settings

Base = declarative_base()


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class User(Base):
    """Telegram bot users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    transactions = relationship("Transaction", back_populates="user")
    customers = relationship("Customer", back_populates="user")
    card_info = relationship("CardInfo", back_populates="user")


class Transaction(Base):
    """Financial transactions: income, expense, debt, receivable."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Type: income, expense, debt, receivable
    transaction_type = Column(String(50), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    subcategory = Column(String(255), nullable=True)
    
    # Person/Company for debts and receivables
    party_name = Column(String(255), nullable=True)
    
    # Customer relation
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    # Dates in Jalali format
    jalali_date = Column(String(20), nullable=False)
    jalali_time = Column(String(20), nullable=False)
    jalali_full = Column(String(50), nullable=False)
    
    # Due date for debts/receivables
    due_jalali_date = Column(String(20), nullable=True)
    due_jalali_time = Column(String(20), nullable=True)
    
    # Photo attachment (optional)
    photo_path = Column(String(500), nullable=True)

    # Card/IBAN info (optional, for debts and receivables)
    card_number = Column(String(16), nullable=True)
    sheba = Column(String(26), nullable=True)
    bank_name = Column(String(255), nullable=True)

    # Internal UTC timestamp
    created_at = Column(DateTime, default=_utcnow)
    
    is_settled = Column(Boolean, default=False)
    settled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")


class Customer(Base):
    """Customer management."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Financial summary - cached for performance
    total_debt = Column(Float, default=0.0)
    total_receivable = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="customers")
    transactions = relationship("Transaction", back_populates="customer")


class Reminder(Base):
    """Reminders for debts, receivables, etc."""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    reminder_type = Column(String(50), nullable=False)  # debt, receivable, custom
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    
    reminder_jalali_date = Column(String(20), nullable=False)
    reminder_time = Column(String(20), nullable=True)
    
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=_utcnow)


class CardInfo(Base):
    """Credit card and IBAN (Sheba) records."""
    __tablename__ = "card_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Associated name (manual or from customers)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # Optional link to customer
    card_number = Column(String(16), nullable=True)  # Exactly 16 digits
    sheba = Column(String(26), nullable=True)  # IR + 24 digits
    bank_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="card_info")
    customer = relationship("Customer")


class Backup(Base):
    """Database backup records."""
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, default=0)
    jalali_date = Column(String(20), nullable=False)
    jalali_time = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=_utcnow)


class Payment(Base):
    """Payment history for debts and receivables."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    payment_type = Column(String(50), nullable=False)  # debt_payment, receivable_payment
    description = Column(Text, nullable=True)
    photo_path = Column(String(500), nullable=True)
    
    jalali_date = Column(String(20), nullable=False)
    jalali_time = Column(String(20), nullable=False)
    jalali_full = Column(String(50), nullable=False)
    
    created_at = Column(DateTime, default=_utcnow)

    transaction = relationship("Transaction", back_populates="payments")
    user = relationship("User")


# Add relationship to Transaction
Transaction.payments = relationship("Payment", back_populates="transaction", cascade="all, delete-orphan")


_engine = None
_SessionLocal = None


def init_database():
    """Initialize the database and create all tables."""
    global _engine, _SessionLocal
    
    import os
    from sqlalchemy import inspect, text
    
    # Ensure data directory exists
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    _engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    Base.metadata.create_all(_engine)
    
    # Auto-migrate: add missing columns to existing tables
    inspector = inspect(_engine)
    with _engine.connect() as conn:
        for table_name, table_obj in Base.metadata.tables.items():
            if table_name in inspector.get_table_names():
                existing_cols = {c['name'] for c in inspector.get_columns(table_name)}
                for column in table_obj.columns:
                    if column.name not in existing_cols:
                        col_type = column.type.compile(_engine.dialect)
                        nullable = "NULL" if column.nullable else "NOT NULL"
                        default = ""
                        if column.default is not None:
                            default_val = column.default.arg if hasattr(column.default, 'arg') else None
                            if default_val is not None:
                                default = f" DEFAULT '{default_val}'"
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable}{default}"
                        conn.execute(text(sql))
                        conn.commit()
    
    _SessionLocal = sessionmaker(bind=_engine)
    return _engine, _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager that provides a database session with automatic cleanup."""
    global _SessionLocal
    if _SessionLocal is None:
        init_database()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()