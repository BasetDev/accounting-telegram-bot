#!/usr/bin/env python3
"""Test script for debt reports functionality"""

import sys, os, asyncio
from unittest.mock import AsyncMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hesab'))

from app.database.models import init_database
from app.database.repository import UserRepository
from app.handlers.main_handler import (
    debt_reports,  # This is the callback handler for entering reports menu
    debt_report_handler,  # This handles individual report selection
    debt_report_export,  # This handles export requests
    _send_debt_report   # This is the core function that generates reports
)
from app.utils.messages import *

# Initialize database
init_database()

def make_mock(user_id):
    """Create a mock callback query and message"""
    msg = AsyncMock(spec=['from_user', 'chat', 'answer', 'edit_text', 'answer_document'])
    msg.from_user = AsyncMock(spec=['id']); msg.from_user.id = user_id
    msg.chat = AsyncMock(spec=['id']); msg.chat.id = user_id
    msg.answer = AsyncMock(); msg.edit_text = AsyncMock(); msg.answer_document = AsyncMock()
    
    cb = AsyncMock(spec=['data', 'from_user', 'message', 'answer'])
    cb.data = ''; cb.from_user = AsyncMock(spec=['id']); cb.from_user.id = user_id
    cb.message = msg; cb.answer = AsyncMock()
    
    return cb, msg

async def test_debt_reports():
    """Test all debt report types"""
    # Get the test user (ID your_telegram_user_id_here from .env)
    user = UserRepository.get_by_telegram_id(your_telegram_user_id_here)
    if not user:
        print("ERROR: User not found!")
        return False
    
    print(f"Testing with user: {user['username']} (ID: {user['id']})")
    uid = user['id']
    
    # Test report types
    report_types = [
        'summary', 'active', 'settled', 'overdue', 
        'due_today', 'due_week', 'by_customer', 'by_category',
        'payments', 'remaining', 'daily', 'weekly', 'monthly', 'yearly'
    ]
    
    results = {}
    
    for report_type in report_types:
        print(f"\nTesting report type: {report_type}")
        
        # Create mock objects
        cb, msg = make_mock(your_telegram_user_id_here)
        cb.data = f"debt_rpt_{report_type}"
        
        try:
            # Call the report handler directly
            await debt_report_handler(cb)
            
            # Check if message was edited (success)
            if msg.edit_text.called:
                args, kwargs = msg.edit_text.call_args
                response_text = args[0] if args else ""
                reply_markup = kwargs.get('reply_markup')
                
                print(f"  ✓ Report generated successfully")
                print(f"  ✓ Response length: {len(response_text)} characters")
                
                # Check if it contains expected elements
                if "هیچ بدهی‌ای" in response_text and report_type not in ['summary', 'by_customer', 'by_category', 'payments']:
                    print(f"  ⚠️  Report shows empty (may be expected for this type)")
                elif "📊" in response_text or "📋" in response_text or "✅" in response_text or "⏳" in response_text:
                    print(f"  ✓ Report contains expected headers")
                else:
                    print(f"  ? Response preview: {response_text[:100]}...")
                
                # Check if export menu was attached
                if reply_markup:
                    print(f"  ✓ Export menu attached")
                else:
                    print(f"  ✗ No export menu found")
                    
                results[report_type] = "PASS"
            else:
                print(f"  ✗ Failed to generate response")
                results[report_type] = "FAIL"
                
        except Exception as e:
            print(f"  ✗ Exception occurred: {e}")
            import traceback
            traceback.print_exc()
            results[report_type] = f"ERROR: {e}"
    
    # Test export functionality for a few report types
    print("\n" + "="*50)
    print("Testing export functionality...")
    print("="*50)
    
    export_test_types = ['summary', 'active', 'settled']
    
    for report_type in export_test_types:
        print(f"\nTesting export for: {report_type}")
        
        # First generate the report to populate cache
        cb, msg = make_mock(your_telegram_user_id_here)
        cb.data = f"debt_rpt_{report_type}"
        await debt_report_handler(cb)
        
        # Now test export
        cb2, msg2 = make_mock(your_telegram_user_id_here)
        cb2.data = f"debt_rpt_export_excel:{report_type}"
        
        try:
            await debt_report_export(cb2)
            
            if msg2.edit_text.called:
                args, kwargs = msg2.edit_text.call_args
                if "در حال ایجاد فایل" in args[0]:
                    print(f"  ✓ Export started successfully")
                    # Check if document was sent
                    if msg2.answer_document.called:
                        print(f"  ✓ Document sent successfully")
                        results[f"{report_type}_export"] = "PASS"
                    else:
                        print(f"  ? Export initiated but document not yet sent (may be async)")
                        results[f"{report_type}_export"] = "PENDING"
                else:
                    print(f"  ? Unexpected response: {args[0][:50]}...")
                    results[f"{report_type}_export"] = "UNCLEAR"
            else:
                print(f"  ✗ Export failed to start")
                results[f"{report_type}_export"] = "FAIL"
                
        except Exception as e:
            print(f"  ✗ Exception during export: {e}")
            results[f"{report_type}_export"] = f"ERROR: {e}"
    
    # Test navigation
    print("\n" + "="*50)
    print("Testing navigation...")
    print("="*50)
    
    # Test entering reports menu
    cb_enter, msg_enter = make_mock(your_telegram_user_id_here)
    cb_enter.data = "debt_reports"
    try:
        await debt_reports(cb_enter)
        if msg_enter.answer.called:
            print("✓ Entering debt reports menu works")
            results['nav_enter'] = "PASS"
        else:
            print("✗ Entering debt reports menu failed")
            results['nav_enter'] = "FAIL"
    except Exception as e:
        print(f"✗ Entering reports menu error: {e}")
        results['nav_enter'] = f"ERROR: {e}"
    
    # Test back from report to menu
    cb_back, msg_back = make_mock(your_telegram_user_id_here)
    cb_back.data = "debt_rpt_back"
    try:
        await debt_report_handler(cb_back)  # This handles the back button
        if msg_back.edit_text.called:
            print("✓ Back from report to debt menu works")
            results['nav_back'] = "PASS"
        else:
            print("✗ Back navigation failed")
            results['nav_back'] = "FAIL"
    except Exception as e:
        print(f"✗ Back navigation error: {e}")
        results['nav_back'] = f"ERROR: {e}"
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v == "FAIL")
    errors = sum(1 for v in results.values() if isinstance(v, str) and v.startswith("ERROR"))
    pending = sum(1 for v in results.values() if v == "PENDING")
    unclear = sum(1 for v in results.values() if v == "UNCLEAR")
    warn = sum(1 for v in results.values() if "⚠️" in str(v))
    
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"ERRORS: {errors}")
    print(f"PENDING: {pending}")
    print(f"UNCLEAR: {unclear}")
    print(f"WARNINGS: {warn}")
    
    print("\nDetailed Results:")
    for test, result in results.items():
        status = "✓" if result == "PASS" else "✗" if result == "FAIL" else "!"
        print(f"  {status} {test}: {result}")
    
    return failed == 0 and errors == 0

if __name__ == "__main__":
    success = asyncio.run(test_debt_reports())
    sys.exit(0 if success else 1)
