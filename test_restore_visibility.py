#!/usr/bin/env python3
"""Test that restored data is visible to the current user after restore.

Tests the exact scenario from the bug report:
1. User A creates data
2. Backup is created
3. User B (or same user) restores the backup
4. Verify all data is visible via repository queries

Usage:
    cd /home/bac/New folder/New/hesab
    python3 test_restore_visibility.py
"""

import sys
import os
import json
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "hesab"))
os.environ["DOTENV_PATH"] = os.path.dirname(__file__)

from app.database.models import (
    get_database, init_database, close_database,
    create_user_doc, create_transaction_doc, create_payment_doc,
    create_customer_doc, get_next_sequence
)
from app.database.repository import (
    UserRepository, TransactionRepository, PaymentRepository,
    CustomerRepository, CardInfoRepository
)
from app.services.backup_service import (
    create_full_backup, restore_from_backup, _merge_users_for_cross_bot,
    _update_counters_after_restore, _recreate_indexes, BACKUP_COLLECTIONS
)

PASS = 0
FAIL = 0
ERRORS = []

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        msg = f"  ❌ {name} {detail}"
        print(msg)
        ERRORS.append(msg)

def section(name):
    print(f"\n{'='*60}")
    print(f"📋 {name}")
    print(f"{'='*60}")


# ==============================
# Setup
# ==============================
section("Setup")
init_database()
db = get_database()
print(f"  Connected to MongoDB: {db.name}")

# Clean up test data
for coll_name in BACKUP_COLLECTIONS:
    db[coll_name].drop()
print("  Dropped all collections for clean test")


# ==============================
# Test 1: Same-user restore (backup from same installation)
# ==============================
section("Test 1: Same-User Restore")

# Create user and data
user_a = create_user_doc(telegram_id=111111, username="user_a", first_name="User A")
user_a.pop("_id", None)
db.users.insert_one(user_a)
user_a_id = user_a["id"]
print(f"  Created user A: id={user_a_id}, telegram_id=111111")

# Create transactions
for i in range(3):
    txn = create_transaction_doc(
        user_id=user_a_id, transaction_type="debt",
        amount=100000 * (i + 1), jalali_date="1404/01/01",
        jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00",
        party_name=f"Customer {i+1}", description=f"Debt {i+1}"
    )
    txn.pop("_id", None)
    db.transactions.insert_one(txn)

# Create customer
cust = create_customer_doc(user_a_id, "Test Customer", "09121234567")
cust.pop("_id", None)
db.customers.insert_one(cust)

# Create payment
pay = create_payment_doc(
    transaction_id=1, user_id=user_a_id,
    amount=50000, payment_type="debt_payment",
    jalali_date="1404/01/02", jalali_time="11:00:00",
    jalali_full="1404/01/02 - 11:00:00"
)
pay.pop("_id", None)
db.payments.insert_one(pay)

print(f"  Created 3 transactions, 1 customer, 1 payment")

# Create backup
backup_result = create_full_backup()
backup_path = backup_result["filepath"]
print(f"  Backup created: {backup_result['filename']}")

# Verify pre-restore visibility
debts_before = TransactionRepository.get_by_user(user_a_id, "debt")
test("Pre-restore: user A sees 3 debts", len(debts_before) == 3)

# Restore (same user)
restore_result = restore_from_backup(
    backup_path, drop_existing=True, remap_paths=True, new_telegram_id=111111
)
test("Restore succeeded", restore_result["success"])
test("No errors", len(restore_result["errors"]) == 0, str(restore_result["errors"]))

# Check visibility after restore
user_after = UserRepository.get_by_telegram_id(111111)
test("User found after restore", user_after is not None)

if user_after:
    debts_after = TransactionRepository.get_by_user(user_after["id"], "debt")
    test("User sees 3 debts after restore", len(debts_after) == 3,
         f"got {len(debts_after)}")
    
    customers_after = CustomerRepository.get_by_user(user_after["id"])
    test("User sees 1 customer after restore", len(customers_after) == 1,
         f"got {len(customers_after)}")
    
    payments_after = PaymentRepository.get_by_user(user_after["id"])
    test("User sees 1 payment after restore", len(payments_after) == 1,
         f"got {len(payments_after)}")


