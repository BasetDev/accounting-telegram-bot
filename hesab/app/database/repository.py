"""Database repository layer for CRUD operations."""

from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database.models import User, Transaction, Customer, Reminder, Backup, CardInfo, Payment


class UserRepository:
    """User CRUD operations."""

    @staticmethod
    def get_or_create(session: Session, telegram_id: int, username: str = None,
                      first_name: str = None, last_name: str = None) -> User:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=False,
                is_active=True
            )
            session.add(user)
            session.commit()
        else:
            # Update info if changed
            changed = False
            if username and user.username != username:
                user.username = username
                changed = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                changed = True
            if changed:
                session.commit()
        return user

    @staticmethod
    def get_by_telegram_id(session: Session, telegram_id: int) -> Optional[User]:
        return session.query(User).filter_by(telegram_id=telegram_id).first()

    @staticmethod
    def get_by_id(session: Session, user_id: int) -> Optional[User]:
        return session.query(User).filter_by(id=user_id).first()

    @staticmethod
    def make_admin(session: Session, telegram_id: int) -> bool:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.is_admin = True
            session.commit()
            return True
        return False

    @staticmethod
    def get_all_users(session: Session) -> List[User]:
        return session.query(User).all()

class TransactionRepository:
    """Transaction CRUD operations."""

    @staticmethod
    def create(session: Session, user_id: int, transaction_type: str,
               amount: float, jalali_date: str, jalali_time: str, jalali_full: str,
               description: str = None, category: str = None, subcategory: str = None,
               party_name: str = None, customer_id: int = None,
               due_jalali_date: str = None, due_jalali_time: str = None,
               photo_path: str = None, card_number: str = None, sheba: str = None,
               bank_name: str = None) -> Transaction:
        txn = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            category=category,
            subcategory=subcategory,
            party_name=party_name,
            customer_id=customer_id,
            jalali_date=jalali_date,
            jalali_time=jalali_time,
            jalali_full=jalali_full,
            due_jalali_date=due_jalali_date,
            due_jalali_time=due_jalali_time,
            photo_path=photo_path,
            card_number=card_number,
            sheba=sheba,
            bank_name=bank_name
        )
        session.add(txn)
        session.commit()
        return txn

    @staticmethod
    def get_by_id(session: Session, txn_id: int) -> Optional[Transaction]:
        return session.query(Transaction).filter_by(id=txn_id).first()

    @staticmethod
    def get_by_user(session: Session, user_id: int,
                    transaction_type: str = None,
                    limit: int = 50, offset: int = 0) -> List[Transaction]:
        query = session.query(Transaction).filter_by(user_id=user_id)
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        return query.order_by(Transaction.id.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def get_active(session: Session, user_id: int, transaction_type: str,
                   limit: int = 50) -> List[Transaction]:
        """Get non-settled transactions of a given type."""
        return session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            Transaction.is_settled == False
        ).order_by(Transaction.id.desc()).limit(limit).all()

    @staticmethod
    def get_settled(session: Session, user_id: int, transaction_type: str,
                    limit: int = 50) -> List[Transaction]:
        """Get settled transactions of a given type."""
        return session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            Transaction.is_settled == True
        ).order_by(Transaction.id.desc()).limit(limit).all()

    @staticmethod
    def get_with_payments(session: Session, user_id: int, transaction_type: str,
                          limit: int = 50) -> List[Transaction]:
        """Get transactions that have at least one payment recorded (partial or full)."""
        from app.database.models import Payment
        return session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            Transaction.id.in_(
                session.query(Payment.transaction_id).filter(
                    Payment.user_id == user_id
                ).distinct()
            )
        ).order_by(Transaction.id.desc()).limit(limit).all()

    @staticmethod
    def get_overdue(session: Session, user_id: int, transaction_type: str,
                    today_jalali: str, limit: int = 50) -> List[Transaction]:
        """Get non-settled transactions with due date before today."""
        return session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            Transaction.is_settled == False,
            Transaction.due_jalali_date.isnot(None),
            Transaction.due_jalali_date < today_jalali
        ).order_by(Transaction.due_jalali_date.asc()).limit(limit).all()

    @staticmethod
    def get_due_today(session: Session, user_id: int, transaction_type: str,
                      today_jalali: str, limit: int = 50) -> List[Transaction]:
        """Get non-settled transactions with due date = today."""
        return session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            Transaction.is_settled == False,
            Transaction.due_jalali_date == today_jalali
        ).order_by(Transaction.id.desc()).limit(limit).all()

    @staticmethod
    def get_due_this_week(session: Session, user_id: int, transaction_type: str,
                          today_jalali: str, week_end_jalali: str,
                          limit: int = 50) -> List[Transaction]:
        """Get non-settled transactions with due date between today and end of week."""
        return session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            Transaction.is_settled == False,
            Transaction.due_jalali_date.isnot(None),
            Transaction.due_jalali_date >= today_jalali,
            Transaction.due_jalali_date <= week_end_jalali
        ).order_by(Transaction.due_jalali_date.asc()).limit(limit).all()

    @staticmethod
    def get_by_date_range(session: Session, user_id: int,
                           start_date: str, end_date: str,
                           transaction_type: str = None) -> List[Transaction]:
        query = session.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.jalali_date >= start_date,
                Transaction.jalali_date <= end_date
            )
        )
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        return query.order_by(Transaction.id.desc()).all()

    @staticmethod
    def get_by_customer(session: Session, customer_id: int) -> List[Transaction]:
        return session.query(Transaction).filter_by(
            customer_id=customer_id
        ).order_by(Transaction.id.desc()).all()

    @staticmethod
    def get_summary(session: Session, user_id: int,
                    transaction_type: str = None) -> float:
        query = session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_settled == False
        )
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        result = query.scalar()
        return float(result) if result else 0.0

    @staticmethod
    def get_total_by_type(session: Session, user_id: int) -> dict:
        """Get total amounts grouped by transaction type."""
        results = {}
        for ttype in ['income', 'expense', 'debt', 'receivable']:
            total = session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.transaction_type == ttype,
                Transaction.is_settled == False
            ).scalar()
            results[ttype] = float(total) if total else 0.0
        return results

    @staticmethod
    def update(session: Session, txn_id: int, **kwargs) -> bool:
        """Update transaction fields. Only provided kwargs are updated."""
        txn = session.query(Transaction).filter_by(id=txn_id).first()
        if not txn:
            return False
        
        allowed_fields = {
            'amount', 'description', 'category', 'subcategory', 'party_name',
            'due_jalali_date', 'due_jalali_time', 'jalali_date', 'jalali_time', 'jalali_full',
            'is_settled', 'settled_at', 'photo_path', 'card_number', 'sheba', 'bank_name'
        }
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(txn, key, value)
        
        session.commit()
        return True

    @staticmethod
    def settle_transaction(session: Session, txn_id: int) -> bool:
        txn = session.query(Transaction).filter_by(id=txn_id).first()
        if txn:
            txn.is_settled = True
            txn.settled_at = datetime.now(timezone.utc)
            session.commit()
            return True
        return False

    @staticmethod
    def delete(session: Session, txn_id: int) -> bool:
        txn = session.query(Transaction).filter_by(id=txn_id).first()
        if txn:
            session.delete(txn)
            session.commit()
            return True
        return False

    @staticmethod
    def search(session: Session, user_id: int, query_text: str = None,
               transaction_type: str = None, min_amount: float = None,
               max_amount: float = None, start_date: str = None,
               end_date: str = None, category: str = None,
               party_name: str = None, limit: int = 20) -> List[Transaction]:
        q = session.query(Transaction).filter(Transaction.user_id == user_id)
        
        conditions = []
        
        if query_text:
            like_pattern = f"%{query_text}%"
            conditions.append(
                or_(
                    Transaction.description.ilike(like_pattern),
                    Transaction.category.ilike(like_pattern),
                    Transaction.party_name.ilike(like_pattern)
                )
            )
        
        if transaction_type:
            conditions.append(Transaction.transaction_type == transaction_type)
        if min_amount is not None:
            conditions.append(Transaction.amount >= min_amount)
        if max_amount is not None:
            conditions.append(Transaction.amount <= max_amount)
        if start_date:
            conditions.append(Transaction.jalali_date >= start_date)
        if end_date:
            conditions.append(Transaction.jalali_date <= end_date)
        if category:
            conditions.append(Transaction.category == category)
        if party_name:
            conditions.append(Transaction.party_name.ilike(f"%{party_name}%"))
        
        if conditions:
            q = q.filter(and_(*conditions))
        
        return q.order_by(Transaction.id.desc()).limit(limit).all()


