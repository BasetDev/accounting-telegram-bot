"""Main Telegram bot handlers for the accounting bot."""

import os
import re
import shutil
import asyncio
import time

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, PhotoSize, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ContentType
from aiogram.types import ErrorEvent

from app.database.repository import (
    UserRepository, TransactionRepository, CustomerRepository,
    ReminderRepository, BackupRepository, CardInfoRepository, PaymentRepository
)
from app.database.models import get_collection
from app.keyboards.markups import (
    main_menu, cancel_menu, back_menu, cancel_back_menu,
    customer_menu, customer_skip_menu, report_menu, income_categories, expense_categories,
    confirm_keyboard, due_date_keyboard, party_keyboard, export_menu, backup_menu, settings_menu,
    transaction_type_keyboard,
    debt_list_keyboard, receivable_list_keyboard, edit_field_keyboard, edit_photo_keyboard,
    photo_skip_menu, card_skip_menu, card_menu, card_submenu, card_name_choice_keyboard,
    card_list_keyboard, card_edit_field_keyboard,
    card_customer_keyboard, card_items_keyboard, card_detail_keyboard,
    card_sort_keyboard, card_filter_keyboard, card_owner_overview_keyboard,
    card_linked_txn_keyboard,
    customer_select_keyboard, debt_submenu, receivable_submenu,
    debt_category_keyboard, debt_subcategory_keyboard,
    receivable_category_keyboard, receivable_subcategory_keyboard,
    DEBT_CATEGORIES, RECEIVABLE_CATEGORIES,
    payment_select_keyboard, payment_type_keyboard, payment_confirm_keyboard,
    card_select_keyboard, sheba_select_keyboard,
    bank_name_select_keyboard, debt_category_filter_keyboard,
    debt_subcategory_filter_keyboard, receivable_category_filter_keyboard,
    receivable_subcategory_filter_keyboard, customer_receivable_keyboard,
    debt_customer_keyboard,
    debt_customer_debts_keyboard,
    debt_detail_keyboard,
    recv_customer_keyboard,
    recv_customer_debts_keyboard,
    recv_detail_keyboard,
    settled_recv_customer_keyboard,
    settled_recv_items_keyboard,
    settled_recv_detail_keyboard,
    settled_debt_customer_keyboard,
    settled_debt_items_keyboard,
    settled_debt_detail_keyboard
)
from app.utils.messages import *
from app.utils.jdatetime_helper import (
    get_jalali_date, get_jalali_time, get_jalali_full,
    get_current_jalali_period, format_amount, get_days_until,
    get_week_end_jalali,
    amount_to_persian_words,
    normalize_bank_name
)
from app.utils.logger import logger
from app.config import settings
from app.services.export_service import export_transactions_excel, export_transactions_pdf

router = Router()

# ==============================
# Logging Middleware
# ==============================

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

class LoggingMiddleware(BaseMiddleware):
    """Middleware to log all incoming updates for debugging."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Log message updates
        if isinstance(event, Message):
            user = event.from_user
            user_info = f"user_id={user.id}, username={user.username}" if user else "unknown"
            content_type = event.content_type
            text_preview = (event.text or "")[:50] if event.text else content_type
            logger.debug(f"Message from {user_info}: {text_preview}")

        # Log callback query updates
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            user_info = f"user_id={user.id}, username={user.username}" if user else "unknown"
            callback_data = event.data or ""
            logger.debug(f"Callback from {user_info}: {callback_data}")

        return await handler(event, data)

# Attach middleware to router
router.message.middleware(LoggingMiddleware())
router.callback_query.middleware(LoggingMiddleware())

# ==============================
# Global Error Handler
# ==============================

@router.error()
async def error_handler(event: ErrorEvent):
    """Handle all unhandled exceptions in handlers."""
    logger.error(f"Unhandled error: {event.exception}", exc_info=True)
    return True

async def safe_callback_answer(callback: CallbackQuery, text: str = "", show_alert: bool = False):
    """Safely answer a callback query, handling cases where the callback was already answered."""
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception as e:
        logger.debug(f"Could not answer callback (may have been already answered): {e}")

def safe_parse_callback_id(callback: CallbackQuery, index: int = 1) -> int | None:
    """Safely parse an integer ID from callback data. Returns None if parsing fails."""
    try:
        parts = callback.data.split(":")
        if len(parts) > index:
            return int(parts[index])
    except (ValueError, IndexError) as e:
        logger.debug(f"Could not parse callback data '{callback.data}' at index {index}: {e}")
    return None

async def safe_edit(message, text, reply_markup=None, parse_mode=None):
    """Safely edit a message, handling cases where the message was deleted."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.debug(f"Could not edit message (may have been deleted): {e}")
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

async def safe_delete(message):
    """Safely delete a message."""
    try:
        await message.delete()
    except Exception:
        pass

# ==============================
# FSM States
# ==============================

class IncomeForm(StatesGroup):
    amount = State()
    description = State()
    category = State()
    photo = State()
    confirm = State()

class ExpenseForm(StatesGroup):
    amount = State()
    description = State()
    category = State()
    photo = State()
    confirm = State()

class DebtForm(StatesGroup):
    category = State()
    subcategory = State()
    amount = State()
    party = State()
    description = State()
    due_date = State()
    photo = State()
    card_select = State()
    manual_card = State()
    sheba_select = State()
    manual_sheba = State()
    bank_name_select = State()
    manual_bank_name = State()
    customer_id = State()
    confirm = State()

class ReceivableForm(StatesGroup):
    category = State()
    subcategory = State()
    amount = State()
    party = State()
    description = State()
    due_date = State()
    photo = State()
    card_select = State()
    manual_card = State()
    sheba_select = State()
    manual_sheba = State()
    bank_name_select = State()
    manual_bank_name = State()
    customer_id = State()
    confirm = State()

class CustomerForm(StatesGroup):
    name = State()
    phone = State()
    address = State()
    notes = State()
    confirm = State()

class CustomerEditForm(StatesGroup):
    select = State()
    name = State()
    phone = State()
    address = State()
    notes = State()

class CustomerDeleteForm(StatesGroup):
    select = State()
    confirm = State()

class SearchForm(StatesGroup):
    query = State()
    transaction_type = State()

class CustomerSearchForm(StatesGroup):
    query = State()

class DebtEditForm(StatesGroup):
    edit_id = State()
    amount = State()
    party = State()
    description = State()
    due_date = State()
    photo = State()
    confirm = State()
    delete_confirm = State()

class ReceivableEditForm(StatesGroup):
    edit_id = State()
    amount = State()
    party = State()
    description = State()
    due_date = State()
    photo = State()
    confirm = State()
    delete_confirm = State()

class CardForm(StatesGroup):
    """Card and Sheba registration with name."""
    name_choice = State()  # manual or customer
    name_manual = State()
    name_customer_select = State()
    card_number = State()
    sheba = State()
    bank_name = State()
    confirm = State()

class CardEditForm(StatesGroup):
    """Edit card info."""
    select = State()
    field = State()
    value = State()
    confirm = State()

class CardDeleteForm(StatesGroup):
    select = State()
    confirm = State()

class CardSearchForm(StatesGroup):
    query = State()

class PaymentForm(StatesGroup):
    """FSM states for debt payment / receivable collection flow."""
    select = State()
    payment_type = State()
    amount = State()
    description = State()
    photo = State()
    confirm = State()

# ==============================
# Helper Functions
# ==============================

def get_user(message: Message):
    """Get or create user from Telegram message."""
    user = message.from_user
    return UserRepository.get_or_create(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

async def _save_photo(bot: Bot, photo: PhotoSize, user_id: int) -> str:
    """Download and save a photo from Telegram. Returns the local file path."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    if not file.file_path:
        raise ValueError("Could not retrieve photo file path from Telegram")
    
    ext = os.path.splitext(file.file_path)[1] if '.' in file.file_path else '.jpg'
    jalali_date = get_jalali_date().replace('/', '')
    jalali_time = get_jalali_time().replace(':', '')
    unique_suffix = file_id[-8:] if len(file_id) > 8 else file_id
    filename = f"{user_id}_{jalali_date}_{jalali_time}_{unique_suffix}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    
    await bot.download_file(file.file_path, destination=filepath)
    
    # Verify file was saved
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        raise Exception(f"Failed to save photo to {filepath}")
    
    logger.info(f"Photo saved: {filepath} ({os.path.getsize(filepath)} bytes)")
    return filepath

def _build_dashboard_text(user_id: int) -> str:
    """Build the financial dashboard text."""
    totals = TransactionRepository.get_total_by_type(user_id)
    
    income = totals["income"]
    expense = totals["expense"]
    debts = totals["debt"]
    receivables = totals["receivable"]
    
    # Net balance: income - expense + receivables - debts
    balance = income - expense + receivables - debts
    
    # Status
    if balance > 0:
        status = DASHBOARD_POSITIVE
    elif balance < 0:
        status = DASHBOARD_NEGATIVE
    else:
        status = DASHBOARD_ZERO
    
    # Calculate percentages
    total_inflow = income + receivables
    total_outflow = expense + debts
    
    if total_inflow > 0:
        income_pct = (income / total_inflow) * 100
        recv_pct = (receivables / total_inflow) * 100
    else:
        income_pct = 0
        recv_pct = 0
    
    if total_outflow > 0:
        expense_pct = (expense / total_outflow) * 100
        debt_pct = (debts / total_outflow) * 100
    else:
        expense_pct = 0
        debt_pct = 0
    
    # Build progress bars
    def make_bar(pct, length=10):
        filled = int(pct / 100 * length)
        return "█" * filled + "░" * (length - filled)
    
    return f"""📊 داشبورد مالی
━━━━━━━━━━━━━━━━━━

💰 درآمدها
├── مجموع: {format_amount(income)} تومان
└── {make_bar(income_pct)} {income_pct:.1f}%

💸 هزینه‌ها
├── مجموع: {format_amount(expense)} تومان
└── {make_bar(expense_pct)} {expense_pct:.1f}%

📌 طلب‌ها
├── مجموع: {format_amount(receivables)} تومان
└── {make_bar(recv_pct)} {recv_pct:.1f}%

📋 بدهی‌ها
├── مجموع: {format_amount(debts)} تومان
└── {make_bar(debt_pct)} {debt_pct:.1f}%

━━━━━━━━━━━━━━━━━━
✅ موجودی نهایی: {format_amount(balance)} تومان

{status}"""

# ==============================
# Command Handlers
# ==============================

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    get_user(message)
    await message.answer(WELCOME, reply_markup=main_menu())

@router.message(Command("menu"))
@router.message(F.text == "🔙 بازگشت به منو")
async def cmd_menu(message: Message, state: FSMContext):
    """Handle /menu or back to menu."""
    await state.clear()
    await message.answer(MENU_TEXT, reply_markup=main_menu())

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(HELP, reply_markup=main_menu())

# ==============================
# Income Handlers
# ==============================

@router.message(F.text == "💰 ثبت درآمد")
async def income_start(message: Message, state: FSMContext):
    """Start income registration flow."""
    await state.set_state(IncomeForm.amount)
    await message.answer(INCOME_AMOUNT, reply_markup=cancel_menu())

@router.message(IncomeForm.amount)
async def income_amount(message: Message, state: FSMContext):
    """Handle income amount input."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    try:
        amount = float(message.text.replace(",", "").replace("٬", ""))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await state.set_state(IncomeForm.description)
        await message.answer(INCOME_DESC, reply_markup=cancel_back_menu())
    except ValueError:
        await message.answer(INVALID_AMOUNT)

@router.message(IncomeForm.description)
async def income_description(message: Message, state: FSMContext):
    """Handle income description."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    await state.update_data(description=message.text)
    await state.set_state(IncomeForm.category)
    await message.answer(INCOME_CATEGORY, reply_markup=income_categories())

@router.message(IncomeForm.category)
async def income_category(message: Message, state: FSMContext):
    """Handle income category selection."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(IncomeForm.description)
        await message.answer(INCOME_DESC, reply_markup=cancel_back_menu())
        return
    
    await state.update_data(category=message.text)
    await state.set_state(IncomeForm.photo)
    await message.answer(
        "📸 در صورت تمایل عکس مدرک یا فیش را ارسال کنید.\n"
        "یا گزینه «⏭️ بدون عکس» را انتخاب کنید:",
        reply_markup=photo_skip_menu()
    )

@router.message(IncomeForm.photo)
async def income_photo(message: Message, state: FSMContext):
    """Handle income photo upload."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    photo_path = None
    
    if message.text == "⏭️ بدون عکس":
        photo_path = None
    elif message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        try:
            photo_path = await _save_photo(message.bot, photo, message.from_user.id)
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            await message.answer("⚠️ خطا در ذخیره عکس. لطفاً دوباره تلاش کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
            return
    else:
        await message.answer("📸 لطفاً یک عکس ارسال کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
        return
    
    await state.update_data(photo_path=photo_path)
    
    # Save transaction
    data = await state.get_data()
    try:
        user = get_user(message)
        TransactionRepository.create(
            user_id=user["id"],
            transaction_type="income",
            amount=data["amount"],
            description=data["description"],
            category=data["category"],
            photo_path=data.get("photo_path"),
            jalali_date=get_jalali_date(),
            jalali_time=get_jalali_time(),
            jalali_full=get_jalali_full()
        )
        logger.info(f"Income recorded: {data['amount']} by user {user['telegram_id']}")
        
        await state.clear()
        
        reply = f"{INCOME_SAVED}\n\n💰 مبلغ: {format_amount(data['amount'])} تومان\n🏷 دسته: {data['category']}\n📝 توضیحات: {data['description']}\n📅 تاریخ: {get_jalali_date()} ساعت {get_jalali_time()}"
        if photo_path:
            reply += f"\n📸 عکس: ✅ ضمیمه شد"
        
        await message.answer(reply, reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Error saving income: {e}")
        await message.answer(ERROR_GENERAL, reply_markup=main_menu())

# ==============================
# Expense Handlers
# ==============================

@router.message(F.text == "💸 ثبت هزینه")
async def expense_start(message: Message, state: FSMContext):
    """Start expense registration flow."""
    await state.set_state(ExpenseForm.amount)
    await message.answer(EXPENSE_AMOUNT, reply_markup=cancel_menu())

@router.message(ExpenseForm.amount)
async def expense_amount(message: Message, state: FSMContext):
    """Handle expense amount."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    try:
        amount = float(message.text.replace(",", "").replace("٬", ""))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await state.set_state(ExpenseForm.description)
        await message.answer(EXPENSE_DESC, reply_markup=cancel_back_menu())
    except ValueError:
        await message.answer(INVALID_AMOUNT)

@router.message(ExpenseForm.description)
async def expense_description(message: Message, state: FSMContext):
    """Handle expense description."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    await state.update_data(description=message.text)
    await state.set_state(ExpenseForm.category)
    await message.answer(EXPENSE_CATEGORY, reply_markup=expense_categories())

@router.message(ExpenseForm.category)
async def expense_category(message: Message, state: FSMContext):
    """Handle expense category."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(ExpenseForm.description)
        await message.answer(EXPENSE_DESC, reply_markup=cancel_back_menu())
        return
    
    await state.update_data(category=message.text)
    await state.set_state(ExpenseForm.photo)
    await message.answer(
        "📸 در صورت تمایل عکس رسید یا مدرک را ارسال کنید.\n"
        "یا گزینه «⏭️ بدون عکس» را انتخاب کنید:",
        reply_markup=photo_skip_menu()
    )

@router.message(ExpenseForm.photo)
async def expense_photo(message: Message, state: FSMContext):
    """Handle expense photo upload."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    photo_path = None
    
    if message.text == "⏭️ بدون عکس":
        photo_path = None
    elif message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        try:
            photo_path = await _save_photo(message.bot, photo, message.from_user.id)
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            await message.answer("⚠️ خطا در ذخیره عکس. لطفاً دوباره تلاش کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
            return
    else:
        await message.answer("📸 لطفاً یک عکس ارسال کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
        return
    
    await state.update_data(photo_path=photo_path)
    
    # Save transaction
    data = await state.get_data()
    try:
        user = get_user(message)
        TransactionRepository.create(
            user_id=user["id"],
            transaction_type="expense",
            amount=data["amount"],
            description=data["description"],
            category=data["category"],
            photo_path=data.get("photo_path"),
            jalali_date=get_jalali_date(),
            jalali_time=get_jalali_time(),
            jalali_full=get_jalali_full()
        )
        logger.info(f"Expense recorded: {data['amount']} by user {user['telegram_id']}")
        
        await state.clear()
        
        reply = f"{EXPENSE_SAVED}\n\n💸 مبلغ: {format_amount(data['amount'])} تومان\n🏷 دسته: {data['category']}\n📝 توضیحات: {data['description']}\n📅 تاریخ: {get_jalali_date()} ساعت {get_jalali_time()}"
        if photo_path:
            reply += f"\n📸 عکس: ✅ ضمیمه شد"
        
        await message.answer(reply, reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Error saving expense: {e}")
        await message.answer(ERROR_GENERAL, reply_markup=main_menu())

# ==============================
# Debt Handlers
# ==============================

@router.callback_query(F.data == "debt_register")
async def debt_register_from_submenu(callback: CallbackQuery, state: FSMContext):
    """Handle 'register new debt' from submenu - show category selection."""
    await safe_delete(callback.message)
    await state.set_state(DebtForm.category)
    await callback.message.answer(DEBT_CATEGORY_PROMPT, reply_markup=debt_category_keyboard())
    await safe_callback_answer(callback)

@router.callback_query(DebtForm.category, F.data.startswith("debt_cat:"))
async def debt_category_selected(callback: CallbackQuery, state: FSMContext):
    """Handle debt category selection."""
    cat = callback.data.split(":", 1)[1]

    if cat == "cancel":
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        await safe_callback_answer(callback)
        return

    await state.update_data(category=cat)

    # If category has no subcategories (e.g. "سایر"), skip to amount
    subs = DEBT_CATEGORIES.get(cat, [])
    if not subs:
        await state.update_data(subcategory=cat)
        await state.set_state(DebtForm.amount)
        await callback.message.edit_text(
            f"🏷 دسته: {cat}\n\n{DEBT_AMOUNT}", reply_markup=None
        )
    else:
        await state.set_state(DebtForm.subcategory)
        await callback.message.edit_text(
            f"🏷 دسته: {cat}\n\n{DEBT_SUBCATEGORY_PROMPT}",
            reply_markup=debt_subcategory_keyboard(cat)
        )

    await safe_callback_answer(callback)

@router.callback_query(DebtForm.subcategory, F.data.startswith("debt_sub:"))
async def debt_subcategory_selected(callback: CallbackQuery, state: FSMContext):
    """Handle debt subcategory selection."""
    sub = callback.data.split(":", 1)[1]

    if sub == "back":
        await state.set_state(DebtForm.category)
        await callback.message.edit_text(
            DEBT_CATEGORY_PROMPT, reply_markup=debt_category_keyboard()
        )
        await safe_callback_answer(callback)
        return

    data = await state.get_data()
    cat = data.get("category", "")
    await state.update_data(subcategory=sub)
    await state.set_state(DebtForm.amount)

    await callback.message.edit_text(
        f"🏷 دسته: {cat} / {sub}\n\n{DEBT_AMOUNT}", reply_markup=None
    )
    await safe_callback_answer(callback)

@router.message(DebtForm.amount)
async def debt_amount(message: Message, state: FSMContext):
    """Handle debt amount."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    try:
        amount = float(message.text.replace(",", "").replace("٬", ""))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await state.set_state(DebtForm.party)
        # Get customer list
        user = get_user(message)
        customers = CustomerRepository.get_by_user(user["id"])
        if customers:
            await message.answer(DEBT_PARTY, reply_markup=party_keyboard(customers))
        else:
            await message.answer(DEBT_PARTY + "\n\n💡 ابتدا از بخش «مدیریت مشتریان» مشتری اضافه کنید یا نام را دستی وارد کنید:", reply_markup=cancel_back_menu())
    except ValueError:
        await message.answer(INVALID_AMOUNT)

@router.message(DebtForm.party)
async def debt_party(message: Message, state: FSMContext):
    """Handle debt party name."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    await state.update_data(party=message.text)
    await state.set_state(DebtForm.description)
    await message.answer(DEBT_DESC, reply_markup=cancel_back_menu())

@router.message(DebtForm.description)
async def debt_description(message: Message, state: FSMContext):
    """Handle debt description."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    await state.update_data(description=message.text)
    await state.set_state(DebtForm.due_date)
    await message.answer(DEBT_DUE, reply_markup=due_date_keyboard())

@router.message(DebtForm.due_date)
async def debt_due_date(message: Message, state: FSMContext):
    """Handle debt due date."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    # Handle "today" option
    if message.text == "📅 امروز":
        due_date = get_jalali_date()
        due_time = get_jalali_time()
    else:
        if not re.match(r"^\d{4}/\d{2}/\d{2}$", message.text):
            await message.answer(INVALID_DATE)
            return
        due_date = message.text
        due_time = None
    
    await state.update_data(due_date=due_date, due_time=due_time)
    
    # Ask for optional photo
    await state.set_state(DebtForm.photo)
    await message.answer(
        "📸 در صورت تمایل عکس مدرک یا سند بدهی را ارسال کنید.\n"
        "یا گزینه «⏭️ بدون عکس» را انتخاب کنید:",
        reply_markup=photo_skip_menu()
    )

@router.message(DebtForm.photo)
async def debt_photo(message: Message, state: FSMContext):
    """Handle debt photo upload and show card selection."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    photo_path = None
    
    if message.text == "⏭️ بدون عکس":
        photo_path = None
    elif message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        try:
            photo_path = await _save_photo(message.bot, photo, message.from_user.id)
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            await message.answer("⚠️ خطا در ذخیره عکس. لطفاً دوباره تلاش کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
            return
    else:
        await message.answer("📸 لطفاً یک عکس ارسال کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
        return
    
    await state.update_data(photo_path=photo_path)
    
    # Step: Card number selection (optional)
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await state.set_state(DebtForm.card_select)
    await message.answer(CARD_INFO_DEBT_PROMPT, reply_markup=card_select_keyboard(cards))

@router.message(DebtForm.card_select)
async def debt_card_select(message: Message, state: FSMContext):
    """Handle card number selection for debt registration."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(card_number=None)
        # Move to sheba selection
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(DebtForm.sheba_select)
        await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))
        return

    if message.text == "✏️ ورود دستی شماره کارت":
        await state.set_state(DebtForm.manual_card)
        await message.answer(CARD_INFO_MANUAL_CARD, reply_markup=card_skip_menu())
        return

    # Try to match selected card from existing cards
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    selected_card = None
    for card in cards:
        if not card["card_number"]:
            continue
        label = f"{card["name"]} | {card["card_number"][-4:]}****"
        if label == message.text:
            selected_card = card
            break
    if selected_card:
        await state.update_data(card_number=selected_card["card_number"])
        # Move to sheba selection
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(DebtForm.sheba_select)
        await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))
        return

    # Unrecognized input - re-show the keyboard
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await message.answer("⚠️ لطفاً از گزینه‌های موجود استفاده کنید.", reply_markup=card_select_keyboard(cards))

@router.message(DebtForm.manual_card)
async def debt_manual_card(message: Message, state: FSMContext):
    """Handle manual card number input for debt."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        # Go back to card_select
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(DebtForm.card_select)
        await message.answer(CARD_INFO_DEBT_PROMPT, reply_markup=card_select_keyboard(cards))
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(card_number=None)
    else:
        card_number = message.text.replace(" ", "").replace("-", "")
        if not card_number.isdigit() or len(card_number) != 16:
            await message.answer(CARD_VALID_ERROR_16)
            return
        await state.update_data(card_number=card_number)

    # Move to sheba selection
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await state.set_state(DebtForm.sheba_select)
    await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))

@router.message(DebtForm.sheba_select)
async def debt_sheba_select(message: Message, state: FSMContext):
    """Handle sheba/IBAN selection for debt registration."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(sheba=None)
        # Move to bank name selection
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        bank_names = list({c.bank_name for c in cards if c.bank_name})
        await state.set_state(DebtForm.bank_name_select)
        await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))
        return

    if message.text == "✏️ ورود دستی شماره شبا":
        await state.set_state(DebtForm.manual_sheba)
        await message.answer(SHEBA_MANUAL_PROMPT, reply_markup=card_skip_menu())
        return

    # Try to match selected sheba from existing cards
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    selected_card = None
    for card in cards:
        if not card["sheba"]:
            continue
        label = f"{card["name"]} | IR{card["sheba"][-4:]}****"
        if label == message.text:
            selected_card = card
            break
    if selected_card:
        sheba_val = selected_card["sheba"]
        if sheba_val and not sheba_val.upper().startswith("IR"):
            sheba_val = f"IR{sheba_val}"
        await state.update_data(sheba=sheba_val)
        # Move to bank name selection
        cards = CardInfoRepository.get_by_user(user["id"])
        bank_names = list({c.bank_name for c in cards if c.bank_name})
        await state.set_state(DebtForm.bank_name_select)
        await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))
        return

    # Unrecognized input - re-show the keyboard
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await message.answer("⚠️ لطفاً از گزینه‌های موجود استفاده کنید.", reply_markup=sheba_select_keyboard(cards))

@router.message(DebtForm.manual_sheba)
async def debt_manual_sheba(message: Message, state: FSMContext):
    """Handle manual sheba input for debt."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        # Go back to sheba_select
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(DebtForm.sheba_select)
        await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(sheba=None)
    else:
        sheba_digits = message.text.replace(" ", "").replace("-", "")
        if sheba_digits.upper().startswith("IR"):
            sheba_digits = sheba_digits[2:]
        if not sheba_digits.isdigit() or len(sheba_digits) != 24:
            await message.answer(CARD_VALID_ERROR_SHEBA)
            return
        await state.update_data(sheba=f"IR{sheba_digits}")

    # Move to bank name selection
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    bank_names = list({c.bank_name for c in cards if c.bank_name})
    await state.set_state(DebtForm.bank_name_select)
    await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))

@router.message(DebtForm.bank_name_select)
async def debt_bank_name_select(message: Message, state: FSMContext):
    """Handle bank name selection for debt registration."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(bank_name=None)
        await _show_debt_confirm(message, state)
        return

    if message.text == "✏️ ورود دستی نام بانک":
        await state.set_state(DebtForm.manual_bank_name)
        await message.answer(BANK_NAME_MANUAL_PROMPT, reply_markup=card_skip_menu())
        return

    # Try to match selected bank name
    if message.text.startswith("🏛 "):
        bank_name = normalize_bank_name(message.text[3:])
        await state.update_data(bank_name=bank_name)
        await _show_debt_confirm(message, state)
        return

    # Unrecognized input - re-show the keyboard
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    bank_names = list({c.bank_name for c in cards if c.bank_name})
    await message.answer("⚠️ لطفاً از گزینه‌های موجود استفاده کنید.", reply_markup=bank_name_select_keyboard(bank_names))

@router.message(DebtForm.manual_bank_name)
async def debt_manual_bank_name(message: Message, state: FSMContext):
    """Handle manual bank name input for debt."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        # Go back to bank_name_select
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        bank_names = list({c.bank_name for c in cards if c.bank_name})
        await state.set_state(DebtForm.bank_name_select)
        await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(bank_name=None)
    else:
        await state.update_data(bank_name=normalize_bank_name(message.text))

    await _show_debt_confirm(message, state)

async def _show_debt_confirm(message: Message, state: FSMContext):
    """Show debt summary confirmation."""
    data = await state.get_data()
    amount = data["amount"]
    party = data["party"]
    due_date = data["due_date"]
    due_time = data.get("due_time")
    cat = data.get("category", "-")
    sub = data.get("subcategory", "-")

    summary = f"📋 خلاصه بدهی:\n\n🏷 دسته: {cat} / {sub}\nمبلغ: {format_amount(amount)} تومان\nطرف حساب: {party}\nسررسید: {due_date}"
    if due_time:
        summary += f" ساعت {due_time}"
    if data.get("photo_path"):
        summary += "\n📸 عکس: ✅ ضمیمه شد"
    if data.get("card_number"):
        summary += f"\n💳 کارت: {data['card_number']}"
    if data.get("sheba"):
        summary += f"\n🏦 شبا: {data['sheba']}"
    if data.get("bank_name"):
        summary += f"\n🏛 بانک: {data['bank_name']}"

    await message.answer(summary, reply_markup=confirm_keyboard())
    await state.set_state(DebtForm.confirm)

@router.callback_query(DebtForm.confirm)
async def debt_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle debt confirmation."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        try:
            user = UserRepository.get_or_create(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )
            TransactionRepository.create(
                user_id=user["id"],
                transaction_type="debt",
                amount=data["amount"],
                party_name=data["party"],
                description=data["description"],
                category=data.get("category"),
                subcategory=data.get("subcategory"),
                due_jalali_date=data["due_date"],
                due_jalali_time=data.get("due_time"),
                photo_path=data.get("photo_path"),
                card_number=data.get("card_number"),
                sheba=data.get("sheba"),
                bank_name=data.get("bank_name"),
                jalali_date=get_jalali_date(),
                jalali_time=get_jalali_time(),
                jalali_full=get_jalali_full()
            )
            logger.info(f"Debt recorded: {data['amount']} by user {user["telegram_id"]}")
            
            await state.clear()
            await callback.message.edit_text(f"{DEBT_SAVED}", reply_markup=None)
            await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Error saving debt: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
    
    await safe_callback_answer(callback)

# ==============================
# Receivable Handlers
# ==============================

@router.callback_query(F.data == "receivable_register")
async def receivable_register_from_submenu(callback: CallbackQuery, state: FSMContext):
    """Handle 'register new receivable' from submenu - show category selection."""
    await safe_delete(callback.message)
    await state.set_state(ReceivableForm.category)
    await callback.message.answer(RECEIVABLE_CATEGORY_PROMPT, reply_markup=receivable_category_keyboard())
    await safe_callback_answer(callback)

@router.callback_query(ReceivableForm.category, F.data.startswith("recv_cat:"))
async def receivable_category_selected(callback: CallbackQuery, state: FSMContext):
    """Handle receivable category selection."""
    cat = callback.data.split(":", 1)[1]

    if cat == "cancel":
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        await safe_callback_answer(callback)
        return

    await state.update_data(category=cat)

    # If category has no subcategories (e.g. "سایر"), skip to amount
    subs = RECEIVABLE_CATEGORIES.get(cat, [])
    if not subs:
        await state.update_data(subcategory=cat)
        await state.set_state(ReceivableForm.amount)
        await callback.message.edit_text(
            f"🏷 دسته: {cat}\n\n{RECEIVABLE_AMOUNT}", reply_markup=None
        )
    else:
        await state.set_state(ReceivableForm.subcategory)
        await callback.message.edit_text(
            f"🏷 دسته: {cat}\n\n{RECEIVABLE_SUBCATEGORY_PROMPT}",
            reply_markup=receivable_subcategory_keyboard(cat)
        )

    await safe_callback_answer(callback)

@router.callback_query(ReceivableForm.subcategory, F.data.startswith("recv_sub:"))
async def receivable_subcategory_selected(callback: CallbackQuery, state: FSMContext):
    """Handle receivable subcategory selection."""
    sub = callback.data.split(":", 1)[1]

    if sub == "back":
        await state.set_state(ReceivableForm.category)
        await callback.message.edit_text(
            RECEIVABLE_CATEGORY_PROMPT, reply_markup=receivable_category_keyboard()
        )
        await safe_callback_answer(callback)
        return

    data = await state.get_data()
    cat = data.get("category", "")
    await state.update_data(subcategory=sub)
    await state.set_state(ReceivableForm.amount)

    await callback.message.edit_text(
        f"🏷 دسته: {cat} / {sub}\n\n{RECEIVABLE_AMOUNT}", reply_markup=None
    )
    await safe_callback_answer(callback)

