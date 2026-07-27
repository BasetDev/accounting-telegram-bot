import sys
sys.path.insert(0, 'hesab')

from app.database.models import init_database, get_database
from app.database.repository import (
    UserRepository, TransactionRepository, CustomerRepository, 
    PaymentRepository, CardInfoRepository
)
from app.services.backup_service import (
    create_full_backup, restore_from_backup
)
from app.utils.jdatetime_helper import get_jalali_date, get_jalali_time

init_database()
db = get_database()

print('=' * 70)
print('FINAL VERIFICATION: Testing the exact scenario from the bug report')
print('=' * 70)

# Clean up test users from previous runs
for tid in [555555, 666666]:
    user = UserRepository.get_by_telegram_id(tid)
    if user:
        db.users.delete_one({'telegram_id': tid})
        db.transactions.delete_many({'user_id': user['id']})
        db.payments.delete_many({'user_id': user['id']})
        db.customers.delete_many({'user_id': user['id']})

from app.database.models import create_user_doc, create_transaction_doc, create_payment_doc, create_customer_doc

# Simulate the EXACT bug report scenario:
# 1. User A (telegram_id=555555) creates some data
# 2. User B (telegram_id=666666) restores a backup from User A
# 3. User B should see User A's data as their own

print('Step 1: Creating data for User A (telegram_id=555555)')
user_a_doc = create_user_doc(telegram_id=555555, username='user_a', first_name='User A')
user_a_doc.pop('_id', None)
db.users.insert_one(user_a_doc)
user_a_id = user_a_doc['id']
print(f'   User A: id={user_a_id}, telegram_id=555555')

# Create data for User A
cust_a = create_customer_doc(user_a_id, 'مشتری الف', '09120000001', 'تهران', 'مشتری اول')
cust_a.pop('_id', None)
db.customers.insert_one(cust_a)
print(f'   Customer A: id={cust_a["id"]}')

# Create 2 debts for User A
for i in range(2):
    t = create_transaction_doc(user_a_id, 'debt', 100000*(i+1), f'بدهی الف {i+1}',
        '🏢 کسب\u200cوکار', 'تأمین\u200cکنندگان', f'فروشگاه {i+1}', None,
        get_jalali_date(), get_jalali_time(), f'{get_jalali_date()} - {get_jalali_time()}', get_jalali_date())
    t.pop('_id', None)
    db.transactions.insert_one(t)
print(f'   Created 2 debts for User A')

# Create 1 receivable for User A
r = create_transaction_doc(user_a_id, 'receivable', 200000, 'طلب الف',
    '🏢 کسب\u200cوکار', 'مشتریان', 'مشتری دو', None,
    get_jalali_date(), get_jalali_time(), f'{get_jalali_date()} - {get_jalali_time()}', get_jalali_date())
r.pop('_id', None)
db.transactions.insert_one(r)
print(f'   Created 1 receivable for User A')

# Verify User A can see their data
print(f'\nStep 2: Verifying User A can see their data BEFORE restore:')
debts_a = len(TransactionRepository.get_by_user(user_a_id, 'debt', limit=100))
recvs_a = len(TransactionRepository.get_by_user(user_a_id, 'receivable', limit=100))
custs_a = len(CustomerRepository.get_by_user(user_a_id))
print(f'   User A sees: Debts={debts_a}, Receivables={recvs_a}, Customers={custs_a}')

# Step 3: Create backup of User A's data
print(f'\nStep 3: Creating backup of User A\'s data')
backup_result = create_full_backup()
backup_path = backup_result['filepath']
print(f'   Backup: {backup_result["filename"]} ({backup_result["file_size"]} bytes)')

# Step 4: Create User B (the restorer) - they exist but have no data
print(f'\nStep 4: Creating User B (telegram_id=666666) with no data')
user_b_doc = create_user_doc(telegram_id=666666, username='user_b', first_name='User B')
user_b_doc.pop('_id', None)
db.users.insert_one(user_b_doc)
user_b_id = user_b_doc['id']
print(f'   User B: id={user_b_id}, telegram_id=666666')