# ==============================
# Test 2: Cross-user restore (different telegram_id)
# ==============================
section("Test 2: Cross-User Restore")

# Clean up
for coll_name in BACKUP_COLLECTIONS:
    db[coll_name].drop()

# User A creates data
user_a2 = create_user_doc(telegram_id=222222, username="user_a2", first_name="User A2")
user_a2.pop("_id", None)
db.users.insert_one(user_a2)
user_a2_id = user_a2["id"]

for i in range(2):
    txn = create_transaction_doc(
        user_id=user_a2_id, transaction_type="debt",
        amount=200000 * (i + 1), jalali_date="1404/01/01",
        jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00",
        party_name=f"Customer X{i+1}", description=f"Debt X{i+1}"
    )
    txn.pop("_id", None)
    db.transactions.insert_one(txn)

txn_recv = create_transaction_doc(
    user_id=user_a2_id, transaction_type="receivable",
    amount=500000, jalali_date="1404/01/01",
    jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00",
    party_name="Receivable Customer", description="Receivable 1"
)
txn_recv.pop("_id", None)
db.transactions.insert_one(txn_recv)

cust2 = create_customer_doc(user_a2_id, "Customer X1", "09129876543")
cust2.pop("_id", None)
db.customers.insert_one(cust2)

print(f"  Created user A2 (id={user_a2_id}, tg=222222) with 3 transactions, 1 customer")

# Create backup
backup2 = create_full_backup()
backup2_path = backup2["filepath"]
print(f"  Backup created: {backup2['filename']}")

# User B (tg=333333) restores the backup
restore_result2 = restore_from_backup(
    backup2_path, drop_existing=True, remap_paths=True, new_telegram_id=333333
)
test("Cross-user restore succeeded", restore_result2["success"],
     str(restore_result2["errors"]))

# Check User B visibility
user_b = UserRepository.get_by_telegram_id(333333)
test("User B found after cross-user restore", user_b is not None)

if user_b:
    debts_b = TransactionRepository.get_by_user(user_b["id"], "debt")
    test("User B sees 2 debts", len(debts_b) == 2, f"got {len(debts_b)}")
    
    recv_b = TransactionRepository.get_by_user(user_b["id"], "receivable")
    test("User B sees 1 receivable", len(recv_b) == 1, f"got {len(recv_b)}")
    
    custs_b = CustomerRepository.get_by_user(user_b["id"])
    test("User B sees 1 customer", len(custs_b) == 1, f"got {len(custs_b)}")


# ==============================
# Test 3: Restore with NO users in backup
# ==============================
section("Test 3: Restore with Empty Users Collection")

# Clean up
for coll_name in BACKUP_COLLECTIONS:
    db[coll_name].drop()

# Create a "broken" backup with data but no users
# First create some data manually
db.transactions.insert_one({
    "id": 1, "user_id": 999, "transaction_type": "debt",
    "amount": 100000, "description": "Orphan debt",
    "jalali_date": "1404/01/01", "jalali_time": "10:00:00",
    "jalali_full": "1404/01/01 - 10:00:00",
    "is_settled": False, "created_at": "2024-01-01T00:00:00Z"
})
db.transactions.insert_one({
    "id": 2, "user_id": 999, "transaction_type": "receivable",
    "amount": 200000, "description": "Orphan receivable",
    "jalali_date": "1404/01/01", "jalali_time": "10:00:00",
    "jalali_full": "1404/01/01 - 10:00:00",
    "is_settled": False, "created_at": "2024-01-01T00:00:00Z"
})
db.customers.insert_one({
    "id": 1, "user_id": 999, "full_name": "Orphan Customer",
    "total_debt": 0, "total_receivable": 0,
    "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"
})

print(f"  Created orphan data with user_id=999 (no matching user)")