@router.message(ReceivableForm.amount)
async def receivable_amount(message: Message, state: FSMContext):
    """Handle receivable amount."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    try:
        amount = float(message.text.replace(",", "").replace("٬", ""))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await state.set_state(ReceivableForm.party)
        # Get customer list
        user = get_user(message)
        customers = CustomerRepository.get_by_user(user["id"])
        if customers:
            await message.answer(RECEIVABLE_PARTY, reply_markup=party_keyboard(customers))
        else:
            await message.answer(RECEIVABLE_PARTY + "\n\n💡 ابتدا از بخش «مدیریت مشتریان» مشتری اضافه کنید یا نام را دستی وارد کنید:", reply_markup=cancel_back_menu())
    except ValueError:
        await message.answer(INVALID_AMOUNT)

@router.message(ReceivableForm.party)
async def receivable_party(message: Message, state: FSMContext):
    """Handle receivable party."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    await state.update_data(party=message.text)
    await state.set_state(ReceivableForm.description)
    await message.answer(RECEIVABLE_DESC, reply_markup=cancel_back_menu())

@router.message(ReceivableForm.description)
async def receivable_description(message: Message, state: FSMContext):
    """Handle receivable description."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    await state.update_data(description=message.text)
    await state.set_state(ReceivableForm.due_date)
    await message.answer(RECEIVABLE_DUE, reply_markup=due_date_keyboard())

@router.message(ReceivableForm.due_date)
async def receivable_due_date(message: Message, state: FSMContext):
    """Handle receivable due date."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    # Handle "today" option
    if message.text == "📅 امروز":
        due_date = get_jalali_date()
        due_time = get_jalali_time()
    else:
        if not re.match(r"^\d{4}/\d{2}/\d{2}$", message.text):
            await message.answer(INVALID_DATE)
            return
        due_date = message.text
        due_time = None
    
    await state.update_data(due_date=due_date, due_time=due_time)
    
    await state.set_state(ReceivableForm.photo)
    await message.answer(
        "📸 در صورت تمایل عکس مدرک یا سند طلب را ارسال کنید.\n"
        "یا گزینه «⏭️ بدون عکس» را انتخاب کنید:",
        reply_markup=photo_skip_menu()
    )

@router.message(ReceivableForm.photo)
async def receivable_photo(message: Message, state: FSMContext):
    """Handle receivable photo upload and show card selection."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    photo_path = None
    
    if message.text == "⏭️ بدون عکس":
        photo_path = None
    elif message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        try:
            photo_path = await _save_photo(message.bot, photo, message.from_user.id)
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            await message.answer("⚠️ خطا در ذخیره عکس. لطفاً دوباره تلاش کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
            return
    else:
        await message.answer("📸 لطفاً یک عکس ارسال کنید یا گزینه «⏭️ بدون عکس» را انتخاب کنید.")
        return
    
    await state.update_data(photo_path=photo_path)
    
    # Step: Card number selection (optional)
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await state.set_state(ReceivableForm.card_select)
    await message.answer(CARD_INFO_RECV_PROMPT, reply_markup=card_select_keyboard(cards))

@router.message(ReceivableForm.card_select)
async def receivable_card_select(message: Message, state: FSMContext):
    """Handle card number selection for receivable registration."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(card_number=None)
        # Move to sheba selection
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(ReceivableForm.sheba_select)
        await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))
        return

    if message.text == "✏️ ورود دستی شماره کارت":
        await state.set_state(ReceivableForm.manual_card)
        await message.answer(CARD_INFO_MANUAL_CARD, reply_markup=card_skip_menu())
        return

    # Try to match selected card from existing cards
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    selected_card = None
    for card in cards:
        if not card["card_number"]:
            continue
        label = f"{card["name"]} | {card["card_number"][-4:]}****"
        if label == message.text:
            selected_card = card
            break
    if selected_card:
        await state.update_data(card_number=selected_card["card_number"])
        # Move to sheba selection
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(ReceivableForm.sheba_select)
        await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))
        return

    # Unrecognized input - re-show the keyboard
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await message.answer("⚠️ لطفاً از گزینه‌های موجود استفاده کنید.", reply_markup=card_select_keyboard(cards))

@router.message(ReceivableForm.manual_card)
async def receivable_manual_card(message: Message, state: FSMContext):
    """Handle manual card number input for receivable."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        # Go back to card_select
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(ReceivableForm.card_select)
        await message.answer(CARD_INFO_RECV_PROMPT, reply_markup=card_select_keyboard(cards))
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(card_number=None)
    else:
        card_number = message.text.replace(" ", "").replace("-", "")
        if not card_number.isdigit() or len(card_number) != 16:
            await message.answer(CARD_VALID_ERROR_16)
            return
        await state.update_data(card_number=card_number)

    # Move to sheba selection
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await state.set_state(ReceivableForm.sheba_select)
    await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))

@router.message(ReceivableForm.sheba_select)
async def receivable_sheba_select(message: Message, state: FSMContext):
    """Handle sheba/IBAN selection for receivable registration."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(sheba=None)
        # Move to bank name selection
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        bank_names = list({c.bank_name for c in cards if c.bank_name})
        await state.set_state(ReceivableForm.bank_name_select)
        await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))
        return

    if message.text == "✏️ ورود دستی شماره شبا":
        await state.set_state(ReceivableForm.manual_sheba)
        await message.answer(SHEBA_MANUAL_PROMPT, reply_markup=card_skip_menu())
        return

    # Try to match selected sheba from existing cards
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    selected_card = None
    for card in cards:
        if not card["sheba"]:
            continue
        label = f"{card["name"]} | IR{card["sheba"][-4:]}****"
        if label == message.text:
            selected_card = card
            break
    if selected_card:
        sheba_val = selected_card["sheba"]
        if sheba_val and not sheba_val.upper().startswith("IR"):
            sheba_val = f"IR{sheba_val}"
        await state.update_data(sheba=sheba_val)
        # Move to bank name selection
        cards = CardInfoRepository.get_by_user(user["id"])
        bank_names = list({c.bank_name for c in cards if c.bank_name})
        await state.set_state(ReceivableForm.bank_name_select)
        await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))
        return

    # Unrecognized input - re-show the keyboard
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    await message.answer("⚠️ لطفاً از گزینه‌های موجود استفاده کنید.", reply_markup=sheba_select_keyboard(cards))

@router.message(ReceivableForm.manual_sheba)
async def receivable_manual_sheba(message: Message, state: FSMContext):
    """Handle manual sheba input for receivable."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        # Go back to sheba_select
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        await state.set_state(ReceivableForm.sheba_select)
        await message.answer(SHEBA_SELECT_PROMPT, reply_markup=sheba_select_keyboard(cards))
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(sheba=None)
    else:
        sheba_digits = message.text.replace(" ", "").replace("-", "")
        if sheba_digits.upper().startswith("IR"):
            sheba_digits = sheba_digits[2:]
        if not sheba_digits.isdigit() or len(sheba_digits) != 24:
            await message.answer(CARD_VALID_ERROR_SHEBA)
            return
        await state.update_data(sheba=f"IR{sheba_digits}")

    # Move to bank name selection
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    bank_names = list({c.bank_name for c in cards if c.bank_name})
    await state.set_state(ReceivableForm.bank_name_select)
    await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))

@router.message(ReceivableForm.bank_name_select)
async def receivable_bank_name_select(message: Message, state: FSMContext):
    """Handle bank name selection for receivable registration."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(bank_name=None)
        await _show_receivable_confirm(message, state)
        return

    if message.text == "✏️ ورود دستی نام بانک":
        await state.set_state(ReceivableForm.manual_bank_name)
        await message.answer(BANK_NAME_MANUAL_PROMPT, reply_markup=card_skip_menu())
        return

    # Try to match selected bank name
    if message.text.startswith("🏛 "):
        bank_name = normalize_bank_name(message.text[3:])
        await state.update_data(bank_name=bank_name)
        await _show_receivable_confirm(message, state)
        return

    # Unrecognized input - re-show the keyboard
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    bank_names = list({c.bank_name for c in cards if c.bank_name})
    await message.answer("⚠️ لطفاً از گزینه‌های موجود استفاده کنید.", reply_markup=bank_name_select_keyboard(bank_names))

@router.message(ReceivableForm.manual_bank_name)
async def receivable_manual_bank_name(message: Message, state: FSMContext):
    """Handle manual bank name input for receivable."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        # Go back to bank_name_select
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        bank_names = list({c.bank_name for c in cards if c.bank_name})
        await state.set_state(ReceivableForm.bank_name_select)
        await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(bank_name=None)
    else:
        await state.update_data(bank_name=normalize_bank_name(message.text))

    await _show_receivable_confirm(message, state)

async def _show_receivable_confirm(message: Message, state: FSMContext):
    """Show receivable summary confirmation."""
    data = await state.get_data()
    due_time = data.get("due_time")
    cat = data.get("category", "-")
    sub = data.get("subcategory", "-")
    summary = f"📌 خلاصه طلب:\n\n🏷 دسته: {cat} / {sub}\nمبلغ: {format_amount(data['amount'])} تومان\nطرف حساب: {data['party']}\nسررسید: {data['due_date']}"
    if due_time:
        summary += f" ساعت {due_time}"
    if data.get("photo_path"):
        summary += "\n📸 عکس: ✅ ضمیمه شد"
    if data.get("card_number"):
        summary += f"\n💳 کارت: {data['card_number']}"
    if data.get("sheba"):
        summary += f"\n🏦 شبا: {data['sheba']}"
    if data.get("bank_name"):
        summary += f"\n🏛 بانک: {data['bank_name']}"
    await message.answer(summary, reply_markup=confirm_keyboard())
    await state.set_state(ReceivableForm.confirm)

@router.callback_query(ReceivableForm.confirm)
async def receivable_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle receivable confirmation."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        try:
            user = UserRepository.get_or_create(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )
            TransactionRepository.create(
                user_id=user["id"],
                transaction_type="receivable",
                amount=data["amount"],
                party_name=data["party"],
                description=data["description"],
                category=data.get("category"),
                subcategory=data.get("subcategory"),
                due_jalali_date=data["due_date"],
                due_jalali_time=data.get("due_time"),
                photo_path=data.get("photo_path"),
                card_number=data.get("card_number"),
                sheba=data.get("sheba"),
                bank_name=data.get("bank_name"),
                jalali_date=get_jalali_date(),
                jalali_time=get_jalali_time(),
                jalali_full=get_jalali_full()
            )
            logger.info(f"Receivable recorded: {data['amount']} by user {user["telegram_id"]}")
            
            await state.clear()
            await callback.message.edit_text(RECEIVABLE_SAVED, reply_markup=None)
            await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Error saving receivable: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
    
    await safe_callback_answer(callback)

# ==============================
# Debt and Receivable Edit Handlers (Inline Button)
# ==============================

async def _start_edit_by_id(target_id: int, user_id: int, state: FSMContext, edit_form_class, text_prefix: str, callback_or_message):
    """Start edit flow for a debt or receivable by its transaction ID."""
    txn = TransactionRepository.get_by_id( target_id)
        
    if not txn or txn["user_id"] != user_id:
        msg = "⚠️ تراکنشی با این شناسه یافت نشد."
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.answer(msg, show_alert=True)
        else:
            await callback_or_message.answer(msg)
        return
        
    # Check type matches
    expected_type = "debt" if edit_form_class == DebtEditForm else "receivable"
    if txn["transaction_type"] != expected_type:
        msg = f"⚠️ این شناسه مربوط به {'بدهی' if expected_type == 'receivable' else 'طلب'} است."
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.answer(msg, show_alert=True)
        else:
            await callback_or_message.answer(msg)
        return
        
    await state.update_data(
        edit_id=txn["id"],
        amount=txn["amount"],
        party=txn["party_name"] or "",
        description=txn["description"] or "",
        due_date=txn["due_jalali_date"] or "",
        due_time=txn["due_jalali_time"] or "",
        category=txn["category"] or "",
        subcategory=txn["subcategory"] or "",
        photo_path=txn["photo_path"],
        edit_type=expected_type,
    )
        
    # Show current values and field selection
    due_display = txn["due_jalali_date"] or '-'
    if txn["due_jalali_time"]:
        due_display += f" ساعت {txn["due_jalali_time"]}"
    cat_display = txn["category"] or '-'
    if txn["subcategory"]:
        cat_display += f" / {txn["subcategory"]}"
    photo_display = "✅ دارد" if txn["photo_path"] else "❌ ندارد"
    summary = (
        f"✏️ ویرایش {text_prefix} (شناسه: {txn["id"]})\n\n"
        f"🏷 دسته: {cat_display}\n"
        f"💰 مبلغ فعلی: {format_amount(txn["amount"])} تومان\n"
        f"👤 طرف حساب: {txn["party_name"] or '-'}\n"
        f"📝 توضیحات: {txn["description"] or '-'}\n"
        f"📅 سررسید: {due_display}\n"
        f"📸 عکس: {photo_display}\n\n"
        f"فیلدی که می‌خواهید ویرایش کنید را انتخاب کنید:"
    )
        
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(summary, reply_markup=edit_field_keyboard())
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(summary, reply_markup=edit_field_keyboard())
        
    await state.set_state(edit_form_class.edit_id)

# --- Callback: Edit button pressed in list ---

@router.callback_query(F.data.startswith("edit_debt:"))
async def debt_edit_callback(callback: CallbackQuery, state: FSMContext):
    """Handle edit button press in debt list."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
        return
    await _start_edit_by_id(txn_id, user["id"], state, DebtEditForm, "بدهی", callback)

@router.callback_query(F.data.startswith("edit_receivable:"))
async def receivable_edit_callback(callback: CallbackQuery, state: FSMContext):
    """Handle edit button press in receivable list."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
        return
    await _start_edit_by_id(txn_id, user["id"], state, ReceivableEditForm, "طلب", callback)

# --- Callback: Field selection for edit ---

@router.callback_query(F.data.startswith("edit_field:"), DebtEditForm.edit_id)
@router.callback_query(F.data.startswith("edit_field:"), ReceivableEditForm.edit_id)
async def edit_field_selected(callback: CallbackQuery, state: FSMContext):
    """Handle field selection for editing."""
    field = callback.data.split(":")[1]
    data = await state.get_data()
    
    if field == "save":
        # Show confirmation
        due_display = data['due_date'] or '-'
        if data.get('due_time'):
            due_display += f" ساعت {data['due_time']}"
        cat_display = data.get('category') or '-'
        if data.get('subcategory'):
            cat_display += f" / {data['subcategory']}"
        photo_display = "✅ دارد" if data.get('photo_path') else "❌ ندارد"
        text = (
            f"✏️ خلاصه ویرایش:\n\n"
            f"🏷 دسته: {cat_display}\n"
            f"💰 مبلغ: {format_amount(data['amount'])} تومان\n"
            f"👤 طرف حساب: {data['party'] or '-'}\n"
            f"📝 توضیحات: {data['description'] or '-'}\n"
            f"📅 سررسید: {due_display}\n"
            f"📸 عکس: {photo_display}\n\n"
            f"آیا تأیید می‌کنید؟"
        )
        await callback.message.edit_text(text, reply_markup=confirm_keyboard())
        # Determine which confirm state to use
        edit_type = data.get("edit_type", "debt")
        if edit_type == "debt":
            await state.set_state(DebtEditForm.confirm)
        else:
            await state.set_state(ReceivableEditForm.confirm)
        await safe_callback_answer(callback)
        return
    
    # Handle category field - show category keyboard
    if field == "category":
        edit_type = data.get("edit_type", "debt")
        cat_display = data.get('category') or '-'
        if data.get('subcategory'):
            cat_display += f" / {data['subcategory']}"
        prompt = f"🏷 دسته‌بندی فعلی: {cat_display}\n\nدسته جدید را انتخاب کنید:"
        await callback.message.edit_text(prompt, reply_markup=None)
        if edit_type == "debt":
            await callback.message.answer(DEBT_CATEGORY_PROMPT, reply_markup=debt_category_keyboard())
        else:
            await callback.message.answer(RECEIVABLE_CATEGORY_PROMPT, reply_markup=receivable_category_keyboard())
        await safe_callback_answer(callback)
        return
    
    # Handle photo field - show photo management options
    if field == "photo":
        edit_type = data.get("edit_type", "debt")
        has_photo = bool(data.get('photo_path'))
        form_class = DebtEditForm if edit_type == "debt" else ReceivableEditForm
        
        if has_photo:
            prompt = (
                "📸 مدیریت عکس\n\n"
                "عکس فعلی: ✅ موجود\n\n"
                "یک عکس جدید ارسال کنید یا از گزینه‌های زیر استفاده کنید:"
            )
        else:
            prompt = (
                "📸 مدیریت عکس\n\n"
                "عکس فعلی: ❌ ندارد\n\n"
                "یک عکس ارسال کنید یا از گزینه‌های زیر استفاده کنید:"
            )
        
        await callback.message.edit_text(callback.message.text, reply_markup=None)
        await callback.message.answer(prompt, reply_markup=edit_photo_keyboard(has_photo))
        await state.set_state(form_class.photo)
        await safe_callback_answer(callback)
        return
    
    # Set the appropriate state for the selected field
    edit_type = data.get("edit_type", "debt")
    form_class = DebtEditForm if edit_type == "debt" else ReceivableEditForm
    
    due_display = data['due_date'] or '-'
    if data.get('due_time'):
        due_display += f" ساعت {data['due_time']}"
    field_prompts = {
        "amount": f"💰 مبلغ جدید را وارد کنید:\n(مبلغ فعلی: {format_amount(data['amount'])} تومان)\n\nبرای عدم تغییر، عدد 0 را وارد کنید.",
        "party": f"👤 نام طرف حساب جدید را وارد کنید:\n(مقدار فعلی: {data['party'] or '-'})\n\nبرای عدم تغییر، - را وارد کنید.",
        "description": f"📝 توضیحات جدید را وارد کنید:\n(مقدار فعلی: {data['description'] or '-'})\n\nبرای عدم تغییر، - را وارد کنید.",
        "due_date": f"📅 تاریخ سررسید جدید را وارد کنید (فرمت: YYYY/MM/DD):\n(مقدار فعلی: {due_display})\n\nبرای عدم تغییر، - را وارد کنید.\n📅 امروز برای تنظیم سررسید به امروز.",
    }
    
    state_map = {
        "amount": form_class.amount,
        "party": form_class.party,
        "description": form_class.description,
        "due_date": form_class.due_date,
    }
    
    await state.set_state(state_map[field])
    
    # Remove inline keyboard from current message
    await callback.message.edit_text(callback.message.text, reply_markup=None)
    # Send new message with the reply keyboard
    if field == "due_date":
        await callback.message.answer(field_prompts[field], reply_markup=due_date_keyboard())
    else:
        await callback.message.answer(field_prompts[field], reply_markup=cancel_back_menu())
    
    await safe_callback_answer(callback)

# --- Message handlers for each edit field ---

@router.message(DebtEditForm.amount)
@router.message(ReceivableEditForm.amount)
async def edit_amount_handler(message: Message, state: FSMContext):
    """Handle amount input for edit."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    if message.text not in ["0", "0.0"]:
        try:
            amount = float(message.text.replace(",", "").replace("٬", ""))
            if amount <= 0:
                raise ValueError
            await state.update_data(amount=amount)
        except ValueError:
            await message.answer("⚠️ مبلغ وارد شده معتبر نیست. عدد 0 برای عدم تغییر.")
            return
    
    data = await state.get_data()
    await message.answer(
        f"✅ مبلغ ثبت شد.\n\nفیلد بعدی را انتخاب کنید:",
        reply_markup=edit_field_keyboard()
    )
    edit_type = data.get("edit_type", "debt")
    form_class = DebtEditForm if edit_type == "debt" else ReceivableEditForm
    await state.set_state(form_class.edit_id)

@router.message(DebtEditForm.party)
@router.message(ReceivableEditForm.party)
async def edit_party_handler(message: Message, state: FSMContext):
    """Handle party input for edit."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    if message.text not in ["-", "0"]:
        await state.update_data(party=message.text)
    
    data = await state.get_data()
    await message.answer(
        f"✅ طرف حساب ثبت شد.\n\nفیلد بعدی را انتخاب کنید:",
        reply_markup=edit_field_keyboard()
    )
    edit_type = data.get("edit_type", "debt")
    form_class = DebtEditForm if edit_type == "debt" else ReceivableEditForm
    await state.set_state(form_class.edit_id)

@router.message(DebtEditForm.description)
@router.message(ReceivableEditForm.description)
async def edit_description_handler(message: Message, state: FSMContext):
    """Handle description input for edit."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    if message.text not in ["-", "0"]:
        await state.update_data(description=message.text)
    
    data = await state.get_data()
    await message.answer(
        f"✅ توضیحات ثبت شد.\n\nفیلد بعدی را انتخاب کنید:",
        reply_markup=edit_field_keyboard()
    )
    edit_type = data.get("edit_type", "debt")
    form_class = DebtEditForm if edit_type == "debt" else ReceivableEditForm
    await state.set_state(form_class.edit_id)

@router.message(DebtEditForm.due_date)
@router.message(ReceivableEditForm.due_date)
async def edit_due_date_handler(message: Message, state: FSMContext):
    """Handle due date input for edit."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    if message.text == "📅 امروز":
        await state.update_data(due_date=get_jalali_date(), due_time=get_jalali_time())
    elif message.text not in ["-", "0"]:
        if not re.match(r"^\d{4}/\d{2}/\d{2}$", message.text):
            await message.answer(INVALID_DATE)
            return
        await state.update_data(due_date=message.text, due_time=None)
    
    data = await state.get_data()
    await message.answer(
        f"✅ سررسید ثبت شد.\n\nفیلد بعدی را انتخاب کنید:",
        reply_markup=edit_field_keyboard()
    )
    edit_type = data.get("edit_type", "debt")
    form_class = DebtEditForm if edit_type == "debt" else ReceivableEditForm
    await state.set_state(form_class.edit_id)

@router.message(DebtEditForm.photo)
@router.message(ReceivableEditForm.photo)
async def edit_photo_handler(message: Message, state: FSMContext):
    """Handle photo input for edit."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    data = await state.get_data()
    edit_type = data.get("edit_type", "debt")
    form_class = DebtEditForm if edit_type == "debt" else ReceivableEditForm
    
    # Handle "no change" - keep current photo
    if message.text == "⏭️ بدون تغییر":
        await message.answer(
            "✅ عکس بدون تغییر باقی ماند.\n\nفیلد بعدی را انتخاب کنید:",
            reply_markup=edit_field_keyboard()
        )
        await state.set_state(form_class.edit_id)
        return
    
    # Handle "remove photo"
    if message.text == "🗑 حذف عکس":
        # Delete old photo file if exists
        old_photo = data.get('photo_path')
        if old_photo and os.path.exists(old_photo):
            try:
                os.remove(old_photo)
                logger.info(f"Deleted old photo: {old_photo}")
            except Exception as e:
                logger.error(f"Error deleting old photo: {e}")
        
        await state.update_data(photo_path=None)
        await message.answer(
            "✅ عکس حذف شد.\n\nفیلد بعدی را انتخاب کنید:",
            reply_markup=edit_field_keyboard()
        )
        await state.set_state(form_class.edit_id)
        return
    
    # Handle photo upload
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        try:
            # Delete old photo file if exists
            old_photo = data.get('photo_path')
            if old_photo and os.path.exists(old_photo):
                try:
                    os.remove(old_photo)
                    logger.info(f"Deleted old photo: {old_photo}")
                except Exception as e:
                    logger.error(f"Error deleting old photo: {e}")
            
            photo_path = await _save_photo(message.bot, photo, message.from_user.id)
            await state.update_data(photo_path=photo_path)
            await message.answer(
                "✅ عکس جدید ذخیره شد.\n\nفیلد بعدی را انتخاب کنید:",
                reply_markup=edit_field_keyboard()
            )
            await state.set_state(form_class.edit_id)
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            await message.answer("⚠️ خطا در ذخیره عکس. لطفاً دوباره تلاش کنید.")
        return
    
    # Invalid input
    has_photo = bool(data.get('photo_path'))
    await message.answer(
        "📸 لطفاً یک عکس ارسال کنید یا از گزینه‌های موجود استفاده کنید.",
        reply_markup=edit_photo_keyboard(has_photo)
    )

# --- Category edit callbacks ---

@router.callback_query(F.data.startswith("debt_cat:"), DebtEditForm.edit_id)
async def edit_debt_category_selected(callback: CallbackQuery, state: FSMContext):
    """Handle debt category selection during edit."""
    cat = callback.data.split(":", 1)[1]

    if cat == "cancel":
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(
            "فیلد مورد نظر را انتخاب کنید:", reply_markup=edit_field_keyboard()
        )
        await state.set_state(DebtEditForm.edit_id)
        await safe_callback_answer(callback)
        return

    await state.update_data(category=cat)

    subs = DEBT_CATEGORIES.get(cat, [])
    if not subs:
        await state.update_data(subcategory=cat)
        await callback.message.edit_text(
            f"✅ دسته‌بندی ثبت شد: {cat}\n\nفیلد بعدی را انتخاب کنید:",
            reply_markup=edit_field_keyboard()
        )
        await state.set_state(DebtEditForm.edit_id)
    else:
        await callback.message.edit_text(
            f"🏷 دسته: {cat}\n\n{DEBT_SUBCATEGORY_PROMPT}",
            reply_markup=debt_subcategory_keyboard(cat)
        )

    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_sub:"), DebtEditForm.edit_id)
async def edit_debt_subcategory_selected(callback: CallbackQuery, state: FSMContext):
    """Handle debt subcategory selection during edit."""
    sub = callback.data.split(":", 1)[1]

    if sub == "back":
        await callback.message.edit_text(
            DEBT_CATEGORY_PROMPT, reply_markup=debt_category_keyboard()
        )
        await safe_callback_answer(callback)
        return

    data = await state.get_data()
    cat = data.get("category", "")
    await state.update_data(subcategory=sub)

    await callback.message.edit_text(
        f"✅ دسته‌بندی ثبت شد: {cat} / {sub}\n\nفیلد بعدی را انتخاب کنید:",
        reply_markup=edit_field_keyboard()
    )
    await state.set_state(DebtEditForm.edit_id)
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_cat:"), ReceivableEditForm.edit_id)
async def edit_receivable_category_selected(callback: CallbackQuery, state: FSMContext):
    """Handle receivable category selection during edit."""
    cat = callback.data.split(":", 1)[1]

    if cat == "cancel":
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(
            "فیلد مورد نظر را انتخاب کنید:", reply_markup=edit_field_keyboard()
        )
        await state.set_state(ReceivableEditForm.edit_id)
        await safe_callback_answer(callback)
        return

    await state.update_data(category=cat)

    subs = RECEIVABLE_CATEGORIES.get(cat, [])
    if not subs:
        await state.update_data(subcategory=cat)
        await callback.message.edit_text(
            f"✅ دسته‌بندی ثبت شد: {cat}\n\nفیلد بعدی را انتخاب کنید:",
            reply_markup=edit_field_keyboard()
        )
        await state.set_state(ReceivableEditForm.edit_id)
    else:
        await callback.message.edit_text(
            f"🏷 دسته: {cat}\n\n{RECEIVABLE_SUBCATEGORY_PROMPT}",
            reply_markup=receivable_subcategory_keyboard(cat)
        )

    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_sub:"), ReceivableEditForm.edit_id)
async def edit_receivable_subcategory_selected(callback: CallbackQuery, state: FSMContext):
    """Handle receivable subcategory selection during edit."""
    sub = callback.data.split(":", 1)[1]

    if sub == "back":
        await callback.message.edit_text(
            RECEIVABLE_CATEGORY_PROMPT, reply_markup=receivable_category_keyboard()
        )
        await safe_callback_answer(callback)
        return

    data = await state.get_data()
    cat = data.get("category", "")
    await state.update_data(subcategory=sub)

    await callback.message.edit_text(
        f"✅ دسته‌بندی ثبت شد: {cat} / {sub}\n\nفیلد بعدی را انتخاب کنید:",
        reply_markup=edit_field_keyboard()
    )
    await state.set_state(ReceivableEditForm.edit_id)
    await safe_callback_answer(callback)

# --- Confirm edit ---

@router.callback_query(DebtEditForm.confirm)
async def debt_edit_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle debt edit confirmation."""
    await _process_edit_confirm(callback, state, "بدهی")

@router.callback_query(ReceivableEditForm.confirm)
async def receivable_edit_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle receivable edit confirmation."""
    await _process_edit_confirm(callback, state, "طلب")

async def _process_edit_confirm(callback: CallbackQuery, state: FSMContext, text_type: str):
    """Handle edit confirmation and save."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        try:
            user = UserRepository.get_or_create(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )
            
            update_kwargs = {
                'amount': data['amount'],
                'party_name': data['party'],
                'description': data['description'],
                'due_jalali_date': data['due_date'],
                'due_jalali_time': data.get('due_time'),
                'category': data.get('category'),
                'subcategory': data.get('subcategory'),
                'photo_path': data.get('photo_path'),
            }
            
            TransactionRepository.update( data['edit_id'], **update_kwargs)
            logger.info(f"{text_type} updated: {data['edit_id']} by user {user["telegram_id"]}")
            
            await state.clear()
            type_emoji = "📋" if text_type == "بدهی" else "📌"
            await callback.message.edit_text(f"✅ {type_emoji} {text_type} با موفقیت ویرایش شد!", reply_markup=None)
            await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Error updating {text_type}: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
    
    await safe_callback_answer(callback)

# --- Delete handlers ---

@router.callback_query(F.data.startswith("delete_debt:"))
async def debt_delete_callback(callback: CallbackQuery, state: FSMContext):
    """Handle delete button press in debt list."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    await state.update_data(delete_id=txn_id, delete_type="debt")
    await callback.message.edit_text(
        f"⚠️ آیا از حذف این بدهی (شناسه: {txn_id}) اطمینان دارید؟",
        reply_markup=confirm_keyboard()
    )
    await state.set_state(DebtEditForm.delete_confirm)
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("delete_receivable:"))
async def receivable_delete_callback(callback: CallbackQuery, state: FSMContext):
    """Handle delete button press in receivable list."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    await state.update_data(delete_id=txn_id, delete_type="receivable")
    await callback.message.edit_text(
        f"⚠️ آیا از حذف این طلب (شناسه: {txn_id}) اطمینان دارید؟",
        reply_markup=confirm_keyboard()
    )
    await state.set_state(ReceivableEditForm.delete_confirm)
    await safe_callback_answer(callback)

async def _process_delete_confirm(callback: CallbackQuery, state: FSMContext, text_type: str, type_emoji: str):
    """Handle delete confirmation and execute deletion."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        try:
            user = UserRepository.get_or_create(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )
            
            delete_id = data.get("delete_id")
            if delete_id:
                TransactionRepository.delete( delete_id)
                logger.info(f"{text_type} deleted: {delete_id} by user {user["telegram_id"]}")
            
            await state.clear()
            await callback.message.edit_text(f"🗑 {type_emoji} {text_type} با موفقیت حذف شد!", reply_markup=None)
            await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Error deleting {text_type}: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
    
    await safe_callback_answer(callback)

@router.callback_query(DebtEditForm.delete_confirm)
async def debt_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle debt delete confirmation."""
    await _process_delete_confirm(callback, state, "بدهی", "📋")

@router.callback_query(ReceivableEditForm.delete_confirm)
async def receivable_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle receivable delete confirmation."""
    await _process_delete_confirm(callback, state, "طلب", "📌")

# ==============================
# Debt & Receivable Submenus & Filtered Lists
# ==============================

def _group_receivables_by_customer(txns: list) -> list:
    """Group receivable transactions by customer (party_name).

    Returns a sorted list of dicts:
      {
        "party": str,
        "total": float,
        "remaining": float,
        "count": int,
        "active_count": int,
        "settled_count": int,
        "overdue_count": int,
        "txns": list[Transaction]  # sorted newest first
      }
    """
    today = get_jalali_date()
    groups = {}
    for txn in txns:
        key = txn["party_name"] or "-"
        if key not in groups:
            groups[key] = {
                "party": key, "total": 0, "remaining": 0,
                "count": 0, "active_count": 0, "settled_count": 0,
                "overdue_count": 0, "txns": []
            }
        groups[key]["total"] += txn["amount"]
        groups[key]["count"] += 1
        rem = txn["amount"]
        if not txn["is_settled"]:
            rem = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        if txn["is_settled"]:
            groups[key]["settled_count"] += 1
        else:
            groups[key]["active_count"] += 1
            groups[key]["remaining"] += rem
            if txn["due_jalali_date"] and txn["due_jalali_date"] < today:
                groups[key]["overdue_count"] += 1
        groups[key]["txns"].append(txn)

    for g in groups.values():
        g["txns"].sort(key=lambda t: t["id"], reverse=True)

    result = sorted(groups.values(), key=lambda g: (-g["remaining"], -g["count"]))
    return result