class CustomerRepository:
    """Customer CRUD operations."""

    @staticmethod
    def create(session: Session, user_id: int, full_name: str,
               phone: str = None, address: str = None,
               notes: str = None) -> Customer:
        customer = Customer(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            address=address,
            notes=notes
        )
        session.add(customer)
        session.commit()
        return customer

    @staticmethod
    def get_by_id(session: Session, customer_id: int) -> Optional[Customer]:
        return session.query(Customer).filter_by(id=customer_id).first()

    @staticmethod
    def get_by_user(session: Session, user_id: int) -> List[Customer]:
        return session.query(Customer).filter_by(user_id=user_id).order_by(
            Customer.full_name.asc()
        ).all()

    @staticmethod
    def search(session: Session, user_id: int, query: str) -> List[Customer]:
        like_pattern = f"%{query}%"
        return session.query(Customer).filter(
            and_(
                Customer.user_id == user_id,
                or_(
                    Customer.full_name.ilike(like_pattern),
                    Customer.phone.ilike(like_pattern)
                )
            )
        ).all()

    @staticmethod
    def update(session: Session, customer_id: int,
               full_name: str = None, phone: str = None,
               address: str = None, notes: str = None) -> bool:
        customer = session.query(Customer).filter_by(id=customer_id).first()
        if customer:
            if full_name:
                customer.full_name = full_name
            if phone is not None:
                customer.phone = phone
            if address is not None:
                customer.address = address
            if notes is not None:
                customer.notes = notes
            session.commit()
            return True
        return False

    @staticmethod
    def delete(session: Session, customer_id: int) -> bool:
        customer = session.query(Customer).filter_by(id=customer_id).first()
        if customer:
            session.delete(customer)
            session.commit()
            return True
        return False

    @staticmethod
    def update_financial_summary(session: Session, customer_id: int) -> bool:
        """Recalculate and update customer's total debt and receivable."""
        customer = session.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return False
        
        total_debt = session.query(func.sum(Transaction.amount)).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == 'debt',
            Transaction.is_settled == False
        ).scalar() or 0
        
        total_receivable = session.query(func.sum(Transaction.amount)).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == 'receivable',
            Transaction.is_settled == False
        ).scalar() or 0
        
        customer.total_debt = float(total_debt)
        customer.total_receivable = float(total_receivable)
        session.commit()
        return True


