#!/usr/bin/env python3
"""Create test data for debt reports testing"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hesab'))

from app.database.models import init_database
from app.database.repository import UserRepository, TransactionRepository, PaymentRepository
from app.utils.jdatetime_helper import get_jalali_date, get_now_jalali
import jdatetime

# Initialize database
init_database()

# Get or create test user (using the admin user from .env)
telegram_id = your_telegram_user_id_here
user = UserRepository.get_or_create(telegram_id=telegram_id, username='testuser')
print(f"Using user: {user['username']} (ID: {user['id']})")

# Get current Jalali date
now_jalali = get_now_jalali()
today_str = now_jalali.strftime('%Y/%m/%d')
print(f"Today (Jalali): {today_str}")

# Calculate some dates for testing
# 30 days ago (should be overdue if debt has 30-day term)
past_date = (now_jalali - jdatetime.timedelta(days=45)).strftime('%Y/%m/%d')
# 10 days ago (should be recent)
recent_date = (now_jalali - jdatetime.timedelta(days=10)).strftime('%Y/%m/%d')
# 5 days in future (should be upcoming)
future_date = (now_jalali + jdatetime.timedelta(days=5)).strftime('%Y/%m/%d')
# 15 days in future (should be upcoming)
future_date2 = (now_jalali + jdatetime.timedelta(days=15)).strftime('%Y/%m/%d')

print(f"Past date (45 days ago): {past_date}")
print(f"Recent date (10 days ago): {recent_date}")
print(f"Future date (5 days): {future_date}")
print(f"Future date2 (15 days): {future_date2}")

# Create test debts
debts_data = [
    {
        'amount': 1000000,
        'party_name': 'مشتری الف',
        'category': '🏢 کسب‌وکار',
        'description': 'بستانکاری jahad keshavarzi',
        'date': past_date,  # 45 days ago - should be overdue if term is 30 days
        'due_date': (now_jalali - jdatetime.timedelta(days=15)).strftime('%Y/%m/%d'),  # 15 days ago - definitely overdue
    },
    {
        'amount': 500000,
        'party_name': 'محمدReza',
        'category': '👤 شخصی',
        'description': 'وام شخصی برای ремонт خانه',
        'date': recent_date,  # 10 days ago
        'due_date': future_date,  # 5 days in future
    },
    {
        'amount': 300000,
        'party_name': 'شرکت XYZ',
        'category': '🏢 کسب‌وکار',
        'description': 'خرید materijal prima',
        'date': recent_date,  # 10 days ago
        'due_date': future_date2,  # 15 days in future
    },
    {
        'amount': 200000,
        'party_name': 'علی_ACCOUNT',
        'category': '👤 شخصی',
        'description': 'homage shakhsi',
        'date': today_str,  # Today
        'due_date': today_str,  # Due today
    }
]

created_debts = []
for i, debt_data in enumerate(debts_data):
    txn = TransactionRepository.create(
        user_id=user['id'],
        transaction_type='debt',
        amount=debt_data['amount'],
        party_name=debt_data['party_name'],
        category=debt_data['category'],
        description=debt_data['description'],
        jalali_date=debt_data['date'],
        jalali_time='10:00:00',
        jalali_full=f"{debt_data['date']} - 10:00:00",
        due_jalali_date=debt_data['due_date']
    )
    # Mark some as settled with payments
    if i == 0:  # First debt - partially paid
        # Create partial payment
        PaymentRepository.create(
            transaction_id=txn['id'],
            user_id=user['id'],
            amount=400000,  # 400k paid of 1M
            payment_type='debt_payment',
            description='قسط اول',
            jalali_date=recent_date,
            jalali_time='11:00:00',
            jalali_full=f"{recent_date} - 11:00:00"
        )
    elif i == 1:  # Second debt - fully paid
        # Create full payment
        PaymentRepository.create(
            transaction_id=txn['id'],
            user_id=user['id'],
            amount=500000,  # Full amount
            payment_type='debt_payment',
            description='پرداخت کامل',
            jalali_date=recent_date,
            jalali_time='11:00:00',
            jalali_full=f"{recent_date} - 11:00:00"
        )
    elif i == 3:  # Fourth debt - partially paid
        PaymentRepository.create(
            transaction_id=txn['id'],
            user_id=user['id'],
            amount=50000,  # 50k paid of 200k
            payment_type='debt_payment',
            description='وادیعه',
            jalali_date=today_str,
            jalali_time='11:00:00',
            jalali_full=f"{today_str} - 11:00:00"
        )
    
    created_debts.append(txn)
    print(f"Created debt {i+1}: {debt_data['party_name']} - {debt_data['amount']:,} تومان")

print(f"\nCreated {len(created_debts)} debts")

# Show summary
print("\n=== Debt Summary ===")
all_debts = TransactionRepository.get_by_user(user['id'], transaction_type='debt', limit=50)
for debt in all_debts:
    remaining = PaymentRepository.get_remaining(debt['id'], debt['amount'])
    status = "SETTLED" if remaining <= 0 else f"OUTSTANDING: {remaining:,}"
    print(f"- {debt['party_name']}: {debt['amount']:,} تومان | {status} | Due: {debt.get('due_jalali_date', 'N/A')}")

print("\nTest data creation completed!")