def _build_customer_group_text(group: dict) -> str:
    """Build formatted text for a single customer's receivable summary (parent node)."""
    party = group["party"]
    remaining = group["remaining"]
    count = group["count"]
    active = group["active_count"]
    settled = group["settled_count"]
    overdue = group["overdue_count"]

    status_parts = []
    if active > 0:
        status_parts.append(f"⏳ {active} فعال")
    if overdue > 0:
        status_parts.append(f"🔴 {overdue} سررسید گذشته")
    if settled > 0:
        status_parts.append(f"✅ {settled} تسویه")

    text = f"👤 {party}\n"
    text += f"📌 {count} مورد"
    if status_parts:
        text += f" ({' | '.join(status_parts)})"
    if remaining > 0:
        text += f"\n💰 باقی‌مانده: {format_amount(remaining)} تومان"
    else:
        text += f"\n✅ تسویه شده"
    return text

def _build_customer_detail_text(group: dict) -> str:
    """Build detailed chronological view of a customer's receivables (newest first)."""
    party = group["party"]
    txns = group["txns"]
    total = group["total"]
    remaining = group["remaining"]
    count = group["count"]
    active = group["active_count"]
    settled = group["settled_count"]
    overdue = group["overdue_count"]

    text = f"👤 {party}\n"
    text += f"💰 مجموع: {format_amount(total)} تومان\n"
    if remaining > 0:
        text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    text += f"📌 {count} مورد"
    status_parts = []
    if active > 0:
        status_parts.append(f"⏳ {active} فعال")
    if overdue > 0:
        status_parts.append(f"🔴 {overdue} سررسید گذشته")
    if settled > 0:
        status_parts.append(f"✅ {settled} تسویه")
    if status_parts:
        text += f" ({' | '.join(status_parts)})"
    text += "\n——————————"

    for txn in txns:
        if txn["is_settled"]:
            icon = "✅"
        elif txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            if days_left < 0:
                icon = "🔴"
            elif days_left == 0:
                icon = "🟡"
            else:
                icon = "⏳"
        else:
            icon = "⏳"

        text += f"\n\n{icon} #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        if not txn["is_settled"]:
            rem = PaymentRepository.get_remaining( txn["id"], txn["amount"])
            if rem != txn["amount"]:
                text += f"\n   💰 باقی‌مانده: {format_amount(rem)} تومان"
        if txn["category"]:
            cat_str = txn["category"]
            if txn["subcategory"]:
                cat_str += f" / {txn["subcategory"]}"
            text += f"\n   🏷 {cat_str}"
        if txn["description"]:
            text += f"\n   📝 {txn["description"]}"
        if txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            time_str = f" ساعت {txn["due_jalali_time"]}" if txn["due_jalali_time"] else ""
            if txn["is_settled"]:
                text += f"\n   📅 سررسید: {txn["due_jalali_date"]}{time_str}"
            elif days_left < 0:
                text += f"\n   🔴 سررسید: {txn["due_jalali_date"]}{time_str} (منقضی)"
            elif days_left == 0:
                text += f"\n   🟡 سررسید: {txn["due_jalali_date"]}{time_str} (امروز)"
            else:
                text += f"\n   🟢 سررسید: {txn["due_jalali_date"]}{time_str} ({days_left} روز)"
        text += f"\n   📅 ثبت: {txn["jalali_date"]}"

    return text

def _build_txn_list_text(txns: list, txn_type: str, title: str) -> tuple:
    """Build formatted text for a list of debt/receivable transactions.
    
    Returns: (lines, total, total_remaining, remaining_map) or None if empty.
    """
    type_label = "بدهی" if txn_type == "debt" else "طلب"
    type_emoji = "📋" if txn_type == "debt" else "📌"

    if not txns:
        return None

    total = 0
    total_remaining = 0
    lines = []
    remaining_map = {}
    for i, txn in enumerate(txns, 1):
        total += txn["amount"]
        settled = "✅" if txn["is_settled"] else "⏳"

        # Calculate remaining balance
        remaining = txn["amount"]
        if not txn["is_settled"]:
            remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        remaining_map[txn["id"]] = remaining
        if not txn["is_settled"]:
            total_remaining += remaining

        text = f"{type_emoji} {type_label} {i}:\n"
        text += f"🆔 شناسه: {txn["id"]}\n"
        if txn["is_settled"]:
            text += f"{settled} مبلغ: {format_amount(txn["amount"])} تومان\n"
        else:
            text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
            text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
        if txn["category"]:
            cat_str = txn["category"]
            if txn["subcategory"]:
                cat_str += f" / {txn["subcategory"]}"
            text += f"🏷 دسته: {cat_str}\n"
        if txn["party_name"]:
            text += f"👤 طرف حساب: {txn["party_name"]}\n"
        if txn["description"]:
            text += f"📝 توضیحات: {txn["description"]}\n"
        if txn["photo_path"]:
            text += f"📸 عکس: ✅ دارد\n"
        if txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            time_str = f" ساعت {txn["due_jalali_time"]}" if txn["due_jalali_time"] else ""
            if txn["is_settled"]:
                text += f"📅 سررسید: {txn["due_jalali_date"]}{time_str}\n"
            elif days_left < 0:
                text += f"🔴 سررسید: {txn["due_jalali_date"]}{time_str} (منقضی)\n"
            elif days_left == 0:
                text += f"🟡 سررسید: {txn["due_jalali_date"]}{time_str} (امروز)\n"
            else:
                text += f"🟢 سررسید: {txn["due_jalali_date"]}{time_str} ({days_left} روز مانده)\n"
        if txn["card_number"]:
            card_fmt = "-".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
            text += f"💳 کارت: {card_fmt}\n"
        if txn["sheba"]:
            text += f"🏦 شبا: {txn["sheba"]}\n"
        if txn["bank_name"]:
            text += f"🏛 بانک: {normalize_bank_name(txn["bank_name"])}\n"
        text += f"📅 ثبت: {txn["jalali_date"]} ساعت {txn["jalali_time"]}"
        lines.append(text)

    return lines, total, total_remaining, remaining_map

async def _send_filtered_list(message: Message, txns: list, txn_type: str,
                              title: str, empty_msg: str, keyboard_fn):
    """Send a filtered list of debt/receivable transactions."""
    if not txns:
        await message.answer(empty_msg, reply_markup=main_menu())
        return

    result = _build_txn_list_text(txns, txn_type, title)
    lines, total, total_remaining, remaining_map = result

    for i, text in enumerate(lines):
        txn = txns[i]
        rem = remaining_map.get(txn["id"])
        has_pay_info = bool(txn["card_number"] or txn["sheba"] or txn["bank_name"])
        await message.answer(text, reply_markup=keyboard_fn(txn["id"], has_photo=bool(txn["photo_path"]), remaining=rem, has_payment_info=has_pay_info))

    type_label = "بدهی‌ها" if txn_type == "debt" else "طلب‌ها"
    summary = f"——————————\n📊 مجموع {type_label}: {format_amount(total)} تومان"
    if total_remaining > 0 and total_remaining != total:
        summary += f"\n💰 مجموع باقی‌مانده: {format_amount(total_remaining)} تومان"
    await message.answer(summary, reply_markup=main_menu())

# --- Grouped receivable display ---

# In-memory storage for customer groups (keyed by a unique session key)
_RECV_CACHE_MAX = 100
_recv_groups_cache: dict = {}
_recv_groups_lock = asyncio.Lock()

# In-memory storage for debt customer groups (hierarchical navigation)
_debt_groups_cache: dict = {}
_debt_groups_lock = asyncio.Lock()

# In-memory storage for card groups (grouped by customer/name)
_card_groups_cache: dict = {}
_card_groups_lock = asyncio.Lock()

def _evict_cache(cache: dict, max_size: int = _RECV_CACHE_MAX):
    """Evict oldest entries from cache if it exceeds max size."""
    if len(cache) > max_size:
        keys_to_remove = list(cache.keys())[:len(cache) - max_size]
        for k in keys_to_remove:
            del cache[k]

async def _send_grouped_receivable_list(message: Message, txns: list, title: str,
                                        empty_msg: str, cache_key: str = None):
    """Send receivables grouped by customer.

    Main list shows ONLY customers as parent nodes.
    Each customer button opens detail view with individual items.
    """
    if not txns:
        await message.answer(empty_msg, reply_markup=main_menu())
        return

    groups = _group_receivables_by_customer(txns)

    if cache_key:
        async with _recv_groups_lock:
            _recv_groups_cache[cache_key] = {g["party"]: g for g in groups}
            _evict_cache(_recv_groups_cache)

    total_amount = sum(g["total"] for g in groups)
    total_remaining = sum(g["remaining"] for g in groups)
    total_items = sum(g["count"] for g in groups)
    total_customers = len(groups)

    summary = f"📊 {title}\n\n"
    summary += f"💰 مجموع: {format_amount(total_amount)} تومان\n"
    if total_remaining > 0 and total_remaining != total_amount:
        summary += f"💰 باقی‌مانده: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} مورد"

    await message.answer(summary)

    buttons_data = []
    for g in groups:
        if g["remaining"] > 0:
            label = f"👤 {g['party']} | {format_amount(g['remaining'])} تومان ({g['count']} مورد)"
        else:
            label = f"✅ {g['party']} | تسویه شده ({g['count']} مورد)"
        safe_key = g["party"].replace(":", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"recv_detail:{cache_key}:{safe_key}"
        })

    await message.answer(
        "👤 مشتری مورد نظر را انتخاب کنید:",
        reply_markup=customer_receivable_keyboard(buttons_data)
    )

async def _send_settled_customer_list(message: Message, txns: list, title: str,
                                       empty_msg: str, cache_key: str = None):
    """Send settled receivables grouped by customer for the hierarchical view.

    Shows summary and customer buttons. Each customer button triggers
    rs_cust:{cache_key}:{safe_party} to show that customer's settled items.
    Includes partially paid and fully settled receivables.
    """
    if not txns:
        await message.answer(empty_msg, reply_markup=main_menu())
        return

    groups = _group_receivables_by_customer(txns)

    if cache_key:
        async with _recv_groups_lock:
            _recv_groups_cache[cache_key] = {g["party"]: g for g in groups}
            _evict_cache(_recv_groups_cache)

    total_amount = sum(g["total"] for g in groups)
    total_items = sum(g["count"] for g in groups)
    total_customers = len(groups)
    total_remaining = sum(g["remaining"] for g in groups)
    total_paid = total_amount - total_remaining

    summary = f"📊 {title}\n\n"
    summary += f"💰 مجموع طلب: {format_amount(total_amount)} تومان\n"
    summary += f"💰 مجموع دریافتی: {format_amount(total_paid)} تومان\n"
    if total_remaining > 0:
        summary += f"💰 مجموع باقی‌مانده: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} مورد"

    await message.answer(summary)

    buttons_data = []
    for g in groups:
        paid = g["total"] - g["remaining"]
        if g["remaining"] <= 0:
            label = f"🟢 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        elif paid > 0:
            pct = int((paid / g["total"]) * 100) if g["total"] > 0 else 0
            label = f"🟡 {g['party']} | {format_amount(paid)} / {format_amount(g['total'])} تومان ({pct}%) ({g['count']} مورد)"
        else:
            label = f"🔴 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        safe_key = g["party"].replace(":", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"rs_cust:{cache_key}:{safe_key}"
        })

    await message.answer(
        "👤 مشتری مورد نظر را انتخاب کنید:",
        reply_markup=settled_recv_customer_keyboard(buttons_data)
    )

async def _send_settled_debt_list(message: Message, txns: list, title: str,
                                   empty_msg: str, cache_key: str = None):
    """Send settled debts grouped by customer for the hierarchical view.

    Shows summary and customer buttons. Each customer button triggers
    ds_cust:{cache_key}:{safe_party} to show that customer's settled items.
    Includes partially paid and fully settled debts.
    """
    if not txns:
        await message.answer(empty_msg, reply_markup=main_menu())
        return

    groups = _group_receivables_by_customer(txns)

    if cache_key:
        async with _debt_groups_lock:
            _debt_groups_cache[cache_key] = {g["party"]: g for g in groups}
            _evict_cache(_debt_groups_cache)

    total_amount = sum(g["total"] for g in groups)
    total_items = sum(g["count"] for g in groups)
    total_customers = len(groups)
    total_remaining = sum(g["remaining"] for g in groups)
    total_paid = total_amount - total_remaining

    summary = f"📊 {title}\n\n"
    summary += f"💰 مجموع بدهی: {format_amount(total_amount)} تومان\n"
    summary += f"💰 مجموع پرداختی: {format_amount(total_paid)} تومان\n"
    if total_remaining > 0:
        summary += f"💰 مجموع باقی‌مانده: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} مورد"

    await message.answer(summary)

    buttons_data = []
    for g in groups:
        paid = g["total"] - g["remaining"]
        if g["remaining"] <= 0:
            label = f"🟢 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        elif paid > 0:
            pct = int((paid / g["total"]) * 100) if g["total"] > 0 else 0
            label = f"🟡 {g['party']} | {format_amount(paid)} / {format_amount(g['total'])} تومان ({pct}%) ({g['count']} مورد)"
        else:
            label = f"🔴 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        safe_key = g["party"].replace(":", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"ds_cust:{cache_key}:{safe_key}"
        })

    await message.answer(
        "👤 مشتری مورد نظر را انتخاب کنید:",
        reply_markup=settled_debt_customer_keyboard(buttons_data)
    )

async def _send_grouped_customer_pay_list(message: Message, txns: list):
    """Send customers grouped for receive payment selection.

    Shows each customer ONCE with total outstanding, not individual transactions.
    Customer button callback: recv_pay_cust:<cache_key>:<safe_party>
    """
    if not txns:
        await message.answer(RECEIVE_RECV_NO_ACTIVE, reply_markup=main_menu())
        return

    groups = _group_receivables_by_customer(txns)

    cache_key = f"recv_pay_cust_{id(message)}"
    async with _recv_groups_lock:
        _recv_groups_cache[cache_key] = {g["party"]: g for g in groups}
        _evict_cache(_recv_groups_cache)

    active_groups = [g for g in groups if g["remaining"] > 0]
    total_remaining = sum(g["remaining"] for g in active_groups)
    total_customers = len(active_groups)
    total_items = sum(g["count"] for g in active_groups)

    summary = f"📋 مشتریان دارای طلب:\n\n"
    summary += f"💰 مجموع طلب: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} فقره"

    await message.answer(summary)

    buttons_data = []
    for g in active_groups:
        safe_key = g["party"].replace(":", "_")
        label = f"👤 {g['party']} | {format_amount(g['remaining'])} تومان ({g['active_count']} فقره)"
        buttons_data.append({
            "label": label,
            "callback_data": f"recv_pay_cust:{cache_key}:{safe_key}"
        })

    if buttons_data:
        await message.answer(
            "👤 مشتری مورد نظر را برای دریافت طلب انتخاب کنید:",
            reply_markup=customer_receivable_keyboard(buttons_data)
        )

@router.callback_query(F.data.startswith("recv_pay_cust:"))
async def recv_pay_cust_handler(callback: CallbackQuery, state: FSMContext):
    """Handle customer selection — skip individual txn selection, go directly to payment flow."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    active_txns = [t for t in group["txns"] if not t["is_settled"]]
    if not active_txns:
        await safe_callback_answer(callback, "⚠️ طلب فعالی برای این مشتری وجود ندارد.", show_alert=True)
        return

    total_remaining = 0
    for txn in active_txns:
        rem = PaymentRepository.get_remaining( txn["id"], txn["amount"])
        total_remaining += rem

    await state.update_data(
        payment_type="receivable",
        customer_party=group["party"],
        customer_cache_key=cache_key,
        customer_safe_party=safe_party,
        customer_total_remaining=total_remaining,
        customer_txn_ids=[t["id"] for t in active_txns]
    )

    text = f"💵 دریافت طلب\n\n"
    text += f"👤 مشتری: {group['party']}\n"
    text += f"💰 کل طلب: {format_amount(total_remaining)} تومان\n\n"
    text += f"━━━━━━━━━━━━━━━━━━\n\n"
    text += f"نوع دریافت را انتخاب کنید:\n"
    text += f"├── 💰 کامل ({format_amount(total_remaining)})\n"
    text += f"└── ✂️ جزئی (ورود مبلغ)"

    await callback.message.answer(text, reply_markup=payment_type_keyboard())
    await state.set_state(PaymentForm.payment_type)
    await safe_callback_answer(callback)

async def _send_grouped_customer_debt_list(message: Message, txns: list):
    """Send customers grouped for pay debt selection.

    Shows each customer ONCE with total outstanding, not individual transactions.
    Customer button callback: debt_pay_cust:<cache_key>:<safe_party>
    """
    if not txns:
        await message.answer(PAY_DEBT_NO_ACTIVE, reply_markup=main_menu())
        return

    groups = _group_receivables_by_customer(txns)

    cache_key = f"debt_pay_cust_{id(message)}"
    async with _recv_groups_lock:
        _recv_groups_cache[cache_key] = {g["party"]: g for g in groups}
        _evict_cache(_recv_groups_cache)

    active_groups = [g for g in groups if g["remaining"] > 0]
    total_remaining = sum(g["remaining"] for g in active_groups)
    total_customers = len(active_groups)
    total_items = sum(g["count"] for g in active_groups)

    summary = f"📋 مشتریان دارای بدهی:\n\n"
    summary += f"💰 مجموع بدهی: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} فقره"

    await message.answer(summary)

    buttons_data = []
    for g in active_groups:
        safe_key = g["party"].replace(":", "_")
        label = f"👤 {g['party']} | {format_amount(g['remaining'])} تومان ({g['active_count']} فقره)"
        buttons_data.append({
            "label": label,
            "callback_data": f"debt_pay_cust:{cache_key}:{safe_key}"
        })

    if buttons_data:
        await message.answer(
            "👤 مشتری مورد نظر را برای پرداخت بدهی انتخاب کنید:",
            reply_markup=customer_receivable_keyboard(buttons_data)
        )

@router.callback_query(F.data.startswith("debt_pay_cust:"))
async def debt_pay_cust_handler(callback: CallbackQuery, state: FSMContext):
    """Handle customer selection for pay debt — go directly to payment flow."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    active_txns = [t for t in group["txns"] if not t["is_settled"]]
    if not active_txns:
        await safe_callback_answer(callback, "⚠️ بدهی فعالی برای این مشتری وجود ندارد.", show_alert=True)
        return

    total_remaining = 0
    for txn in active_txns:
        rem = PaymentRepository.get_remaining( txn["id"], txn["amount"])
        total_remaining += rem

    await state.update_data(
        payment_type="debt",
        customer_party=group["party"],
        customer_cache_key=cache_key,
        customer_safe_party=safe_party,
        customer_total_remaining=total_remaining,
        customer_txn_ids=[t["id"] for t in active_txns]
    )

    text = f"💳 پرداخت بدهی\n\n"
    text += f"👤 مشتری: {group['party']}\n"
    text += f"💰 کل بدهی: {format_amount(total_remaining)} تومان\n\n"
    text += f"━━━━━━━━━━━━━━━━━━\n\n"
    text += f"نوع پرداخت را انتخاب کنید:\n"
    text += f"├── 💰 کامل ({format_amount(total_remaining)})\n"
    text += f"└── ✂️ جزئی (ورود مبلغ)"

    await callback.message.answer(text, reply_markup=payment_type_keyboard())
    await state.set_state(PaymentForm.payment_type)
    await safe_callback_answer(callback)

# --- Grouped debt display for "All Debts" ---

async def _send_grouped_debt_list(message: Message, txns: list, title: str,
                                   empty_msg: str, cache_key: str = None):
    """Send debts grouped by customer for hierarchical navigation.

    Main list shows ONLY customers as parent nodes.
    Each customer button opens detail view with individual items.
    Follows same pattern as _send_grouped_receivable_list.
    """
    if not txns:
        await message.answer(empty_msg, reply_markup=main_menu())
        return

    groups = _group_receivables_by_customer(txns)

    if cache_key:
        async with _debt_groups_lock:
            _debt_groups_cache[cache_key] = {g["party"]: g for g in groups}
            _evict_cache(_debt_groups_cache)

    total_amount = sum(g["total"] for g in groups)
    total_remaining = sum(g["remaining"] for g in groups)
    total_items = sum(g["count"] for g in groups)
    total_customers = len(groups)

    summary = f"📊 {title}\n\n"
    summary += f"💰 مجموع: {format_amount(total_amount)} تومان\n"
    if total_remaining > 0 and total_remaining != total_amount:
        summary += f"💰 باقی‌مانده: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} مورد"

    await message.answer(summary)

    buttons_data = []
    for g in groups:
        if g["remaining"] > 0:
            label = f"👤 {g['party']} | {format_amount(g['remaining'])} تومان ({g['count']} مورد)"
        else:
            label = f"✅ {g['party']} | تسویه شده ({g['count']} مورد)"
        safe_key = g["party"].replace(":", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"debt_all_cust:{cache_key}:{safe_key}"
        })

    await message.answer(
        "👤 مشتری مورد نظر را انتخاب کنید:",
        reply_markup=debt_customer_keyboard(buttons_data)
    )

# --- Debt submenu ---

@router.message(F.text == "💳 بدهی‌ها")
async def debt_menu(message: Message):
    """Show debt submenu."""
    await message.answer(DEBT_MENU_TITLE, reply_markup=debt_submenu())

@router.callback_query(F.data == "debt_active")
async def debt_active_list(callback: CallbackQuery):
    """Level 1: Show active debts grouped by customer overview."""
    try:
        await safe_delete(callback.message)
    except Exception:
        pass
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_active( user["id"], "debt")
        if not txns:
            await callback.message.answer(DEBT_ACTIVE_EMPTY, reply_markup=main_menu())
            await safe_callback_answer(callback)
            return

        groups = _group_receivables_by_customer(txns)
        cache_key = f"debt_active_{user["id"]}"
        async with _debt_groups_lock:
            _debt_groups_cache[cache_key] = {g["party"]: g for g in groups}
            _evict_cache(_debt_groups_cache)

        total_amount = sum(g["total"] for g in groups)
        total_remaining = sum(g["remaining"] for g in groups)
        total_items = sum(g["count"] for g in groups)
        total_customers = len(groups)

        text = f"💳 {DEBT_ACTIVE}\n\n"
        text += "📊 خلاصه کلی\n"
        text += f"• تعداد مشتریان: {total_customers}\n"
        text += f"• تعداد بدهی‌ها: {total_items}\n"
        text += f"• مجموع بدهی‌ها: {format_amount(total_amount)} تومان\n"
        text += f"• مجموع باقی‌مانده: {format_amount(total_remaining)} تومان"
        text += "\n\n────────────────────"

        for g in groups:
            text += f"\n\n👤 {g['party']}\n"
            text += f"• تعداد بدهی‌ها: {g['count']}\n"
            text += f"• مجموع: {format_amount(g['total'])} تومان\n"
            if g['remaining'] > 0:
                text += f"• باقی‌مانده: {format_amount(g['remaining'])} تومان"
            else:
                text += "• ✅ تسویه شده"

        buttons_data = []
        for g in groups:
            safe_key = g["party"].replace(":", "_")
            buttons_data.append({
                "label": f"▶ مشاهده بدهی‌های {g['party']}",
                "callback_data": f"debt_cust_detail:{cache_key}:{safe_key}"
            })

        await callback.message.answer(
            text,
            reply_markup=debt_customer_keyboard(buttons_data)
        )
    except Exception as e:
        logger.error(f"Error in debt_active_list: {e}", exc_info=True)
        try:
            await callback.message.answer("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.", reply_markup=main_menu())
        except Exception:
            pass
    await safe_callback_answer(callback)

@router.callback_query(F.data == "debt_overdue")
async def debt_overdue_list(callback: CallbackQuery):
    """Show overdue debts grouped by customer."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    today = get_jalali_date()
    txns = TransactionRepository.get_overdue( user["id"], "debt", today)
    cache_key = f"debt_overdue_{user["id"]}"
    await _send_grouped_debt_list(
        callback.message, txns, DEBT_OVERDUE,
        DEBT_OVERDUE_EMPTY, cache_key
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "debt_due_today")
async def debt_due_today_list(callback: CallbackQuery):
    """Show debts due today grouped by customer."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    today = get_jalali_date()
    txns = TransactionRepository.get_due_today( user["id"], "debt", today)
    cache_key = f"debt_today_{user["id"]}"
    await _send_grouped_debt_list(
        callback.message, txns, DEBT_DUE_TODAY,
        DEBT_DUE_TODAY_EMPTY, cache_key
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "debt_due_week")
async def debt_due_week_list(callback: CallbackQuery):
    """Show debts due this week grouped by customer."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    today = get_jalali_date()
    week_end = get_week_end_jalali()
    txns = TransactionRepository.get_due_this_week( user["id"], "debt", today, week_end)
    cache_key = f"debt_week_{user["id"]}"
    await _send_grouped_debt_list(
        callback.message, txns, DEBT_DUE_WEEK,
        DEBT_DUE_WEEK_EMPTY, cache_key
    )
    await safe_callback_answer(callback)

# --- Debt category-filtered lists ---

def _filter_by_category(txns: list, category: str = None, subcategory: str = None) -> list:
    """Filter transactions by category and/or subcategory."""
    if not category and not subcategory:
        return txns
    filtered = []
    for txn in txns:
        if category and txn["category"] != category:
            continue
        if subcategory and txn["subcategory"] != subcategory:
            continue
        filtered.append(txn)
    return filtered

@router.callback_query(F.data == "debt_all_cat")
async def debt_all_cat_menu(callback: CallbackQuery):
    """Show category filter for all debts."""
    await callback.message.edit_text(
        "📋 همه بدهی‌ها\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=debt_category_filter_keyboard("debt_all")
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_all_cat:"))
async def debt_all_cat_selected(callback: CallbackQuery):
    """Handle category selection for all debts."""
    category = callback.data.split(":", 1)[1]

    if category == "back":
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    if category == "all":
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_by_user(user["id"], transaction_type="debt", limit=1000)
        await safe_delete(callback.message)
        cache_key = f"debt_all_{user["id"]}"
        await _send_grouped_debt_list(
            callback.message, txns, DEBT_ALL,
            DEBT_EMPTY, cache_key
        )
        await safe_callback_answer(callback)
        return

    subs = DEBT_CATEGORIES.get(category, [])
    if not subs:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_by_user(user["id"], transaction_type="debt", limit=1000)
        filtered = _filter_by_category(txns, category=category)
        await safe_delete(callback.message)
        cache_key = f"debt_all_{user["id"]}_{category}"
        await _send_grouped_debt_list(
            callback.message, filtered, f"{DEBT_ALL} ({category})",
            DEBT_EMPTY, cache_key
        )
        await safe_callback_answer(callback)
        return

    await callback.message.edit_text(
        f"📋 همه بدهی‌ها ({category})\n\nزیرمجموعه را انتخاب کنید:",
        reply_markup=debt_subcategory_filter_keyboard("debt_all", category)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_all_sub:"))
async def debt_all_sub_selected(callback: CallbackQuery):
    """Handle subcategory selection for all debts."""
    subcategory = callback.data.split(":", 1)[1]

    if subcategory == "back":
        await callback.message.edit_text(
            "📋 همه بدهی‌ها\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=debt_category_filter_keyboard("debt_all")
        )
        await safe_callback_answer(callback)
        return

    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txns = TransactionRepository.get_by_user(user["id"], transaction_type="debt", limit=1000)

    if subcategory != "all":
        parent_cat = None
        for cat, subs in DEBT_CATEGORIES.items():
            if subcategory in subs:
                parent_cat = cat
                break
        txns = _filter_by_category(txns, category=parent_cat, subcategory=subcategory)

    await safe_delete(callback.message)
    title = f"{DEBT_ALL} ({subcategory})" if subcategory != "all" else DEBT_ALL
    cache_key = f"debt_all_{user["id"]}_{subcategory}"
    await _send_grouped_debt_list(
        callback.message, txns, title,
        DEBT_EMPTY, cache_key
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "debt_settled_cat")
async def debt_settled_cat_menu(callback: CallbackQuery):
    """Show category filter for settled debts."""
    await callback.message.edit_text(
        "🟢 تسویه شده\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=debt_category_filter_keyboard("debt_settled")
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_settled_cat:"))
async def debt_settled_cat_selected(callback: CallbackQuery):
    """Handle category selection for settled debts."""
    category = callback.data.split(":", 1)[1]

    if category == "back":
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    if category == "all":
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_with_payments( user["id"], "debt")
        await safe_delete(callback.message)
        cache_key = f"debt_settled_{user["id"]}"
        await _send_settled_debt_list(callback.message, txns, DEBT_SETTLED, DEBT_SETTLED_EMPTY, cache_key)
        await safe_callback_answer(callback)
        return

    subs = DEBT_CATEGORIES.get(category, [])
    if not subs:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_with_payments( user["id"], "debt")
        filtered = _filter_by_category(txns, category=category)
        await safe_delete(callback.message)
        cache_key = f"debt_settled_{user["id"]}_{category}"
        await _send_settled_debt_list(callback.message, filtered, f"{DEBT_SETTLED} ({category})", DEBT_SETTLED_EMPTY, cache_key)
        await safe_callback_answer(callback)
        return

    await callback.message.edit_text(
        f"🟢 تسویه شده ({category})\n\nزیرمجموعه را انتخاب کنید:",
        reply_markup=debt_subcategory_filter_keyboard("debt_settled", category)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_settled_sub:"))
async def debt_settled_sub_selected(callback: CallbackQuery):
    """Handle subcategory selection for settled debts."""
    subcategory = callback.data.split(":", 1)[1]

    if subcategory == "back":
        await callback.message.edit_text(
            "🟢 تسویه شده\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=debt_category_filter_keyboard("debt_settled")
        )
        await safe_callback_answer(callback)
        return

    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txns = TransactionRepository.get_with_payments( user["id"], "debt")

    if subcategory != "all":
        parent_cat = None
        for cat, subs in DEBT_CATEGORIES.items():
            if subcategory in subs:
                parent_cat = cat
                break
        txns = _filter_by_category(txns, category=parent_cat, subcategory=subcategory)

    await safe_delete(callback.message)
    title = f"{DEBT_SETTLED} ({subcategory})" if subcategory != "all" else DEBT_SETTLED
    cache_key = f"debt_settled_{user["id"]}_{subcategory}"
    await _send_settled_debt_list(callback.message, txns, title, DEBT_SETTLED_EMPTY, cache_key)
    await safe_callback_answer(callback)

@router.callback_query(F.data == "debt_pay_cat")
async def debt_pay_cat_menu(callback: CallbackQuery):
    """Show category filter for pay debt."""
    await callback.message.edit_text(
        "💳 پرداخت بدهی\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=debt_category_filter_keyboard("debt_pay")
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_pay_cat:"))
async def debt_pay_cat_selected(callback: CallbackQuery, state: FSMContext):
    """Handle category selection for pay debt."""
    category = callback.data.split(":", 1)[1]

    if category == "back":
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    if category == "all":
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_active( user["id"], "debt")
        if not txns:
            await callback.message.edit_text(PAY_DEBT_NO_ACTIVE, reply_markup=debt_submenu())
            await safe_callback_answer(callback)
            return

        await _send_grouped_customer_debt_list(
            callback.message, txns
        )
        await safe_callback_answer(callback)
        return

    subs = DEBT_CATEGORIES.get(category, [])
    if not subs:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_active( user["id"], "debt")
        filtered = _filter_by_category(txns, category=category)
        if not filtered:
            await callback.message.edit_text(
                f"{PAY_DEBT_NO_ACTIVE}\n\nدسته: {category}",
                reply_markup=debt_submenu()
            )
            await safe_callback_answer(callback)
            return

        await _send_grouped_customer_debt_list(
            callback.message, filtered
        )
        await safe_callback_answer(callback)
        return

    await callback.message.edit_text(
        f"💳 پرداخت بدهی ({category})\n\nزیرمجموعه را انتخاب کنید:",
        reply_markup=debt_subcategory_filter_keyboard("debt_pay", category)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_pay_sub:"))
async def debt_pay_sub_selected(callback: CallbackQuery, state: FSMContext):
    """Handle subcategory selection for pay debt."""
    subcategory = callback.data.split(":", 1)[1]

    if subcategory == "back":
        await callback.message.edit_text(
            "💳 پرداخت بدهی\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=debt_category_filter_keyboard("debt_pay")
        )
        await safe_callback_answer(callback)
        return

    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txns = TransactionRepository.get_active( user["id"], "debt")

    if subcategory != "all":
        parent_cat = None
        for cat, subs in DEBT_CATEGORIES.items():
            if subcategory in subs:
                parent_cat = cat
                break
        txns = _filter_by_category(txns, category=parent_cat, subcategory=subcategory)

    if not txns:
        label = subcategory if subcategory != "all" else ""
        await callback.message.edit_text(
            f"{PAY_DEBT_NO_ACTIVE}\n\n{label}",
            reply_markup=debt_submenu()
        )
        await safe_callback_answer(callback)
        return

    await _send_grouped_customer_debt_list(
        callback.message, txns
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "debt_reports")
async def debt_reports(callback: CallbackQuery):
    """Show debt summary report."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id(callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return

    all_debts = TransactionRepository.get_by_user(user["id"], transaction_type="debt", limit=1000)
    today = get_jalali_date()

    total = len(all_debts)
    total_amount = sum(t["amount"] for t in all_debts)

    active = [t for t in all_debts if not t["is_settled"]]
    active_count = len(active)
    active_amount = sum(t["amount"] for t in active)

    settled = [t for t in all_debts if t["is_settled"]]
    settled_count = len(settled)
    settled_amount = sum(t["amount"] for t in settled)

    overdue = [t for t in active if t["due_jalali_date"] and t["due_jalali_date"] < today]
    overdue_count = len(overdue)
    overdue_amount = sum(t["amount"] for t in overdue)

    due_today = [t for t in active if t["due_jalali_date"] == today]
    due_today_count = len(due_today)

    # Calculate additional metrics
    settlement_rate = (settled_count / total * 100) if total > 0 else 0
    avg_debt = (total_amount / total) if total > 0 else 0

    report = DEBT_REPORT_TITLE.format(
        total=total,
        total_amount=format_amount(total_amount),
        active=active_count,
        active_amount=format_amount(active_amount),
        settled=settled_count,
        settled_amount=format_amount(settled_amount),
        overdue=overdue_count,
        overdue_amount=format_amount(overdue_amount),
        due_today=due_today_count,
        settlement_rate=f"{settlement_rate:.1f}",
        avg_debt=format_amount(avg_debt)
    )

    await callback.message.answer(report, reply_markup=debt_submenu())
    await safe_callback_answer(callback)