class ReminderRepository:
    """Reminder CRUD operations."""

    @staticmethod
    def create(session: Session, user_id: int, reminder_type: str,
               title: str, reminder_jalali_date: str,
               message: str = None, transaction_id: int = None,
               reminder_time: str = None) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            transaction_id=transaction_id,
            reminder_type=reminder_type,
            title=title,
            message=message,
            reminder_jalali_date=reminder_jalali_date,
            reminder_time=reminder_time
        )
        session.add(reminder)
        session.commit()
        return reminder

    @staticmethod
    def get_pending(session: Session, jalali_date: str) -> List[Reminder]:
        return session.query(Reminder).filter(
            Reminder.reminder_jalali_date <= jalali_date,
            Reminder.is_sent == False
        ).all()

    @staticmethod
    def mark_sent(session: Session, reminder_id: int) -> bool:
        reminder = session.query(Reminder).filter_by(id=reminder_id).first()
        if reminder:
            reminder.is_sent = True
            reminder.sent_at = datetime.now(timezone.utc)
            session.commit()
            return True
        return False


class CardInfoRepository:
    """Card info (شماره کارت و شبا) CRUD operations."""

    @staticmethod
    def create(session: Session, user_id: int, name: str,
               card_number: str = None, sheba: str = None,
               customer_id: int = None, bank_name: str = None) -> CardInfo:
        card = CardInfo(
            user_id=user_id,
            name=name,
            card_number=card_number,
            sheba=sheba,
            customer_id=customer_id,
            bank_name=bank_name
        )
        session.add(card)
        session.commit()
        return card

    @staticmethod
    def get_by_id(session: Session, card_id: int) -> Optional[CardInfo]:
        return session.query(CardInfo).filter_by(id=card_id).first()

    @staticmethod
    def get_by_user(session: Session, user_id: int) -> List[CardInfo]:
        return session.query(CardInfo).filter_by(user_id=user_id).order_by(
            CardInfo.id.desc()
        ).all()

    @staticmethod
    def update(session: Session, card_id: int, name: str = None,
               card_number: str = None, sheba: str = None,
               customer_id: int = None, bank_name: str = None) -> bool:
        card = session.query(CardInfo).filter_by(id=card_id).first()
        if not card:
            return False
        if name is not None:
            card.name = name
        if card_number is not None:
            card.card_number = card_number
        if sheba is not None:
            card.sheba = sheba
        if customer_id is not None:
            card.customer_id = customer_id
        if bank_name is not None:
            card.bank_name = bank_name
        session.commit()
        return True

    @staticmethod
    def delete(session: Session, card_id: int) -> bool:
        card = session.query(CardInfo).filter_by(id=card_id).first()
        if card:
            session.delete(card)
            session.commit()
            return True
        return False

    @staticmethod
    def search(session: Session, user_id: int, query: str) -> List[CardInfo]:
        like_pattern = f"%{query}%"
        return session.query(CardInfo).filter(
            and_(
                CardInfo.user_id == user_id,
                or_(
                    CardInfo.name.ilike(like_pattern),
                    CardInfo.card_number.ilike(like_pattern),
                    CardInfo.sheba.ilike(like_pattern)
                )
            )
        ).all()