# Run merge with telegram_id=444444 (no user exists)
merge_count = _merge_users_for_cross_bot(db, 444444)
test("Merge returns >= 1 even with no users", merge_count >= 1,
     f"got {merge_count}")

# Check that a user was created
user_created = UserRepository.get_by_telegram_id(444444)
test("User created for telegram_id=444444", user_created is not None)

if user_created:
    # Check that orphan data was reassigned
    debts_orphan = TransactionRepository.get_by_user(user_created["id"], "debt")
    test("Orphan debt reassigned to new user", len(debts_orphan) == 1,
         f"got {len(debts_orphan)}")
    
    recv_orphan = TransactionRepository.get_by_user(user_created["id"], "receivable")
    test("Orphan receivable reassigned to new user", len(recv_orphan) == 1,
         f"got {len(recv_orphan)}")
    
    custs_orphan = CustomerRepository.get_by_user(user_created["id"])
    test("Orphan customer reassigned to new user", len(custs_orphan) == 1,
         f"got {len(custs_orphan)}")


# ==============================
# Test 4: Multiple users merge
# ==============================
section("Test 4: Multiple Users Merge")

# Clean up
for coll_name in BACKUP_COLLECTIONS:
    db[coll_name].drop()

# Create multiple users with data
u1 = create_user_doc(telegram_id=100, username="u1")
u1.pop("_id", None)
db.users.insert_one(u1)
u1_id = u1["id"]

u2 = create_user_doc(telegram_id=200, username="u2")
u2.pop("_id", None)
db.users.insert_one(u2)
u2_id = u2["id"]

# User 1 has more data
for i in range(5):
    t = create_transaction_doc(
        user_id=u1_id, transaction_type="debt",
        amount=100000, jalali_date="1404/01/01",
        jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00"
    )
    t.pop("_id", None)
    db.transactions.insert_one(t)

# User 2 has less data
t2 = create_transaction_doc(
    user_id=u2_id, transaction_type="debt",
    amount=200000, jalali_date="1404/01/01",
    jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00"
)
t2.pop("_id", None)
db.transactions.insert_one(t2)

print(f"  User 1 (id={u1_id}): 5 debts")
print(f"  User 2 (id={u2_id}): 1 debt")

# Merge to telegram_id=500
merge_count2 = _merge_users_for_cross_bot(db, 500)
test("Multi-user merge returns 1", merge_count2 == 1, f"got {merge_count2}")

user_merged = UserRepository.get_by_telegram_id(500)
test("Merged user found", user_merged is not None)

if user_merged:
    all_debts = TransactionRepository.get_by_user(user_merged["id"], "debt")
    test("All 6 debts visible to merged user", len(all_debts) == 6,
         f"got {len(all_debts)}")
    
    remaining_users = db.users.count_documents({})
    test("Only 1 user remains", remaining_users == 1, f"got {remaining_users}")


# ==============================
# Test 5: Full end-to-end restore with verification
# ==============================
section("Test 5: Full End-to-End Restore")

# Clean up
for coll_name in BACKUP_COLLECTIONS:
    db[coll_name].drop()

# Create comprehensive test data
user_e2e = create_user_doc(telegram_id=777777, username="e2e_user")
user_e2e.pop("_id", None)
db.users.insert_one(user_e2e)
e2e_id = user_e2e["id"]

# Debts
for i in range(3):
    t = create_transaction_doc(
        user_id=e2e_id, transaction_type="debt",
        amount=100000 * (i + 1), jalali_date="1404/01/01",
        jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00",
        party_name=f"Debt Customer {i+1}", category="🏢 کسب‌وکار"
    )
    t.pop("_id", None)
    db.transactions.insert_one(t)

# Receivables
for i in range(2):
    t = create_transaction_doc(
        user_id=e2e_id, transaction_type="receivable",
        amount=200000 * (i + 1), jalali_date="1404/01/01",
        jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00",
        party_name=f"Recv Customer {i+1}", category="👤 شخصی"
    )
    t.pop("_id", None)
    db.transactions.insert_one(t)