# --- Debt hierarchical navigation (Level 2 & 3) ---

@router.callback_query(F.data.startswith("debt_cust_detail:"))
async def debt_customer_detail(callback: CallbackQuery):
    """Level 2: Show debts for a selected customer."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _debt_groups_lock:
        cached = _debt_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    party = group["party"]
    txns = group["txns"]
    active_txns = [t for t in txns if not t["is_settled"]]

    text = f"💳 {party}\n\n"
    text += f"📊 خلاصه مشتری\n"
    text += f"• تعداد بدهی‌ها: {group['count']}\n"
    text += f"• مجموع: {format_amount(group['total'])} تومان\n"
    if group['remaining'] > 0:
        text += f"• باقی‌مانده: {format_amount(group['remaining'])} تومان"
    text += "\n────────────────────"

    await callback.message.edit_text(text)

    txns_data = []
    for txn in active_txns:
        due_emoji = ""
        if txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            if days_left < 0:
                due_emoji = "🔴"
            elif days_left == 0:
                due_emoji = "🟡"
            else:
                due_emoji = "🟢"
        label = f"📋 #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        if due_emoji:
            label = f"{due_emoji} #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        txns_data.append({
            "label": label,
            "callback_data": f"debt_item_detail:{cache_key}:{safe_party}:{txn["id"]}"
        })

    await callback.message.answer(
        DEBT_SELECT_DEBT,
        reply_markup=debt_customer_debts_keyboard(txns_data)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_all_cust:"))
async def debt_all_customer_detail(callback: CallbackQuery):
    """Level 2: Show all debts for a selected customer (from All Debts view)."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _debt_groups_lock:
        cached = _debt_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    party = group["party"]
    txns = group["txns"]

    text = f"📋 {party}\n\n"
    text += f"📊 خلاصه مشتری\n"
    text += f"• تعداد بدهی‌ها: {group['count']}\n"
    text += f"• مجموع: {format_amount(group['total'])} تومان\n"
    if group['remaining'] > 0:
        text += f"• باقی‌مانده: {format_amount(group['remaining'])} تومان"
    text += "\n────────────────────"

    await callback.message.edit_text(text)

    txns_data = []
    for txn in txns:
        # Determine status emoji
        if txn["is_settled"]:
            due_emoji = "✅"
        elif txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            if days_left < 0:
                due_emoji = "🔴"
            elif days_left == 0:
                due_emoji = "🟡"
            else:
                due_emoji = "🟢"
        else:
            due_emoji = "⏳"

        # Calculate remaining for display
        remaining = txn["amount"]
        if not txn["is_settled"]:
            remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])

        if txn["is_settled"]:
            label = f"✅ #{txn["id"]} | {format_amount(txn["amount"])} تومان (تسویه)"
        elif remaining != txn["amount"]:
            label = f"{due_emoji} #{txn["id"]} | {format_amount(remaining)}/{format_amount(txn["amount"])} تومان"
        else:
            label = f"{due_emoji} #{txn["id"]} | {format_amount(txn["amount"])} تومان"

        txns_data.append({
            "label": label,
            "callback_data": f"debt_item_detail:{cache_key}:{safe_party}:{txn["id"]}"
        })

    # Determine back callback based on cache key prefix
    back_callback = "debt_group_back"
    if cache_key.startswith("debt_all_"):
        back_callback = f"debt_all_back:{cache_key}"

    await callback.message.answer(
        "📋 بدهی مورد نظر را انتخاب کنید:",
        reply_markup=debt_customer_debts_keyboard(txns_data, back_callback)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_all_back:"))
async def debt_all_back_handler(callback: CallbackQuery):
    """Navigate back from Level 2 (customer debt list) to Level 1 (customer list) for All Debts."""
    cache_key = callback.data.split(":", 1)[1]

    async with _debt_groups_lock:
        cached = _debt_groups_cache.get(cache_key)
    if not cached:
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    # Rebuild customer list from cache
    groups = list(cached.values())
    total_amount = sum(g["total"] for g in groups)
    total_remaining = sum(g["remaining"] for g in groups)
    total_items = sum(g["count"] for g in groups)
    total_customers = len(groups)

    # Determine title from cache key
    title = DEBT_ALL
    if cache_key.startswith("debt_all_"):
        suffix = cache_key[len("debt_all_"):]
        # Remove user ID prefix (first segment before _ or end)
        parts = suffix.split("_", 1)
        if len(parts) > 1:
            filter_part = parts[1]
            title = f"{DEBT_ALL} ({filter_part})"

    summary = f"📊 {title}\n\n"
    summary += f"💰 مجموع: {format_amount(total_amount)} تومان\n"
    if total_remaining > 0 and total_remaining != total_amount:
        summary += f"💰 باقی‌مانده: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} مورد"

    await callback.message.edit_text(summary)

    buttons_data = []
    for g in groups:
        if g["remaining"] > 0:
            label = f"👤 {g['party']} | {format_amount(g['remaining'])} تومان ({g['count']} مورد)"
        else:
            label = f"✅ {g['party']} | تسویه شده ({g['count']} مورد)"
        safe_key = g["party"].replace(":", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"debt_all_cust:{cache_key}:{safe_key}"
        })

    await callback.message.answer(
        "👤 مشتری مورد نظر را انتخاب کنید:",
        reply_markup=debt_customer_keyboard(buttons_data)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_item_detail:"))
async def debt_item_detail(callback: CallbackQuery):
    """Level 3: Show full details for a specific debt."""
    parts = callback.data.split(":", 3)
    if len(parts) < 4:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]
    try:
        txn_id = int(parts[3])
    except ValueError:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    txn = TransactionRepository.get_by_id( txn_id)
    if not txn:
        await safe_callback_answer(callback, "⚠️ بدهی یافت نشد.", show_alert=True)
        return

    remaining = txn["amount"]
    if not txn["is_settled"]:
        remaining = PaymentRepository.get_remaining( txn_id, txn["amount"])

    text = f"📋 جزئیات بدهی\n\n"
    text += f"🆔 شناسه: {txn["id"]}\n"
    text += f"👤 طرف حساب: {txn["party_name"] or '-'}\n"
    cat_str = txn["category"] or "-"
    if txn["subcategory"]:
        cat_str += f" / {txn["subcategory"]}"
    text += f"🏷 دسته: {cat_str}\n"
    text += f"🏢 نوع: {txn["category"] or '-'}\n"
    text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
    text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    if txn["description"]:
        text += f"📝 توضیحات: {txn["description"]}\n"
    if txn["due_jalali_date"]:
        days_left = get_days_until(txn["due_jalali_date"])
        time_str = f" ساعت {txn["due_jalali_time"]}" if txn["due_jalali_time"] else ""
        if txn["is_settled"]:
            text += f"📅 سررسید: {txn["due_jalali_date"]}{time_str}\n"
        elif days_left < 0:
            text += f"🔴 سررسید: {txn["due_jalali_date"]}{time_str} (منقضی)\n"
        elif days_left == 0:
            text += f"🟡 سررسید: {txn["due_jalali_date"]}{time_str} (امروز)\n"
        else:
            text += f"🟢 سررسید: {txn["due_jalali_date"]}{time_str} ({days_left} روز)\n"
    if txn["card_number"]:
        card_fmt = "-".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
        text += f"💳 کارت: {card_fmt}\n"
    if txn["sheba"]:
        text += f"🏦 شبا: {txn["sheba"]}\n"
    if txn["bank_name"]:
        text += f"🏛 بانک: {normalize_bank_name(txn["bank_name"])}\n"
    text += f"📅 ثبت: {txn["jalali_date"]} ساعت {txn["jalali_time"]}"

    # Check for payment receipt photos
    payments = PaymentRepository.get_by_transaction(txn["id"])
    has_payment_photo = any(p["photo_path"] for p in payments) if payments else False

    has_photo = bool(txn["photo_path"])
    has_pay_info = bool(txn["card_number"] or txn["sheba"] or txn["bank_name"])

    # Add photo/attachment info
    if has_photo:
        text += f"📸 عکس: ✅ دارد\n"
    if has_payment_photo:
        text += f"📸 رسید پرداخت: ✅ دارد\n"

    # Payment details from payments table
    if payments:
        total_paid = sum(p["amount"] for p in payments)
        text += f"\n📊 سوابق پرداخت ({len(payments)} فقره):\n"
        for p in payments:
            text += f"  💰 {format_amount(p['amount'])} تومان"
            text += f" | {p['jalali_date']} ساعت {p['jalali_time']}"
            if p["description"]:
                text += f" | {p['description']}"
            if p["photo_path"]:
                text += f" | 📸 رسید"
            text += "\n"

    kb = debt_detail_keyboard(txn["id"], cache_key, safe_party, has_photo, remaining, has_pay_info, has_payment_photo)
    await callback.message.edit_text(text, reply_markup=kb)
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_detail_back:"))
async def debt_detail_back_handler(callback: CallbackQuery):
    """Navigate back from Level 3 (debt details) to Level 2 (customer debt list)."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _debt_groups_lock:
        cached = _debt_groups_cache.get(cache_key)
    if not cached:
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    party = group["party"]
    txns = group["txns"]

    # Determine if this is "All Debts" view or "Active" view
    is_all_debts = cache_key.startswith("debt_all_")

    if is_all_debts:
        # Show all debts (active + settled)
        text = f"📋 {party}\n\n"
        text += f"📊 خلاصه مشتری\n"
        text += f"• تعداد بدهی‌ها: {group['count']}\n"
        text += f"• مجموع: {format_amount(group['total'])} تومان\n"
        if group['remaining'] > 0:
            text += f"• باقی‌مانده: {format_amount(group['remaining'])} تومان"
        text += "\n────────────────────"
    else:
        # Show only active debts
        active_txns = [t for t in txns if not t["is_settled"]]
        text = f"💳 {party}\n\n"
        text += f"📊 خلاصه مشتری\n"
        text += f"• تعداد بدهی‌ها: {group['count']}\n"
        text += f"• مجموع: {format_amount(group['total'])} تومان\n"
        if group['remaining'] > 0:
            text += f"• باقی‌مانده: {format_amount(group['remaining'])} تومان"
        text += "\n────────────────────"

    txns_data = []
    display_txns = txns if is_all_debts else [t for t in txns if not t["is_settled"]]
    for txn in display_txns:
        # Determine status emoji
        if txn["is_settled"]:
            due_emoji = "✅"
        elif txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            if days_left < 0:
                due_emoji = "🔴"
            elif days_left == 0:
                due_emoji = "🟡"
            else:
                due_emoji = "🟢"
        else:
            due_emoji = "⏳"

        if is_all_debts:
            # Calculate remaining for display
            remaining = txn["amount"]
            if not txn["is_settled"]:
                remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])

            if txn["is_settled"]:
                label = f"✅ #{txn["id"]} | {format_amount(txn["amount"])} تومان (تسویه)"
            elif remaining != txn["amount"]:
                label = f"{due_emoji} #{txn["id"]} | {format_amount(remaining)}/{format_amount(txn["amount"])} تومان"
            else:
                label = f"{due_emoji} #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        else:
            label = f"{due_emoji} #{txn["id"]} | {format_amount(txn["amount"])} تومان"

        txns_data.append({
            "label": label,
            "callback_data": f"debt_item_detail:{cache_key}:{safe_party}:{txn["id"]}"
        })

    # Determine back callback
    back_callback = "debt_group_back"
    if is_all_debts:
        back_callback = f"debt_all_back:{cache_key}"

    await callback.message.edit_text(text)
    await callback.message.answer(
        DEBT_SELECT_DEBT,
        reply_markup=debt_customer_debts_keyboard(txns_data, back_callback)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "debt_group_back")
async def debt_group_back(callback: CallbackQuery):
    """Navigate back to Level 1 (customer overview) or debt submenu."""
    await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("debt_payment_history:"))
async def debt_payment_history(callback: CallbackQuery):
    """Show payment history for a debt."""
    try:
        txn_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    payments = PaymentRepository.get_by_transaction( txn_id)
    if not payments:
        await safe_callback_answer(callback, DEBT_PAYMENT_HISTORY_EMPTY, show_alert=True)
        return

    text = f"{DEBT_PAYMENT_HISTORY_TITLE} - بدهی #{txn_id}\n\n"
    total_paid = 0
    for p in payments:
        total_paid += p["amount"]
        text += f"💰 {format_amount(p['amount'])} تومان\n"
        text += f"📅 {p['jalali_date']} ساعت {p['jalali_time']}\n"
        if p["description"]:
            text += f"📝 {p['description']}\n"
        if p["photo_path"]:
            text += f"📸 رسید: ✅ دارد\n"
        text += "──────────\n"
    text += f"\n💰 مجموع پرداختی: {format_amount(total_paid)} تومان"

    await callback.message.answer(text)
    await safe_callback_answer(callback)

# --- Receivable submenu ---

@router.message(F.text == "💵 طلب‌ها")
async def receivable_menu(message: Message):
    """Show receivable submenu."""
    await message.answer(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())

@router.callback_query(F.data == "receivable_active")
async def receivable_active_list(callback: CallbackQuery):
    """Level 1: Show active receivables grouped by customer overview."""
    try:
        await safe_delete(callback.message)
    except Exception:
        pass
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_active( user["id"], "receivable")
        if not txns:
            await callback.message.answer(RECEIVABLE_ACTIVE_EMPTY, reply_markup=main_menu())
            await safe_callback_answer(callback)
            return

        groups = _group_receivables_by_customer(txns)
        cache_key = f"recv_active_{user["id"]}"
        async with _recv_groups_lock:
            _recv_groups_cache[cache_key] = {g["party"]: g for g in groups}
            _evict_cache(_recv_groups_cache)

        total_amount = sum(g["total"] for g in groups)
        total_remaining = sum(g["remaining"] for g in groups)
        total_items = sum(g["count"] for g in groups)
        total_customers = len(groups)

        text = f"💵 {RECEIVABLE_ACTIVE}\n\n"
        text += "📊 خلاصه کلی\n"
        text += f"• تعداد مشتریان: {total_customers}\n"
        text += f"• تعداد طلب‌ها: {total_items}\n"
        text += f"• مجموع طلب‌ها: {format_amount(total_amount)} تومان\n"
        text += f"• مجموع باقی‌مانده: {format_amount(total_remaining)} تومان"
        text += "\n\n────────────────────"

        for g in groups:
            text += f"\n\n👤 {g['party']}\n"
            text += f"• تعداد طلب‌ها: {g['count']}\n"
            text += f"• مجموع: {format_amount(g['total'])} تومان\n"
            if g['remaining'] > 0:
                text += f"• باقی‌مانده: {format_amount(g['remaining'])} تومان"
            else:
                text += "• ✅ تسویه شده"

        buttons_data = []
        for g in groups:
            safe_key = g["party"].replace(":", "_")
            buttons_data.append({
                "label": f"▶ مشاهده طلب‌های {g['party']}",
                "callback_data": f"recv_cust_detail:{cache_key}:{safe_key}"
            })

        await callback.message.answer(
            text,
            reply_markup=recv_customer_keyboard(buttons_data)
        )
    except Exception as e:
        logger.error(f"Error in receivable_active_list: {e}", exc_info=True)
        try:
            await callback.message.answer("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.", reply_markup=main_menu())
        except Exception:
            pass
    await safe_callback_answer(callback)

@router.callback_query(F.data == "receivable_overdue")
async def receivable_overdue_list(callback: CallbackQuery):
    """Show overdue receivables grouped by customer."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    today = get_jalali_date()
    txns = TransactionRepository.get_overdue( user["id"], "receivable", today)
    cache_key = f"overdue_{user["id"]}"
    await _send_grouped_receivable_list(
        callback.message, txns, RECEIVABLE_OVERDUE,
        RECEIVABLE_OVERDUE_EMPTY, cache_key
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "receivable_due_today")
async def receivable_due_today_list(callback: CallbackQuery):
    """Show receivables due today grouped by customer."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    today = get_jalali_date()
    txns = TransactionRepository.get_due_today( user["id"], "receivable", today)
    cache_key = f"due_today_{user["id"]}"
    await _send_grouped_receivable_list(
        callback.message, txns, RECEIVABLE_DUE_TODAY,
        RECEIVABLE_DUE_TODAY_EMPTY, cache_key
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "receivable_due_week")
async def receivable_due_week_list(callback: CallbackQuery):
    """Show receivables due this week grouped by customer."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    today = get_jalali_date()
    week_end = get_week_end_jalali()
    txns = TransactionRepository.get_due_this_week( user["id"], "receivable", today, week_end)
    cache_key = f"due_week_{user["id"]}"
    await _send_grouped_receivable_list(
        callback.message, txns, RECEIVABLE_DUE_WEEK,
        RECEIVABLE_DUE_WEEK_EMPTY, cache_key
    )
    await safe_callback_answer(callback)

# --- Receivable 3-level hierarchy (active view) ---

@router.callback_query(F.data.startswith("recv_cust_detail:"))
async def receivable_customer_detail_active(callback: CallbackQuery):
    """Level 2: Show receivables for a selected customer (active view)."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    party = group["party"]
    txns = group["txns"]
    active_txns = [t for t in txns if not t["is_settled"]]

    text = f"💵 {party}\n\n"
    text += f"📊 خلاصه مشتری\n"
    text += f"• تعداد طلب‌ها: {group['count']}\n"
    text += f"• مجموع: {format_amount(group['total'])} تومان\n"
    if group['remaining'] > 0:
        text += f"• باقی‌مانده: {format_amount(group['remaining'])} تومان"
    text += "\n────────────────────"

    await callback.message.edit_text(text)

    txns_data = []
    for txn in active_txns:
        due_emoji = ""
        if txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            if days_left < 0:
                due_emoji = "🔴"
            elif days_left == 0:
                due_emoji = "🟡"
            else:
                due_emoji = "🟢"
        label = f"📋 #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        if due_emoji:
            label = f"{due_emoji} #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        txns_data.append({
            "label": label,
            "callback_data": f"recv_item_detail:{cache_key}:{safe_party}:{txn["id"]}"
        })

    await callback.message.answer(
        RECEIVABLE_SELECT_RECV,
        reply_markup=recv_customer_debts_keyboard(txns_data)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_item_detail:"))
async def receivable_item_detail(callback: CallbackQuery):
    """Level 3: Show full details for a specific receivable."""
    parts = callback.data.split(":", 3)
    if len(parts) < 4:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]
    try:
        txn_id = int(parts[3])
    except ValueError:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    txn = TransactionRepository.get_by_id( txn_id)
    if not txn:
        await safe_callback_answer(callback, "⚠️ طلب یافت نشد.", show_alert=True)
        return

    remaining = txn["amount"]
    if not txn["is_settled"]:
        remaining = PaymentRepository.get_remaining( txn_id, txn["amount"])

    text = f"📋 جزئیات طلب\n\n"
    text += f"🆔 شناسه: {txn["id"]}\n"
    text += f"👤 طرف حساب: {txn["party_name"] or '-'}\n"
    cat_str = txn["category"] or "-"
    if txn["subcategory"]:
        cat_str += f" / {txn["subcategory"]}"
    text += f"🏷 دسته: {cat_str}\n"
    text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
    text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    if txn["description"]:
        text += f"📝 توضیحات: {txn["description"]}\n"
    if txn["due_jalali_date"]:
        days_left = get_days_until(txn["due_jalali_date"])
        time_str = f" ساعت {txn["due_jalali_time"]}" if txn["due_jalali_time"] else ""
        if txn["is_settled"]:
            text += f"📅 سررسید: {txn["due_jalali_date"]}{time_str}\n"
        elif days_left < 0:
            text += f"🔴 سررسید: {txn["due_jalali_date"]}{time_str} (منقضی)\n"
        elif days_left == 0:
            text += f"🟡 سررسید: {txn["due_jalali_date"]}{time_str} (امروز)\n"
        else:
            text += f"🟢 سررسید: {txn["due_jalali_date"]}{time_str} ({days_left} روز)\n"
    if txn["card_number"]:
        card_fmt = "-".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
        text += f"💳 کارت: {card_fmt}\n"
    if txn["sheba"]:
        text += f"🏦 شبا: {txn["sheba"]}\n"
    if txn["bank_name"]:
        text += f"🏛 بانک: {normalize_bank_name(txn["bank_name"])}\n"
    text += f"📅 ثبت: {txn["jalali_date"]} ساعت {txn["jalali_time"]}"

    has_photo = bool(txn["photo_path"])
    has_pay_info = bool(txn["card_number"] or txn["sheba"] or txn["bank_name"])

    kb = recv_detail_keyboard(txn_id, cache_key, safe_party, has_photo, remaining, has_pay_info)
    await callback.message.edit_text(text, reply_markup=kb)
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_detail_back:"))
async def receivable_detail_back_handler(callback: CallbackQuery):
    """Navigate back from Level 3 (receivable details) to Level 2 (customer receivable list)."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    active_txns = [t for t in group["txns"] if not t["is_settled"]]

    text = f"💵 {group['party']}\n\n"
    text += f"📊 خلاصه مشتری\n"
    text += f"• تعداد طلب‌ها: {group['count']}\n"
    text += f"• مجموع: {format_amount(group['total'])} تومان\n"
    if group['remaining'] > 0:
        text += f"• باقی‌مانده: {format_amount(group['remaining'])} تومان"
    text += "\n────────────────────"

    txns_data = []
    for txn in active_txns:
        due_emoji = ""
        if txn["due_jalali_date"]:
            days_left = get_days_until(txn["due_jalali_date"])
            if days_left < 0:
                due_emoji = "🔴"
            elif days_left == 0:
                due_emoji = "🟡"
            else:
                due_emoji = "🟢"
        label = f"📋 #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        if due_emoji:
            label = f"{due_emoji} #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        txns_data.append({
            "label": label,
            "callback_data": f"recv_item_detail:{cache_key}:{safe_party}:{txn["id"]}"
        })

    await callback.message.edit_text(text)
    await callback.message.answer(
        RECEIVABLE_SELECT_RECV,
        reply_markup=recv_customer_debts_keyboard(txns_data)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("receivable_payment_history:"))
async def receivable_payment_history(callback: CallbackQuery):
    """Show payment history for a receivable."""
    try:
        txn_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    payments = PaymentRepository.get_by_transaction( txn_id)
    if not payments:
        await safe_callback_answer(callback, DEBT_PAYMENT_HISTORY_EMPTY, show_alert=True)
        return

    text = f"{DEBT_PAYMENT_HISTORY_TITLE} - طلب #{txn_id}\n\n"
    total_paid = 0
    for p in payments:
        total_paid += p["amount"]
        text += f"💰 {format_amount(p['amount'])} تومان\n"
        text += f"📅 {p['jalali_date']} ساعت {p['jalali_time']}\n"
        if p["description"]:
            text += f"📝 {p['description']}\n"
        if p["photo_path"]:
            text += f"📸 رسید: ✅ دارد\n"
        text += "──────────\n"
    text += f"\n💰 مجموع دریافتی: {format_amount(total_paid)} تومان"

    await callback.message.answer(text)
    await safe_callback_answer(callback)

# --- Receivable customer detail view (legacy, used by overdue/settled/due_today/due_week) ---

@router.callback_query(F.data.startswith("recv_detail:"))
async def receivable_customer_detail(callback: CallbackQuery):
    """Show detailed receivables for a selected customer with item-level and group-level actions."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    detail_text = _build_customer_detail_text(group)
    has_pay_info = any(t["card_number"] or t["sheba"] or t["bank_name"] for t in group["txns"])
    has_active = any(not t["is_settled"] for t in group["txns"])

    await callback.message.edit_text(detail_text)

    builder = InlineKeyboardBuilder()

    # Group-level: pay entire customer ledger
    if has_active:
        builder.row(InlineKeyboardButton(
            text=f"💵 دریافت از {group['party']}",
            callback_data=f"recv_pay_customer:{cache_key}:{safe_party}"
        ))

    # Group-level: SMS
    if has_pay_info:
        builder.row(InlineKeyboardButton(text="📩 پیامک همه", callback_data=f"recv_group_sms:{cache_key}:{safe_party}"))

    # Item-level: individual payment (advanced mode)
    active_txns = [t for t in group["txns"] if not t["is_settled"]]
    if len(active_txns) > 1:
        for txn in active_txns[:5]:
            label = f"#{txn["id"]} | {format_amount(txn["amount"])} تومان"
            builder.row(InlineKeyboardButton(text=f"💵 پرداخت {label}", callback_data=f"quick_pay_recv:{txn["id"]}"))

    builder.row(InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data="recv_group_back"))
    await callback.message.answer("عملیات:", reply_markup=builder.as_markup())
    await safe_callback_answer(callback)

@router.callback_query(F.data == "recv_group_back")
async def receivable_group_back(callback: CallbackQuery):
    """Handle back button from customer detail - return to submenu."""
    await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_group_sms:"))
async def receivable_group_sms(callback: CallbackQuery):
    """Send SMS info for all receivables of a customer."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    # Find the first transaction with payment info
    txn_with_info = None
    for txn in group["txns"]:
        if txn["card_number"] or txn["sheba"] or txn["bank_name"]:
            txn_with_info = txn
            break

    if not txn_with_info:
        await safe_callback_answer(callback, "⚠️ اطلاعات پرداختی موجود نیست.", show_alert=True)
        return

    party = group["party"]
    amount_fmt = format_amount(group["remaining"])
    amount_words = amount_to_persian_words(group["remaining"])

    lines = []
    if txn_with_info.card_number:
        card_fmt = " ".join([txn_with_info.card_number[i:i+4] for i in range(0, 16, 4)])
        lines.append("کارت:")
        lines.append(card_fmt)
        lines.append("")
    if txn_with_info.sheba:
        lines.append("شبا:")
        lines.append(txn_with_info.sheba)
        lines.append("")
    lines.append(party)
    if txn_with_info.bank_name:
        lines.append(f"بانک: {normalize_bank_name(txn_with_info.bank_name)}")
    lines.append(f"{amount_fmt} تومان")
    lines.append(amount_words)

    text_to_copy = "\n".join(lines)
    await safe_callback_answer(callback, "✅ کپی شد", show_alert=True)
    await callback.message.answer(
        f"📩 اطلاعات پرداخت\n\n<code>{text_to_copy}</code>",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("recv_group_pay:"))
async def receivable_group_pay(callback: CallbackQuery, state: FSMContext):
    """Start customer-level payment flow - show customer ledger and prompt for amount."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    active_txns = [t for t in group["txns"] if not t["is_settled"]]
    if not active_txns:
        await safe_callback_answer(callback, "⚠️ طلب فعالی برای دریافت وجود ندارد.", show_alert=True)
        return

    total_remaining = 0
    txn_details = []
    for txn in active_txns:
        rem = PaymentRepository.get_remaining( txn["id"], txn["amount"])
        total_remaining += rem
        txn_details.append(txn)

    # Store in state for FIFO processing
    await state.update_data(
        payment_type="receivable",
        customer_party=group["party"],
        customer_cache_key=cache_key,
        customer_safe_party=safe_party,
        customer_total_remaining=total_remaining,
        customer_txn_ids=[t["id"] for t in txn_details]
    )

    text = f"💵 دریافت طلب\n\n"
    text += f"👤 مشتری: {group['party']}\n"
    text += f"💰 بدهی کل: {format_amount(total_remaining)} تومان\n\n"
    text += f"━━━━━━━━━━━━━━━━━━\n\n"
    text += f"STEP 1:\n💰 انتخاب نوع پرداخت:\n"
    text += f"├── 💰 کامل ({format_amount(total_remaining)})\n"
    text += f"└── ✂️ جزئی (ورود مبلغ)"

    await callback.message.answer(text, reply_markup=payment_type_keyboard())
    await state.set_state(PaymentForm.payment_type)
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_pay_customer:"))
async def recv_pay_customer_start(callback: CallbackQuery, state: FSMContext):
    """Start customer-level payment from detail view."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    active_txns = [t for t in group["txns"] if not t["is_settled"]]
    if not active_txns:
        await safe_callback_answer(callback, "⚠️ طلب فعالی برای دریافت وجود ندارد.", show_alert=True)
        return

    total_remaining = 0
    for txn in active_txns:
        rem = PaymentRepository.get_remaining( txn["id"], txn["amount"])
        total_remaining += rem

    await state.update_data(
        payment_type="receivable",
        customer_party=group["party"],
        customer_cache_key=cache_key,
        customer_safe_party=safe_party,
        customer_total_remaining=total_remaining,
        customer_txn_ids=[t["id"] for t in active_txns]
    )

    text = f"💵 دریافت طلب\n\n"
    text += f"👤 مشتری: {group['party']}\n"
    text += f"💰 بدهی کل: {format_amount(total_remaining)} تومان\n\n"
    text += f"━━━━━━━━━━━━━━━━━━\n\n"
    text += f"STEP 1:\n💰 انتخاب نوع پرداخت:\n"
    text += f"├── 💰 کامل ({format_amount(total_remaining)})\n"
    text += f"└── ✂️ جزئی (ورود مبلغ)"

    await callback.message.answer(text, reply_markup=payment_type_keyboard())
    await state.set_state(PaymentForm.payment_type)
    await safe_callback_answer(callback)

# --- Receivable category-filtered lists ---