# Verify User B sees nothing initially
print(f'\nStep 5: Verifying User B sees NO data BEFORE restore:')
debts_b = len(TransactionRepository.get_by_user(user_b_id, 'debt', limit=100))
recvs_b = len(TransactionRepository.get_by_user(user_b_id, 'receivable', limit=100))
custs_b = len(CustomerRepository.get_by_user(user_b_id))
print(f'   User B sees: Debts={debts_b}, Receivables={recvs_b}, Customers={custs_b}')
assert debts_b == 0 and recvs_b == 0 and custs_b == 0, 'User B should see no data initially'

# Step 6: User B restores User A's backup (THIS IS THE CRITICAL TEST)
print(f'\nStep 6: User B restores User A\'s backup (THE FIX)')
print(f'   Calling restore_from_backup with new_telegram_id=666666')
restore_result = restore_from_backup(
    backup_path,
    drop_existing=True,
    remap_paths=True,
    new_telegram_id=666666  # User B's telegram_id
)
print(f'   Restore success: {restore_result["success"]}')
print(f'   Collections restored: {restore_result["collections_restored"]}')
print(f'   Docs restored: {restore_result["total_docs"]}')
if restore_result.get('errors'):
    for err in restore_result['errors']:
        print(f'   ERROR: {err}')

# Step 7: Check if User B can now see User A's data as their own
print(f'\nStep 7: Checking if User B can see the restored data as their own:')
user_b_after = UserRepository.get_by_telegram_id(666666)
if user_b_after:
    user_b_id_after = user_b_after['id']
    print(f'   User B after restore: id={user_b_id_after}, telegram_id={user_b_after["telegram_id"]}')
    
    debts_b_after = len(TransactionRepository.get_by_user(user_b_id_after, 'debt', limit=100))
    recvs_b_after = len(TransactionRepository.get_by_user(user_b_id_after, 'receivable', limit=100))
    custs_b_after = len(CustomerRepository.get_by_user(user_b_id_after))
    
    print(f'   User B now sees: Debts={debts_b_after}, Receivables={recvs_b_after}, Customers={custs_b_after}')
    
    # The key test: User B should see User A's data as their own
    if debts_b_after >= 2 and recvs_b_after >= 1 and custs_b_after >= 1:
        print(f'   ✅ SUCCESS: User B can see User A\'s data as their own!')
        print(f'   ✅ THE BUG IS FIXED!')
        
        # Additional verification: Check user_id consistency
        user_ids_in_txns = set(t.get('user_id') for t in db.transactions.find({}))
        user_ids_in_pmts = set(p.get('user_id') for p in db.payments.find({}))
        user_ids_in_custs = set(c.get('user_id') for c in db.customers.find({}))
        
        print(f'\n   Additional verification:')
        print(f'   All transactions user_id: {sorted(user_ids_in_txns)}')
        print(f'   All payments user_id: {sorted(user_ids_in_pmts)}')
        print(f'   All customers user_id: {sorted(user_ids_in_custs)}')
        print(f'   User B\'s id: {user_b_id_after}')
        
        tx_ok = (len(user_ids_in_txns) == 1 and user_b_id_after in user_ids_in_txns)
        pmts_ok = (len(user_ids_in_pmts) == 0 or user_b_id_after in user_ids_in_pmts)
        custs_ok = (len(user_ids_in_custs) == 0 or user_b_id_after in user_ids_in_custs)
        
        if tx_ok and pmts_ok and custs_ok:
            print(f'   ✅ PERFECT: All data belongs exclusively to User B!')
        else:
            print(f'   ⚠️  WARNING: Some data may belong to other users (but User B can see theirs)')
    else:
        print(f'   ❌ FAILURE: User B still cannot see the data!')
        print(f'   Expected: Debts>=2, Receivables>=1, Customers>=1')
        print(f'   Got: Debts={debts_b_after}, Receivables={recvs_b_after}, Customers={custs_b_after}')
else:
    print(f'   ❌ CRITICAL: User B not found after restore!')

print(f'\n' + '='*70)
print('VERIFICATION COMPLETE')
print('='*70)