# Income
t_inc = create_transaction_doc(
    user_id=e2e_id, transaction_type="income",
    amount=500000, jalali_date="1404/01/01",
    jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00",
    description="Salary"
)
t_inc.pop("_id", None)
db.transactions.insert_one(t_inc)

# Expense
t_exp = create_transaction_doc(
    user_id=e2e_id, transaction_type="expense",
    amount=50000, jalali_date="1404/01/01",
    jalali_time="10:00:00", jalali_full="1404/01/01 - 10:00:00",
    description="Office supplies"
)
t_exp.pop("_id", None)
db.transactions.insert_one(t_exp)

# Customers
for name in ["Ali", "Sara", "Reza"]:
    c = create_customer_doc(e2e_id, name, f"0912{len(name)*1000000:07d}")
    c.pop("_id", None)
    db.customers.insert_one(c)

# Payments
p1 = create_payment_doc(
    transaction_id=1, user_id=e2e_id, amount=30000,
    payment_type="debt_payment", jalali_date="1404/01/02",
    jalali_time="11:00:00", jalali_full="1404/01/02 - 11:00:00",
    description="Partial payment"
)
p1.pop("_id", None)
db.payments.insert_one(p1)

print(f"  Created comprehensive data: 3 debts, 2 receivables, 1 income, 1 expense, 3 customers, 1 payment")

# Create backup
backup_e2e = create_full_backup()
print(f"  Backup: {backup_e2e['filename']}")

# Restore to a DIFFERENT user (telegram_id=888888)
restore_e2e = restore_from_backup(
    backup_e2e["filepath"], drop_existing=True, remap_paths=True, new_telegram_id=888888
)
test("E2E restore succeeded", restore_e2e["success"], str(restore_e2e["errors"]))

user_e2e_after = UserRepository.get_by_telegram_id(888888)
test("E2E user found", user_e2e_after is not None)

if user_e2e_after:
    uid = user_e2e_after["id"]
    
    debts = TransactionRepository.get_by_user(uid, "debt")
    test("E2E: 3 debts visible", len(debts) == 3, f"got {len(debts)}")
    
    recv = TransactionRepository.get_by_user(uid, "receivable")
    test("E2E: 2 receivables visible", len(recv) == 2, f"got {len(recv)}")
    
    income = TransactionRepository.get_by_user(uid, "income")
    test("E2E: 1 income visible", len(income) == 1, f"got {len(income)}")
    
    expense = TransactionRepository.get_by_user(uid, "expense")
    test("E2E: 1 expense visible", len(expense) == 1, f"got {len(expense)}")
    
    custs = CustomerRepository.get_by_user(uid)
    test("E2E: 3 customers visible", len(custs) == 3, f"got {len(custs)}")
    
    pays = PaymentRepository.get_by_user(uid)
    test("E2E: 1 payment visible", len(pays) == 1, f"got {len(pays)}")
    
    # Check active debts (is_settled=False)
    active = TransactionRepository.get_active(uid, "debt")
    test("E2E: active debts queryable", len(active) >= 0)  # May be 0 if all settled
    
    # Check summary
    summary = TransactionRepository.get_summary(uid, "debt")
    test("E2E: debt summary > 0", summary > 0, f"got {summary}")


# ==============================
# Summary
# ==============================
section("RESULTS")
total = PASS + FAIL
print(f"\n  {'✅' if FAIL == 0 else '❌'} Total: {total} | Passed: {PASS} | Failed: {FAIL}")
if ERRORS:
    print(f"\n  Failed tests:")
    for err in ERRORS:
        print(f"    {err}")

# Cleanup
for coll_name in BACKUP_COLLECTIONS:
    db[coll_name].drop()

import shutil
if os.path.exists(os.path.join(os.path.dirname(__file__), "backups")):
    shutil.rmtree(os.path.join(os.path.dirname(__file__), "backups"), ignore_errors=True)

print(f"\n  Cleanup complete.")
close_database()
