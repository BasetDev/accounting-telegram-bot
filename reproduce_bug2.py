#!/usr/bin/env python3
"""Comprehensive reproduction of receipt text display bug in Debt → Active Debts."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hesab'))

from app.database.models import init_database, get_collection
from app.database.repository import (
    UserRepository, TransactionRepository, PaymentRepository
)
from app.utils.jdatetime_helper import get_jalali_date, get_jalali_time, get_jalali_full

init_database()

TEST_USER_ID = your_telegram_user_id_here
user = UserRepository.get_or_create(telegram_id=TEST_USER_ID, username="testuser")
print(f"User ID: {user['id']}")

# Clean old test data
get_collection("transactions").delete_many({"party_name": {"$regex": "BUGTEST"}})
get_collection("payments").delete_many({})

# Create a debt with a PARTIAL payment so it stays in Active Debts
txn = TransactionRepository.create(
    user_id=user["id"],
    transaction_type="debt",
    amount=500000,
    party_name="BUGTEST مشتری تست",
    description="بدهی تست برای پرداخت جزئی",
    category="👤 شخصی",
    subcategory="دوستان",
    jalali_date=get_jalali_date(),
    jalali_time=get_jalali_time(),
    jalali_full=get_jalali_full(),
    due_jalali_date=get_jalali_date(),
)
print(f"\nDebt #{txn['id']} created: 500,000 تومان")

# Make a PARTIAL payment with receipt text
PaymentRepository.create(
    transaction_id=txn["id"],
    user_id=user["id"],
    amount=150000,
    payment_type="debt_payment",
    description="رسید شماره 1234 - پرداخت قسط اول",
    photo_path=None,
    jalali_date=get_jalali_date(),
    jalali_time=get_jalali_time(),
    jalali_full=get_jalali_full(),
)
print(f"Payment with receipt text saved: 'رسید شماره 1234 - پرداخت قسط اول'")

# Verify payment saved correctly
payments = PaymentRepository.get_by_transaction(txn["id"])
print(f"\n=== PAYMENTS IN DB ===")
for p in payments:
    print(f"  Payment #{p['id']}: desc={repr(p.get('description'))}, photo={p.get('photo_path')}")

remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
print(f"Remaining: {remaining} (still active)")

# Now simulate what happens in Active Debts flow
print(f"\n{'='*60}")
print(f"1. ACTIVE DEBTS LEVEL 1 (debt_active_list)")
print(f"{'='*60}")
# Get active debts
txns = TransactionRepository.get_active(user["id"], "debt")
print(f"Active debts returned: {len(txns)}")
for t in txns:
    print(f"  #{t['id']}: {t['party_name']} - {t['amount']} تومان - settled={t['is_settled']}")
    txn_payments = PaymentRepository.get_by_transaction(t["id"])
    if txn_payments:
        for p in txn_payments:
            print(f"    Payment: desc={repr(p.get('description'))}, photo={p.get('photo_path')}")

print(f"\n{'='*60}")
print(f"2. ACTIVE DEBTS LEVEL 2 (debt_customer_detail)")
print(f"{'='*60}")
from app.handlers.main_handler import _group_receivables_by_customer
groups = _group_receivables_by_customer(txns)
for g in groups:
    print(f"Customer: {g['party']}")
    print(f"  Transactions:")
    for t in g['txns']:
        print(f"    #{t['id']}: {t['amount']} تومان - settled={t['is_settled']}")
    print(f"  Active count: {g['active_count']}")

print(f"\n{'='*60}")
print(f"3. ACTIVE DEBTS LEVEL 3 (debt_item_detail)")
print(f"{'='*60}")
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
    text += f"\n📸 رسید پرداخت: ✅ دارد\n"

if payments_check:
    total_paid = sum(p["amount"] for p in payments_check)
    text += f"\n📊 سوابق پرداخت ({len(payments_check)} فقره):\n"
    for p in payments_check:
        text += f"  💰 {p['amount']} تومان"
        text += f" | {p['jalali_date']} ساعت {p['jalali_time']}"
        if p["description"]:
            text += f" | 📝 رسید: {p['description']}"
        if p["photo_path"]:
            text += f" | 📸 عکس: ✅ دارد"
        text += "\n"

print(text)

print(f"\n{'='*60}")
print(f"4. PAYMENT HISTORY (debt_payment_history)")
print(f"{'='*60}")
text2 = f"📋 تاریخچه پرداخت - بدهی #{txn['id']}\n\n"
total_paid2 = 0
for p in payments_check:
    total_paid2 += p["amount"]
    text2 += f"💰 {p['amount']} تومان\n"
    text2 += f"📅 {p['jalali_date']} ساعت {p['jalali_time']}\n"
    if p["description"]:
        text2 += f"📝 {p['description']}\n"
    if p["photo_path"]:
        text2 += f"📸 رسید: ✅ دارد\n"
    text2 += "──────────\n"
text2 += f"\n💰 مجموع پرداختی: {total_paid2} تومان"
print(text2)

# Clean up
get_collection("transactions").delete_many({"party_name": "BUGTEST مشتری تست"})
get_collection("payments").delete_many({"transaction_id": txn["id"]})
print("\nTest data cleaned up.")
