"""MongoDB repository layer for CRUD operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pymongo.collection import Collection
from pymongo import DESCENDING, ASCENDING

from app.database.models import (
    get_collection, get_next_sequence,
    create_user_doc, create_transaction_doc, create_customer_doc,
    create_reminder_doc, create_card_info_doc, create_backup_doc,
    create_payment_doc, _utcnow
)
from app.utils.logger import logger


class UserRepository:
    """User CRUD operations."""

    @staticmethod
    def get_or_create(telegram_id: int, username: str = None,
                      first_name: str = None, last_name: str = None) -> Dict:
        users = get_collection("users")
        user = users.find_one({"telegram_id": telegram_id})

        if not user:
            user = create_user_doc(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            users.insert_one(user)
        else:
            # Update info if changed
            update_fields = {}
            if username and user.get("username") != username:
                update_fields["username"] = username
            if first_name and user.get("first_name") != first_name:
                update_fields["first_name"] = first_name
            if last_name and user.get("last_name") != last_name:
                update_fields["last_name"] = last_name
            if update_fields:
                update_fields["updated_at"] = _utcnow()
                users.update_one({"_id": user["_id"]}, {"$set": update_fields})
                user.update(update_fields)

        user.pop("_id", None)
        return user

    @staticmethod
    def get_by_telegram_id(telegram_id: int) -> Optional[Dict]:
        users = get_collection("users")
        user = users.find_one({"telegram_id": telegram_id})
        if user:
            user.pop("_id", None)
        return user

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        users = get_collection("users")
        user = users.find_one({"id": user_id})
        if user:
            user.pop("_id", None)
        return user

    @staticmethod
    def make_admin(telegram_id: int) -> bool:
        users = get_collection("users")
        result = users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"is_admin": True, "updated_at": _utcnow()}}
        )
        return result.modified_count > 0

    @staticmethod
    def get_all_users() -> List[Dict]:
        users = get_collection("users")
        result = []
        for user in users.find():
            user.pop("_id", None)
            result.append(user)
        return result


class TransactionRepository:
    """Transaction CRUD operations."""

    @staticmethod
    def create(user_id: int, transaction_type: str,
               amount: float, jalali_date: str, jalali_time: str, jalali_full: str,
               description: str = None, category: str = None, subcategory: str = None,
               party_name: str = None, customer_id: int = None,
               due_jalali_date: str = None, due_jalali_time: str = None,
               photo_path: str = None, card_number: str = None, sheba: str = None,
               bank_name: str = None) -> Dict:
        transactions = get_collection("transactions")
        txn = create_transaction_doc(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            jalali_date=jalali_date,
            jalali_time=jalali_time,
            jalali_full=jalali_full,
            description=description,
            category=category,
            subcategory=subcategory,
            party_name=party_name,
            customer_id=customer_id,
            due_jalali_date=due_jalali_date,
            due_jalali_time=due_jalali_time,
            photo_path=photo_path,
            card_number=card_number,
            sheba=sheba,
            bank_name=bank_name
        )
        transactions.insert_one(txn)
        txn.pop("_id", None)
        return txn

    @staticmethod
    def get_by_id(txn_id: int) -> Optional[Dict]:
        transactions = get_collection("transactions")
        txn = transactions.find_one({"id": txn_id})
        if txn:
            txn.pop("_id", None)
        return txn

    @staticmethod
    def get_by_user(user_id: int, transaction_type: str = None,
                    limit: int = 50, offset: int = 0) -> List[Dict]:
        transactions = get_collection("transactions")
        query = {"user_id": user_id}
        if transaction_type:
            query["transaction_type"] = transaction_type
        result = []
        for txn in transactions.find(query).sort("id", DESCENDING).skip(offset).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_active(user_id: int, transaction_type: str,
                   limit: int = 50) -> List[Dict]:
        """Get non-settled transactions of a given type."""
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "is_settled": False
        }
        result = []
        for txn in transactions.find(query).sort("id", DESCENDING).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_settled(user_id: int, transaction_type: str,
                    limit: int = 50) -> List[Dict]:
        """Get settled transactions of a given type."""
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "is_settled": True
        }
        result = []
        for txn in transactions.find(query).sort("id", DESCENDING).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_with_payments(user_id: int, transaction_type: str,
                          limit: int = 50) -> List[Dict]:
        """Get transactions that have at least one payment recorded.

        Returns both partially paid AND fully settled transactions.
        This is the primary query for the Settlement (تسویه) section.
        """
        payments = get_collection("payments")
        txn_ids = payments.distinct("transaction_id", {"user_id": user_id})

        if not txn_ids:
            return []

        # Also include transactions marked as settled (is_settled=True)
        # in case settle was done without a payment record
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "$or": [
                {"id": {"$in": txn_ids}},
                {"is_settled": True}
            ]
        }
        result = []
        for txn in transactions.find(query).sort("id", DESCENDING).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_overdue(user_id: int, transaction_type: str,
                    today_jalali: str, limit: int = 50) -> List[Dict]:
        """Get non-settled transactions with due date before today."""
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "is_settled": False,
            "due_jalali_date": {"$ne": None, "$lt": today_jalali}
        }
        result = []
        for txn in transactions.find(query).sort("due_jalali_date", ASCENDING).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_due_today(user_id: int, transaction_type: str,
                      today_jalali: str, limit: int = 50) -> List[Dict]:
        """Get non-settled transactions with due date = today."""
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "is_settled": False,
            "due_jalali_date": today_jalali
        }
        result = []
        for txn in transactions.find(query).sort("id", DESCENDING).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_due_this_week(user_id: int, transaction_type: str,
                          today_jalali: str, week_end_jalali: str,
                          limit: int = 50) -> List[Dict]:
        """Get non-settled transactions with due date between today and end of week."""
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "is_settled": False,
            "due_jalali_date": {"$ne": None, "$gte": today_jalali, "$lte": week_end_jalali}
        }
        result = []
        for txn in transactions.find(query).sort("due_jalali_date", ASCENDING).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_by_date_range(user_id: int, start_date: str, end_date: str,
                          transaction_type: str = None) -> List[Dict]:
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "jalali_date": {"$gte": start_date, "$lte": end_date}
        }
        if transaction_type:
            query["transaction_type"] = transaction_type
        result = []
        for txn in transactions.find(query).sort("id", DESCENDING):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_by_customer(customer_id: int) -> List[Dict]:
        transactions = get_collection("transactions")
        result = []
        for txn in transactions.find({"customer_id": customer_id}).sort("id", DESCENDING):
            txn.pop("_id", None)
            result.append(txn)
        return result

    @staticmethod
    def get_summary(user_id: int, transaction_type: str = None) -> float:
        transactions = get_collection("transactions")
        query = {
            "user_id": user_id,
            "is_settled": False
        }
        if transaction_type:
            query["transaction_type"] = transaction_type

        pipeline = [
            {"$match": query},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = list(transactions.aggregate(pipeline))
        return float(result[0]["total"]) if result else 0.0

    @staticmethod
    def get_total_by_type(user_id: int) -> dict:
        """Get total amounts grouped by transaction type."""
        results = {}
        for ttype in ['income', 'expense', 'debt', 'receivable']:
            total = TransactionRepository.get_summary(user_id, ttype)
            results[ttype] = total
        return results

    @staticmethod
    def update(txn_id: int, **kwargs) -> bool:
        """Update transaction fields. Only provided kwargs are updated."""
        transactions = get_collection("transactions")
        allowed_fields = {
            'amount', 'description', 'category', 'subcategory', 'party_name',
            'due_jalali_date', 'due_jalali_time', 'jalali_date', 'jalali_time', 'jalali_full',
            'is_settled', 'settled_at', 'photo_path', 'card_number', 'sheba', 'bank_name'
        }
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not update_data:
            return False

        result = transactions.update_one(
            {"id": txn_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    def settle_transaction(txn_id: int) -> bool:
        transactions = get_collection("transactions")
        result = transactions.update_one(
            {"id": txn_id},
            {"$set": {
                "is_settled": True,
                "settled_at": datetime.now(timezone.utc)
            }}
        )
        return result.modified_count > 0

    @staticmethod
    def delete(txn_id: int) -> bool:
        transactions = get_collection("transactions")
        result = transactions.delete_one({"id": txn_id})
        return result.deleted_count > 0

    @staticmethod
    def search(user_id: int, query_text: str = None,
               transaction_type: str = None, min_amount: float = None,
               max_amount: float = None, start_date: str = None,
               end_date: str = None, category: str = None,
               party_name: str = None, limit: int = 20) -> List[Dict]:
        transactions = get_collection("transactions")
        query = {"user_id": user_id}

        if query_text:
            query["$or"] = [
                {"description": {"$regex": query_text, "$options": "i"}},
                {"category": {"$regex": query_text, "$options": "i"}},
                {"party_name": {"$regex": query_text, "$options": "i"}}
            ]

        if transaction_type:
            query["transaction_type"] = transaction_type
        if min_amount is not None:
            query.setdefault("amount", {})["$gte"] = min_amount
        if max_amount is not None:
            query.setdefault("amount", {})["$lte"] = max_amount
        if start_date:
            query.setdefault("jalali_date", {})["$gte"] = start_date
        if end_date:
            query.setdefault("jalali_date", {})["$lte"] = end_date
        if category:
            query["category"] = category
        if party_name:
            query["party_name"] = {"$regex": party_name, "$options": "i"}

        result = []
        for txn in transactions.find(query).sort("id", DESCENDING).limit(limit):
            txn.pop("_id", None)
            result.append(txn)
        return result


class CustomerRepository:
    """Customer CRUD operations."""

    @staticmethod
    def create(user_id: int, full_name: str,
               phone: str = None, address: str = None,
               notes: str = None) -> Dict:
        customers = get_collection("customers")
        customer = create_customer_doc(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            address=address,
            notes=notes
        )
        customers.insert_one(customer)
        customer.pop("_id", None)
        return customer

    @staticmethod
    def get_by_id(customer_id: int) -> Optional[Dict]:
        customers = get_collection("customers")
        customer = customers.find_one({"id": customer_id})
        if customer:
            customer.pop("_id", None)
        return customer

    @staticmethod
    def get_by_user(user_id: int) -> List[Dict]:
        customers = get_collection("customers")
        result = []
        for customer in customers.find({"user_id": user_id}).sort("full_name", ASCENDING):
            customer.pop("_id", None)
            result.append(customer)
        return result

    @staticmethod
    def search(user_id: int, query: str) -> List[Dict]:
        customers = get_collection("customers")
        regex = {"$regex": query, "$options": "i"}
        query_filter = {
            "user_id": user_id,
            "$or": [
                {"full_name": regex},
                {"phone": regex}
            ]
        }
        result = []
        for customer in customers.find(query_filter):
            customer.pop("_id", None)
            result.append(customer)
        return result

    @staticmethod
    def update(customer_id: int, full_name: str = None, phone: str = None,
               address: str = None, notes: str = None) -> bool:
        customers = get_collection("customers")
        update_data = {"updated_at": _utcnow()}
        if full_name:
            update_data["full_name"] = full_name
        if phone is not None:
            update_data["phone"] = phone
        if address is not None:
            update_data["address"] = address
        if notes is not None:
            update_data["notes"] = notes

        result = customers.update_one(
            {"id": customer_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    def delete(customer_id: int) -> bool:
        customers = get_collection("customers")
        result = customers.delete_one({"id": customer_id})
        return result.deleted_count > 0

    @staticmethod
    def update_financial_summary(customer_id: int) -> bool:
        """Recalculate and update customer's total debt and receivable."""
        transactions = get_collection("transactions")
        customers = get_collection("customers")

        # Calculate total debt
        debt_pipeline = [
            {"$match": {
                "customer_id": customer_id,
                "transaction_type": "debt",
                "is_settled": False
            }},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        debt_result = list(transactions.aggregate(debt_pipeline))
        total_debt = float(debt_result[0]["total"]) if debt_result else 0.0

        # Calculate total receivable
        recv_pipeline = [
            {"$match": {
                "customer_id": customer_id,
                "transaction_type": "receivable",
                "is_settled": False
            }},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        recv_result = list(transactions.aggregate(recv_pipeline))
        total_receivable = float(recv_result[0]["total"]) if recv_result else 0.0

        result = customers.update_one(
            {"id": customer_id},
            {"$set": {
                "total_debt": total_debt,
                "total_receivable": total_receivable,
                "updated_at": _utcnow()
            }}
        )
        return result.modified_count > 0


class ReminderRepository:
    """Reminder CRUD operations."""

    @staticmethod
    def create(user_id: int, reminder_type: str,
               title: str, reminder_jalali_date: str,
               message: str = None, transaction_id: int = None,
               reminder_time: str = None) -> Dict:
        reminders = get_collection("reminders")
        reminder = create_reminder_doc(
            user_id=user_id,
            reminder_type=reminder_type,
            title=title,
            reminder_jalali_date=reminder_jalali_date,
            message=message,
            transaction_id=transaction_id,
            reminder_time=reminder_time
        )
        reminders.insert_one(reminder)
        reminder.pop("_id", None)
        return reminder

    @staticmethod
    def get_pending(jalali_date: str) -> List[Dict]:
        reminders = get_collection("reminders")
        query = {
            "reminder_jalali_date": {"$lte": jalali_date},
            "is_sent": False
        }
        result = []
        for reminder in reminders.find(query):
            reminder.pop("_id", None)
            result.append(reminder)
        return result

    @staticmethod
    def mark_sent(reminder_id: int) -> bool:
        reminders = get_collection("reminders")
        result = reminders.update_one(
            {"id": reminder_id},
            {"$set": {
                "is_sent": True,
                "sent_at": datetime.now(timezone.utc)
            }}
        )
        return result.modified_count > 0


class CardInfoRepository:
    """Card info (شماره کارت و شبا) CRUD operations."""

    @staticmethod
    def create(user_id: int, name: str,
               card_number: str = None, sheba: str = None,
               customer_id: int = None, bank_name: str = None) -> Dict:
        cards = get_collection("card_info")
        card = create_card_info_doc(
            user_id=user_id,
            name=name,
            card_number=card_number,
            sheba=sheba,
            customer_id=customer_id,
            bank_name=bank_name
        )
        cards.insert_one(card)
        card.pop("_id", None)
        return card

    @staticmethod
    def get_by_id(card_id: int) -> Optional[Dict]:
        cards = get_collection("card_info")
        card = cards.find_one({"id": card_id})
        if card:
            card.pop("_id", None)
        return card

    @staticmethod
    def get_by_user(user_id: int) -> List[Dict]:
        cards = get_collection("card_info")
        result = []
        for card in cards.find({"user_id": user_id}).sort("id", DESCENDING):
            card.pop("_id", None)
            result.append(card)
        return result

    @staticmethod
    def update(card_id: int, name: str = None,
               card_number: str = None, sheba: str = None,
               customer_id: int = None, bank_name: str = None) -> bool:
        cards = get_collection("card_info")
        update_data = {"updated_at": _utcnow()}
        if name is not None:
            update_data["name"] = name
        if card_number is not None:
            update_data["card_number"] = card_number
        if sheba is not None:
            update_data["sheba"] = sheba
        if customer_id is not None:
            update_data["customer_id"] = customer_id
        if bank_name is not None:
            update_data["bank_name"] = bank_name

        result = cards.update_one(
            {"id": card_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    def delete(card_id: int) -> bool:
        cards = get_collection("card_info")
        result = cards.delete_one({"id": card_id})
        return result.deleted_count > 0

    @staticmethod
    def search(user_id: int, query: str) -> List[Dict]:
        cards = get_collection("card_info")
        regex = {"$regex": query, "$options": "i"}
        query_filter = {
            "user_id": user_id,
            "$or": [
                {"name": regex},
                {"card_number": regex},
                {"sheba": regex}
            ]
        }
        result = []
        for card in cards.find(query_filter):
            card.pop("_id", None)
            result.append(card)
        return result


class BackupRepository:
    """Backup record CRUD operations."""

    @staticmethod
    def create(user_id: int, filename: str,
               file_size: int, jalali_date: str,
               jalali_time: str = None) -> Dict:
        backups = get_collection("backups")
        backup = create_backup_doc(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            jalali_date=jalali_date,
            jalali_time=jalali_time
        )
        backups.insert_one(backup)
        backup.pop("_id", None)
        return backup

    @staticmethod
    def get_recent(limit: int = 5) -> List[Dict]:
        backups = get_collection("backups")
        result = []
        for backup in backups.find().sort("id", DESCENDING).limit(limit):
            backup.pop("_id", None)
            result.append(backup)
        return result


class PaymentRepository:
    """Payment history CRUD operations for debts and receivables."""

    @staticmethod
    def create(transaction_id: int, user_id: int,
               amount: float, payment_type: str,
               jalali_date: str, jalali_time: str, jalali_full: str,
               description: str = None, photo_path: str = None) -> Dict:
        payments = get_collection("payments")
        payment = create_payment_doc(
            transaction_id=transaction_id,
            user_id=user_id,
            amount=amount,
            payment_type=payment_type,
            jalali_date=jalali_date,
            jalali_time=jalali_time,
            jalali_full=jalali_full,
            description=description,
            photo_path=photo_path
        )
        payments.insert_one(payment)
        payment.pop("_id", None)
        return payment

    @staticmethod
    def get_by_transaction(transaction_id: int) -> List[Dict]:
        payments = get_collection("payments")
        result = []
        for payment in payments.find({"transaction_id": transaction_id}).sort("created_at", ASCENDING):
            payment.pop("_id", None)
            result.append(payment)
        return result

    @staticmethod
    def get_total_paid(transaction_id: int) -> float:
        payments = get_collection("payments")
        pipeline = [
            {"$match": {"transaction_id": transaction_id}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = list(payments.aggregate(pipeline))
        return float(result[0]["total"]) if result else 0.0

    @staticmethod
    def get_remaining(transaction_id: int, original_amount: float) -> float:
        paid = PaymentRepository.get_total_paid(transaction_id)
        return max(0.0, original_amount - paid)

    @staticmethod
    def get_by_user(user_id: int, limit: int = 50) -> List[Dict]:
        payments = get_collection("payments")
        result = []
        for payment in payments.find({"user_id": user_id}).sort("id", DESCENDING).limit(limit):
            payment.pop("_id", None)
            result.append(payment)
        return result
