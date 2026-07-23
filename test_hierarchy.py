#!/usr/bin/env python3
"""End-to-end test for the 3-level debt payments hierarchy."""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hesab'))

from unittest.mock import AsyncMock
from app.database.models import init_database
from app.database.repository import UserRepository, TransactionRepository, PaymentRepository
from app.handlers.main_handler import (
    debt_view_payments_handler, debt_payments_customer_selected,
    debt_payments_detail, debt_payments_back_to_level1
)

init_database()

def make_mock(user_id):
    msg = AsyncMock(spec=['from_user', 'chat', 'answer', 'edit_text'])
    msg.from_user = AsyncMock(spec=['id']); msg.from_user.id = user_id
    msg.chat = AsyncMock(spec=['id']); msg.chat.id = user_id
    msg.answer = AsyncMock(); msg.edit_text = AsyncMock()
    cb = AsyncMock(spec=['data', 'from_user', 'message', 'answer'])
    cb.data = ''; cb.from_user = AsyncMock(spec=['id']); cb.from_user.id = user_id
    cb.message = msg; cb.answer = AsyncMock()
    return cb

async def run_tests():
    uid = 777006
    empty_uid = 777007

    user = UserRepository.get_or_create(telegram_id=uid, username='hier_final')
    txn1 = TransactionRepository.create(
        user_id=user['id'], transaction_type='debt', amount=500000,
        party_name='مشتری الف', category='🏢 کسب\u200cوکار',
        jalali_date='1405/04/01', jalali_time='10:00:00',
        jalali_full='1405/04/01 - 10:00:00'
    )
    PaymentRepository.create(
        transaction_id=txn1['id'], user_id=user['id'], amount=200000,
        payment_type='debt_payment', description='پرداخت اول', photo_path='/tmp/p1.jpg',
        jalali_date='1405/04/10', jalali_time='14:00:00', jalali_full='1405/04/10 - 14:00:00'
    )
    PaymentRepository.create(
        transaction_id=txn1['id'], user_id=user['id'], amount=300000,
        payment_type='debt_payment', description='پرداخت نهایی',
        jalali_date='1405/04/20', jalali_time='15:00:00', jalali_full='1405/04/20 - 15:00:00'
    )
    print('✅ Test data created')

    results = {"pass": 0, "fail": 0}
    def check(level, name, ok):
        if ok:
            results["pass"] += 1
            print(f'  ✅ {level} - {name}')
        else:
            results["fail"] += 1
            print(f'  ❌ {level} - {name}')

    # ===== Level 1 =====
    cb = make_mock(uid); cb.data = 'debt_view_payments'
    await debt_view_payments_handler(cb)

    call_args_list = cb.message.answer.call_args_list
    l1_summary = call_args_list[0][0][0] if len(call_args_list) > 0 else ''

    check('L1', 'Title shows', 'پرداخت\u200cهای انجام شده' in l1_summary)
    check('L1', 'Customer count', '1 مشتری' in l1_summary)
    check('L1', 'Total paid', '۵۰۰,۰۰۰' in l1_summary or '500,000' in l1_summary)
    check('L1', 'Payment count', '2 پرداخت' in l1_summary)

    # Extract customer callback from second message
    cust_cb = None
    if len(call_args_list) > 1:
        markup = call_args_list[1][1].get('reply_markup')
        if markup:
            for row in markup.inline_keyboard:
                for btn in row:
                    if 'مشتری الف' in btn.text:
                        cust_cb = btn.callback_data
    check('L1', 'Customer button found', cust_cb is not None)

    # ===== Level 2 =====
    cb2 = make_mock(uid); cb2.data = cust_cb
    await debt_payments_customer_selected(cb2)

    l2_edit_text = ''
    if cb2.message.edit_text.call_args:
        l2_edit_text = cb2.message.edit_text.call_args[0][0]
    check('L2', 'Customer name', 'مشتری الف' in l2_edit_text)
    check('L2', 'Total paid', '۵۰۰,۰۰۰' in l2_edit_text or '500,000' in l2_edit_text)
    check('L2', 'Payment count', '2 پرداخت' in l2_edit_text)
    check('L2', 'Receipt in payment line', '📸 رسید' in l2_edit_text)
    check('L2', 'Payment text shown', 'پرداخت نهایی' in l2_edit_text)

    # Extract detail callback
    detail_cb = None
    l2_answer_calls = cb2.message.answer.call_args_list
    if l2_answer_calls:
        markup = l2_answer_calls[0][1].get('reply_markup')
        if markup:
            for row in markup.inline_keyboard:
                for btn in row:
                    if 'dvp_detail' in btn.callback_data:
                        detail_cb = btn.callback_data
    check('L2', 'Detail button found', detail_cb is not None)

    # ===== Level 3 =====
    cb3 = make_mock(uid); cb3.data = detail_cb
    await debt_payments_detail(cb3)

    l3_text = ''
    if cb3.message.edit_text.call_args:
        l3_text = cb3.message.edit_text.call_args[0][0]
    check('L3', 'Txn ID', str(txn1['id']) in l3_text)
    check('L3', 'Party name', 'مشتری الف' in l3_text)
    check('L3', 'Total paid', '۵۰۰,۰۰۰' in l3_text or '500,000' in l3_text)
    check('L3', 'Receipt photo indicator', 'رسید پرداخت: ✅ دارد' in l3_text)
    check('L3', 'Receipt text shown', 'پرداخت اول' in l3_text)
    check('L3', 'Payment history section', 'سوابق پرداخت' in l3_text)
    check('L3', 'Category shown', 'کسب\u200cوکار' in l3_text)
    check('L3', 'Settlement 100%', '100%' in l3_text)
    check('L3', 'Resid payment text', 'پرداخت نهایی' in l3_text)

    # Check keyboard has photo button
    if cb3.message.edit_text.call_args:
        l3_markup = cb3.message.edit_text.call_args[1].get('reply_markup')
        has_photo_btn = False
        if l3_markup:
            for row in l3_markup.inline_keyboard:
                for btn in row:
                    if 'مشاهده عکس' in btn.text or 'رسید پرداخت' in btn.text:
                        has_photo_btn = True
        check('L3', 'Keyboard has photo btn', has_photo_btn)

    # ===== Back to Level 1 =====
    real_cache_key = f"debt_payments_{user['id']}"
    cb_back = make_mock(uid); cb_back.data = f'dvp_bc:{real_cache_key}'
    await debt_payments_back_to_level1(cb_back)
    check('Back', 'Level 1 restored (edit_text)', cb_back.message.edit_text.called)
    
    back_edit_text = ''
    if cb_back.message.edit_text.call_args:
        back_edit_text = cb_back.message.edit_text.call_args[0][0]
    check('Back', 'Summary shown', 'پرداخت\u200cهای انجام شده' in back_edit_text)
    check('Back', 'Customer list sent', cb_back.message.answer.called)

    # ===== Empty state =====
    UserRepository.get_or_create(telegram_id=empty_uid, username='empty_final')
    cb_empty = make_mock(empty_uid); cb_empty.data = 'debt_view_payments'
    await debt_view_payments_handler(cb_empty)
    empty_text = cb_empty.message.answer.call_args[0][0]
    check('Empty', 'Empty message', 'پرداختی ثبت نشده' in empty_text)

    # ===== Summary =====
    print(f'\n📊 Results: {results["pass"]} passed, {results["fail"]} failed')

    # Cleanup
    from app.database.models import get_collection
    get_collection('transactions').delete_many({'user_id': user['id']})
    get_collection('payments').delete_many({'user_id': user['id']})

    return results["fail"] == 0

if __name__ == '__main__':
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