@router.callback_query(F.data == "receivable_all_cat")
async def receivable_all_cat_menu(callback: CallbackQuery):
    """Show category filter for all receivables."""
    await callback.message.edit_text(
        "📋 همه طلب‌ها\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=receivable_category_filter_keyboard("recv_all")
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_all_cat:"))
async def receivable_all_cat_selected(callback: CallbackQuery):
    """Handle category selection for all receivables."""
    category = callback.data.split(":", 1)[1]

    if category == "back":
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    if category == "all":
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_by_user(user["id"], transaction_type="receivable", limit=50)
        await safe_delete(callback.message)
        cache_key = f"recv_all_{user["id"]}"
        await _send_grouped_receivable_list(callback.message, txns, RECEIVABLE_ALL, RECEIVABLE_EMPTY, cache_key)
        await safe_callback_answer(callback)
        return

    subs = RECEIVABLE_CATEGORIES.get(category, [])
    if not subs:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_by_user(user["id"], transaction_type="receivable", limit=50)
        filtered = _filter_by_category(txns, category=category)
        await safe_delete(callback.message)
        cache_key = f"recv_all_{user["id"]}_{category}"
        await _send_grouped_receivable_list(callback.message, filtered, f"{RECEIVABLE_ALL} ({category})", RECEIVABLE_EMPTY, cache_key)
        await safe_callback_answer(callback)
        return

    await callback.message.edit_text(
        f"📋 همه طلب‌ها ({category})\n\nزیرمجموعه را انتخاب کنید:",
        reply_markup=receivable_subcategory_filter_keyboard("recv_all", category)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_all_sub:"))
async def receivable_all_sub_selected(callback: CallbackQuery):
    """Handle subcategory selection for all receivables."""
    subcategory = callback.data.split(":", 1)[1]

    if subcategory == "back":
        await callback.message.edit_text(
            "📋 همه طلب‌ها\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=receivable_category_filter_keyboard("recv_all")
        )
        await safe_callback_answer(callback)
        return

    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txns = TransactionRepository.get_by_user(user["id"], transaction_type="receivable", limit=50)

    if subcategory != "all":
        parent_cat = None
        for cat, subs in RECEIVABLE_CATEGORIES.items():
            if subcategory in subs:
                parent_cat = cat
                break
        txns = _filter_by_category(txns, category=parent_cat, subcategory=subcategory)

    await safe_delete(callback.message)
    title = f"{RECEIVABLE_ALL} ({subcategory})" if subcategory != "all" else RECEIVABLE_ALL
    cache_key = f"recv_all_{user["id"]}_{subcategory}"
    await _send_grouped_receivable_list(callback.message, txns, title, RECEIVABLE_EMPTY, cache_key)
    await safe_callback_answer(callback)

@router.callback_query(F.data == "receivable_settled_cat")
async def receivable_settled_cat_menu(callback: CallbackQuery):
    """Show category filter for settled receivables."""
    await callback.message.edit_text(
        "🟢 تسویه شده\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=receivable_category_filter_keyboard("recv_settled")
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_settled_cat:"))
async def receivable_settled_cat_selected(callback: CallbackQuery):
    """Handle category selection for settled receivables."""
    category = callback.data.split(":", 1)[1]

    if category == "back":
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    if category == "all":
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_with_payments( user["id"], "receivable")
        await safe_delete(callback.message)
        cache_key = f"recv_settled_{user["id"]}"
        await _send_settled_customer_list(callback.message, txns, RECEIVABLE_SETTLED, RECEIVABLE_SETTLED_EMPTY, cache_key)
        await safe_callback_answer(callback)
        return

    subs = RECEIVABLE_CATEGORIES.get(category, [])
    if not subs:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_with_payments( user["id"], "receivable")
        filtered = _filter_by_category(txns, category=category)
        await safe_delete(callback.message)
        cache_key = f"recv_settled_{user["id"]}_{category}"
        await _send_settled_customer_list(callback.message, filtered, f"{RECEIVABLE_SETTLED} ({category})", RECEIVABLE_SETTLED_EMPTY, cache_key)
        await safe_callback_answer(callback)
        return

    await callback.message.edit_text(
        f"🟢 تسویه شده ({category})\n\nزیرمجموعه را انتخاب کنید:",
        reply_markup=receivable_subcategory_filter_keyboard("recv_settled", category)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_settled_sub:"))
async def receivable_settled_sub_selected(callback: CallbackQuery):
    """Handle subcategory selection for settled receivables."""
    subcategory = callback.data.split(":", 1)[1]

    if subcategory == "back":
        await callback.message.edit_text(
            "🟢 تسویه شده\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=receivable_category_filter_keyboard("recv_settled")
        )
        await safe_callback_answer(callback)
        return

    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txns = TransactionRepository.get_with_payments( user["id"], "receivable")

    if subcategory != "all":
        parent_cat = None
        for cat, subs in RECEIVABLE_CATEGORIES.items():
            if subcategory in subs:
                parent_cat = cat
                break
        txns = _filter_by_category(txns, category=parent_cat, subcategory=subcategory)

    await safe_delete(callback.message)
    title = f"{RECEIVABLE_SETTLED} ({subcategory})" if subcategory != "all" else RECEIVABLE_SETTLED
    cache_key = f"recv_settled_{user["id"]}_{subcategory}"
    await _send_settled_customer_list(callback.message, txns, title, RECEIVABLE_SETTLED_EMPTY, cache_key)
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("rs_cust:"))
async def receivable_settled_customer_selected(callback: CallbackQuery):
    """Show list of settled receivables for a selected customer."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    txns = group["txns"]
    party = group["party"]
    total = group["total"]
    count = group["count"]
    remaining = group.get("remaining", 0)
    paid = total - remaining

    text = f"👤 {party}\n"
    text += f"💰 مجموع طلب: {format_amount(total)} تومان\n"
    text += f"💰 مجموع دریافتی: {format_amount(paid)} تومان\n"
    if remaining > 0:
        text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    text += f"📌 {count} مورد\n"
    text += "——————————"

    items_data = []
    for txn in txns:
        txn_remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])
        txn_paid = txn["amount"] - txn_remaining
        if txn["is_settled"] or txn_remaining <= 0:
            label = f"🟢 #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        else:
            txn_pct = int((txn_paid / txn["amount"]) * 100) if txn["amount"] > 0 else 0
            label = f"🟡 #{txn["id"]} | {format_amount(txn_paid)} / {format_amount(txn["amount"])} تومان ({txn_pct}%)"
        items_data.append({
            "label": label,
            "callback_data": f"rs_item:{txn["id"]}",
            "detail_callback": f"rs_item:{txn["id"]}"
        })

    await callback.message.edit_text(text)
    await callback.message.answer(
        "📋 طلب مورد نظر را انتخاب کنید:",
        reply_markup=settled_recv_items_keyboard(items_data, cache_key)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("rs_item:"))
async def receivable_settled_item_detail(callback: CallbackQuery):
    """Show full details for a settled/partially-paid receivable."""
    try:
        txn_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    txn = TransactionRepository.get_by_id( txn_id)
    if not txn:
        await safe_callback_answer(callback, "⚠️ طلب یافت نشد.", show_alert=True)
        return

    # Build full detail text
    payments = PaymentRepository.get_by_transaction( txn["id"])
    total_paid = sum(p["amount"] for p in payments) if payments else 0
    remaining = max(0, txn["amount"] - total_paid)
    is_fully_settled = txn["is_settled"] or remaining <= 0
    recv_pct = int((total_paid / txn["amount"]) * 100) if txn["amount"] > 0 else 0

    if is_fully_settled:
        text = f"🟢 جزئیات طلب تسویه شده\n\n"
    else:
        text = f"🟡 جزئیات طلب با پرداخت جزئی ({recv_pct}%)\n\n"

    text += f"🆔 شناسه: {txn["id"]}\n"
    text += f"👤 مشتری: {txn["party_name"] or '-'}\n"

    cat_str = txn["category"] or "-"
    if txn["subcategory"]:
        cat_str += f" / {txn["subcategory"]}"
    text += f"🏷 دسته‌بندی: {cat_str}\n"
    text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
    text += f"💰 مبلغ دریافتی: {format_amount(total_paid)} تومان\n"
    if remaining > 0:
        text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"

    # Settlement date
    if txn["settled_at"]:
        import jdatetime
        from pytz import timezone as tz
        iran_tz = tz("Asia/Tehran")
        settled_local = txn["settled_at"].replace(tzinfo=tz("UTC")).astimezone(iran_tz) if txn["settled_at"].tzinfo else txn["settled_at"].astimezone(iran_tz)
        settled_jalali = jdatetime.datetime.fromgregorian(datetime=settled_local)
        text += f"✅ تاریخ تسویه: {settled_jalali.strftime('%Y/%m/%d - %H:%M:%S')}\n"

    if txn["description"]:
        text += f"📝 توضیحات: {txn["description"]}\n"

    # Due date
    if txn["due_jalali_date"]:
        time_str = f" ساعت {txn["due_jalali_time"]}" if txn["due_jalali_time"] else ""
        text += f"📅 سررسید: {txn["due_jalali_date"]}{time_str}\n"

    # Photo/attachment - check both transaction photo and payment receipt photos
    has_photo = bool(txn["photo_path"])
    has_payment_photo = any(p["photo_path"] for p in payments) if payments else False
    if has_photo:
        text += f"📸 عکس: ✅ دارد\n"
    if has_payment_photo:
        text += f"📸 رسید پرداخت: ✅ دارد\n"

    # Payment method info
    if txn["card_number"]:
        card_fmt = "-".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
        text += f"💳 شماره کارت: {card_fmt}\n"
    if txn["sheba"]:
        text += f"🏦 شبا: {txn["sheba"]}\n"
    if txn["bank_name"]:
        text += f"🏛 بانک: {txn["bank_name"]}\n"

    # Payment details from payments table
    if payments:
        text += f"\n📊 سوابق پرداخت ({len(payments)} فقره):\n"
        for p in payments:
            text += f"  💰 {format_amount(p['amount'])} تومان"
            text += f" | {p['jalali_date']} ساعت {p['jalali_time']}"
            if p["description"]:
                text += f" | {p['description']}"
            if p["photo_path"]:
                text += f" | 📸 رسید"
            text += "\n"

    # Registration date
    text += f"\n📅 تاریخ ثبت: {txn["jalali_date"]} ساعت {txn["jalali_time"]}"

    # Find the cache key for back navigation
    # We need to determine which cache key this customer belongs to
    cache_key = ""
    safe_party = ""
    async with _recv_groups_lock:
        for ck, groups_dict in _recv_groups_cache.items():
            for party, g in groups_dict.items():
                for t in g.get("txns", []):
                    if t["id"] == txn["id"]:
                        cache_key = ck
                        safe_party = party.replace(":", "_")
                        break
                if cache_key:
                    break
            if cache_key:
                break

    await callback.message.edit_text(
        text,
        reply_markup=settled_recv_detail_keyboard(txn["id"], cache_key, safe_party, has_photo, has_payment_photo)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("rs_bc:"))
async def receivable_settled_back_to_customers(callback: CallbackQuery):
    """Navigate back from receivable list to customer list."""
    cache_key = callback.data.split(":", 1)[1]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    # Rebuild customer list from cache
    groups = list(cached.values())
    total_amount = sum(g["total"] for g in groups)
    total_items = sum(g["count"] for g in groups)
    total_customers = len(groups)
    total_remaining = sum(g["remaining"] for g in groups)
    total_paid = total_amount - total_remaining

    # Determine title from cache key
    title = RECEIVABLE_SETTLED
    if cache_key.startswith("recv_settled_"):
        suffix = cache_key[len("recv_settled_"):]
        # Remove user ID prefix (first segment before _ or end)
        parts = suffix.split("_", 1)
        if len(parts) > 1:
            filter_part = parts[1]
            title = f"{RECEIVABLE_SETTLED} ({filter_part})"

    summary = f"📊 {title}\n\n"
    summary += f"💰 مجموع طلب: {format_amount(total_amount)} تومان\n"
    summary += f"💰 مجموع دریافتی: {format_amount(total_paid)} تومان\n"
    if total_remaining > 0:
        summary += f"💰 مجموع باقی‌مانده: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} مورد"

    buttons_data = []
    for g in groups:
        paid = g["total"] - g["remaining"]
        if g["remaining"] <= 0:
            label = f"🟢 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        elif paid > 0:
            pct = int((paid / g["total"]) * 100) if g["total"] > 0 else 0
            label = f"🟡 {g['party']} | {format_amount(paid)} / {format_amount(g['total'])} تومان ({pct}%) ({g['count']} مورد)"
        else:
            label = f"🔴 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        safe_key = g["party"].replace(":", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"rs_cust:{cache_key}:{safe_key}"
        })

    await callback.message.edit_text(summary)
    await callback.message.answer(
        "👤 مشتری مورد نظر را انتخاب کنید:",
        reply_markup=settled_recv_customer_keyboard(buttons_data)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("rs_bi:"))
async def receivable_settled_back_to_items(callback: CallbackQuery):
    """Navigate back from detail to receivable list."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _recv_groups_lock:
        cached = _recv_groups_cache.get(cache_key)
    if not cached:
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    txns = group["txns"]
    party = group["party"]
    total = group["total"]
    count = group["count"]
    remaining = group.get("remaining", 0)
    paid = total - remaining

    text = f"👤 {party}\n"
    text += f"💰 مجموع طلب: {format_amount(total)} تومان\n"
    text += f"💰 مجموع دریافتی: {format_amount(paid)} تومان\n"
    if remaining > 0:
        text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    text += f"📌 {count} مورد\n"
    text += "——————————"

    items_data = []
    for txn in txns:
        txn_remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])
        txn_paid = txn["amount"] - txn_remaining
        if txn["is_settled"] or txn_remaining <= 0:
            label = f"🟢 #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        else:
            txn_pct = int((txn_paid / txn["amount"]) * 100) if txn["amount"] > 0 else 0
            label = f"🟡 #{txn["id"]} | {format_amount(txn_paid)} / {format_amount(txn["amount"])} تومان ({txn_pct}%)"
        items_data.append({
            "label": label,
            "callback_data": f"rs_item:{txn["id"]}",
            "detail_callback": f"rs_item:{txn["id"]}"
        })

    await callback.message.edit_text(text)
    await callback.message.answer(
        "📋 طلب مورد نظر را انتخاب کنید:",
        reply_markup=settled_recv_items_keyboard(items_data, cache_key)
    )
    await safe_callback_answer(callback)

# ==============================
# Debt Settlement Handlers
# ==============================

@router.callback_query(F.data.startswith("ds_cust:"))
async def debt_settled_customer_selected(callback: CallbackQuery):
    """Show list of settled debts for a selected customer."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _debt_groups_lock:
        cached = _debt_groups_cache.get(cache_key)
    if not cached:
        await safe_callback_answer(callback, "⚠️ اطلاعات قدیمی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await safe_callback_answer(callback, "⚠️ مشتری یافت نشد.", show_alert=True)
        return

    txns = group["txns"]
    party = group["party"]
    total = group["total"]
    count = group["count"]
    remaining = group.get("remaining", 0)
    paid = total - remaining
    percentage = int((paid / total) * 100) if total > 0 else 0

    text = f"👤 {party}\n"
    text += f"💰 مجموع بدهی: {format_amount(total)} تومان\n"
    text += f"💰 مجموع پرداختی: {format_amount(paid)} تومان\n"
    if remaining > 0:
        text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    text += f"📊 درصد تسویه: {percentage}%\n"
    text += f"📌 {count} مورد\n"
    text += "——————————"

    items_data = []
    for txn in txns:
        txn_remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        txn_paid = txn["amount"] - txn_remaining
        if txn["is_settled"] or txn_remaining <= 0:
            label = f"🟢 #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        else:
            txn_percentage = int((txn_paid / txn["amount"]) * 100) if txn["amount"] > 0 else 0
            label = f"🟡 #{txn["id"]} | {format_amount(txn_paid)} / {format_amount(txn["amount"])} تومان ({txn_percentage}%)"
        items_data.append({
            "label": label,
            "callback_data": f"ds_item:{txn["id"]}",
            "detail_callback": f"ds_item:{txn["id"]}"
        })

    await callback.message.edit_text(text)
    await callback.message.answer(
        "📋 بدهی مورد نظر را انتخاب کنید:",
        reply_markup=settled_debt_items_keyboard(items_data, cache_key)
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("ds_item:"))
async def debt_settled_item_detail(callback: CallbackQuery):
    """Show full details for a settled/partially-paid debt."""
    try:
        txn_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    txn = TransactionRepository.get_by_id(txn_id)
    if not txn:
        await safe_callback_answer(callback, "⚠️ بدهی یافت نشد.", show_alert=True)
        return

    # Build full detail text
    payments = PaymentRepository.get_by_transaction(txn["id"])
    total_paid = sum(p["amount"] for p in payments) if payments else 0
    remaining = max(0, txn["amount"] - total_paid)
    is_fully_settled = txn["is_settled"] or remaining <= 0
    percentage = int((total_paid / txn["amount"]) * 100) if txn["amount"] > 0 else 0

    if is_fully_settled:
        text = f"🟢 جزئیات بدهی تسویه شده\n\n"
    else:
        text = f"🟡 جزئیات بدهی با پرداخت جزئی ({percentage}%)\n\n"

    text += f"🆔 شناسه: {txn["id"]}\n"
    text += f"👤 مشتری: {txn["party_name"] or '-'}\n"

    cat_str = txn["category"] or "-"
    if txn["subcategory"]:
        cat_str += f" / {txn["subcategory"]}"
    text += f"🏷 دسته‌بندی: {cat_str}\n"
    text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
    text += f"💰 مبلغ پرداختی: {format_amount(total_paid)} تومان\n"
    if remaining > 0:
        text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    text += f"📊 درصد تسویه: {percentage}%\n"

    # Settlement date
    if txn["settled_at"]:
        import jdatetime
        from pytz import timezone as tz
        iran_tz = tz("Asia/Tehran")
        settled_local = txn["settled_at"].replace(tzinfo=tz("UTC")).astimezone(iran_tz) if txn["settled_at"].tzinfo else txn["settled_at"].astimezone(iran_tz)
        settled_jalali = jdatetime.datetime.fromgregorian(datetime=settled_local)
        text += f"✅ تاریخ تسویه: {settled_jalali.strftime('%Y/%m/%d - %H:%M:%S')}\n"

    if txn["description"]:
        text += f"📝 توضیحات: {txn["description"]}\n"

    # Due date
    if txn["due_jalali_date"]:
        time_str = f" ساعت {txn["due_jalali_time"]}" if txn["due_jalali_time"] else ""
        text += f"📅 سررسید: {txn["due_jalali_date"]}{time_str}\n"

    # Photo/attachment - check both transaction photo and payment receipt photos
    has_photo = bool(txn["photo_path"])
    has_payment_photo = any(p["photo_path"] for p in payments) if payments else False
    if has_photo:
        text += f"📸 عکس: ✅ دارد\n"
    if has_payment_photo:
        text += f"📸 رسید پرداخت: ✅ دارد\n"

    # Payment method info
    if txn["card_number"]:
        card_fmt = "-".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
        text += f"💳 شماره کارت: {card_fmt}\n"
    if txn["sheba"]:
        text += f"🏦 شبا: {txn["sheba"]}\n"
    if txn["bank_name"]:
        text += f"🏛 بانک: {txn["bank_name"]}\n"

    # Payment details from payments table
    if payments:
        text += f"\n📊 سوابق پرداخت ({len(payments)} فقره):\n"
        for p in payments:
            text += f"  💰 {format_amount(p['amount'])} تومان"
            text += f" | {p['jalali_date']} ساعت {p['jalali_time']}"
            if p["description"]:
                text += f" | {p['description']}"
            if p["photo_path"]:
                text += f" | 📸 رسید"
            text += "\n"

    # Registration date
    text += f"\n📅 تاریخ ثبت: {txn["jalali_date"]} ساعت {txn["jalali_time"]}"

    # Find the cache key for back navigation
    cache_key = ""
    safe_party = ""
    async with _debt_groups_lock:
        for ck, groups_dict in _debt_groups_cache.items():
            for party, g in groups_dict.items():
                for t in g.get("txns", []):
                    if t["id"] == txn["id"]:
                        cache_key = ck
                        safe_party = party.replace(":", "_")
                        break
                if cache_key:
                    break
            if cache_key:
                break

    await callback.message.edit_text(
        text,
        reply_markup=settled_debt_detail_keyboard(txn["id"], cache_key, safe_party, has_photo, has_payment_photo)
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("ds_bc:"))
async def debt_settled_back_to_customers(callback: CallbackQuery):
    """Navigate back from debt list to customer list."""
    cache_key = callback.data.split(":", 1)[1]

    async with _debt_groups_lock:
        cached = _debt_groups_cache.get(cache_key)
    if not cached:
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    # Rebuild customer list from cache
    groups = list(cached.values())
    total_amount = sum(g["total"] for g in groups)
    total_items = sum(g["count"] for g in groups)
    total_customers = len(groups)
    total_remaining = sum(g["remaining"] for g in groups)
    total_paid = total_amount - total_remaining

    # Determine title from cache key
    title = DEBT_SETTLED
    if cache_key.startswith("debt_settled_"):
        suffix = cache_key[len("debt_settled_"):]
        parts = suffix.split("_", 1)
        if len(parts) > 1:
            filter_part = parts[1]
            title = f"{DEBT_SETTLED} ({filter_part})"

    summary = f"📊 {title}\n\n"
    summary += f"💰 مجموع بدهی: {format_amount(total_amount)} تومان\n"
    summary += f"💰 مجموع پرداختی: {format_amount(total_paid)} تومان\n"
    if total_remaining > 0:
        summary += f"💰 مجموع باقی‌مانده: {format_amount(total_remaining)} تومان\n"
    summary += f"👥 {total_customers} مشتری | 📌 {total_items} مورد"

    buttons_data = []
    for g in groups:
        paid = g["total"] - g["remaining"]
        if g["remaining"] <= 0:
            label = f"🟢 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        elif paid > 0:
            pct = int((paid / g["total"]) * 100) if g["total"] > 0 else 0
            label = f"🟡 {g['party']} | {format_amount(paid)} / {format_amount(g['total'])} تومان ({pct}%) ({g['count']} مورد)"
        else:
            label = f"🔴 {g['party']} | {format_amount(g['total'])} تومان ({g['count']} مورد)"
        safe_key = g["party"].replace(":", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"ds_cust:{cache_key}:{safe_key}"
        })

    await callback.message.edit_text(summary)
    await callback.message.answer(
        "👤 مشتری مورد نظر را انتخاب کنید:",
        reply_markup=settled_debt_customer_keyboard(buttons_data)
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("ds_bi:"))
async def debt_settled_back_to_items(callback: CallbackQuery):
    """Navigate back from detail to debt list."""
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_party = parts[2]

    async with _debt_groups_lock:
        cached = _debt_groups_cache.get(cache_key)
    if not cached:
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    group = None
    for party, g in cached.items():
        if party.replace(":", "_") == safe_party:
            group = g
            break

    if not group:
        await callback.message.edit_text(DEBT_MENU_TITLE, reply_markup=debt_submenu())
        await safe_callback_answer(callback)
        return

    txns = group["txns"]
    party = group["party"]
    total = group["total"]
    count = group["count"]
    remaining = group.get("remaining", 0)
    paid = total - remaining
    percentage = int((paid / total) * 100) if total > 0 else 0

    text = f"👤 {party}\n"
    text += f"💰 مجموع بدهی: {format_amount(total)} تومان\n"
    text += f"💰 مجموع پرداختی: {format_amount(paid)} تومان\n"
    if remaining > 0:
        text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    text += f"📊 درصد تسویه: {percentage}%\n"
    text += f"📌 {count} مورد\n"
    text += "——————————"

    items_data = []
    for txn in txns:
        txn_remaining = PaymentRepository.get_remaining(txn["id"], txn["amount"])
        txn_paid = txn["amount"] - txn_remaining
        if txn["is_settled"] or txn_remaining <= 0:
            label = f"🟢 #{txn["id"]} | {format_amount(txn["amount"])} تومان"
        else:
            txn_percentage = int((txn_paid / txn["amount"]) * 100) if txn["amount"] > 0 else 0
            label = f"🟡 #{txn["id"]} | {format_amount(txn_paid)} / {format_amount(txn["amount"])} تومان ({txn_percentage}%)"
        items_data.append({
            "label": label,
            "callback_data": f"ds_item:{txn["id"]}",
            "detail_callback": f"ds_item:{txn["id"]}"
        })

    await callback.message.edit_text(text)
    await callback.message.answer(
        "📋 بدهی مورد نظر را انتخاب کنید:",
        reply_markup=settled_debt_items_keyboard(items_data, cache_key)
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "receivable_receive_cat")
async def receivable_receive_cat_menu(callback: CallbackQuery):
    """Show category filter for receive receivable."""
    await callback.message.edit_text(
        "💵 دریافت طلب\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=receivable_category_filter_keyboard("recv_receive")
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_receive_cat:"))
async def receivable_receive_cat_selected(callback: CallbackQuery, state: FSMContext):
    """Handle category selection for receive receivable - show customers grouped by name."""
    category = callback.data.split(":", 1)[1]

    if category == "back":
        await callback.message.edit_text(RECEIVABLE_MENU_TITLE, reply_markup=receivable_submenu())
        await safe_callback_answer(callback)
        return

    if category == "all":
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_active( user["id"], "receivable")
        if not txns:
            await callback.message.edit_text(RECEIVE_RECV_NO_ACTIVE, reply_markup=receivable_submenu())
            await safe_callback_answer(callback)
            return

        await _send_grouped_customer_pay_list(
            callback.message, txns
        )
        await safe_callback_answer(callback)
        return

    subs = RECEIVABLE_CATEGORIES.get(category, [])
    if not subs:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
            return
        txns = TransactionRepository.get_active( user["id"], "receivable")
        filtered = _filter_by_category(txns, category=category)
        if not filtered:
            await callback.message.edit_text(
                f"{RECEIVE_RECV_NO_ACTIVE}\n\nدسته: {category}",
                reply_markup=receivable_submenu()
            )
            await safe_callback_answer(callback)
            return

        await _send_grouped_customer_pay_list(
            callback.message, filtered
        )
        await safe_callback_answer(callback)
        return

    await callback.message.edit_text(
        f"💵 دریافت طلب ({category})\n\nزیرمجموعه را انتخاب کنید:",
        reply_markup=receivable_subcategory_filter_keyboard("recv_receive", category)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("recv_receive_sub:"))
async def receivable_receive_sub_selected(callback: CallbackQuery, state: FSMContext):
    """Handle subcategory selection for receive receivable."""
    subcategory = callback.data.split(":", 1)[1]

    if subcategory == "back":
        await callback.message.edit_text(
            "💵 دریافت طلب\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=receivable_category_filter_keyboard("recv_receive")
        )
        await safe_callback_answer(callback)
        return

    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txns = TransactionRepository.get_active( user["id"], "receivable")

    if subcategory != "all":
        parent_cat = None
        for cat, subs in RECEIVABLE_CATEGORIES.items():
            if subcategory in subs:
                parent_cat = cat
                break
        txns = _filter_by_category(txns, category=parent_cat, subcategory=subcategory)

    if not txns:
        label = subcategory if subcategory != "all" else ""
        await callback.message.edit_text(
            f"{RECEIVE_RECV_NO_ACTIVE}\n\n{label}",
            reply_markup=receivable_submenu()
        )
        await safe_callback_answer(callback)
        return

    await _send_grouped_customer_pay_list(
        callback.message, txns
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data == "receivable_reports")
async def receivable_reports(callback: CallbackQuery):
    """Show receivable summary report."""
    await safe_delete(callback.message)
    user = UserRepository.get_by_telegram_id(callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return

    all_receivables = TransactionRepository.get_by_user(user["id"], transaction_type="receivable", limit=1000)
    today = get_jalali_date()

    total = len(all_receivables)
    total_amount = sum(t["amount"] for t in all_receivables)

    # Get receivables with any payments (partial or full)
    with_payments = TransactionRepository.get_with_payments(user["id"], "receivable", limit=1000)
    with_payment_ids = {t["id"] for t in with_payments}

    # Fully settled: is_settled flag OR remaining <= 0
    fully_settled = [t for t in all_receivables if t["is_settled"]]
    # Partially paid: has payments but not fully settled
    partially_paid = [t for t in with_payments if not t["is_settled"]]
    # All with payments (settled + partially paid)
    all_with_payments = [t for t in all_receivables if t["id"] in with_payment_ids or t["is_settled"]]
    # Active: no payments at all
    active = [t for t in all_receivables if t["id"] not in with_payment_ids and not t["is_settled"]]
    active_count = len(active)
    active_amount = sum(t["amount"] for t in active)

    settled_count = len(all_with_payments)
    settled_amount = sum(t["amount"] for t in all_with_payments)

    overdue = [t for t in active if t["due_jalali_date"] and t["due_jalali_date"] < today]
    overdue_count = len(overdue)
    overdue_amount = sum(t["amount"] for t in overdue)

    due_today = [t for t in active if t["due_jalali_date"] == today]
    due_today_count = len(due_today)

    # Calculate total paid amount
    total_paid_amount = 0
    for t in all_with_payments:
        payments = PaymentRepository.get_by_transaction(t["id"])
        total_paid_amount += sum(p["amount"] for p in payments) if payments else 0

    # Calculate additional metrics
    collection_rate = (settled_count / total * 100) if total > 0 else 0
    avg_receivable = (total_amount / total) if total > 0 else 0

    report = RECEIVABLE_REPORT_TITLE.format(
        total=total,
        total_amount=format_amount(total_amount),
        active=active_count,
        active_amount=format_amount(active_amount),
        settled=settled_count,
        settled_amount=format_amount(settled_amount),
        overdue=overdue_count,
        overdue_amount=format_amount(overdue_amount),
        due_today=due_today_count,
        collection_rate=f"{collection_rate:.1f}",
        avg_receivable=format_amount(avg_receivable),
        total_paid=format_amount(total_paid_amount)
    )

    # Add partial payment breakdown
    if partially_paid:
        partial_amount = sum(t["amount"] for t in partially_paid)
        report += f"\n\n⏳ پرداخت جزئی: {len(partially_paid)} مورد ({format_amount(partial_amount)} تومان)"
        report += f"\n✅ تسویه کامل: {len(fully_settled)} مورد"

    await callback.message.answer(report, reply_markup=receivable_submenu())
    await safe_callback_answer(callback)

# ==============================
# Payment Handlers (Pay Debt / Receive Receivable)
# ==============================

@router.callback_query(F.data.startswith("quick_pay_debt:"))
async def quick_pay_debt(callback: CallbackQuery, state: FSMContext):
    """Handle quick pay debt button from list view."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txn = TransactionRepository.get_by_id( txn_id)
    if not txn or txn["user_id"] != user["id"] or txn["is_settled"]:
        await safe_callback_answer(callback, "⚠️ بدهی یافت نشد یا تسویه شده است.", show_alert=True)
        return

    remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])
    payments_data = {txn["id"]: remaining}
    await state.update_data(payment_type="debt", payments_data=payments_data, selected_txn_id=txn["id"])

    # Build payment info display
    text = f"💳 پرداخت بدهی\n\n"
    text += f"👤 طرف حساب: {txn["party_name"] or '-'}\n"
    text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
    text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    if txn["card_number"]:
        card_fmt = " ".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
        text += f"💳 کارت: {card_fmt}\n"
    if txn["sheba"]:
        text += f"🏦 شبا: {txn["sheba"]}\n"
    if txn["bank_name"]:
        text += f"🏛 بانک: {normalize_bank_name(txn["bank_name"])}\n"
    text += f"\nنوع پرداخت را انتخاب کنید:"

    await callback.message.answer(text, reply_markup=payment_type_keyboard())
    await state.set_state(PaymentForm.payment_type)
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("quick_pay_recv:"))
async def quick_pay_recv(callback: CallbackQuery, state: FSMContext):
    """Handle quick receive receivable button from list view."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    user = UserRepository.get_by_telegram_id( callback.from_user.id)
    if not user:
        await safe_callback_answer(callback, ACCESS_DENIED, show_alert=True)
        return
    txn = TransactionRepository.get_by_id( txn_id)
    if not txn or txn["user_id"] != user["id"] or txn["is_settled"]:
        await safe_callback_answer(callback, "⚠️ طلب یافت نشد یا تسویه شده است.", show_alert=True)
        return

    remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])
    payments_data = {txn["id"]: remaining}
    await state.update_data(payment_type="receivable", payments_data=payments_data, selected_txn_id=txn["id"])

    # Build payment info display
    text = f"💵 دریافت طلب\n\n"
    text += f"👤 طرف حساب: {txn["party_name"] or '-'}\n"
    text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
    text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    if txn["card_number"]:
        card_fmt = " ".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
        text += f"💳 کارت: {card_fmt}\n"
    if txn["sheba"]:
        text += f"🏦 شبا: {txn["sheba"]}\n"
    if txn["bank_name"]:
        text += f"🏛 بانک: {normalize_bank_name(txn["bank_name"])}\n"
    text += f"\nنوع دریافت را انتخاب کنید:"

    await callback.message.answer(text, reply_markup=payment_type_keyboard())
    await state.set_state(PaymentForm.payment_type)
    await safe_callback_answer(callback)

@router.callback_query(PaymentForm.select, F.data.startswith("pay_select:"))
async def payment_select_handler(callback: CallbackQuery, state: FSMContext):
    """Handle transaction selection for payment."""
    data = callback.data.split(":", 1)[1]

    if data == "cancel":
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        await safe_callback_answer(callback)
        return

    txn_id = int(data)
    fsm_data = await state.get_data()
    payments_data = fsm_data.get("payments_data", {})
    remaining = payments_data.get(txn_id, 0)

    txn = TransactionRepository.get_by_id( txn_id)
    if not txn:
        await safe_callback_answer(callback, "⚠️ تراکنش یافت نشد.", show_alert=True)
        return

    pay_type_name = fsm_data.get("payment_type", "debt")
    type_emoji = "💳" if pay_type_name == "debt" else "💵"
    type_label = "بدهی" if pay_type_name == "debt" else "طلب"
    action_verb = "پرداخت" if pay_type_name == "debt" else "دریافت"

    text = f"{type_emoji} {action_verb} {type_label}\n\n"
    text += f"👤 طرف حساب: {txn["party_name"] or '-'}\n"
    text += f"💰 مبلغ کل: {format_amount(txn["amount"])} تومان\n"
    text += f"💰 باقی‌مانده: {format_amount(remaining)} تومان\n"
    if txn["card_number"]:
        card_fmt = " ".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
        text += f"💳 کارت: {card_fmt}\n"
    if txn["sheba"]:
        text += f"🏦 شبا: {txn["sheba"]}\n"
    if txn["bank_name"]:
        text += f"🏛 بانک: {normalize_bank_name(txn["bank_name"])}\n"
    text += f"\nنوع پرداخت را انتخاب کنید:"

    await callback.message.edit_text(text, reply_markup=payment_type_keyboard())
    await state.update_data(selected_txn_id=txn_id)
    await state.set_state(PaymentForm.payment_type)
    await safe_callback_answer(callback)

@router.callback_query(PaymentForm.payment_type, F.data.startswith("pay_type:"))
async def payment_type_handler(callback: CallbackQuery, state: FSMContext):
    """Handle payment type selection (full/partial)."""
    pay_type = callback.data.split(":", 1)[1]

    if pay_type == "cancel":
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        await safe_callback_answer(callback)
        return

    data = await state.get_data()

    # Customer-level FIFO payment
    if data.get("customer_party"):
        total_remaining = data.get("customer_total_remaining", 0)
        party = data["customer_party"]

        if pay_type == "full":
            pay_amount = total_remaining
            # Calculate FIFO distribution for full amount
            txn_ids = data.get("customer_txn_ids", [])
            distribution = []
            remaining_amount = pay_amount
            for txn_id in txn_ids:
                if remaining_amount <= 0:
                    break
                txn = TransactionRepository.get_by_id( txn_id)
                if not txn:
                    continue
                txn_remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])
                pay_for_this = min(remaining_amount, txn_remaining)
                if pay_for_this > 0:
                    distribution.append({"txn_id": txn_id, "amount": pay_for_this, "original_amount": txn["amount"]})
                    remaining_amount -= pay_for_this
            await state.update_data(pay_amount=pay_amount, fifo_distribution=distribution)

            pay_type_name = data.get("payment_type", "receivable")
            type_emoji = "💳" if pay_type_name == "debt" else "💵"
            type_label = "بدهی" if pay_type_name == "debt" else "طلب"
            action_verb = "پرداخت" if pay_type_name == "debt" else "دریافت"
            await callback.message.edit_text(
                f"{type_emoji} {action_verb} {type_label}\n\n"
                f"💰 مبلغ: {format_amount(pay_amount)} تومان (کامل)\n\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"STEP 3:\n📝 توضیحات:\n(اختیاری - برای رد کردن «⏭️ رد کردن» را بزنید)",
                reply_markup=None
            )
            await callback.message.answer(
                f"📝 توضیحات {action_verb} (اختیاری):",
                reply_markup=customer_skip_menu()
            )
            await state.set_state(PaymentForm.description)
        else:
            pay_type_name = data.get("payment_type", "receivable")
            type_emoji = "💳" if pay_type_name == "debt" else "💵"
            type_label = "بدهی" if pay_type_name == "debt" else "طلب"
            action_verb = "پرداخت" if pay_type_name == "debt" else "دریافت"
            await callback.message.edit_text(
                f"{type_emoji} {action_verb} {type_label}\n\n"
                f"👤 مشتری: {party}\n"
                f"💰 {type_label} کل: {format_amount(total_remaining)} تومان\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"STEP 2:\n💰 مبلغ:\n"
                f"مبلغ مورد نظر را وارد کنید (حداکثر {format_amount(total_remaining)} تومان):",
                reply_markup=None
            )
            await state.set_state(PaymentForm.amount)

        await safe_callback_answer(callback)
        return

    # Single transaction payment
    txn_id = data.get("selected_txn_id")
    payments_data = data.get("payments_data", {})
    remaining = payments_data.get(txn_id, 0)

    if pay_type == "full":
        await state.update_data(pay_amount=remaining)
        pay_type_name = data.get("payment_type", "debt")
        type_emoji = "💳" if pay_type_name == "debt" else "💵"
        type_label = "بدهی" if pay_type_name == "debt" else "طلب"
        await callback.message.edit_text(
            f"{type_emoji} پرداخت {type_label}\n\n"
            f"💰 مبلغ: {format_amount(remaining)} تومان (کامل)\n\n"
            f"📝 توضیحات پرداخت (اختیاری):\nبرای رد کردن، «⏭️ رد کردن» را بزنید.",
            reply_markup=None
        )
        await callback.message.answer(
            "📝 توضیحات پرداخت (اختیاری):",
            reply_markup=customer_skip_menu()
        )
        await state.set_state(PaymentForm.description)
        await safe_callback_answer(callback)
        return

    # Partial: ask for amount
    await callback.message.edit_text(
        PAY_DEBT_AMOUNT_PROMPT.format(remaining=format_amount(remaining)),
        reply_markup=None
    )
    await state.set_state(PaymentForm.amount)
    await safe_callback_answer(callback)

@router.message(PaymentForm.amount)
async def payment_amount_handler(message: Message, state: FSMContext):
    """Handle partial payment amount input - supports both single-txn and customer-level FIFO."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return

    try:
        amount = float(message.text.replace(",", "").replace("٬", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(INVALID_AMOUNT)
        return

    data = await state.get_data()

    # Customer-level FIFO payment
    if data.get("customer_party"):
        total_remaining = data.get("customer_total_remaining", 0)
        if amount > total_remaining:
            await message.answer(PAYMENT_INVALID_AMOUNT)
            return

        # Calculate FIFO distribution
        txn_ids = data.get("customer_txn_ids", [])
        distribution = []
        remaining_amount = amount
        for txn_id in txn_ids:
            if remaining_amount <= 0:
                break
            txn = TransactionRepository.get_by_id( txn_id)
            if not txn:
                continue
            txn_remaining = PaymentRepository.get_remaining( txn["id"], txn["amount"])
            pay_for_this = min(remaining_amount, txn_remaining)
            if pay_for_this > 0:
                distribution.append({"txn_id": txn_id, "amount": pay_for_this, "original_amount": txn["amount"]})
                remaining_amount -= pay_for_this

        await state.update_data(pay_amount=amount, fifo_distribution=distribution)

        pay_type_name = data.get("payment_type", "receivable")
        type_emoji = "💳" if pay_type_name == "debt" else "💵"
        type_label = "بدهی" if pay_type_name == "debt" else "طلب"
        action_verb = "پرداخت" if pay_type_name == "debt" else "دریافت"
        await message.answer(
            f"{type_emoji} {action_verb} {type_label}\n\n"
            f"💰 مبلغ: {format_amount(amount)} تومان\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"STEP 3:\n📝 توضیحات:\n(اختیاری - برای رد کردن «⏭️ رد کردن» را بزنید)",
            reply_markup=customer_skip_menu()
        )
        await state.set_state(PaymentForm.description)
        return

    # Single transaction payment
    txn_id = data.get("selected_txn_id")
    payments_data = data.get("payments_data", {})
    remaining = payments_data.get(txn_id, 0)

    if amount > remaining:
        await message.answer(PAYMENT_INVALID_AMOUNT)
        return

    await state.update_data(pay_amount=amount)

    pay_type_name = data.get("payment_type", "receivable")
    type_emoji = "💳" if pay_type_name == "debt" else "💵"
    type_label = "بدهی" if pay_type_name == "debt" else "طلب"
    action_verb = "پرداخت" if pay_type_name == "debt" else "دریافت"

    await message.answer(
        f"{type_emoji} {action_verb} {type_label}\n\n"
        f"💰 مبلغ: {format_amount(amount)} تومان\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"STEP 3:\n📝 توضیحات:\n(اختیاری - برای رد کردن «⏭️ رد کردن» را بزنید)",
        reply_markup=customer_skip_menu()
    )
    await state.set_state(PaymentForm.description)

@router.message(PaymentForm.description)
async def payment_description_handler(message: Message, state: FSMContext):
    """Handle optional payment description input."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return

    if message.text == "🔙 بازگشت":
        # Go back to payment type selection
        data = await state.get_data()
        if data.get("customer_party"):
            party = data["customer_party"]
            total_remaining = data.get("customer_total_remaining", 0)
            text = f"💵 دریافت طلب\n\n"
            text += f"👤 مشتری: {party}\n"
            text += f"💰 بدهی کل: {format_amount(total_remaining)} تومان\n\n"
            text += f"━━━━━━━━━━━━━━━━━━\n\n"
            text += f"STEP 1:\n💰 انتخاب نوع پرداخت:\n"
            text += f"├── 💰 کامل ({format_amount(total_remaining)})\n"
            text += f"└── ✂️ جزئی (ورود مبلغ)"
            await message.answer(text, reply_markup=payment_type_keyboard())
        else:
            txn_id = data.get("selected_txn_id")
            payments_data = data.get("payments_data", {})
            remaining = payments_data.get(txn_id, 0)
            await message.answer(
                "نوع دریافت را انتخاب کنید:",
                reply_markup=payment_type_keyboard()
            )
        await state.set_state(PaymentForm.payment_type)
        return

    if message.text and message.text != "⏭️ رد کردن":
        await state.update_data(pay_description=message.text.strip())

    data = await state.get_data()
    pay_type_name = data.get("payment_type", "receivable")
    type_emoji = "💳" if pay_type_name == "debt" else "💵"
    type_label = "بدهی" if pay_type_name == "debt" else "طلب"
    action_verb = "پرداخت" if pay_type_name == "debt" else "دریافت"

    await message.answer(
        f"{type_emoji} {action_verb} {type_label}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"STEP 4:\n📸 رسید پرداخت:\n(اختیاری - عکس ارسال کنید یا «⏭️ بدون عکس» را بزنید)",
        reply_markup=photo_skip_menu()
    )
    await state.set_state(PaymentForm.photo)

@router.message(PaymentForm.photo)
async def payment_photo_handler(message: Message, state: FSMContext):
    """Handle optional receipt photo upload."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return

    if message.text == "🔙 بازگشت":
        # Go back to description step
        await message.answer(
            "📝 توضیحات پرداخت (اختیاری):",
            reply_markup=customer_skip_menu()
        )
        await state.set_state(PaymentForm.description)
        return

    photo_path = None
    if message.text and message.text in ("⏭️ بدون عکس", "⏭️ رد کردن"):
        photo_path = None
    elif message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        try:
            photo_path = await _save_photo(message.bot, photo, message.from_user.id)
        except Exception as e:
            logger.error(f"Error saving payment receipt photo: {e}")
            await message.answer("⚠️ خطا در ذخیره عکس. لطفاً دوباره تلاش کنید یا «⏭️ بدون عکس» را بزنید.")
            return
    else:
        await message.answer("📸 لطفاً یک عکس ارسال کنید یا «⏭️ بدون عکس» را انتخاب کنید.")
        return

    if photo_path:
        await state.update_data(pay_photo=photo_path)

    # Build confirmation
    data = await state.get_data()
    pay_amount = data.get("pay_amount", 0)
    pay_description = data.get("pay_description")

    if data.get("customer_party"):
        # Customer-level FIFO confirmation
        party = data["customer_party"]
        total_remaining = data.get("customer_total_remaining", 0)

        text = f"⚠️ تأیید نهایی\n\n"
        text += f"├── 👤 مشتری: {party}\n"
        text += f"├── 💰 مبلغ: {format_amount(pay_amount)} تومان\n"
        text += f"├── 📝 توضیحات: {pay_description or '—'}\n"
        text += f"└── 📸 رسید: {'✅ دارد' if data.get('pay_photo') else '❌ ندارد'}\n"
        text += f"\n💰 باقی‌مانده: {format_amount(max(0, total_remaining - pay_amount))} تومان\n"

        await message.answer(text, reply_markup=payment_confirm_keyboard())
        await state.set_state(PaymentForm.confirm)
    else:
        # Single transaction confirmation
        txn_id = data.get("selected_txn_id")
        payments_data = data.get("payments_data", {})
        remaining = payments_data.get(txn_id, 0)

        txn = TransactionRepository.get_by_id( txn_id)
        pay_type = data.get("payment_type", "debt")
        type_label = "بدهی" if pay_type == "debt" else "طلب"
        type_emoji = "💳" if pay_type == "debt" else "💵"

        text = f"⚠️ تأیید نهایی\n\n"
        text += f"├── 👤 مشتری: {txn["party_name"] or '-'}\n"
        text += f"├── 💰 مبلغ: {format_amount(pay_amount)} تومان\n"
        text += f"├── 📝 توضیحات: {pay_description or '—'}\n"
        text += f"└── 📸 رسید: {'✅ دارد' if data.get('pay_photo') else '❌ ندارد'}\n"
        text += f"\n💰 باقی‌مانده: {format_amount(max(0, remaining - pay_amount))} تومان\n"
        if txn["card_number"]:
            card_fmt = " ".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
            text += f"💳 کارت: {card_fmt}\n"
        if txn["sheba"]:
            text += f"🏦 شبا: {txn["sheba"]}\n"
        if txn["bank_name"]:
            text += f"🏛 بانک: {normalize_bank_name(txn["bank_name"])}\n"

        has_pay_info = bool(txn["card_number"] or txn["sheba"] or txn["bank_name"])
        await message.answer(text, reply_markup=payment_confirm_keyboard(txn["id"], has_pay_info))
        await state.set_state(PaymentForm.confirm)

@router.callback_query(F.data.startswith("pay_sms:"))
async def payment_sms_callback(callback: CallbackQuery):
    """Handle SMS copy from payment confirmation screen."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        txn = TransactionRepository.get_by_id( txn_id)
        if not txn or txn["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ مورد یافت نشد.", show_alert=True)
            return

        if not txn["card_number"] and not txn["sheba"] and not txn["bank_name"]:
            await safe_callback_answer(callback, "⚠️ اطلاعات پرداختی موجود نیست.", show_alert=True)
            return

        party = txn["party_name"] or "-"
        amount_fmt = format_amount(txn["amount"])
        amount_words = amount_to_persian_words(txn["amount"])

        lines = []

        if txn["card_number"]:
            card_fmt = " ".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
            lines.append("کارت:")
            lines.append(card_fmt)
            lines.append("")

        if txn["sheba"]:
            lines.append("شبا:")
            lines.append(txn["sheba"])
            lines.append("")

        lines.append(party)
        if txn["bank_name"]:
            lines.append(f"بانک: {normalize_bank_name(txn["bank_name"])}")
        lines.append(f"{amount_fmt} تومان")
        lines.append(amount_words)

        text_to_copy = "\n".join(lines)

        await safe_callback_answer(callback, "✅ کپی شد", show_alert=True)
        await callback.message.answer(
            f"📩 اطلاعات پرداخت\n\n<code>{text_to_copy}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in payment sms callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در کپی.", show_alert=True)

@router.callback_query(PaymentForm.confirm, F.data.startswith("pay_confirm"))
async def payment_confirm_handler(callback: CallbackQuery, state: FSMContext):
    """Handle payment confirmation - supports single-txn and customer-level FIFO."""
    if callback.data == "pay_confirm_no":
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        await safe_callback_answer(callback)
        return

    data = await state.get_data()
    pay_amount = data.get("pay_amount")

    # Customer-level FIFO payment
    if data.get("customer_party"):
        distribution = data.get("fifo_distribution", [])
        party = data["customer_party"]
        pay_description = data.get("pay_description")
        pay_photo = data.get("pay_photo")

        pay_type = data.get("payment_type", "receivable")
        type_emoji = "💳" if pay_type == "debt" else "💵"
        type_label = "بدهی" if pay_type == "debt" else "طلب"
        action_verb = "پرداخت" if pay_type == "debt" else "دریافت"
        payment_type_str = "debt_payment" if pay_type == "debt" else "receivable_payment"

        try:
            user = UserRepository.get_or_create(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )

            settled_ids = []
            for d in distribution:
                PaymentRepository.create(
                    transaction_id=d["txn_id"],
                    user_id=user["id"],
                    amount=d["amount"],
                    payment_type=payment_type_str,
                    description=pay_description,
                    photo_path=pay_photo,
                    jalali_date=get_jalali_date(),
                    jalali_time=get_jalali_time(),
                    jalali_full=get_jalali_full()
                )
                remaining = PaymentRepository.get_remaining( d["txn_id"], d.get("original_amount", d["amount"]))
                if remaining <= 0:
                    txn = TransactionRepository.get_by_id( d["txn_id"])
                    if txn:
                        TransactionRepository.settle_transaction( d["txn_id"])
                        settled_ids.append(d["txn_id"])

            # Update customer financial summaries for all affected customers
            updated_customers = set()
            for d in distribution:
                txn = TransactionRepository.get_by_id( d["txn_id"])
                if txn and txn["customer_id"] and txn["customer_id"] not in updated_customers:
                    CustomerRepository.update_financial_summary( txn["customer_id"])
                    updated_customers.add(txn["customer_id"])

            logger.info(f"FIFO payment recorded: {pay_amount} for customer {party} by user {user["telegram_id"]}")

            success_msg = (
                f"✅ {action_verb} {type_label} با موفقیت ثبت شد\n"
                f"👤 {party}\n"
                f"💰 مبلغ: {format_amount(pay_amount)} تومان\n"
                f"📌 {len(distribution)} مورد {action_verb} شد"
            )
            await state.clear()
            await callback.message.edit_text(success_msg, reply_markup=None)
            if settled_ids:
                await callback.message.answer(f"🎉 {len(settled_ids)} مورد کاملاً تسویه شد!")
            await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Error processing FIFO payment: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
            await state.clear()
        await safe_callback_answer(callback)
        return

    # Single transaction payment
    txn_id = data.get("selected_txn_id")
    await _process_payment(callback, state, txn_id, pay_amount)

async def _process_payment(callback: CallbackQuery, state: FSMContext,
                           txn_id: int, amount: float):
    """Process a payment (debt or receivable)."""
    data = await state.get_data()
    pay_type = data.get("payment_type", "debt")
    type_label = "بدهی" if pay_type == "debt" else "طلب"
    type_emoji = "💳" if pay_type == "debt" else "💵"
    payment_type_str = "debt_payment" if pay_type == "debt" else "receivable_payment"
    pay_description = data.get("pay_description")
    pay_photo = data.get("pay_photo")

    try:
        user = UserRepository.get_or_create(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )

        txn = TransactionRepository.get_by_id( txn_id)
        if not txn:
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
            await state.clear()
            await safe_callback_answer(callback)
            return

        # Record payment
        PaymentRepository.create(
            transaction_id=txn_id,
            user_id=user["id"],
            amount=amount,
            payment_type=payment_type_str,
            description=pay_description,
            photo_path=pay_photo,
            jalali_date=get_jalali_date(),
            jalali_time=get_jalali_time(),
            jalali_full=get_jalali_full()
        )

        # Check if fully paid
        remaining = PaymentRepository.get_remaining( txn_id, txn["amount"])
        settled = False
        if remaining <= 0:
            TransactionRepository.settle_transaction( txn_id)
            settled = True

        # Update customer financial summary
        if txn["customer_id"]:
            CustomerRepository.update_financial_summary( txn["customer_id"])

        logger.info(f"Payment recorded: {amount} for {type_label} #{txn_id} by user {user["telegram_id"]}")

        action_verb = "پرداخت" if pay_type == "debt" else "دریافت"
        await state.clear()
        await callback.message.edit_text(
            f"{type_emoji} {type_label} #{txn_id}\n"
            f"💰 {action_verb}: {format_amount(amount)} تومان\n"
            f"💰 باقی‌مانده: {format_amount(max(0, remaining))} تومان",
            reply_markup=None
        )

        if settled:
            settle_msg = PAY_DEBT_SETTLED if pay_type == "debt" else RECEIVE_RECV_SETTLED
            await callback.message.answer(f"🎉 {settle_msg}")

        await callback.message.answer(
            PAY_DEBT_SUCCESS if pay_type == "debt" else RECEIVE_RECV_SUCCESS,
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
        await state.clear()

    await safe_callback_answer(callback)

# ==============================
# Dashboard
# ==============================

@router.message(F.text == "📊 داشبورد مالی")
@router.message(Command("dashboard"))
async def show_dashboard(message: Message):
    """Display financial dashboard."""
    try:
        user = get_user(message)
        dashboard_text = _build_dashboard_text( user["id"])
        await message.answer(dashboard_text, reply_markup=export_menu())
        await message.answer(MENU_TEXT, reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Error showing dashboard: {e}")
        await message.answer(ERROR_GENERAL)

# ==============================
# Customer Management
# ==============================

@router.message(F.text == "👥 مدیریت مشتریان")
async def customer_management(message: Message, state: FSMContext):
    """Show customer management menu."""
    await state.clear()
    await message.answer("👥 مدیریت مشتریان", reply_markup=customer_menu())

@router.message(F.text == "👤 افزودن مشتری")
async def customer_add_start(message: Message, state: FSMContext):
    """Start add customer flow."""
    await state.set_state(CustomerForm.name)
    await message.answer(CUSTOMER_NAME, reply_markup=cancel_menu())

@router.message(CustomerForm.name)
async def customer_add_name(message: Message, state: FSMContext):
    """Handle customer name."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=customer_menu())
        return
    if not message.text or len(message.text.strip()) == 0:
        await message.answer("⚠️ لطفاً نام مشتری را وارد کنید.")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(CustomerForm.phone)
    await message.answer(CUSTOMER_PHONE, reply_markup=customer_skip_menu())

@router.message(CustomerForm.phone)
async def customer_add_phone(message: Message, state: FSMContext):
    """Handle customer phone."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=customer_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(CustomerForm.name)
        await message.answer(CUSTOMER_NAME, reply_markup=cancel_menu())
        return
    
    if message.text == "⏭️ رد کردن":
        await state.update_data(phone="")
    else:
        await state.update_data(phone=message.text.strip())
    await state.set_state(CustomerForm.address)
    await message.answer(CUSTOMER_ADDRESS, reply_markup=customer_skip_menu())

@router.message(CustomerForm.address)
async def customer_add_address(message: Message, state: FSMContext):
    """Handle customer address."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=customer_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(CustomerForm.phone)
        await message.answer(CUSTOMER_PHONE, reply_markup=customer_skip_menu())
        return
    
    if message.text == "⏭️ رد کردن":
        await state.update_data(address="")
    else:
        await state.update_data(address=message.text.strip())
    await state.set_state(CustomerForm.notes)
    await message.answer(CUSTOMER_NOTES, reply_markup=customer_skip_menu())

@router.message(CustomerForm.notes)
async def customer_add_notes(message: Message, state: FSMContext):
    """Handle customer notes and save."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=customer_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(CustomerForm.address)
        await message.answer(CUSTOMER_ADDRESS, reply_markup=customer_skip_menu())
        return
    
    notes = "" if message.text == "⏭️ رد کردن" else message.text.strip()
    
    data = await state.get_data()
    try:
        user = get_user(message)
        CustomerRepository.create(
            user_id=user["id"],
            full_name=data["name"],
            phone=data.get("phone", ""),
            address=data.get("address", ""),
            notes=notes
        )
        logger.info(f"Customer added: {data['name']} by user {user["telegram_id"]}")
        
        await state.clear()
        await message.answer(
            f"{CUSTOMER_SAVED}\n\n👤 نام: {data['name']}",
            reply_markup=customer_menu()
        )
    except Exception as e:
        logger.error(f"Error adding customer: {e}")
        await message.answer(ERROR_GENERAL, reply_markup=customer_menu())

@router.message(F.text == "📋 لیست مشتریان")
async def customer_list(message: Message):
    """Show list of customers."""
    user = get_user(message)
    customers = CustomerRepository.get_by_user(user["id"])
        
    if not customers:
        await message.answer(CUSTOMER_EMPTY, reply_markup=customer_menu())
        return
        
    text = "👤 لیست مشتریان:\n\n"
    for i, c in enumerate(customers, 1):
        debt_str = format_amount(c["total_debt"])
        recv_str = format_amount(c["total_receivable"])
        text += f"{i}. {c['full_name']}\n   📞 {c['phone'] or '-'}\n   💳 بدهی: {debt_str} | طلب: {recv_str}\n\n"
        
    # Simple pagination: show first 10
    lines = text.split("\n\n")
    if len(lines) > 15:
        text = "\n\n".join(lines[:15]) + "\n\n..."
        
    if len(customers) > 10:
        text += f"\n📊 مجموع: {len(customers)} مشتری"
        
    await message.answer(text, reply_markup=customer_menu())

@router.message(F.text == "🔍 جستجوی مشتری")
async def customer_search_start(message: Message, state: FSMContext):
    """Start customer search."""
    await state.set_state(CustomerSearchForm.query)
    await message.answer(CUSTOMER_SEARCH, reply_markup=cancel_menu())

@router.message(CustomerSearchForm.query)
async def customer_search_result(message: Message, state: FSMContext):
    """Show customer search results."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=customer_menu())
        return
    
    query = message.text
    user = get_user(message)
    customers = CustomerRepository.search( user["id"], query)
        
    if not customers:
        await message.answer(CUSTOMER_NOT_FOUND, reply_markup=customer_menu())
        await state.clear()
        return
        
    text = "🔍 نتایج جستجو:\n\n"
    for c in customers:
        debt_str = format_amount(c["total_debt"])
        recv_str = format_amount(c["total_receivable"])
        text += f"🆔 {c['id']}\n👤 {c['full_name']}\n📞 {c['phone'] or '-'}\n💳 بدهی: {debt_str} | طلب: {recv_str}\n\n"
        
    await message.answer(text, reply_markup=customer_menu())
    await state.clear()

@router.message(F.text == "✏️ ویرایش مشتری")
async def customer_edit_select(message: Message, state: FSMContext):
    """Start customer edit - show customer list for selection."""
    user = get_user(message)
    customers = CustomerRepository.get_by_user(user["id"])

    if not customers:
        await message.answer(CUSTOMER_EMPTY, reply_markup=customer_menu())
        return

    await state.set_state(CustomerEditForm.select)
    await message.answer(
        "👤 مشتری مورد نظر را برای ویرایش انتخاب کنید:",
        reply_markup=customer_select_keyboard(customers, action="edit")
    )

@router.callback_query(CustomerEditForm.select, F.data.startswith("edit_customer:"))
async def customer_edit_callback(callback: CallbackQuery, state: FSMContext):
    """Handle customer selection for editing."""
    data_str = callback.data
    customer_id_str = data_str.split(":", 1)[1]

    if customer_id_str == "cancel":
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=customer_menu())
        await safe_callback_answer(callback)
        return

    try:
        customer_id = int(customer_id_str)
        await state.update_data(customer_id=customer_id)
        await state.set_state(CustomerEditForm.name)
        await callback.message.edit_text("👤 مشتری انتخاب شد. نام جدید را وارد کنید (یا - برای عدم تغییر):")
        await callback.message.answer("لطفاً نام جدید را ارسال کنید:", reply_markup=cancel_back_menu())
    except ValueError:
        await safe_callback_answer(callback, "⚠️ خطا در انتخاب مشتری.")

    await safe_callback_answer(callback)

@router.message(CustomerEditForm.name)
async def customer_edit_name(message: Message, state: FSMContext):
    """Handle customer edit name."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=customer_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    data = await state.get_data()
    try:
        name = None if message.text == "-" else message.text
        CustomerRepository.update( data["customer_id"], full_name=name)
        
        await state.clear()
        await message.answer(CUSTOMER_UPDATED, reply_markup=customer_menu())
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        await message.answer(ERROR_GENERAL)

@router.message(F.text == "🗑 حذف مشتری")
async def customer_delete_select(message: Message, state: FSMContext):
    """Start customer delete - show customer list for selection."""
    user = get_user(message)
    customers = CustomerRepository.get_by_user(user["id"])

    if not customers:
        await message.answer(CUSTOMER_EMPTY, reply_markup=customer_menu())
        return

    await state.set_state(CustomerDeleteForm.select)
    await message.answer(
        "👤 مشتری مورد نظر را برای حذف انتخاب کنید:",
        reply_markup=customer_select_keyboard(customers, action="delete")
    )

@router.callback_query(CustomerDeleteForm.select, F.data.startswith("delete_customer:"))
async def customer_delete_callback(callback: CallbackQuery, state: FSMContext):
    """Handle customer selection for deletion."""
    data_str = callback.data
    customer_id_str = data_str.split(":", 1)[1]

    if customer_id_str == "cancel":
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=customer_menu())
        await safe_callback_answer(callback)
        return

    try:
        customer_id = int(customer_id_str)
        await state.update_data(customer_id=customer_id)

        customer = CustomerRepository.get_by_id( customer_id)
        name = customer["full_name"] if customer else f"شناسه {customer_id}"

        await callback.message.edit_text(
            f"⚠️ آیا از حذف مشتری «{name}» اطمینان دارید؟",
            reply_markup=confirm_keyboard()
        )
        await state.set_state(CustomerDeleteForm.confirm)
    except ValueError:
        await safe_callback_answer(callback, "⚠️ خطا در انتخاب مشتری.")

    await safe_callback_answer(callback)

@router.callback_query(CustomerDeleteForm.confirm)
async def customer_delete_execute(callback: CallbackQuery, state: FSMContext):
    """Execute customer deletion."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        try:
            CustomerRepository.delete( data["customer_id"])
            await state.clear()
            await callback.message.edit_text(CUSTOMER_DELETED, reply_markup=None)
            await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Error deleting customer: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
    
    await safe_callback_answer(callback)

# ==============================
# Financial Reports
# ==============================

async def _send_report(message: Message, period: str):
    """Generate and send a financial report."""
    try:
        user = get_user(message)
        start, end = get_current_jalali_period(period)
        
        transactions = TransactionRepository.get_by_date_range(
            user_id=user["id"], start_date=start, end_date=end
        )
        
        totals = {"income": 0, "expense": 0, "debt": 0, "receivable": 0}
        for txn in transactions:
            if txn["transaction_type"] in totals:
                totals[txn["transaction_type"]] += txn["amount"]
        
        income = totals["income"]
        expense = totals["expense"]
        debts = totals["debt"]
        receivables = totals["receivable"]
        balance = income - expense + receivables - debts
        
        if balance > 0:
            status = "✅ مثبت و سودده 🟢"
        elif balance < 0:
            status = "⚠️ منفی و دارای زیان 🔴"
        else:
            status = "⚪️ صفر و تسویه شده"
        
        balance_line = f"{DASHBOARD_BALANCE}: {format_amount(balance)} تومان"
        
        # Calculate additional metrics
        txn_count = len(transactions)
        
        # Calculate days in period for averages
        from app.utils.jdatetime_helper import get_days_between
        days_in_period = max(1, get_days_between(start, end))
        avg_daily_income = income / days_in_period
        avg_daily_expense = expense / days_in_period
        
        period_name = REPORT_PERIODS.get(period, period)
        report_text = REPORT_TITLE.format(
            period=period_name,
            start=start,
            end=end,
            income=format_amount(income),
            expense=format_amount(expense),
            debt=format_amount(debts),
            receivable=format_amount(receivables),
            balance_line=balance_line,
            status=status,
            txn_count=txn_count,
            avg_daily_income=format_amount(avg_daily_income),
            avg_daily_expense=format_amount(avg_daily_expense)
        )
        
        await message.answer(report_text, reply_markup=export_menu())
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await message.answer(ERROR_GENERAL)

@router.message(F.text == "📈 گزارش‌های مالی")
@router.message(Command("report"))
async def show_report_menu(message: Message):
    """Show report menu."""
    await message.answer("📈 گزارش‌های مالی", reply_markup=report_menu())

@router.message(F.text == "📅 گزارش روزانه")
async def report_daily(message: Message):
    """Show daily report."""
    await _send_report(message, "daily")

@router.message(F.text == "📅 گزارش هفتگی")
async def report_weekly(message: Message):
    """Show weekly report."""
    await _send_report(message, "weekly")

@router.message(F.text == "📅 گزارش ماهانه")
async def report_monthly(message: Message):
    """Show monthly report."""
    await _send_report(message, "monthly")

@router.message(F.text == "📅 گزارش سالانه")
async def report_yearly(message: Message):
    """Show yearly report."""
    await _send_report(message, "yearly")

# ==============================
# Export Handlers
# ==============================

@router.callback_query(F.data.startswith("export_"))
async def handle_export(callback: CallbackQuery):
    """Handle export requests."""
    export_type = callback.data.replace("export_", "")
    
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await callback.message.edit_text(ACCESS_DENIED)
            await safe_callback_answer(callback)
            return
        
        transactions = TransactionRepository.get_by_user(user["id"], limit=1000)
        
        if not transactions:
            await callback.message.edit_text("📭 هیچ تراکنشی برای خروجی وجود ندارد.")
            await safe_callback_answer(callback)
            return
        
        await callback.message.edit_text("⏳ در حال ایجاد فایل خروجی...")
        
        if export_type == "excel":
            filepath = await export_transactions_excel(transactions)
        elif export_type == "pdf":
            filepath = await export_transactions_pdf(transactions)
        else:
            await callback.message.edit_text(ERROR_GENERAL)
            await safe_callback_answer(callback)
            return
        
        # Send file
        document = FSInputFile(filepath)
        await callback.message.answer_document(
            document,
            caption=f"📊 گزارش تراکنش‌های مالی - {get_jalali_date()} ساعت {get_jalali_time()}"
        )
        await safe_delete(callback.message)
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        await callback.message.edit_text(ERROR_GENERAL)
    
    await safe_callback_answer(callback)

# ==============================
# Search
# ==============================

@router.message(F.text == "🔍 جستجو")
@router.message(Command("search"))
async def search_start(message: Message, state: FSMContext):
    """Start search flow."""
    await state.set_state(SearchForm.query)
    await message.answer(SEARCH_PROMPT, reply_markup=cancel_menu())

@router.message(SearchForm.query)
async def search_query(message: Message, state: FSMContext):
    """Process search query."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    await state.update_data(query=message.text)
    await state.set_state(SearchForm.transaction_type)
    await message.answer("نوع تراکنش را انتخاب کنید:", reply_markup=transaction_type_keyboard())

@router.callback_query(F.data.in_(["search_type_income", "search_type_expense", "search_type_debt", "search_type_receivable", "search_type_all"]))
async def search_type_selected(callback: CallbackQuery, state: FSMContext):
    """Process search type filter."""
    data = await state.get_data()
    query = data.get("query", "")
    
    ttype = callback.data.replace("search_type_", "")
    if ttype == "all":
        ttype = None
    
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await callback.message.edit_text(ACCESS_DENIED)
            await safe_callback_answer(callback)
            return
        
        results = TransactionRepository.search(
            user_id=user["id"],
            query_text=query,
            transaction_type=ttype,
            limit=20
        )
        
        if not results:
            await callback.message.edit_text(SEARCH_EMPTY)
        else:
            type_icons = {
                "income": "💰", "expense": "💸",
                "debt": "📋", "receivable": "📌"
            }
            type_names = {
                "income": "درآمد", "expense": "هزینه",
                "debt": "بدهی", "receivable": "طلب"
            }
            
            text = f"🔍 نتایج جستجو برای «{query}»:\n\n"
            for txn in results[:10]:
                icon = type_icons.get(txn["transaction_type"], "📄")
                tname = type_names.get(txn["transaction_type"], txn["transaction_type"])
                text += f"{icon} {tname}\n"
                text += f"💵 {format_amount(txn["amount"])} تومان\n"
                if txn["description"]:
                    text += f"📝 {txn["description"]}\n"
                text += f"📅 {txn["jalali_date"]} ساعت {txn["jalali_time"]}\n\n"
            
            if len(results) > 10:
                text += f"\n... و {len(results) - 10} نتیجه دیگر"
        
        await callback.message.edit_text(text)
        await state.clear()
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Search error: {e}")
        await callback.message.edit_text(ERROR_GENERAL)
    
    await safe_callback_answer(callback)

# ==============================
# Backup
# ==============================

@router.message(F.text == "💾 پشتیبان‌گیری")
@router.message(Command("backup"))
async def backup_menu_handler(message: Message):
    """Show backup menu."""
    await message.answer("💾 پشتیبان‌گیری\n\nاز این بخش می‌توانید از دیتابیس خود پشتیبان تهیه کنید.", reply_markup=backup_menu())

@router.callback_query(F.data == "backup_create")
async def backup_create(callback: CallbackQuery):
    """Create database backup."""
    await callback.message.edit_text("⏳ در حال ایجاد پشتیبان...")
    
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await callback.message.edit_text(ACCESS_DENIED)
            await safe_callback_answer(callback)
            return
        
        # Ensure backup dir exists
        os.makedirs(settings.BACKUP_DIR, exist_ok=True)
        
        # Get database file path
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        # Create backup
        backup_filename = f"hesab_backup_{get_jalali_date().replace('/', '-')}_{get_jalali_time().replace(':', '-')}.db"
        backup_path = os.path.join(settings.BACKUP_DIR, backup_filename)
        shutil.copy2(db_path, backup_path)
        
        file_size = os.path.getsize(backup_path)
        
        # Save backup record
        BackupRepository.create(
            user_id=user["id"],
            filename=backup_filename,
            file_size=file_size,
            jalali_date=get_jalali_date(),
            jalali_time=get_jalali_time()
        )
        
        logger.info(f"Backup created: {backup_filename}")
        
        # Send backup file
        document = FSInputFile(backup_path)
        await callback.message.edit_text(f"{BACKUP_CREATED}\n📦 حجم: {file_size / 1024:.1f} KB")
        await callback.message.answer_document(
            document,
            caption=f"💾 پشتیبان تاریخ {get_jalali_date()} ساعت {get_jalali_time()}"
        )
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await callback.message.edit_text(BACKUP_ERROR)
    
    await safe_callback_answer(callback)

@router.callback_query(F.data == "backup_restore")
async def backup_restore(callback: CallbackQuery):
    """Restore from backup - show list of available backups."""
    await callback.message.edit_text("🔄 در حال جستجوی پشتیبان‌ها...")
    
    if not os.path.exists(settings.BACKUP_DIR):
        await callback.message.edit_text("📭 هیچ پشتیبان‌گیری انجام نشده است.\n\nابتدا از بخش پشتیبان‌گیری یک نسخه پشتیبان ایجاد کنید.")
        await safe_callback_answer(callback)
        return
    
    backup_files = sorted([
        f for f in os.listdir(settings.BACKUP_DIR) if f.endswith('.db')
    ], reverse=True)
    
    if not backup_files:
        await callback.message.edit_text("📭 هیچ فایل پشتیبان .db یافت نشد.")
        await safe_callback_answer(callback)
        return
    
    text = "🔄 لیست فایل‌های پشتیبان موجود:\n\n"
    for i, f in enumerate(backup_files[:10], 1):
        fpath = os.path.join(settings.BACKUP_DIR, f)
        fsize = os.path.getsize(fpath)
        text += f"{i}. 📦 {f}\n   📊 {fsize / 1024:.1f} KB\n\n"
    
    text += "⚠️ برای بازیابی، لطفاً به صورت دستی فایل پشتیبان را جایگزین فایل دیتابیس اصلی کنید:\n"
    text += f"📁 مسیر دیتابیس: {settings.DATABASE_URL.replace('sqlite:///', '')}"
    
    await callback.message.edit_text(text)
    await safe_callback_answer(callback)

@router.callback_query(F.data == "backup_list")
async def backup_list(callback: CallbackQuery):
    """Show backup list."""
    try:
        backups = BackupRepository.get_recent()
        if not backups:
            await callback.message.edit_text(BACKUP_LIST_EMPTY)
        else:
            text = "📋 لیست پشتیبان‌ها:\n\n"
            for b in backups:
                size_str = f"{b.file_size / 1024:.1f} KB" if b.file_size else "نامشخص"
                time_str = f" ساعت {b.jalali_time}" if b.jalali_time else ""
                text += f"📦 {b.filename}\n📅 {b.jalali_date}{time_str}\n📊 {size_str}\n\n"
            await callback.message.edit_text(text)
    except Exception as e:
        logger.error(f"Backup list error: {e}")
        await callback.message.edit_text(ERROR_GENERAL)
    
    await safe_callback_answer(callback)

# ==============================
# Settings
# ==============================

@router.message(F.text == "⚙️ تنظیمات")
async def settings_handler(message: Message):
    """Show settings menu."""
    user = get_user(message)
    text = f"⚙️ تنظیمات\n\n👤 نام: {user["first_name"] or 'کاربر'}\n🆔 شناسه: {user["telegram_id"]}\n👑 مدیر: {'✅' if user["is_admin"] else '❌'}"
    await message.answer(text, reply_markup=settings_menu())

@router.message(F.text == "👤 اطلاعات کاربری")
async def user_info(message: Message):
    """Show user info."""
    user = get_user(message)

    # Get transaction counts
    txn_count = len(TransactionRepository.get_by_user(user["id"], limit=1000))
    customer_count = len(CustomerRepository.get_by_user(user["id"]))

    text = f"""👤 اطلاعات کاربری

🆔 شناسه: {user["telegram_id"]}
📝 نام کاربری: @{user.get("username") or 'ندارد'}
👤 نام: {user.get("first_name") or 'ندارد'}
📅 تاریخ ثبت: {get_jalali_date()} ساعت {get_jalali_time()}

📊 آمار:
📄 تعداد تراکنش‌ها: {txn_count}
👥 تعداد مشتریان: {customer_count}"""

    await message.answer(text, reply_markup=settings_menu())

@router.message(F.text == "📊 خلاصه حساب")
async def account_summary(message: Message):
    """Show account summary."""
    await show_dashboard(message)

# ==============================
# View Photo Handler
# ==============================

@router.callback_query(F.data.startswith("view_photo:"))
async def view_photo_callback(callback: CallbackQuery):
    """Handle view photo button press."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    try:
        txn = TransactionRepository.get_by_id( txn_id)
        if not txn or not txn["photo_path"]:
            await safe_callback_answer(callback, "⚠️ عکسی برای این تراکنش وجود ندارد.", show_alert=True)
            return
        
        if os.path.exists(txn["photo_path"]):
            photo = FSInputFile(txn["photo_path"])
            await callback.message.answer_photo(
                photo,
                caption=f"📸 عکس تراکنش (شناسه: {txn["id"]})"
            )
            await safe_callback_answer(callback)
        else:
            await safe_callback_answer(callback, "⚠️ فایل عکس در سرور یافت نشد.", show_alert=True)
    except Exception as e:
        logger.error(f"Error viewing photo: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در نمایش عکس.", show_alert=True)

@router.callback_query(F.data.startswith("view_payment_photo:"))
async def view_payment_photo_callback(callback: CallbackQuery):
    """Handle view payment receipt photo button press."""
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    try:
        payments = PaymentRepository.get_by_transaction( txn_id)
        photo_payments = [p for p in payments if p["photo_path"]]
        if not photo_payments:
            await safe_callback_answer(callback, "⚠️ عکس رسید پرداختی وجود ندارد.", show_alert=True)
            return

        for p in photo_payments:
            if os.path.exists(p["photo_path"]):
                photo = FSInputFile(p["photo_path"])
                await callback.message.answer_photo(
                    photo,
                    caption=f"📸 رسید پرداخت ({format_amount(p['amount'])} تومان - {p['jalali_date']})"
                )
            else:
                await callback.message.answer(f"⚠️ فایل رسید پرداخت #{p['id']} در سرور یافت نشد.")
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error viewing payment photo: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در نمایش عکس.", show_alert=True)

# ==============================
# Card & Sheba Handlers
# ==============================

def _group_cards_by_owner(cards: list) -> list:
    """Group cards by customer name (similar to _group_receivables_by_customer).

    Returns a sorted list of dicts:
      {
        "name": str,
        "customer_id": int | None,
        "cards": list[CardInfo],
        "count": int,
      }
    """
    groups = {}
    for card in cards:
        key = card["name"] or "-"
        if key not in groups:
            groups[key] = {
                "name": key,
                "customer_id": card["customer_id"],
                "cards": [],
                "count": 0,
            }
        groups[key]["cards"].append(card)
        groups[key]["count"] += 1

    result = sorted(groups.values(), key=lambda g: (-g["count"], g["name"]))
    return result

def _build_card_group_summary_text(groups: list, title: str) -> str:
    """Build summary text for the card customer overview."""
    total_cards = sum(g["count"] for g in groups)
    total_owners = len(groups)

    text = f"💳 {title}\n\n"
    text += f"📊 {total_cards} کارت | 👤 {total_owners} نام\n"
    text += "——————————"

    for g in groups:
        text += f"\n\n👤 {g['name']}"
        text += f"\n   📋 {g['count']} کارت/شبا"
        has_card = any(c.card_number for c in g["cards"])
        has_sheba = any(c.sheba for c in g["cards"])
        parts = []
        if has_card:
            parts.append("کارت")
        if has_sheba:
            parts.append("شبا")
        if parts:
            text += f" ({' + '.join(parts)})"

    return text

def _build_card_owner_detail_text(group: dict) -> str:
    """Build detailed view of a customer's cards."""
    name = group["name"]
    cards = group["cards"]
    count = group["count"]

    text = f"👤 {name}\n"
    text += f"📋 {count} کارت/شبا\n"
    text += "——————————"

    for card in cards:
        text += f"\n\n💳 #{card["id"]}"
        if card["card_number"]:
            card_fmt = "-".join([card["card_number"][i:i+4] for i in range(0, 16, 4)])
            text += f"\n   💳 کارت: {card_fmt}"
        if card["sheba"]:
            text += f"\n   🏦 شبا: IR{card["sheba"]}"
        if card["bank_name"]:
            text += f"\n   🏛 بانک: {normalize_bank_name(card["bank_name"])}"
        text += f"\n   📅 ثبت: {card["created_at"].strftime('%Y/%m/%d') if card["created_at"] else '-'}"

    return text

def _build_card_detail_text(card) -> str:
    """Build full detail text for a single card."""
    card_display = card["card_number"] or "—"
    sheba_display = f"IR{card["sheba"]}" if card["sheba"] else "—"
    bank_display = normalize_bank_name(card["bank_name"]) or "—"

    text = f"""💳 {card["name"]}

💳 شماره کارت: <code>{card_display}</code>
🏦 شماره شبا: <code>{sheba_display}</code>
🏛 نام بانک: {bank_display}
📅 ثبت: {card["created_at"].strftime('%Y/%m/%d') if card["created_at"] else '-'}"""
    return text

def _get_card_linked_counts(user_id: int, card_number: str = None, sheba: str = None) -> dict:
    """Count linked debts, receivables, and payments for a card."""
    debt_count = 0
    recv_count = 0
    payment_count = 0

    transactions = get_collection("transactions")
    payments_col = get_collection("payments")

    if card_number:
        debt_count += transactions.count_documents({
            "user_id": user_id, "transaction_type": "debt", "card_number": card_number
        })
        recv_count += transactions.count_documents({
            "user_id": user_id, "transaction_type": "receivable", "card_number": card_number
        })

    if sheba:
        sheba_with_ir = f"IR{sheba}" if not sheba.startswith("IR") else sheba
        sheba_without_ir = sheba.replace("IR", "") if sheba.startswith("IR") else sheba
        debt_count += transactions.count_documents({
            "user_id": user_id, "transaction_type": "debt",
            "sheba": {"$in": [sheba_with_ir, sheba_without_ir]}
        })
        recv_count += transactions.count_documents({
            "user_id": user_id, "transaction_type": "receivable",
            "sheba": {"$in": [sheba_with_ir, sheba_without_ir]}
        })

    if card_number or sheba:
        txn_ids = []
        if card_number:
            for t in transactions.find({"user_id": user_id, "card_number": card_number}, {"id": 1}):
                txn_ids.append(t["id"])
        if sheba:
            sheba_with_ir = f"IR{sheba}" if not sheba.startswith("IR") else sheba
            sheba_without_ir = sheba.replace("IR", "") if sheba.startswith("IR") else sheba
            for t in transactions.find({"user_id": user_id, "sheba": {"$in": [sheba_with_ir, sheba_without_ir]}}, {"id": 1}):
                txn_ids.append(t["id"])

        if txn_ids:
            payment_count = payments_col.count_documents({
                "user_id": user_id, "transaction_id": {"$in": list(set(txn_ids))}
            })

    return {"debt": debt_count, "recv": recv_count, "payment": payment_count}


def _get_linked_transactions(user_id: int, card_number: str = None,
                             sheba: str = None, txn_type: str = None) -> list:
    """Get transactions linked to a specific card."""
    transactions = get_collection("transactions")
    query = {"user_id": user_id}

    if txn_type:
        query["transaction_type"] = txn_type

    card_conditions = []
    if card_number:
        card_conditions.append({"card_number": card_number})
    if sheba:
        sheba_with_ir = f"IR{sheba}" if not sheba.startswith("IR") else sheba
        sheba_without_ir = sheba.replace("IR", "") if sheba.startswith("IR") else sheba
        card_conditions.append({"sheba": {"$in": [sheba_with_ir, sheba_without_ir]}})

    if card_conditions:
        query["$or"] = card_conditions

    result = []
    for txn in transactions.find(query).sort("id", -1):
        txn.pop("_id", None)
        result.append(txn)
    return result

def _build_linked_txn_text(txns: list, txn_type: str, card_name: str) -> str:
    """Build text for linked transactions."""
    type_label = "بدهی" if txn_type == "debt" else "طلب"
    type_emoji = "📋" if txn_type == "debt" else "📌"

    if not txns:
        return f"📭 هیچ {type_label} مرتبطی با کارت {card_name} یافت نشد."

    total = sum(t["amount"] for t in txns)
    text = f"{type_emoji} {type_label}‌های مرتبط با کارت {card_name}\n\n"
    text += f"📊 تعداد: {len(txns)} مورد | 💰 مجموع: {format_amount(total)} تومان\n"
    text += "——————————"

    for i, txn in enumerate(txns[:10], 1):  # Show max 10
        text += f"\n\n{type_emoji} #{txn["id"]}"
        text += f"\n   💰 مبلغ: {format_amount(txn["amount"])} تومان"
        if txn["party_name"]:
            text += f"\n   👤 {txn["party_name"]}"
        if txn["description"]:
            text += f"\n   📝 {txn["description"][:30]}"
        if txn["is_settled"]:
            text += f"\n   ✅ تسویه شده"
        elif txn["due_jalali_date"]:
            text += f"\n   📅 سررسید: {txn["due_jalali_date"]}"

    if len(txns) > 10:
        text += f"\n\n... و {len(txns) - 10} مورد دیگر"

    return text

def _group_cards_by_owner_filtered(cards: list, sort_by: str = "count", filter_by: str = "all") -> list:
    """Group cards by owner with sorting and filtering."""
    # Apply filter
    filtered_cards = cards
    if filter_by == "has_card":
        filtered_cards = [c for c in cards if c.card_number]
    elif filter_by == "has_sheba":
        filtered_cards = [c for c in cards if c.sheba]
    elif filter_by == "both":
        filtered_cards = [c for c in cards if c.card_number and c.sheba]

    # Group
    groups = _group_cards_by_owner(filtered_cards)

    # Apply sort
    if sort_by == "name":
        groups.sort(key=lambda g: g["name"])
    elif sort_by == "count":
        groups.sort(key=lambda g: -g["count"])
    elif sort_by == "bank":
        # Sort by most common bank in group
        def get_bank(g):
            banks = [c.bank_name for c in g["cards"] if c.bank_name]
            return banks[0] if banks else "zzz"
        groups.sort(key=get_bank)
    elif sort_by == "date":
        # Sort by most recent card
        def get_date(g):
            dates = [c.created_at for c in g["cards"] if c.created_at]
            return max(dates) if dates else g["cards"][0].created_at or datetime.min
        groups.sort(key=get_date, reverse=True)

    return groups

@router.message(F.text == "💳 ثبت شماره کارت و شبا")
async def card_info_menu(message: Message):
    """Show card & sheba submenu."""
    await message.answer(CARD_MENU, reply_markup=card_submenu())

@router.callback_query(F.data == "card_register")
async def card_register_from_submenu(callback: CallbackQuery, state: FSMContext):
    """Handle 'register new card' from submenu."""
    await safe_delete(callback.message)
    await state.set_state(CardForm.name_choice)
    await callback.message.answer(CARD_NAME_CHOICE, reply_markup=card_name_choice_keyboard())
    await safe_callback_answer(callback)

@router.callback_query(F.data == "card_all")
async def card_all_callback(callback: CallbackQuery):
    """Show all cards grouped by owner name."""
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        cards = CardInfoRepository.get_by_user(user["id"])

        if not cards:
            await callback.message.edit_text(CARD_EMPTY, reply_markup=card_submenu())
            await safe_callback_answer(callback)
            return

        groups = _group_cards_by_owner(cards)

        # Generate cache key and store groups
        cache_key = f"c{user["id"]}_{int(time.time())}"
        async with _card_groups_lock:
            _card_groups_cache[cache_key] = {g["name"]: g for g in groups}
            _evict_cache(_card_groups_cache)

        # Build summary text
        text = _build_card_group_summary_text(groups, "همه کارت‌ها")

        # Build customer buttons
        buttons_data = []
        for g in groups:
            label = f"👤 {g['name']} | {g['count']} کارت"
            safe_name = g["name"].replace(":", "_").replace(" ", "_")
            buttons_data.append({
                "label": label,
                "callback_data": f"card_cust_detail:{cache_key}:{safe_name}"
            })

        await callback.message.edit_text(text, reply_markup=card_owner_overview_keyboard(buttons_data, cache_key))
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_all_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

@router.callback_query(F.data.startswith("card_cust_detail:"))
async def card_cust_detail_callback(callback: CallbackQuery):
    """Show cards for a specific customer/name."""
    parts = callback.data.split(":")
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_name = parts[2]

    # Find the group in cache
    async with _card_groups_lock:
        groups = _card_groups_cache.get(cache_key)
        if not groups:
            await safe_callback_answer(callback, "⚠️ اطلاعات منقضی شده. لطفاً دوباره تلاش کنید.", show_alert=True)
            return

        # Find by safe_name
        group = None
        for name, g in groups.items():
            if name.replace(":", "_").replace(" ", "_") == safe_name:
                group = g
                break

    if not group:
        await safe_callback_answer(callback, "⚠️ اطلاعات یافت نشد.", show_alert=True)
        return

    # Build detail text
    text = _build_card_owner_detail_text(group)

    # Build items data
    items_data = []
    for card in group["cards"]:
        label = f"💳 #{card["id"]}"
        if card["card_number"]:
            label += f" | {card["card_number"][-4:]}****"
        if card["sheba"]:
            label += f" | IR{card["sheba"][-4:]}****"
        items_data.append({
            "label": label,
            "detail_callback": f"card_detail:{card["id"]}:{cache_key}:{safe_name}"
        })

    await callback.message.edit_text(text, reply_markup=card_items_keyboard(items_data, cache_key))
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("card_detail:"))
async def card_detail_callback(callback: CallbackQuery):
    """Show full detail for a single card."""
    parts = callback.data.split(":")
    if len(parts) < 4:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    card_id = int(parts[1])
    cache_key = parts[2]
    safe_name = parts[3]

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد.", show_alert=True)
            return

        # Get linked transaction counts
        linked_counts = _get_card_linked_counts(user["id"], card["card_number"], card["sheba"])

        text = _build_card_detail_text(card)
        keyboard = card_detail_keyboard(
            card["id"], cache_key, safe_name,
            debt_count=linked_counts["debt"],
            recv_count=linked_counts["recv"],
            payment_count=linked_counts["payment"]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_detail_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

@router.callback_query(F.data == "card_group_back")
async def card_group_back_callback(callback: CallbackQuery):
    """Back to card submenu from any level."""
    await callback.message.edit_text(CARD_MENU, reply_markup=card_submenu())
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("card_back:"))
async def card_back_callback(callback: CallbackQuery):
    """Back to customer list from card items list."""
    parts = callback.data.split(":")
    if len(parts) < 2:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]

    async with _card_groups_lock:
        groups = _card_groups_cache.get(cache_key)

    if not groups:
        await callback.message.edit_text("⚠️ اطلاعات منقضی شده.", reply_markup=card_submenu())
        await safe_callback_answer(callback)
        return

    # Rebuild customer list with full summary text (matching Level 1 original)
    all_cards = []
    for g in groups.values():
        all_cards.extend(g["cards"])

    text = _build_card_group_summary_text(list(groups.values()), "همه کارت‌ها")

    buttons_data = []
    for name, g in groups.items():
        label = f"👤 {name} | {g['count']} کارت"
        safe_name = name.replace(":", "_").replace(" ", "_")
        buttons_data.append({
            "label": label,
            "callback_data": f"card_cust_detail:{cache_key}:{safe_name}"
        })

    await callback.message.edit_text(text, reply_markup=card_owner_overview_keyboard(buttons_data, cache_key))
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("card_detail_back:"))
async def card_detail_back_callback(callback: CallbackQuery):
    """Back to card items list from card detail."""
    parts = callback.data.split(":")
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[1]
    safe_name = parts[2]

    async with _card_groups_lock:
        groups = _card_groups_cache.get(cache_key)
        if not groups:
            await callback.message.edit_text("⚠️ اطلاعات منقضی شده.", reply_markup=card_submenu())
            await safe_callback_answer(callback)
            return

        group = None
        for name, g in groups.items():
            if name.replace(":", "_").replace(" ", "_") == safe_name:
                group = g
                break

    if not group:
        await callback.message.edit_text("⚠️ اطلاعات یافت نشد.", reply_markup=card_submenu())
        await safe_callback_answer(callback)
        return

    text = _build_card_owner_detail_text(group)

    items_data = []
    for card in group["cards"]:
        label = f"💳 #{card["id"]}"
        if card["card_number"]:
            label += f" | {card["card_number"][-4:]}****"
        if card["sheba"]:
            label += f" | IR{card["sheba"][-4:]}****"
        items_data.append({
            "label": label,
            "detail_callback": f"card_detail:{card["id"]}:{cache_key}:{safe_name}"
        })

    await callback.message.edit_text(text, reply_markup=card_items_keyboard(items_data, cache_key))
    await safe_callback_answer(callback)

