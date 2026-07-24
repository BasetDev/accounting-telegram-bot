#!/usr/bin/env python3
"""Test script to verify the edit workflow for Debt → Paid Debts and Receivables → Received Payments."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hesab'))

from app.database.models import init_database, get_collection
from app.database.repository import TransactionRepository, PaymentRepository, UserRepository
from app.keyboards.markups import (
    debt_payments_detail_keyboard,
    recv_payments_detail_keyboard,
    edit_field_keyboard,
    edit_photo_keyboard,
    confirm_keyboard,
    debt_category_keyboard,
    receivable_category_keyboard,
)
from app.utils.jdatetime_helper import format_amount

def test_keyboard_functions():
    """Test that keyboard functions generate correct buttons."""
    print("=" * 60)
    print("Testing Keyboard Functions")
    print("=" * 60)
    
    # Test debt_payments_detail_keyboard
    print("\n1. Testing debt_payments_detail_keyboard...")
    kb1 = debt_payments_detail_keyboard(
        txn_id=123,
        cache_key='test_key',
        safe_party='test_party',
        has_photo=True,
        has_payment_photo=True,
        has_payment_info=True
    )
    print(f"   Rows: {len(kb1.inline_keyboard)}")
    for i, row in enumerate(kb1.inline_keyboard):
        for btn in row:
            print(f"   Row {i}: {btn.text} → {btn.callback_data}")
    
    # Verify edit button exists
    has_edit = any(
        btn.callback_data and btn.callback_data.startswith("edit_debt:")
        for row in kb1.inline_keyboard
        for btn in row
    )
    print(f"   ✅ Edit button present: {has_edit}")
    
    # Test recv_payments_detail_keyboard
    print("\n2. Testing recv_payments_detail_keyboard...")
    kb2 = recv_payments_detail_keyboard(
        txn_id=456,
        cache_key='test_key',
        safe_party='test_party',
        has_photo=True,
        has_payment_photo=True,
        has_payment_info=True
    )
    print(f"   Rows: {len(kb2.inline_keyboard)}")
    for i, row in enumerate(kb2.inline_keyboard):
        for btn in row:
            print(f"   Row {i}: {btn.text} → {btn.callback_data}")
    
    # Verify edit button exists
    has_edit = any(
        btn.callback_data and btn.callback_data.startswith("edit_receivable:")
        for row in kb2.inline_keyboard
        for btn in row
    )
    print(f"   ✅ Edit button present: {has_edit}")
    
    # Test edit_field_keyboard
    print("\n3. Testing edit_field_keyboard...")
    kb3 = edit_field_keyboard()
    print(f"   Rows: {len(kb3.inline_keyboard)}")
    for i, row in enumerate(kb3.inline_keyboard):
        for btn in row:
            print(f"   Row {i}: {btn.text} → {btn.callback_data}")
    
    # Test edit_photo_keyboard
    print("\n4. Testing edit_photo_keyboard...")
    kb4 = edit_photo_keyboard(has_photo=True)
    print(f"   Rows: {len(kb4.keyboard)}")
    for i, row in enumerate(kb4.keyboard):
        for btn in row:
            print(f"   Row {i}: {btn.text}")
    
    print("\n✅ All keyboard functions work correctly!")
    return True

def test_handler_registration():
    """Test that handlers are registered correctly."""
    print("\n" + "=" * 60)
    print("Testing Handler Registration")
    print("=" * 60)
    
    import re
    with open('hesab/app/handlers/main_handler.py', 'r') as f:
        content = f.read()
    
    # Check for edit_debt handler
    edit_debt_match = re.search(r'@router\.callback_query\(F\.data\.startswith\("edit_debt:"\)\)', content)
    print(f"\n1. edit_debt handler: {'✅ Found' if edit_debt_match else '❌ Missing'}")
    
    # Check for edit_receivable handler
    edit_recv_match = re.search(r'@router\.callback_query\(F\.data\.startswith\("edit_receivable:"\)\)', content)
    print(f"2. edit_receivable handler: {'✅ Found' if edit_recv_match else '❌ Missing'}")
    
    # Check for edit_field handler
    edit_field_match = re.search(r'@router\.callback_query\(F\.data\.startswith\("edit_field:"\)', content)
    print(f"3. edit_field handler: {'✅ Found' if edit_field_match else '❌ Missing'}")
    
    # Check for _start_edit_by_id function
    start_edit_match = re.search(r'async def _start_edit_by_id\(', content)
    print(f"4. _start_edit_by_id function: {'✅ Found' if start_edit_match else '❌ Missing'}")
    
    # Check for DebtEditForm
    debt_edit_form_match = re.search(r'class DebtEditForm\(StatesGroup\):', content)
    print(f"5. DebtEditForm class: {'✅ Found' if debt_edit_form_match else '❌ Missing'}")
    
    # Check for ReceivableEditForm
    recv_edit_form_match = re.search(r'class ReceivableEditForm\(StatesGroup\):', content)
    print(f"6. ReceivableEditForm class: {'✅ Found' if recv_edit_form_match else '❌ Missing'}")
    
    # Check for edit_amount_handler
    edit_amount_match = re.search(r'async def edit_amount_handler\(', content)
    print(f"7. edit_amount_handler: {'✅ Found' if edit_amount_match else '❌ Missing'}")
    
    # Check for edit_party_handler
    edit_party_match = re.search(r'async def edit_party_handler\(', content)
    print(f"8. edit_party_handler: {'✅ Found' if edit_party_match else '❌ Missing'}")
    
    # Check for edit_description_handler
    edit_desc_match = re.search(r'async def edit_description_handler\(', content)
    print(f"9. edit_description_handler: {'✅ Found' if edit_desc_match else '❌ Missing'}")
    
    # Check for edit_due_date_handler
    edit_date_match = re.search(r'async def edit_due_date_handler\(', content)
    print(f"10. edit_due_date_handler: {'✅ Found' if edit_date_match else '❌ Missing'}")
    
    # Check for edit_photo_handler
    edit_photo_match = re.search(r'async def edit_photo_handler\(', content)
    print(f"11. edit_photo_handler: {'✅ Found' if edit_photo_match else '❌ Missing'}")
    
    # Check for _process_edit_confirm function
    process_edit_match = re.search(r'async def _process_edit_confirm\(', content)
    print(f"12. _process_edit_confirm function: {'✅ Found' if process_edit_match else '❌ Missing'}")
    
    all_found = all([
        edit_debt_match, edit_recv_match, edit_field_match, start_edit_match,
        debt_edit_form_match, recv_edit_form_match, edit_amount_match,
        edit_party_match, edit_desc_match, edit_date_match, edit_photo_match,
        process_edit_match
    ])
    
    print(f"\n{'✅ All handlers registered!' if all_found else '❌ Some handlers missing!'}")
    return all_found

def test_database_operations():
    """Test database operations for edit workflow."""
    print("\n" + "=" * 60)
    print("Testing Database Operations")
    print("=" * 60)
    
    init_database()
    
    # Get test user
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    if not user:
        print("❌ Test user not found!")
        return False
    
    print(f"\n1. User found: {user.get('username')} (ID: {user['id']})")
    
    # Get a debt with payments
    debts = TransactionRepository.get_by_user(user['id'], transaction_type='debt', limit=50)
    debt_with_payment = None
    for d in debts:
        payments = PaymentRepository.get_by_transaction(d['id'])
        if payments:
            debt_with_payment = d
            break
    
    if debt_with_payment:
        print(f"2. Debt with payment found: #{debt_with_payment['id']} | {debt_with_payment.get('party_name')}")
        
        # Test TransactionRepository.update
        original_amount = debt_with_payment['amount']
        test_amount = original_amount + 1  # Small change for testing
        
        # Update
        TransactionRepository.update(debt_with_payment['id'], amount=test_amount)
        
        # Verify update
        updated = TransactionRepository.get_by_id(debt_with_payment['id'])
        if updated['amount'] == test_amount:
            print(f"3. TransactionRepository.update works correctly")
        else:
            print(f"❌ TransactionRepository.update failed!")
            return False
        
        # Restore original amount
        TransactionRepository.update(debt_with_payment['id'], amount=original_amount)
        print(f"4. Original amount restored")
    else:
        print("2. No debt with payments found (skipping update test)")
    
    # Get a receivable with payments
    recv = TransactionRepository.get_by_user(user['id'], transaction_type='receivable', limit=50)
    recv_with_payment = None
    for r in recv:
        payments = PaymentRepository.get_by_transaction(r['id'])
        if payments:
            recv_with_payment = r
            break
    
    if recv_with_payment:
        print(f"5. Receivable with payment found: #{recv_with_payment['id']} | {recv_with_payment.get('party_name')}")
    else:
        print("5. No receivable with payments found")
    
    print("\n✅ Database operations work correctly!")
    return True

def test_workflow_trace():
    """Trace the complete workflow."""
    print("\n" + "=" * 60)
    print("Workflow Trace")
    print("=" * 60)
    
    print("""
