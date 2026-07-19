#!/usr/bin/env python3
"""Test script for Hesab Telegram Bot - Debt and Receivable modules."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hesab'))

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, User, Chat

from app.handlers.main_handler import (
    router, DebtForm, ReceivableForm, PaymentForm,
    DebtEditForm, ReceivableEditForm,
    debt_menu, debt_register_from_submenu, debt_category_selected,
    debt_subcategory_selected, debt_amount, debt_party,
    debt_description, debt_due_date, debt_photo,
    debt_card_select, debt_sheba_select, debt_bank_name_select,
    debt_confirm, receivable_menu, receivable_register_from_submenu,
    receivable_confirm, edit_field_selected, edit_amount_handler,
    debt_delete_callback, debt_delete_confirm
)
from app.database.models import init_database, get_database
from app.database.repository import (
    UserRepository, TransactionRepository, CustomerRepository,
    PaymentRepository, CardInfoRepository
)
from app.keyboards.markups import main_menu, debt_submenu
from app.utils.messages import *

# Test results tracking
results = {"passed": 0, "failed": 0, "errors": []}

def report(test_name, passed, detail=""):
    if passed:
        results["passed"] += 1
        print(f"  ✅ {test_name}")
    else:
        results["failed"] += 1
        results["errors"].append(f"{test_name}: {detail}")
        print(f"  ❌ {test_name}: {detail}")


async def create_mock_message(text=None, user_id=your_telegram_user_id_here, content_type="text"):
    """Create a mock Message object."""
    msg = AsyncMock(spec=Message)
    msg.text = text
    msg.from_user = AsyncMock(spec=User)
    msg.from_user.id = user_id
    msg.from_user.username = "testuser"
    msg.from_user.first_name = "Test"
    msg.from_user.last_name = "User"
    msg.chat = AsyncMock(spec=Chat)
    msg.chat.id = user_id
    msg.chat.type = "private"
    msg.content_type = content_type
    msg.photo = None
    msg.answer = AsyncMock()
    msg.edit_text = AsyncMock()
    msg.delete = AsyncMock()
    msg.bot = AsyncMock(spec=Bot)
    return msg


async def create_mock_callback(data, user_id=your_telegram_user_id_here, message=None):
    """Create a mock CallbackQuery object."""
    cb = AsyncMock(spec=CallbackQuery)
    cb.data = data
    cb.from_user = AsyncMock(spec=User)
    cb.from_user.id = user_id
    cb.from_user.username = "testuser"
    cb.from_user.first_name = "Test"
    cb.from_user.last_name = "User"
    cb.message = message or await create_mock_message()
    cb.answer = AsyncMock()
    return cb


async def create_fsm_context():
    """Create a mock FSMContext."""
    storage = MemoryStorage()
    ctx = AsyncMock(spec=FSMContext)
    ctx._data = {}
    
    async def mock_get_data():
        return dict(ctx._data)
    
    async def mock_update_data(**kwargs):
        ctx._data.update(kwargs)
    
    async def mock_set_state(state):
        ctx._state = state.state if hasattr(state, 'state') else str(state)
    
    async def mock_clear():
        ctx._data = {}
        ctx._state = None
    
    ctx.get_data = mock_get_data
    ctx.update_data = mock_update_data
    ctx.set_state = mock_set_state
    ctx.clear = mock_clear
    ctx._state = None
    return ctx


async def test_debt_registration_flow():
    """Test the complete debt registration flow."""
    print("\n📋 Testing Debt Registration Flow...")
    
    # Clean up test data
    from app.database.models import get_collection
    get_collection("transactions").delete_many({"user_id": {"$exists": True}})
    get_collection("users").delete_many({"telegram_id": your_telegram_user_id_here})
    
    # Test 1: Debt submenu display
    try:
        msg = await create_mock_message("💳 بدهی‌ها")
        await debt_menu(msg)
        report("Debt menu shows submenu", msg.answer.called)
    except Exception as e:
        report("Debt menu shows submenu", False, str(e))
    
    # Test 2: Register new debt - category selection
    try:
        ctx = await create_fsm_context()
        cb = await create_mock_callback("debt_register")
        await debt_register_from_submenu(cb, ctx)
        report("Debt register shows category", cb.message.answer.called)
        report("FSM state set to category", ctx._state == "DebtForm:category")
    except Exception as e:
        report("Debt register category", False, str(e))
    
    # Test 3: Category selection
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.category)
        cb = await create_mock_callback("debt_cat:🏢 کسب‌وکار")
        await debt_category_selected(cb, ctx)
        data = await ctx.get_data()
        report("Category stored correctly", data.get("category") == "🏢 کسب‌وکار")
        report("FSM state set to subcategory", ctx._state == "DebtForm:subcategory")
    except Exception as e:
        report("Category selection", False, str(e))
    
    # Test 4: Subcategory selection
    try:
        ctx = await create_fsm_context()
        await ctx.update_data(category="🏢 کسب‌وکار")
        await ctx.set_state(DebtForm.subcategory)
        cb = await create_mock_callback("debt_sub:تأمین‌کنندگان")
        await debt_subcategory_selected(cb, ctx)
        data = await ctx.get_data()
        report("Subcategory stored correctly", data.get("subcategory") == "تأمین‌کنندگان")
        report("FSM state set to amount", ctx._state == "DebtForm:amount")
    except Exception as e:
        report("Subcategory selection", False, str(e))
    
    # Test 5: Amount input (valid)
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.amount)
        msg = await create_mock_message("1000000")
        await debt_amount(msg, ctx)
        data = await ctx.get_data()
        report("Amount stored correctly", data.get("amount") == 1000000.0)
        report("FSM state set to party", ctx._state == "DebtForm:party")
    except Exception as e:
        report("Amount input", False, str(e))
    
    # Test 6: Amount input (invalid - should stay in same state)
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.amount)
        msg = await create_mock_message("abc")
        await debt_amount(msg, ctx)
        report("Invalid amount shows error", msg.answer.called)
        report("Invalid amount stays in amount state", ctx._state == "DebtForm:amount")
    except Exception as e:
        report("Invalid amount handling", False, str(e))
    
    # Test 7: Party input
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.party)
        msg = await create_mock_message("شرکت تست")
        await debt_party(msg, ctx)
        data = await ctx.get_data()
        report("Party stored correctly", data.get("party") == "شرکت تست")
        report("FSM state set to description", ctx._state == "DebtForm:description")
    except Exception as e:
        report("Party input", False, str(e))
    
    # Test 8: Description input
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.description)
        msg = await create_mock_message("تست بدهی")
        await debt_description(msg, ctx)
        data = await ctx.get_data()
        report("Description stored correctly", data.get("description") == "تست بدهی")
        report("FSM state set to due_date", ctx._state == "DebtForm:due_date")
    except Exception as e:
        report("Description input", False, str(e))
    
    # Test 9: Due date - today
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.due_date)
        msg = await create_mock_message("📅 امروز")
        await debt_due_date(msg, ctx)
        data = await ctx.get_data()
        report("Due date (today) stored", data.get("due_date") is not None)
        report("Due time (today) stored", data.get("due_time") is not None)
    except Exception as e:
        report("Due date today", False, str(e))
    
    # Test 10: Due date - manual valid
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.due_date)
        msg = await create_mock_message("1405/04/15")
        await debt_due_date(msg, ctx)
        data = await ctx.get_data()
        report("Manual date stored", data.get("due_date") == "1405/04/15")
    except Exception as e:
        report("Manual date", False, str(e))
    
    # Test 11: Due date - invalid date (month 13)
    try:
        ctx = await create_fsm_context()
        await ctx.set_state(DebtForm.due_date)
        msg = await create_mock_message("1405/13/01")
        await debt_due_date(msg, ctx)
        report("Invalid date shows error", msg.answer.called)
    except Exception as e:
        report("Invalid date handling", False, str(e))
    
    # Test 12: Full debt creation end-to-end
    try:
        # Create user first
        user = UserRepository.get_or_create(
            telegram_id=your_telegram_user_id_here,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        # Create a debt transaction
        txn = TransactionRepository.create(
            user_id=user["id"],
            transaction_type="debt",
            amount=500000,
            party_name="شرکت تست",
            description="بدهی تست",
            category="🏢 کسب‌وکار",
            subcategory="تأمین‌کنندگان",
            due_jalali_date="1405/05/01",
            jalali_date="1405/04/28",
            jalali_time="12:00:00",
            jalali_full="1405/04/28 - 12:00:00"
        )
        
        report("Debt created in DB", txn is not None)
        report("Debt has correct amount", txn["amount"] == 500000)
        report("Debt has correct party", txn["party_name"] == "شرکت تست")
        report("Debt is not settled", txn["is_settled"] == False)
        
        # Verify retrieval
        retrieved = TransactionRepository.get_by_id(txn["id"])
        report("Debt retrievable by ID", retrieved is not None)
        report("Retrieved debt matches", retrieved["amount"] == 500000)
        
        # Verify active debts
        active = TransactionRepository.get_active(user["id"], "debt")
        report("Debt appears in active list", len(active) > 0)
        
    except Exception as e:
        report("Full debt creation", False, str(e))


async def test_debt_edit_flow():
    """Test the debt edit flow."""
    print("\n✏️ Testing Debt Edit Flow...")
    
    # Get existing debt
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    if not user:
        report("Edit flow setup", False, "No user found")
        return
    
    txns = TransactionRepository.get_active(user["id"], "debt")
    if not txns:
        report("Edit flow setup", False, "No active debts found")
        return
    
    txn_id = txns[0]["id"]
    
    # Test: Edit amount handler with "-" (no change)
    try:
        ctx = await create_fsm_context()
        await ctx.update_data(edit_id=txn_id, amount=500000, edit_type="debt")
        await ctx.set_state(DebtEditForm.amount)
        msg = await create_mock_message("-")
        await edit_amount_handler(msg, ctx)
        data = await ctx.get_data()
        report("Edit amount '-' keeps original", data.get("amount") == 500000)
    except Exception as e:
        report("Edit amount no change", False, str(e))
    
    # Test: Edit amount with new value
    try:
        ctx = await create_fsm_context()
        await ctx.update_data(edit_id=txn_id, amount=500000, edit_type="debt")
        await ctx.set_state(DebtEditForm.amount)
        msg = await create_mock_message("750000")
        await edit_amount_handler(msg, ctx)
        data = await ctx.get_data()
        report("Edit amount updates value", data.get("amount") == 750000.0)
    except Exception as e:
        report("Edit amount update", False, str(e))


async def test_debt_payment_flow():
    """Test the debt payment flow."""
    print("\n💳 Testing Debt Payment Flow...")
    
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    if not user:
        report("Payment flow setup", False, "No user found")
        return
    
    txns = TransactionRepository.get_active(user["id"], "debt")
    if not txns:
        report("Payment flow setup", False, "No active debts found")
        return
    
    txn = txns[0]
    
    # Test: Partial payment
    try:
        PaymentRepository.create(
            transaction_id=txn["id"],
            user_id=user["id"],
            amount=200000,
            payment_type="debt_payment",
            jalali_date="1405/04/28",
            jalali_time="14:00:00",
            jalali_full="1405/04/28 - 14:00:00"
        )
        
        remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        report("Partial payment recorded", remaining == txn["amount"] - 200000)
        report("Remaining amount correct", remaining == 300000.0)
        
        # Payment history
        payments = PaymentRepository.get_by_transaction(txn["id"])
        report("Payment appears in history", len(payments) > 0)
        
    except Exception as e:
        report("Partial payment", False, str(e))
    
    # Test: Full settlement
    try:
        remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        PaymentRepository.create(
            transaction_id=txn["id"],
            user_id=user["id"],
            amount=remaining,
            payment_type="debt_payment",
            jalali_date="1405/04/28",
            jalali_time="15:00:00",
            jalali_full="1405/04/28 - 15:00:00"
        )
        
        # Mark as settled
        TransactionRepository.settle_transaction(txn["id"])
        
        txn_check = TransactionRepository.get_by_id(txn["id"])
        report("Debt marked as settled", txn_check["is_settled"] == True)
        
        final_remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        report("Remaining is zero after full payment", final_remaining == 0.0)
        
    except Exception as e:
        report("Full settlement", False, str(e))


async def test_debt_delete_flow():
    """Test the debt delete flow."""
    print("\n🗑 Testing Debt Delete Flow...")
    
    # Create a debt to delete
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    txn = TransactionRepository.create(
        user_id=user["id"],
        transaction_type="debt",
        amount=100000,
        party_name="حذف تست",
        jalali_date="1405/04/28",
        jalali_time="16:00:00",
        jalali_full="1405/04/28 - 16:00:00"
    )
    
    txn_id = txn["id"]
    
    # Verify it exists
    report("Debt to delete exists", TransactionRepository.get_by_id(txn_id) is not None)
    
    # Delete it
    result = TransactionRepository.delete(txn_id)
    report("Delete returns True", result == True)
    
    # Verify it's gone
    report("Deleted debt no longer exists", TransactionRepository.get_by_id(txn_id) is None)


async def test_receivable_registration_flow():
    """Test the complete receivable registration flow."""
    print("\n📌 Testing Receivable Registration Flow...")
    
    # Create user
    user = UserRepository.get_or_create(
        telegram_id=your_telegram_user_id_here,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    # Test: Create receivable
    try:
        txn = TransactionRepository.create(
            user_id=user["id"],
            transaction_type="receivable",
            amount=800000,
            party_name="مشتری تست",
            description="طلب تست",
            category="🏢 کسب‌وکار",
            subcategory="مشتریان",
            due_jalali_date="1405/05/15",
            jalali_date="1405/04/28",
            jalali_time="12:00:00",
            jalali_full="1405/04/28 - 12:00:00"
        )
        
        report("Receivable created in DB", txn is not None)
        report("Receivable has correct amount", txn["amount"] == 800000)
        report("Receivable has correct party", txn["party_name"] == "مشتری تست")
        report("Receivable is not settled", txn["is_settled"] == False)
        
        # Verify retrieval
        active = TransactionRepository.get_active(user["id"], "receivable")
        report("Receivable appears in active list", len(active) > 0)
        
    except Exception as e:
        report("Receivable creation", False, str(e))


async def test_receivable_payment_flow():
    """Test the receivable payment flow."""
    print("\n💵 Testing Receivable Payment Flow...")
    
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    txns = TransactionRepository.get_active(user["id"], "receivable")
    if not txns:
        report("Receivable payment setup", False, "No active receivables")
        return
    
    txn = txns[0]
    
    # Test: Partial collection
    try:
        PaymentRepository.create(
            transaction_id=txn["id"],
            user_id=user["id"],
            amount=300000,
            payment_type="receivable_payment",
            jalali_date="1405/04/28",
            jalali_time="14:00:00",
            jalali_full="1405/04/28 - 14:00:00"
        )
        
        remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        report("Partial collection recorded", remaining == txn["amount"] - 300000)
        
    except Exception as e:
        report("Partial collection", False, str(e))
    
    # Test: Full collection
    try:
        remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        PaymentRepository.create(
            transaction_id=txn["id"],
            user_id=user["id"],
            amount=remaining,
            payment_type="receivable_payment",
            jalali_date="1405/04/28",
            jalali_time="15:00:00",
            jalali_full="1405/04/28 - 15:00:00"
        )
        
        TransactionRepository.settle_transaction(txn["id"])
        
        txn_check = TransactionRepository.get_by_id(txn["id"])
        report("Receivable marked as settled", txn_check["is_settled"] == True)
        
    except Exception as e:
        report("Full collection", False, str(e))


async def test_customer_operations():
    """Test customer CRUD operations."""
    print("\n👥 Testing Customer Operations...")
    
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    
    # Create customer
    try:
        customer = CustomerRepository.create(
            user_id=user["id"],
            full_name="مشتری تست CRUD",
            phone="09121234567",
            address="تهران",
            notes="توضیحات تست"
        )
        report("Customer created", customer is not None)
        report("Customer has correct name", customer["full_name"] == "مشتری تست CRUD")
        
        # Read
        retrieved = CustomerRepository.get_by_id(customer["id"])
        report("Customer retrievable", retrieved is not None)
        
        # Update
        updated = CustomerRepository.update(customer["id"], full_name="مشتری ویرایش شده")
        report("Customer updated", updated == True)
        
        # Verify update
        retrieved2 = CustomerRepository.get_by_id(customer["id"])
        report("Updated name correct", retrieved2["full_name"] == "مشتری ویرایش شده")
        
        # Search
        results = CustomerRepository.search(user["id"], "ویرایش")
        report("Customer searchable", len(results) > 0)
        
        # Delete
        deleted = CustomerRepository.delete(customer["id"])
        report("Customer deleted", deleted == True)
        
        # Verify deletion
        retrieved3 = CustomerRepository.get_by_id(customer["id"])
        report("Deleted customer gone", retrieved3 is None)
        
    except Exception as e:
        report("Customer CRUD", False, str(e))


async def test_card_operations():
    """Test card info CRUD operations."""
    print("\n💳 Testing Card Operations...")
    
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    
    # Create card
    try:
        card = CardInfoRepository.create(
            user_id=user["id"],
            name="کارت تست",
            card_number="1234567890123456",
            sheba="123456789012345678901234",
            bank_name="ملت"
        )
        report("Card created", card is not None)
        report("Card has correct number", card["card_number"] == "1234567890123456")
        
        # Read
        retrieved = CardInfoRepository.get_by_id(card["id"])
        report("Card retrievable", retrieved is not None)
        
        # Update
        updated = CardInfoRepository.update(card["id"], bank_name="ملی")
        report("Card updated", updated == True)
        
        # Search
        results = CardInfoRepository.search(user["id"], "تست")
        report("Card searchable", len(results) > 0)
        
        # Delete
        deleted = CardInfoRepository.delete(card["id"])
        report("Card deleted", deleted == True)
        
    except Exception as e:
        report("Card CRUD", False, str(e))


async def test_database_indexes():
    """Test that database indexes are created correctly."""
    print("\n🗄 Testing Database Indexes...")
    
    from app.database.models import get_collection
    
    # Check users collection indexes
    users_indexes = get_collection("users").index_information()
    report("Users has telegram_id index", "telegram_id_1" in users_indexes)
    
    # Check transactions collection indexes
    txn_indexes = get_collection("transactions").index_information()
    report("Transactions has user_id index", "user_id_1" in txn_indexes)
    report("Transactions has type index", "transaction_type_1" in txn_indexes)
    
    # Check payments collection indexes
    pay_indexes = get_collection("payments").index_information()
    report("Payments has transaction_id index", "transaction_id_1" in pay_indexes)


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Hesab Bot - Comprehensive Test Suite")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    # Run tests
    await test_database_indexes()
    await test_debt_registration_flow()
    await test_debt_edit_flow()
    await test_debt_payment_flow()
    await test_debt_delete_flow()
    await test_receivable_registration_flow()
    await test_receivable_payment_flow()
    await test_customer_operations()
    await test_card_operations()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)
    
    if results["errors"]:
        print("\n❌ Failed Tests:")
        for err in results["errors"]:
            print(f"  - {err}")
    
    print()
    return results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
