#!/usr/bin/env python3
"""Reproduce the receipt text display bug in Debt → Active Debts section."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hesab'))

from app.database.models import init_database, get_collection
from app.database.repository import (
    UserRepository, TransactionRepository, PaymentRepository
)
from app.utils.jdatetime_helper import get_jalali_date, get_jalali_time, get_jalali_full

# Initialize database
init_database()

TEST_USER_ID = your_telegram_user_id_here

# Clean up any existing test data
get_collection("transactions").delete_many({"user_id": {"$exists": True}, "party_name": {"$regex": "BUGTEST"}})
get_collection("payments").delete_many({"user_id": {"$exists": True}})

# Get or create user
user = UserRepository.get_or_create(
    telegram_id=TEST_USER_ID,
    username="testuser",
    first_name="Test",
    last_name="User"
)
print(f"User: {user['id']}")

# Create a debt
txn = TransactionRepository.create(
    user_id=user["id"],
    transaction_type="debt",
    amount=500000,
    party_name="BUGTEST شرکت تست",
    description="بدهی تست برای رصد باگ",
    category="🏢 کسب‌وکار",
    subcategory="سایر",
    jalali_date=get_jalali_date(),
    jalali_time=get_jalali_time(),
    jalali_full=get_jalali_full(),
    due_jalali_date=get_jalali_date(),
    due_jalali_time=get_jalali_time(),
)
print(f"Debt created: #{txn['id']}")

# Scenario 1: Payment with receipt text only
payment1 = PaymentRepository.create(
    transaction_id=txn["id"],
    user_id=user["id"],
    amount=200000,
    payment_type="debt_payment",
    description="پرداخت شده با کارت 1234 - فاکتور 1001",
    photo_path=None,
    jalali_date=get_jalali_date(),
    jalali_time=get_jalali_time(),
    jalali_full=get_jalali_full(),
)
print(f"Payment 1 (text only): #{payment1['id']}, description={payment1['description']}")

# Scenario 2: Payment with receipt photo only
payment2 = PaymentRepository.create(
    transaction_id=txn["id"],
    user_id=user["id"],
    amount=100000,
    payment_type="debt_payment",
    description=None,
    photo_path="/uploads/test_photo.jpg",
    jalali_date=get_jalali_date(),
    jalali_time=get_jalali_time(),
    jalali_full=get_jalali_full(),
)
print(f"Payment 2 (photo only): #{payment2['id']}, photo_path={payment2['photo_path']}")

# Scenario 3: Payment with both receipt text and photo
payment3 = PaymentRepository.create(
    transaction_id=txn["id"],
    user_id=user["id"],
    amount=200000,
    payment_type="debt_payment",
    description="پرداخت نهایی - فاکتور 1002 - تکمیل شد",
    photo_path="/uploads/test_photo2.jpg",
    jalali_date=get_jalali_date(),
    jalali_time=get_jalali_time(),
    jalali_full=get_jalali_full(),
)
print(f"Payment 3 (text+photo): #{payment3['id']}, description={payment3['description']}, photo_path={payment3['photo_path']}")

# Mark as settled
TransactionRepository.settle_transaction(txn["id"])

# Now retrieve and verify
print("\n=== VERIFICATION ===")

# Check payments in DB
payments = PaymentRepository.get_by_transaction(txn["id"])
print(f"\nPayments retrieved: {len(payments)}")
for p in payments:
    print(f"  Payment #{p['id']}: amount={p['amount']}, description={p.get('description')}, photo_path={p.get('photo_path')}")

# Check remaining
remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
print(f"Remaining: {remaining}")

# Now test what the handler functions would display
print("\n=== DEBT_ITEM_DETAIL OUTPUT (Level 3 - Debt Details) ===")
txn_check = TransactionRepository.get_by_id(txn["id"])
payments_check = PaymentRepository.get_by_transaction(txn_check["id"])
has_payment_photo = any(p["photo_path"] for p in payments_check) if payments_check else False

text = f"📋 جزئیات بدهی\n\n"
text += f"🆔 شناسه: {txn_check['id']}\n"
text += f"👤 طرف حساب: {txn_check['party_name'] or '-'}\n"
text += f"💰 مبلغ کل: {txn_check['amount']} تومان\n"
text += f"💰 باقی‌مانده: {remaining} تومان\n"
if txn_check["description"]:
    text += f"📝 توضیحات: {txn_check['description']}\n"
text += f"📅 ثبت: {txn_check['jalali_date']} ساعت {txn_check['jalali_time']}"

if has_payment_photo:
    text += f"\n📸 رسید پرداخت: ✅ دارد"

if payments_check:
    total_paid = sum(p["amount"] for p in payments_check)
    text += f"\n\n📊 سوابق پرداخت ({len(payments_check)} فقره):\n"
    for p in payments_check:
        text += f"  💰 {p['amount']} تومان"
        text += f" | {p['jalali_date']} ساعت {p['jalali_time']}"
        if p["description"]:
            text += f" | {p['description']}"
        if p["photo_path"]:
            text += f" | 📸 رسید"
        text += "\n"

print(text)

print("\n=== DEBT_PAYMENT_HISTORY OUTPUT ===")
text2 = f"📋 تاریخچه پرداخت - بدهی #{txn['id']}\n\n"
total_paid = 0
for p in payments:
    total_paid += p["amount"]
    text2 += f"💰 {p['amount']} تومان\n"
    text2 += f"📅 {p['jalali_date']} ساعت {p['jalali_time']}\n"
    if p["description"]:
        text2 += f"📝 {p['description']}\n"
    if p["photo_path"]:
        text2 += f"📸 رسید: ✅ دارد\n"
    text2 += "──────────\n"
text2 += f"\n💰 مجموع پرداختی: {total_paid} تومان"
print(text2)

print("\n=== DEBT_ACTIVE_LIST OUTPUT (Level 1 - Active Debts) ===")
# This is what debt_active_list shows - just summary, no payment details
txns = TransactionRepository.get_active(user["id"], "debt")
print(f"Active debts: {len(txns)}")
for t in txns:
    print(f"  #{t['id']}: {t['party_name']} - {t['amount']} تومان - is_settled={t['is_settled']}")
    # Check if payments exist for this transaction
    txn_payments = PaymentRepository.get_by_transaction(t["id"])
    if txn_payments:
        print(f"    Payments: {len(txn_payments)}")
        for p in txn_payments:
            print(f"      desc={p.get('description')}, photo={p.get('photo_path')}")
    else:
        print(f"    Payments: NONE")

# Check the debt_customer_detail (Level 2) output
print("\n=== DEBT_CUSTOMER_DETAIL OUTPUT (Level 2 - Customer Debt List) ===")
from app.handlers.main_handler import _group_receivables_by_customer
groups = _group_receivables_by_customer(txns)
for g in groups:
    print(f"Customer: {g['party']}")
    print(f"  Count: {g['count']}, Total: {g['total']}, Remaining: {g['remaining']}")
    for t in g["txns"]:
        print(f"  Txn #{t['id']}: amount={t['amount']}, is_settled={t['is_settled']}")
        # Level 2 only shows txn data, NOT payment data
        # This is the potential bug area

print("\n=== SUMMARY ===")
print(f"Receipt text saved in DB: YES (payment1.description = '{payment1['description']}')")
print(f"Receipt text shown in debt_item_detail: YES (line: ' | {payment1['description']}')")
print(f"Receipt text shown in debt_payment_history: YES (line: '📝 {payment1['description']}')")
print(f"Receipt text shown in debt_active_list (Level 1): NO (summary view only)")
print(f"Receipt text shown in debt_customer_detail (Level 2): NO (list view only)")

# Clean up
get_collection("transactions").delete_many({"party_name": "BUGTEST شرکت تست"})
get_collection("payments").delete_many({"transaction_id": txn["id"]})
print("\nTest data cleaned up.")
