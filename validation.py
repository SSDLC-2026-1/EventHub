"""
payment_validation.py

Skeleton file for input validation exercise.
You must implement each validation function according to the
specification provided in the docstrings.

All validation functions must return:

    (clean_value, error_message)

Where:
    clean_value: normalized/validated value (or empty string if invalid)
    error_message: empty string if valid, otherwise error description
"""

import re
import unicodedata
import time
from datetime import datetime
from typing import Tuple, Dict


MAX_ATTEMPTS = 3
LOCK_TIME_SECONDS = 300
LOGIN_STATE: Dict[str, Dict[str, float]] = {}


CARD_DIGITS_RE = re.compile(r"^[0-9]{13,19}$")
CVV_RE = re.compile(r"^[0-9]{3,4}$")
EXP_RE = re.compile(r"^(0[1-9]|1[0-2])/[0-9]{2}$")
EMAIL_BASIC_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")
NAME_ALLOWED_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'\- ]{2,60}$")
PHONE_RE = re.compile(r"^[0-9]{7,15}$")
PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*\(\)\-_=+\[\]{}<>?])[^\s]{8,64}$"
)


def normalize_basic(value: str) -> str:
    return unicodedata.normalize("NFKC", (value or "")).strip()


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value)


def luhn_is_valid(number: str) -> bool:
    if not number.isdigit():
        return False
    digits = [int(d) for d in number]
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def is_account_locked(email: str) -> Tuple[bool, int]:
    record = LOGIN_STATE.get(email)
    if not record:
        return False, 0
    if record["lock_until"] > time.time():
        return True, int(record["lock_until"] - time.time())
    return False, 0


def register_failed_attempt(email: str):
    record = LOGIN_STATE.setdefault(email, {"attempts": 0, "lock_until": 0})
    record["attempts"] += 1
    if record["attempts"] >= MAX_ATTEMPTS:
        print(f"Locking account {email} for {LOCK_TIME_SECONDS} seconds due to failed login attempts.")
        record["lock_until"] = time.time() + LOCK_TIME_SECONDS
        record["attempts"] = 0


def register_successful_login(email: str):
    if email in LOGIN_STATE and not is_account_locked(email)[0]:
        LOGIN_STATE[email] = {"attempts": 0, "lock_until": 0}

# =============================
# Field Validations
# =============================

def validate_card_number(card_number: str) -> Tuple[str, str]:
    card_number = normalize_basic(card_number)
    card_number = card_number.replace(" ", "").replace("-", "")
    if not CARD_DIGITS_RE.fullmatch(card_number):
        return "", "Invalid card number"
    if not luhn_is_valid(card_number):
        return "", "Invalid card number"
    return card_number, ""


def validate_exp_date(exp_date: str) -> Tuple[str, str]:
    exp_date = normalize_basic(exp_date)
    if not EXP_RE.fullmatch(exp_date):
        return "", "Invalid expiration date"
    month_str, year_str = exp_date.split("/")
    month = int(month_str)
    year = int("20" + year_str)
    now = datetime.utcnow()
    if year < now.year or (year == now.year and month < now.month):
        return "", "Card expired"
    if year > now.year + 15:
        return "", "Invalid expiration date"
    return exp_date, ""


def validate_cvv(cvv: str) -> Tuple[str, str]:
    cvv = normalize_basic(cvv)
    if not CVV_RE.fullmatch(cvv):
        return "", "Invalid CVV"
    return "", ""


def validate_billing_email(billing_email: str) -> Tuple[str, str]:
    billing_email = normalize_basic(billing_email).lower()
    if len(billing_email) == 0 or len(billing_email) > 254:
        return "", "Invalid email"
    if not EMAIL_BASIC_RE.fullmatch(billing_email):
        return "", "Invalid email"
    return billing_email, ""


def validate_name_on_card(name_on_card: str) -> Tuple[str, str]:
    name_on_card = normalize_basic(name_on_card)
    name_on_card = collapse_spaces(name_on_card)
    if not NAME_ALLOWED_RE.fullmatch(name_on_card):
        return "", "Invalid name"
    return name_on_card, ""


def validate_full_name(name: str) -> Tuple[str, str]:
    name = normalize_basic(name)
    name = collapse_spaces(name)
    if not NAME_ALLOWED_RE.fullmatch(name):
        return "", "Invalid full name"
    return name, ""


def validate_email(email: str) -> Tuple[str, str]:
    email = normalize_basic(email).lower()
    if len(email) == 0 or len(email) > 254:
        return "", "Invalid email"
    if not EMAIL_BASIC_RE.fullmatch(email):
        return "", "Invalid email"
    return email, ""


def validate_phone(phone: str) -> Tuple[str, str]:
    phone = normalize_basic(phone)
    phone = phone.replace(" ", "")
    if not PHONE_RE.fullmatch(phone):
        return "", "Invalid phone"
    return phone, ""


def validate_password(password: str, email: str = "") -> Tuple[str, str]:
    password = normalize_basic(password)
    if password == email:
        return "", "Invalid password"
    if not PASSWORD_RE.fullmatch(password):
        return "", "Invalid password"
    return password, ""


def validate_password_confirmation(password: str, confirmation: str) -> Tuple[str, str]:
    if password != confirmation:
        return "", "Passwords do not match"
    return password, ""


def validate_login_input(email: str, password: str) -> Tuple[Dict, Dict]:
    clean = {}
    errors = {}

    email_clean, err = validate_email(email)
    if err:
        errors["credentials"] = "Invalid credentials"
    else:
        clean["email"] = email_clean

    if not password:
        errors["credentials"] = "Invalid credentials"

    return clean, errors

# =============================
# Orchestrator Function
# =============================

def validate_payment_form(
    card_number: str,
    exp_date: str,
    cvv: str,
    name_on_card: str,
    billing_email: str
) -> Tuple[Dict, Dict]:

    clean = {}
    errors = {}

    card, err = validate_card_number(card_number)
    if err:
        errors["card_number"] = err
    else:
        clean["card_number"] = card

    exp_clean, err = validate_exp_date(exp_date)
    if err:
        errors["exp_date"] = err
    else:
        clean["exp_date"] = exp_clean

    _, err = validate_cvv(cvv)
    if err:
        errors["cvv"] = err

    name_clean, err = validate_name_on_card(name_on_card)
    if err:
        errors["name_on_card"] = err
    else:
        clean["name_on_card"] = name_clean

    email_clean, err = validate_billing_email(billing_email)
    if err:
        errors["billing_email"] = err
    else:
        clean["billing_email"] = email_clean

    return clean, errors