#!/usr/bin/env python3
"""Comprehensive bot testing script - tests all modules systematically."""

import sys
import asyncio
sys.path.insert(0, 'hesab')

from unittest.mock import AsyncMock, MagicMock
from app.database.models import init_database
from app.database.repository import (
    UserRepository, TransactionRepository, PaymentRepository,
    CustomerRepository, CardInfoRepository
)
from app.utils.messages import *
from app.utils.jdatetime_helper import get_jalali_date, get_now_jalali
from app.keyboards.markups import *

init_database()

# Test user
TEST_USER_ID = your_telegram_user_id_here

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def record(self, test_name, passed, error=None):
        if passed:
            self.passed += 1
            print(f"  ✅ {test_name}")
        else:
            self.failed += 1
            self.errors.append((test_name, error))
            print(f"  ❌ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*70)
        print(f"TEST SUMMARY: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print("\nFailed tests:")
            for name, err in self.errors:
                print(f"  - {name}: {err}")
        print("="*70)
        return self.failed == 0

results = TestResults()

def make_callback(user_id=TEST_USER_ID, data=""):
    """Create a mock callback query."""
    cb = AsyncMock()
    cb.from_user = AsyncMock()
    cb.from_user.id = user_id
    cb.message = AsyncMock()
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()
    cb.message.answer_document = AsyncMock()
    cb.answer = AsyncMock()
    cb.data = data
    return cb

async def test_main_menu():
    """Test main menu keyboard."""
    print("\n📋 Testing Main Menu...")
    
    menu = main_menu()
    results.record("Main menu created", menu is not None)
    results.record("Main menu has buttons", len(menu.inline_keyboard) > 0 if hasattr(menu, 'inline_keyboard') else len(menu.keyboard) > 0)

async def test_dashboard():
    """Test dashboard functionality."""
    print("\n📊 Testing Dashboard...")
    
    user = UserRepository.get_by_telegram_id(TEST_USER_ID)
    results.record("User exists", user is not None)
    
    if user:
        txns = TransactionRepository.get_by_user(user['id'], limit=1000)
        results.record("Can fetch transactions", txns is not None)

async def test_debt_module():
    """Test debt module."""
    print("\n💳 Testing Debt Module...")
    
    # Test debt submenu
    submenu = debt_submenu()
    results.record("Debt submenu created", submenu is not None)
    
    # Test debt reports submenu
    reports_menu = debt_reports_submenu()
    results.record("Debt reports submenu created", reports_menu is not None)
    
    # Test debt report export menu
    export_menu = debt_report_export_menu("summary")
    results.record("Debt export menu created", export_menu is not None)

async def test_receivable_module():
    """Test receivable module."""
    print("\n💵 Testing Receivable Module...")
    
    # Test receivable submenu
    submenu = receivable_submenu()
    results.record("Receivable submenu created", submenu is not None)
    
    # Test receivable reports submenu
    reports_menu = receivable_reports_submenu()
    results.record("Receivable reports submenu created", reports_menu is not None)
    
    # Test receivable report export menu
    export_menu = recv_report_export_menu("summary")
    results.record("Receivable export menu created", export_menu is not None)

async def test_customer_module():
    """Test customer module."""
    print("\n👥 Testing Customer Module...")
    
    customers = CustomerRepository.get_by_user(16)
    results.record("Can fetch customers", customers is not None)

async def test_card_module():
    """Test card module."""
    print("\n💳 Testing Card Module...")
    
    submenu = card_submenu()
    results.record("Card submenu created", submenu is not None)

async def test_export_service():
    """Test export service."""
    print("\n📤 Testing Export Service...")
    
    from app.services.export_service import export_transactions_excel, export_transactions_pdf
    
    # Test data
    test_txns = [{
        'transaction_type': 'debt',
        'amount': 100000,
        'category': 'تست',
        'description': 'Test',
        'jalali_date': '1405/05/01',
        'jalali_time': '10:00:00',
        'party_name': 'Test User',
        'is_settled': False
    }]
    
    try:
        excel_path = await export_transactions_excel(test_txns, "test_export.xlsx")
        results.record("Excel export works", excel_path is not None)
    except Exception as e:
        results.record("Excel export works", False, str(e))
    
    try:
        pdf_path = await export_transactions_pdf(test_txns, "test_export.pdf")
        results.record("PDF export works", pdf_path is not None)
    except Exception as e:
        results.record("PDF export works", False, str(e))

async def test_report_generation():
    """Test report generation for both debt and receivable."""
    print("\n📊 Testing Report Generation...")
    
    from app.handlers.main_handler import _send_debt_report, _send_recv_report
    
    report_types = ['summary', 'active', 'settled', 'overdue', 'due_today',
                    'due_week', 'by_customer', 'by_category', 'payments',
                    'remaining', 'daily', 'weekly', 'monthly', 'yearly']
    
    # Test debt reports
    print("  Debt Reports:")
    for rt in report_types:
        cb = make_callback()
        try:
            await _send_debt_report(cb, rt)
            passed = cb.message.edit_text.called
            results.record(f"Debt {rt}", passed)
        except Exception as e:
            results.record(f"Debt {rt}", False, str(e))
    
    # Test receivable reports
    print("  Receivable Reports:")
    for rt in report_types:
        cb = make_callback()
        try:
            await _send_recv_report(cb, rt)
            passed = cb.message.edit_text.called
            results.record(f"Receivable {rt}", passed)
        except Exception as e:
            results.record(f"Receivable {rt}", False, str(e))

async def test_navigation():
    """Test navigation callbacks."""
    print("\n🧭 Testing Navigation...")
    
    from app.handlers.main_handler import (
        debt_reports, debt_rpt_back, debt_rpt_menu,
        receivable_reports, recv_rpt_back, recv_rpt_menu
    )
    
    # Test debt navigation
    cb = make_callback()
    await debt_reports(cb)
    results.record("Enter debt reports menu", cb.message.answer.called)
    
    cb = make_callback()
    await debt_rpt_back(cb)
    results.record("Back from debt reports", cb.message.edit_text.called)
    
    cb = make_callback()
    await debt_rpt_menu(cb)
    results.record("Debt reports menu", cb.message.edit_text.called)
    
    # Test receivable navigation
    cb = make_callback()
    await receivable_reports(cb)
    results.record("Enter receivable reports menu", cb.message.answer.called)
    
    cb = make_callback()
    await recv_rpt_back(cb)
    results.record("Back from receivable reports", cb.message.edit_text.called)
    
    cb = make_callback()
    await recv_rpt_menu(cb)
    results.record("Receivable reports menu", cb.message.edit_text.called)

async def test_database_operations():
    """Test database operations."""
    print("\n🗄️ Testing Database Operations...")
    
    user = UserRepository.get_by_telegram_id(TEST_USER_ID)
    if user:
        # Test transaction queries
        debts = TransactionRepository.get_by_user(user['id'], transaction_type='debt', limit=10)
        results.record("Fetch debts", debts is not None)
        
        receivables = TransactionRepository.get_by_user(user['id'], transaction_type='receivable', limit=10)
        results.record("Fetch receivables", receivables is not None)
        
        # Test payment queries
        payments = PaymentRepository.get_by_user_and_type(user['id'], 'debt_payment', limit=10)
        results.record("Fetch debt payments", payments is not None)
        
        payments = PaymentRepository.get_by_user_and_type(user['id'], 'receivable_payment', limit=10)
        results.record("Fetch receivable payments", payments is not None)

async def run_all_tests():
    """Run all tests."""
    print("="*70)
    print("COMPREHENSIVE BOT TESTING")
    print("="*70)
    
    await test_main_menu()
    await test_dashboard()
    await test_debt_module()
    await test_receivable_module()
    await test_customer_module()
    await test_card_module()
    await test_database_operations()
    await test_report_generation()
    await test_export_service()
    await test_navigation()
    
    return results.summary()

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