@router.callback_query(F.data == "card_search_inline")
async def card_search_inline_callback(callback: CallbackQuery, state: FSMContext):
    """Handle 'search card' from submenu."""
    await safe_delete(callback.message)
    await state.set_state(CardSearchForm.query)
    await callback.message.answer(CARD_SEARCH, reply_markup=cancel_menu())
    await safe_callback_answer(callback)

@router.callback_query(F.data == "card_reports")
async def card_reports_callback(callback: CallbackQuery):
    """Show card summary report."""
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        cards = CardInfoRepository.get_by_user(user["id"])

        total = len(cards)
        with_card = sum(1 for c in cards if c.card_number)
        with_sheba = sum(1 for c in cards if c.sheba)
        owners = len(set(c.name for c in cards if c.name))

        # Get unique bank names
        banks = list({normalize_bank_name(c.bank_name) for c in cards if c.bank_name})

        text = f"""📊 گزارش کارت‌ها

📋 کل کارت‌ها: {total} مورد
💳 دارای شماره کارت: {with_card} مورد
🏦 دارای شماره شبا: {with_sheba} مورد
👤 تعداد مالکان: {owners} نام"""

        if banks:
            text += f"\n🏛 بانک‌ها: {', '.join(banks)}"

        await callback.message.edit_text(text, reply_markup=card_submenu())
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_reports_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