class BackupRepository:
    """Backup record CRUD operations."""

    @staticmethod
    def create(session: Session, user_id: int, filename: str,
               file_size: int, jalali_date: str, jalali_time: str = None) -> Backup:
        backup = Backup(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            jalali_date=jalali_date,
            jalali_time=jalali_time
        )
        session.add(backup)
        session.commit()
        return backup

    @staticmethod
    def get_recent(session: Session, limit: int = 5) -> List[Backup]:
        return session.query(Backup).order_by(
            Backup.id.desc()
        ).limit(limit).all()


class PaymentRepository:
    """Payment history CRUD operations for debts and receivables."""

    @staticmethod
    def create(session: Session, transaction_id: int, user_id: int,
               amount: float, payment_type: str,
               jalali_date: str, jalali_time: str, jalali_full: str,
               description: str = None, photo_path: str = None) -> Payment:
        payment = Payment(
            transaction_id=transaction_id,
            user_id=user_id,
            amount=amount,
            payment_type=payment_type,
            description=description,
            photo_path=photo_path,
            jalali_date=jalali_date,
            jalali_time=jalali_time,
            jalali_full=jalali_full
        )
        session.add(payment)
        session.commit()
        return payment

    @staticmethod
    def get_by_transaction(session: Session, transaction_id: int) -> List[Payment]:
        return session.query(Payment).filter_by(
            transaction_id=transaction_id
        ).order_by(Payment.created_at.asc()).all()

    @staticmethod
    def get_total_paid(session: Session, transaction_id: int) -> float:
        result = session.query(func.sum(Payment.amount)).filter(
            Payment.transaction_id == transaction_id
        ).scalar()
        return float(result) if result else 0.0

    @staticmethod
    def get_remaining(session: Session, transaction_id: int, original_amount: float) -> float:
        paid = PaymentRepository.get_total_paid(session, transaction_id)
        return max(0.0, original_amount - paid)

    @staticmethod
    def get_by_user(session: Session, user_id: int, limit: int = 50) -> List[Payment]:
        return session.query(Payment).filter_by(
            user_id=user_id
        ).order_by(Payment.id.desc()).limit(limit).all()