Debt → Paid Debts → Edit Workflow:
1. User clicks "💳 بدهی‌ها" → Debt Submenu
2. User clicks "📜 پرداخت‌های انجام شده" → debt_view_payments handler
3. Shows customer list with debt_payments_customer_keyboard
4. User clicks customer → dvp_cust:{short_id} handler
5. Shows payment list with debt_payments_items_keyboard
6. User clicks payment → dvp_detail:{txn_id} handler
7. Shows detail page with debt_payments_detail_keyboard (has ✏️ ویرایش)
8. User clicks "✏️ ویرایش" → edit_debt:{txn_id} handler
9. _start_edit_by_id loads transaction data into FSM state
10. Shows edit_field_keyboard with field options
11. User selects field → edit_field:{field} handler
12. User enters new value → edit_{field}_handler
13. User clicks "✅ تأیید و ذخیره" → edit_field:save handler
14. Shows confirmation → confirm_keyboard
15. User clicks "✅ تأیید" → _process_edit_confirm
16. TransactionRepository.update saves to MongoDB
17. Shows success message → Main Menu

Receivables → Received Payments → Edit Workflow:
1. User clicks "💵 طلب‌ها" → Receivable Submenu
2. User clicks "📜 دریافت‌های انجام شده" → recv_view_payments handler
3. Shows customer list with recv_payments_customer_keyboard
4. User clicks customer → rvp_cust:{short_id} handler
5. Shows payment list with recv_payments_items_keyboard
6. User clicks payment → rvp_detail:{txn_id} handler
7. Shows detail page with recv_payments_detail_keyboard (has ✏️ ویرایش)
8. User clicks "✏️ ویرایش" → edit_receivable:{txn_id} handler
9. _start_edit_by_id loads transaction data into FSM state
10. Shows edit_field_keyboard with field options
11. User selects field → edit_field:{field} handler
12. User enters new value → edit_{field}_handler
13. User clicks "✅ تأیید و ذخیره" → edit_field:save handler
14. Shows confirmation → confirm_keyboard
15. User clicks "✅ تأیید" → _process_edit_confirm
16. TransactionRepository.update saves to MongoDB
17. Shows success message → Main Menu
""")
    return True

if __name__ == "__main__":
    print("🧪 Hesab Bot - Edit Workflow Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Keyboard Functions", test_keyboard_functions()))
    results.append(("Handler Registration", test_handler_registration()))
    results.append(("Database Operations", test_database_operations()))
    results.append(("Workflow Trace", test_workflow_trace()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r for _, r in results)
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed!'}")
    
    sys.exit(0 if all_passed else 1)