# ==============================
# Card Sort & Filter Handlers
# ==============================

@router.callback_query(F.data.startswith("card_sort_menu:"))
async def card_sort_menu_callback(callback: CallbackQuery):
    """Show sort options for card list."""
    cache_key = callback.data.split(":", 1)[1] if ":" in callback.data else None
    await callback.message.edit_text(
        "🔃 مرتب‌سازی کارت‌ها بر اساس:",
        reply_markup=card_sort_keyboard(cache_key)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("card_filter_menu:"))
async def card_filter_menu_callback(callback: CallbackQuery):
    """Show filter options for card list."""
    cache_key = callback.data.split(":", 1)[1] if ":" in callback.data else None
    await callback.message.edit_text(
        "🔽 فیلتر کارت‌ها:",
        reply_markup=card_filter_keyboard(cache_key)
    )
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("card_sort:"))
async def card_sort_callback(callback: CallbackQuery):
    """Apply sorting to card list. Format: card_sort:{cache_key}:{sort_by}"""
    parts = callback.data.split(":")
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    cache_key = parts[1]
    sort_by = parts[2]

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        cards = CardInfoRepository.get_by_user(user["id"])
        if not cards:
            await callback.message.edit_text(CARD_EMPTY, reply_markup=card_submenu())
            await safe_callback_answer(callback)
            return

        groups = _group_cards_by_owner_filtered(cards, sort_by=sort_by)

        # Generate new cache key and store groups
        new_cache_key = f"c{user["id"]}_{int(time.time())}"
        async with _card_groups_lock:
            _card_groups_cache[new_cache_key] = {g["name"]: g for g in groups}
            _evict_cache(_card_groups_cache)

        sort_labels = {"name": "نام", "count": "تعداد", "bank": "بانک", "date": "تاریخ"}
        text = _build_card_group_summary_text(groups, f"همه کارت‌ها (مرتب‌سازی: {sort_labels.get(sort_by, sort_by)})")

        buttons_data = []
        for g in groups:
            label = f"👤 {g['name']} | {g['count']} کارت"
            safe_name = g["name"].replace(":", "_").replace(" ", "_")
            buttons_data.append({
                "label": label,
                "callback_data": f"card_cust_detail:{new_cache_key}:{safe_name}"
            })

        await callback.message.edit_text(text, reply_markup=card_owner_overview_keyboard(buttons_data, new_cache_key))
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_sort_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

@router.callback_query(F.data.startswith("card_filter:"))
async def card_filter_callback(callback: CallbackQuery):
    """Apply filtering to card list. Format: card_filter:{cache_key}:{filter_by}"""
    parts = callback.data.split(":")
    if len(parts) < 3:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    cache_key = parts[1]
    filter_by = parts[2]

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        cards = CardInfoRepository.get_by_user(user["id"])
        if not cards:
            await callback.message.edit_text(CARD_EMPTY, reply_markup=card_submenu())
            await safe_callback_answer(callback)
            return

        groups = _group_cards_by_owner_filtered(cards, filter_by=filter_by)

        # Generate new cache key and store groups
        new_cache_key = f"c{user["id"]}_{int(time.time())}"
        async with _card_groups_lock:
            _card_groups_cache[new_cache_key] = {g["name"]: g for g in groups}
            _evict_cache(_card_groups_cache)

        filter_labels = {
            "has_card": "فقط کارت‌دار",
            "has_sheba": "فقط شبا‌دار",
            "both": "هر دو",
            "all": "همه"
        }
        text = _build_card_group_summary_text(groups, f"کارت‌ها (فیلتر: {filter_labels.get(filter_by, filter_by)})")

        buttons_data = []
        for g in groups:
            label = f"👤 {g['name']} | {g['count']} کارت"
            safe_name = g["name"].replace(":", "_").replace(" ", "_")
            buttons_data.append({
                "label": label,
                "callback_data": f"card_cust_detail:{new_cache_key}:{safe_name}"
            })

        if not buttons_data:
            text += "\n\n📭 هیچ کارتی با این فیلتر یافت نشد."

        await callback.message.edit_text(text, reply_markup=card_owner_overview_keyboard(buttons_data, new_cache_key))
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_filter_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

# ==============================
# Card Linked Transaction Handlers
# ==============================

@router.callback_query(F.data.startswith("card_linked_debt:"))
async def card_linked_debt_callback(callback: CallbackQuery):
    """Show debts linked to a card. Format: card_linked_debt:{card_id} or card_linked_debt:{card_id}:{cache_key}:{safe_name}"""
    parts = callback.data.split(":")
    card_id = safe_parse_callback_id(callback, 1)
    if card_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[2] if len(parts) > 2 else None
    safe_name = parts[3] if len(parts) > 3 else None

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد.", show_alert=True)
            return

        txns = _get_linked_transactions(user["id"], card["card_number"], card["sheba"], "debt")
        text = _build_linked_txn_text(txns, "debt", card["name"])

        keyboard = card_linked_txn_keyboard(card_id, "debt", cache_key, safe_name)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_linked_debt_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

@router.callback_query(F.data.startswith("card_linked_recv:"))
async def card_linked_recv_callback(callback: CallbackQuery):
    """Show receivables linked to a card. Format: card_linked_recv:{card_id} or card_linked_recv:{card_id}:{cache_key}:{safe_name}"""
    parts = callback.data.split(":")
    card_id = safe_parse_callback_id(callback, 1)
    if card_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[2] if len(parts) > 2 else None
    safe_name = parts[3] if len(parts) > 3 else None

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد.", show_alert=True)
            return

        txns = _get_linked_transactions(user["id"], card["card_number"], card["sheba"], "receivable")
        text = _build_linked_txn_text(txns, "receivable", card["name"])

        keyboard = card_linked_txn_keyboard(card_id, "receivable", cache_key, safe_name)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_linked_recv_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

@router.callback_query(F.data.startswith("card_linked_pay:"))
async def card_linked_pay_callback(callback: CallbackQuery):
    """Show payments linked to a card. Format: card_linked_pay:{card_id} or card_linked_pay:{card_id}:{cache_key}:{safe_name}"""
    parts = callback.data.split(":")
    card_id = safe_parse_callback_id(callback, 1)
    if card_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[2] if len(parts) > 2 else None
    safe_name = parts[3] if len(parts) > 3 else None

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد.", show_alert=True)
            return

        # Get transactions with this card
        txns = _get_linked_transactions(user["id"], card["card_number"], card["sheba"])
        txn_ids = [t["id"] for t in txns]

        if not txn_ids:
            text = f"📭 هیچ پرداخت مرتبطی با کارت {card['name']} یافت نشد."
        else:
            payments = PaymentRepository.get_by_user(user["id"], limit=50)
            payments = [p for p in payments if p["transaction_id"] in txn_ids][:10]

            if not payments:
                text = f"📭 هیچ پرداخت مرتبطی با کارت {card['name']} یافت نشد."
            else:
                total_paid = sum(p["amount"] for p in payments)
                text = f"💳 پرداخت‌های مرتبط با کارت {card['name']}\n\n"
                text += f"📊 تعداد: {len(payments)} مورد | 💰 مجموع: {format_amount(total_paid)} تومان\n"
                text += "——————————"

                for p in payments[:10]:
                    text += f"\n\n💳 #{p['id']}"
                    text += f"\n   💰 مبلغ: {format_amount(p['amount'])} تومان"
                    text += f"\n   📅 {p['jalali_date']}"
                    if p["description"]:
                        text += f"\n   📝 {p['description'][:30]}"

        keyboard = card_linked_txn_keyboard(card_id, "payment", cache_key, safe_name)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_linked_pay_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

@router.callback_query(F.data.startswith("card_back_from_linked:"))
async def card_back_from_linked_callback(callback: CallbackQuery):
    """Back to card detail from linked transactions view. Format: card_back_from_linked:{card_id} or card_back_from_linked:{card_id}:{cache_key}:{safe_name}"""
    parts = callback.data.split(":")
    card_id = safe_parse_callback_id(callback, 1)
    if card_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    cache_key = parts[2] if len(parts) > 2 else None
    safe_name = parts[3] if len(parts) > 3 else None

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد.", show_alert=True)
            return

        # Get linked transaction counts
        linked_counts = _get_card_linked_counts(user["id"], card["card_number"], card["sheba"])

        text = _build_card_detail_text(card)
        keyboard = card_detail_keyboard(
            card["id"], cache_key, safe_name,
            debt_count=linked_counts["debt"],
            recv_count=linked_counts["recv"],
            payment_count=linked_counts["payment"]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await safe_callback_answer(callback)
    except Exception as e:
        logger.error(f"Error in card_back_from_linked_callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)

@router.message(F.text == "➕ ثبت جدید")
async def card_add_start(message: Message, state: FSMContext):
    """Start adding new card info."""
    await state.set_state(CardForm.name_choice)
    await message.answer(CARD_NAME_CHOICE, reply_markup=card_name_choice_keyboard())

@router.message(CardForm.name_choice)
async def card_name_choice_handler(message: Message, state: FSMContext):
    """Handle choice of name entry method."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    if message.text == "✏️ ورود دستی نام":
        await state.set_state(CardForm.name_manual)
        await message.answer(CARD_ENTER_NAME_MANUAL, reply_markup=cancel_back_menu())
    elif message.text == "👥 انتخاب از مشتریان":
        await state.set_state(CardForm.name_customer_select)
        # Get customer list
        user = get_user(message)
        customers = CustomerRepository.get_by_user(user["id"])
        if customers:
            await message.answer(CARD_SELECT_CUSTOMER, reply_markup=party_keyboard(customers))
        else:
            await state.set_state(CardForm.name_manual)
            await message.answer("📭 هیچ مشتری یافت نشد. لطفاً نام را به صورت دستی وارد کنید:", reply_markup=cancel_back_menu())

@router.message(CardForm.name_manual)
async def card_name_manual_handler(message: Message, state: FSMContext):
    """Handle manual name entry."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    if not message.text or len(message.text.strip()) == 0:
        await message.answer(CARD_NAME_REQUIRED)
        return
    
    await state.update_data(name=message.text.strip())
    await state.set_state(CardForm.card_number)
    await message.answer(CARD_ENTER_CARD, reply_markup=card_skip_menu())

@router.message(CardForm.name_customer_select)
async def card_name_customer_handler(message: Message, state: FSMContext):
    """Handle customer selection for name."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    # Find selected customer
    user = get_user(message)
    customers = CustomerRepository.get_by_user(user["id"])
    selected_customer = None
    for customer in customers:
        if customer["full_name"] == message.text:
            selected_customer = customer
            break
        
    if selected_customer:
        await state.update_data(name=selected_customer["full_name"], customer_id=selected_customer["id"])
        await state.set_state(CardForm.card_number)
        await message.answer(CARD_ENTER_CARD, reply_markup=card_skip_menu())
    else:
        # Re-fetch customers for the keyboard (still within session)
        await message.answer("⚠️ مشتری انتخاب شده نامعتبر است.")
        await state.set_state(CardForm.name_customer_select)
        await message.answer(CARD_SELECT_CUSTOMER, reply_markup=party_keyboard(customers))

@router.message(CardForm.card_number)
async def card_number_handler(message: Message, state: FSMContext):
    """Handle card number input."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(CardForm.name_choice)
        await message.answer(CARD_NAME_CHOICE, reply_markup=card_name_choice_keyboard())
        return
    
    if message.text == "⏭️ رد کردن":
        await state.update_data(card_number=None)
        await state.set_state(CardForm.sheba)
        await message.answer(CARD_ENTER_SHEBA, reply_markup=card_skip_menu())
        return
    
    # Validate card number (16 digits), strip spaces and dashes
    card_number = message.text.replace(" ", "").replace("-", "")
    if not card_number.isdigit() or len(card_number) != 16:
        await message.answer(CARD_VALID_ERROR_16)
        return
    
    await state.update_data(card_number=card_number)
    await state.set_state(CardForm.sheba)
    await message.answer(CARD_ENTER_SHEBA, reply_markup=card_skip_menu())

@router.message(CardForm.sheba)
async def sheba_handler(message: Message, state: FSMContext):
    """Handle sheba input and move to bank name."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(CardForm.card_number)
        await message.answer(CARD_ENTER_CARD, reply_markup=card_skip_menu())
        return
    
    if message.text == "⏭️ رد کردن":
        await state.update_data(sheba=None)
    else:
        # Validate sheba: user enters only 24 digits (without "IR" prefix)
        sheba_digits = ''.join(filter(str.isdigit, message.text))
        if len(sheba_digits) != 24:
            await message.answer(CARD_VALID_ERROR_SHEBA)
            return
        await state.update_data(sheba=sheba_digits)
    
    # Move to bank name
    user = get_user(message)
    cards = CardInfoRepository.get_by_user(user["id"])
    bank_names = list({c.bank_name for c in cards if c.bank_name})
    await state.set_state(CardForm.bank_name)
    await message.answer(BANK_NAME_SELECT_PROMPT, reply_markup=bank_name_select_keyboard(bank_names))

@router.message(CardForm.bank_name)
async def card_bank_name_handler(message: Message, state: FSMContext):
    """Handle bank name input for standalone card registration."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت":
        await state.set_state(CardForm.sheba)
        await message.answer(CARD_ENTER_SHEBA, reply_markup=card_skip_menu())
        return

    if message.text == "⏭️ رد کردن":
        await state.update_data(bank_name=None)
    elif message.text == "✏️ ورود دستی نام بانک":
        # Show a simple cancel/skip keyboard for manual input
        await state.set_state(CardForm.bank_name)
        await message.answer(BANK_NAME_MANUAL_PROMPT, reply_markup=card_skip_menu())
        return
    elif message.text.startswith("🏛 "):
        bank_name = normalize_bank_name(message.text[3:])
        await state.update_data(bank_name=bank_name)
    else:
        # Treat as manual bank name input
        await state.update_data(bank_name=normalize_bank_name(message.text))

    await state.set_state(CardForm.confirm)
    await _show_card_confirm(message, state)

async def _show_card_confirm(message: Message, state: FSMContext):
    """Show confirmation before saving card info."""
    data = await state.get_data()
    card_display = data.get('card_number', '—')
    sheba_display = f"IR{data.get('sheba', '—')}" if data.get('sheba') else '—'
    bank_display = normalize_bank_name(data.get('bank_name')) or '—'
    
    text = f"""💳 {data['name']}

💳 شماره کارت: <code>{card_display}</code>
🏦 شماره شبا: <code>{sheba_display}</code>
🏛 نام بانک: {bank_display}

📌 برای کپی، روی هر کدام کلیک کنید.

آیا اطلاعات بالا را ذخیره می‌کنید؟"""
    
    await message.answer(text, reply_markup=confirm_keyboard(), parse_mode="HTML")

@router.callback_query(CardForm.confirm)
async def card_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle card confirmation and save."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        
        # Validate that at least one of card_number or sheba is provided
        if not data.get("card_number") and not data.get("sheba"):
            await callback.message.edit_text(CARD_VALID_ERROR_EMPTY, reply_markup=None)
            await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
            await state.clear()
            await safe_callback_answer(callback)
            return
        
        try:
            user = UserRepository.get_by_telegram_id( callback.from_user.id)
            if not user:
                await callback.message.edit_text(ACCESS_DENIED, reply_markup=None)
                await safe_callback_answer(callback)
                return
            
            # Check for duplicates
            existing_cards = CardInfoRepository.get_by_user(user["id"])
            card_number = data.get("card_number")
            sheba = data.get("sheba")
            
            duplicate_found = False
            duplicate_info = ""
            
            for card in existing_cards:
                if card_number and card["card_number"] == card_number:
                    duplicate_found = True
                    duplicate_info = f"شماره کارت {card_number} قبلاً برای '{card["name"]}' ثبت شده است."
                    break
                if sheba and card["sheba"] == sheba:
                    duplicate_found = True
                    duplicate_info = f"شماره شبا IR{sheba} قبلاً برای '{card["name"]}' ثبت شده است."
                    break
            
            if duplicate_found:
                await callback.message.edit_text(f"⚠️ {duplicate_info}", reply_markup=None)
                await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
                await state.clear()
                await safe_callback_answer(callback)
                return
            
            # Save card info
            CardInfoRepository.create(
                user_id=user["id"],
                name=data["name"],
                card_number=card_number,
                sheba=sheba,
                customer_id=data.get("customer_id"),
                bank_name=data.get("bank_name")
            )
            
            await state.clear()
            await callback.message.edit_text(CARD_SAVED, reply_markup=None)
            await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
            logger.info(f"Card info saved: {data['name']} by user {user["telegram_id"]}")
        except Exception as e:
            logger.error(f"Error saving card info: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
    
    await safe_callback_answer(callback)

@router.message(F.text == "📋 لیست شماره کارت‌ها")
async def card_list(message: Message):
    """Show list of card info grouped by owner (hierarchical view)."""
    try:
        user = get_user(message)
        cards = CardInfoRepository.get_by_user(user["id"])
        
        if not cards:
            await message.answer(CARD_EMPTY, reply_markup=card_submenu())
            return
        
        groups = _group_cards_by_owner(cards)
        
        # Generate cache key and store groups
        cache_key = f"c{user["id"]}_{int(time.time())}"
        async with _card_groups_lock:
            _card_groups_cache[cache_key] = {g["name"]: g for g in groups}
            _evict_cache(_card_groups_cache)
        
        # Build summary text
        text = _build_card_group_summary_text(groups, "همه کارت‌ها")
        
        # Build customer buttons
        buttons_data = []
        for g in groups:
            label = f"👤 {g['name']} | {g['count']} کارت"
            safe_name = g["name"].replace(":", "_").replace(" ", "_")
            buttons_data.append({
                "label": label,
                "callback_data": f"card_cust_detail:{cache_key}:{safe_name}"
            })
        
        await message.answer(text, reply_markup=card_owner_overview_keyboard(buttons_data, cache_key))
    except Exception as e:
        logger.error(f"Error listing cards: {e}")
        await message.answer(ERROR_GENERAL, reply_markup=card_submenu())

@router.message(F.text == "🔍 جستجوی کارت")
async def card_search_start(message: Message, state: FSMContext):
    """Start card search."""
    await state.set_state(CardSearchForm.query)
    await message.answer(CARD_SEARCH, reply_markup=cancel_menu())

@router.message(CardSearchForm.query)
async def card_search_result(message: Message, state: FSMContext):
    """Show card search results in hierarchical view."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    
    query = message.text
    try:
        user = get_user(message)
        cards = CardInfoRepository.search( user["id"], query)
        
        if not cards:
            await message.answer(CARD_NOT_FOUND, reply_markup=card_submenu())
            await state.clear()
            return
        
        groups = _group_cards_by_owner(cards)
        
        # Generate cache key and store groups
        cache_key = f"c{user["id"]}_{int(time.time())}"
        async with _card_groups_lock:
            _card_groups_cache[cache_key] = {g["name"]: g for g in groups}
            _evict_cache(_card_groups_cache)
        
        # Build summary text
        text = _build_card_group_summary_text(groups, f"نتایج جستجو: {query}")
        
        # Build customer buttons
        buttons_data = []
        for g in groups:
            label = f"👤 {g['name']} | {g['count']} کارت"
            safe_name = g["name"].replace(":", "_").replace(" ", "_")
            buttons_data.append({
                "label": label,
                "callback_data": f"card_cust_detail:{cache_key}:{safe_name}"
            })
        
        await message.answer(text, reply_markup=card_owner_overview_keyboard(buttons_data, cache_key))
        await state.clear()
    except Exception as e:
        logger.error(f"Error searching cards: {e}")
        await message.answer(ERROR_GENERAL, reply_markup=card_submenu())

@router.callback_query(F.data.startswith("card_edit:"))
async def card_edit_callback(callback: CallbackQuery, state: FSMContext):
    """Handle edit button press in card list."""
    card_id = safe_parse_callback_id(callback, 1)
    if card_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return
        
        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد یا دسترسی ندارید.", show_alert=True)
            return
        
        await state.update_data(edit_id=card["id"])
        await state.set_state(CardEditForm.field)
        
        # Show current values
        card_display = card["card_number"] or "—"
        sheba_display = f"IR{card["sheba"]}" if card["sheba"] else "—"
        bank_display = normalize_bank_name(card["bank_name"]) or "—"
        
        text = f"""✏️ ویرایش شماره کارت و شبا (شناسه: {card["id"]})

💳 نام: {card["name"]}
💳 شماره کارت: <code>{card_display}</code>
🏦 شماره شبا: <code>{sheba_display}</code>
🏛 نام بانک: {bank_display}

فیلدی که می‌خواهید ویرایش کنید را انتخاب کنید:"""
        
        await callback.message.edit_text(text, reply_markup=card_edit_field_keyboard(card["id"]), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in card edit callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)
    
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("card_edit_field:"))
async def card_edit_field_selected(callback: CallbackQuery, state: FSMContext):
    """Handle field selection for card edit."""
    parts = callback.data.split(":")
    card_id = int(parts[1])
    field = parts[2]
    
    data = await state.get_data()
    
    if field == "save":
        # Show confirmation
        await _show_card_edit_confirm(callback, state)
        await state.set_state(CardEditForm.confirm)
        await safe_callback_answer(callback)
        return
    
    # Validate field value
    valid_fields = {"name", "card", "sheba", "bank"}
    if field not in valid_fields:
        await safe_callback_answer(callback, "⚠️ فیلد نامعتبر.", show_alert=True)
        return
    
    # Set the appropriate state for the selected field
    field_prompts = {
        "name": "✏️ نام جدید را وارد کنید:\n(برای عدم تغییر، - را وارد کنید)",
        "card": "💳 شماره کارت جدید را وارد کنید:\n(۱۶ رقم، برای عدم تغییر، - را وارد کنید)",
        "sheba": "🏦 شماره شبا جدید را وارد کنید:\n(با IR شروع شده و ۲۴ رقم، برای عدم تغییر، - را وارد کنید)",
        "bank": "🏛 نام بانک جدید را وارد کنید:\n(برای عدم تغییر، - را وارد کنید)"
    }
    
    await state.update_data(edit_field=field)
    await state.set_state(CardEditForm.value)
    
    # Remove inline keyboard from current message
    await callback.message.edit_text(callback.message.text, reply_markup=None)
    # Send new message with the reply keyboard
    await callback.message.answer(field_prompts[field], reply_markup=cancel_back_menu())
    
    await safe_callback_answer(callback)

@router.message(CardEditForm.value)
async def card_edit_value_handler(message: Message, state: FSMContext):
    """Handle value input for card edit."""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(CANCELED, reply_markup=main_menu())
        return
    if message.text == "🔙 بازگشت به منو":
        await state.clear()
        await message.answer(BACK_TEXT, reply_markup=main_menu())
        return
    
    data = await state.get_data()
    field = data.get("edit_field")
    edit_id = data.get("edit_id")
    
    # Load original card values for "-" (no change) handling
    original_card = CardInfoRepository.get_by_id( edit_id)
    
    if field == "name":
        if message.text == "-":
            # No change: restore original value
            if original_card:
                await state.update_data(name=original_card["name"])
        else:
            if not message.text or len(message.text.strip()) == 0:
                await message.answer(CARD_NAME_REQUIRED)
                return
            await state.update_data(name=message.text.strip())
    elif field == "card":
        if message.text == "-":
            # No change: restore original value
            if original_card:
                await state.update_data(card_number=original_card["card_number"])
        else:
            # Validate card number (16 digits), strip spaces and dashes
            card_number = message.text.replace(" ", "").replace("-", "")
            if card_number and (not card_number.isdigit() or len(card_number) != 16):
                await message.answer(CARD_VALID_ERROR_16)
                return
            await state.update_data(card_number=card_number if card_number else None)
    elif field == "sheba":
        if message.text == "-":
            # No change: restore original value
            if original_card:
                await state.update_data(sheba=original_card["sheba"])
        else:
            # Validate sheba: user enters only 24 digits (without "IR" prefix)
            sheba_digits = ''.join(filter(str.isdigit, message.text))
            if sheba_digits and len(sheba_digits) != 24:
                await message.answer(CARD_VALID_ERROR_SHEBA)
                return
            
            await state.update_data(sheba=sheba_digits if sheba_digits else None)
    elif field == "bank":
        if message.text == "-":
            # No change: restore original value
            if original_card:
                await state.update_data(bank_name=original_card["bank_name"])
        else:
            await state.update_data(bank_name=normalize_bank_name(message.text))
    
    data = await state.get_data()
    await message.answer(
        f"✅ مقدار ثبت شد.\n\nفیلد بعدی را انتخاب کنید:",
        reply_markup=card_edit_field_keyboard(data["edit_id"])
    )
    await state.set_state(CardEditForm.field)

async def _show_card_edit_confirm(callback: CallbackQuery, state: FSMContext):
    """Show confirmation before saving card edit."""
    data = await state.get_data()
    try:
        card = CardInfoRepository.get_by_id( data["edit_id"])
        if not card:
            await callback.message.edit_text("⚠️ کارت یافت نشد.", reply_markup=None)
            return
        
        # Get new values or keep old ones
        name = data.get("name", card["name"])
        card_number = data.get("card_number", card["card_number"])
        sheba = data.get("sheba", card["sheba"])
        bank_name = data.get("bank_name", card["bank_name"])
        
        card_display = card_number or "—"
        sheba_display = f"IR{sheba}" if sheba else "—"
        bank_display = normalize_bank_name(bank_name) or "—"
        
        text = f"""✏️ ویرایش شماره کارت و شبا

💳 نام: {name}
💳 شماره کارت: <code>{card_display}</code>
🏦 شماره شبا: <code>{sheba_display}</code>
🏛 نام بانک: {bank_display}

آیا تأیید می‌کنید؟"""
        
        await callback.message.edit_text(text, reply_markup=confirm_keyboard(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error showing card edit confirm: {e}")
        await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)

@router.callback_query(CardEditForm.confirm)
async def card_edit_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle card edit confirmation."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        try:
            user = UserRepository.get_by_telegram_id( callback.from_user.id)
            if not user:
                await callback.message.edit_text(ACCESS_DENIED, reply_markup=None)
                await safe_callback_answer(callback)
                return
            
            card_id = data.get("edit_id")
            card = CardInfoRepository.get_by_id( card_id)
            if not card or card["user_id"] != user["id"]:
                await callback.message.edit_text("⚠️ کارت یافت نشد یا دسترسی ندارید.", reply_markup=None)
                await safe_callback_answer(callback)
                return
            
            # Check for duplicates (excluding current card)
            existing_cards = CardInfoRepository.get_by_user(user["id"])
            card_number = data.get("card_number")
            sheba = data.get("sheba")
            
            # Validate that at least one of card_number or sheba is provided after edit
            final_card_number = card_number if card_number is not None else card["card_number"]
            final_sheba = sheba if sheba is not None else card["sheba"]
            if not final_card_number and not final_sheba:
                await callback.message.edit_text(CARD_VALID_ERROR_EMPTY, reply_markup=None)
                await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
                await state.clear()
                await safe_callback_answer(callback)
                return
            
            duplicate_found = False
            duplicate_info = ""
            
            for existing_card in existing_cards:
                if existing_card["id"] == card_id:
                    continue  # Skip current card
                
                if card_number and existing_card["card_number"] == card_number:
                    duplicate_found = True
                    duplicate_info = f"شماره کارت {card_number} قبلاً برای '{existing_card["name"]}' ثبت شده است."
                    break
                if sheba and existing_card["sheba"] == sheba:
                    duplicate_found = True
                    duplicate_info = f"شماره شبا IR{sheba} قبلاً برای '{existing_card["name"]}' ثبت شده است."
                    break
            
            if duplicate_found:
                await callback.message.edit_text(f"⚠️ {duplicate_info}", reply_markup=None)
                await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
                await state.clear()
                await safe_callback_answer(callback)
                return
            
            # Update card info
            CardInfoRepository.update(
                card_id,
                name=data.get("name"),
                card_number=data.get("card_number"),
                sheba=data.get("sheba"),
                bank_name=data.get("bank_name")
            )
            
            await state.clear()
            await callback.message.edit_text(CARD_UPDATED, reply_markup=None)
            await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
            logger.info(f"Card info updated: ID {card_id} by user {user["telegram_id"]}")
        except Exception as e:
            logger.error(f"Error updating card info: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
    
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("card_delete:"))
async def card_delete_callback(callback: CallbackQuery, state: FSMContext):
    """Handle delete button press in card list."""
    card_id = safe_parse_callback_id(callback, 1)
    if card_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return
        
        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد یا دسترسی ندارید.", show_alert=True)
            return
        
        await state.update_data(delete_id=card["id"])
        
        # Show confirmation
        card_display = card["card_number"] or "—"
        sheba_display = f"IR{card["sheba"]}" if card["sheba"] else "—"
        
        text = f"""⚠️ آیا از حذف این مورد اطمینان دارید؟

💳 نام: {card["name"]}
💳 شماره کارت: <code>{card_display}</code>
🏦 شماره شبا: <code>{sheba_display}</code>"""
        
        await callback.message.edit_text(text, reply_markup=confirm_keyboard(), parse_mode="HTML")
        await state.set_state(CardDeleteForm.confirm)
    except Exception as e:
        logger.error(f"Error in card delete callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در بارگذاری اطلاعات.", show_alert=True)
    
    await safe_callback_answer(callback)

@router.callback_query(CardDeleteForm.confirm)
async def card_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle card delete confirmation."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        try:
            user = UserRepository.get_by_telegram_id( callback.from_user.id)
            if not user:
                await callback.message.edit_text(ACCESS_DENIED, reply_markup=None)
                await safe_callback_answer(callback)
                return
            
            card_id = data.get("delete_id")
            card = CardInfoRepository.get_by_id( card_id)
            if not card or card["user_id"] != user["id"]:
                await callback.message.edit_text("⚠️ کارت یافت نشد یا دسترسی ندارید.", reply_markup=None)
                await safe_callback_answer(callback)
                return
            
            # Delete card
            CardInfoRepository.delete( card_id)
            
            await state.clear()
            await callback.message.edit_text(CARD_DELETED, reply_markup=None)
            await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
            logger.info(f"Card info deleted: ID {card_id} by user {user["telegram_id"]}")
        except Exception as e:
            logger.error(f"Error deleting card info: {e}")
            await callback.message.edit_text(ERROR_GENERAL, reply_markup=None)
    else:
        await state.clear()
        await callback.message.edit_text(CANCELED, reply_markup=None)
        await callback.message.answer(CARD_MENU, reply_markup=card_submenu())
    
    await safe_callback_answer(callback)

@router.callback_query(F.data.startswith("copy_card:"))
@router.callback_query(F.data.startswith("copy_sheba:"))
@router.callback_query(F.data.startswith("copy_sms:"))
async def card_copy_callback(callback: CallbackQuery):
    """Handle copy card, sheba, or SMS format copy."""
    parts = callback.data.split(":")
    action = parts[0]  # copy_card, copy_sheba, copy_sms
    card_id = safe_parse_callback_id(callback, 1)
    if card_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return
    
    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return
        
        card = CardInfoRepository.get_by_id( card_id)
        if not card or card["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ کارت یافت نشد یا دسترسی ندارید.", show_alert=True)
            return
        
        if action == "copy_card":
            # Copy only card number
            text_to_copy = card["card_number"] or ""
            if not text_to_copy:
                await safe_callback_answer(callback, "⚠️ شماره کارت موجود نیست.", show_alert=True)
                return
            label = "💳 شماره کارت"
        elif action == "copy_sheba":
            # Copy only IBAN (with IR prefix)
            text_to_copy = f"IR{card["sheba"]}" if card["sheba"] else ""
            if not text_to_copy:
                await safe_callback_answer(callback, "⚠️ شماره شبا موجود نیست.", show_alert=True)
                return
            label = "🏦 شماره شبا"
        else:  # copy_sms
            # SMS format: Name + Card Number (formatted with dashes) + IBAN (without IR)
            if not card["card_number"] and not card["sheba"]:
                await safe_callback_answer(callback, "⚠️ هیچ اطلاعاتی برای ارسال وجود ندارد.", show_alert=True)
                return
            
            # Format card number: XXXX-XXXX-XXXX-XXXX
            card_formatted = ""
            if card["card_number"]:
                parts_list = [card["card_number"][i:i+4] for i in range(0, len(card["card_number"]), 4)]
                card_formatted = "-".join(parts_list)
            
            # IBAN digits without IR prefix
            sheba_digits = card["sheba"] if card["sheba"] else ""
            
            lines = [card["name"]]
            if card_formatted:
                lines.append("")
                lines.append("شماره کارت:")
                lines.append(card_formatted)
            if sheba_digits:
                lines.append("")
                lines.append("شماره شبا:")
                lines.append(sheba_digits)
            
            text_to_copy = "\n".join(lines)
            label = "📩 ارسال پیامک"
        
        await safe_callback_answer(callback, CARD_COPIED, show_alert=True)
        
        # Send a message with the copied text for user convenience
        await callback.message.answer(
            f"✅ {label}\n\n<code>{text_to_copy}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in card copy callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در کپی.", show_alert=True)

# ==============================
# Debt/Receivable SMS Copy Handler
# ==============================

@router.callback_query(F.data.startswith("debt_sms:"))
@router.callback_query(F.data.startswith("recv_sms:"))
async def txn_sms_copy_callback(callback: CallbackQuery):
    """Handle SMS copy for debt/receivable payment info."""
    parts = callback.data.split(":")
    action = parts[0]  # debt_sms, recv_sms
    txn_id = safe_parse_callback_id(callback, 1)
    if txn_id is None:
        await safe_callback_answer(callback, "⚠️ خطا.", show_alert=True)
        return

    try:
        user = UserRepository.get_by_telegram_id( callback.from_user.id)
        if not user:
            await safe_callback_answer(callback, "⚠️ کاربر یافت نشد.", show_alert=True)
            return

        txn = TransactionRepository.get_by_id( txn_id)
        if not txn or txn["user_id"] != user["id"]:
            await safe_callback_answer(callback, "⚠️ مورد یافت نشد یا دسترسی ندارید.", show_alert=True)
            return

        if not txn["card_number"] and not txn["sheba"] and not txn["bank_name"]:
            await safe_callback_answer(callback, "⚠️ اطلاعات پرداختی موجود نیست.", show_alert=True)
            return

        type_label = "بدهی" if action == "debt_sms" else "طلب"
        party = txn["party_name"] or "-"
        amount_fmt = format_amount(txn["amount"])
        amount_words = amount_to_persian_words(txn["amount"])

        lines = []

        # Card number (first)
        if txn["card_number"]:
            card_fmt = " ".join([txn["card_number"][i:i+4] for i in range(0, 16, 4)])
            lines.append("کارت:")
            lines.append(card_fmt)
            lines.append("")

        # IBAN (second)
        if txn["sheba"]:
            lines.append("شبا:")
            lines.append(txn["sheba"])
            lines.append("")

        # Name, Bank, Amount
        lines.append(party)
        if txn["bank_name"]:
            lines.append(f"بانک: {normalize_bank_name(txn["bank_name"])}")
        lines.append(f"{amount_fmt} تومان")
        lines.append(amount_words)

        text_to_copy = "\n".join(lines)

        await safe_callback_answer(callback, "✅ کپی شد", show_alert=True)
        await callback.message.answer(
            f"📩 اطلاعات پرداخت {type_label}\n\n<code>{text_to_copy}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in txn sms copy callback: {e}")
        await safe_callback_answer(callback, "⚠️ خطا در کپی.", show_alert=True)

# ==============================
# Fallback Handler
# ==============================

@router.callback_query()
async def callback_fallback_handler(callback: CallbackQuery):
    """Handle unhandled callback queries to prevent timeout."""
    logger.warning(f"Unhandled callback query: {callback.data} from user {callback.from_user.id}")
    await safe_callback_answer(callback, "⚠️ عملیات نامعتبر است.", show_alert=True)

@router.message()
async def fallback_handler(message: Message):
    """Handle unknown commands."""
    # Ignore if it's a known command pattern that was already handled
    text = message.text
    
    # If it's a number (might be mid-flow), just ignore silently
    if text and text.strip().isdigit():
        return
    
    await message.answer(UNKNOWN_COMMAND, reply_markup=main_menu())
