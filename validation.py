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
from datetime import datetime, date
from typing import Tuple, Dict


# =============================
# Regular Patterns
# =============================


CARD_DIGITS_RE = re.compile(r"")     # digits only
CVV_RE = re.compile(r"")             # 3 or 4 digits
EXP_RE = re.compile(r"")             # MM/YY format
EMAIL_BASIC_RE = re.compile(r"")     # basic email structure
NAME_ALLOWED_RE = re.compile(r"")    # allowed name characters


# =============================
# Utility Functions
# =============================

def normalize_basic(value: str) -> str:
    """
    Normalize input using NFKC and strip whitespace.
    """
    return unicodedata.normalize("NFKC", (value or "")).strip()


def luhn_is_valid(number: str) -> bool:
    """
    ****BONUS IMPLEMENTATION****

    Validate credit card number using Luhn algorithm.

    Input:
        number (str) -> digits only

    Returns:
        True if valid according to Luhn algorithm
        False otherwise
    """
    # TODO: Implement Luhn algorithm
    pass


# =============================
# Field Validations
# =============================

def validate_card_number(card_number: str) -> Tuple[str, str]:
    
    card_number=normalize_basic(card_number)
    card_number.replace(" ","").replace("-","")
    if any(digit.isalpha() for digit in card_number):
        return ("", "Card number must contain digits only")
    if len(card_number)<=13 or len(card_number)>=19:
        return ("", "card number length must be between 13 and 19")
    return (card_number, "")

    """
    Validate credit card number.

    Requirements:
    - Normalize input
    - Remove spaces and hyphens before validation
    - Must contain digits only
    - Length between 13 and 19 digits
    - BONUS: Must pass Luhn algorithm

    Input:
        card_number (str)

    Returns:
        (card, error_message)

    Notes:
        - If invalid → return ("", "Error message")
        - If valid → return (all credit card digits, "")
    """
    # TODO: Implement validation
    return "", ""


def validate_exp_date(exp_date: str) -> Tuple[str, str]:
    exp_date = normalize_basic(exp_date)
    exp_date_list = exp_date.split("/")
    if len(exp_date_list) != 2 or any(c.isalpha() for c in exp_date_list[0]) or any(c.isalpha() for c in exp_date_list[1]):
        return ("", "format must be MM/YY")
    if 1< int(exp_date_list[0]) > 12:
        return ("", "Month must be beween 01 and 12")
    if date.today().year[:2]>int(exp_date_list[1]):
        return ("", "Card expired")
    elif date.today().year[:2]==int(exp_date_list[1]) and date.today().month>int(exp_date_list[0]):
        return ("", "Card expired")
    
    return ("exp_date","")

    """
    Validate expiration date.

    Requirements:
    - Format must be MM/YY
    - Month must be between 01 and 12
    - Must not be expired compared to current UTC date
    - Optional: limit to reasonable future (e.g., +15 years)

    Input:
        exp_date (str)

    Returns:
        (normalized_exp_date, error_message)
    """
    # TODO: Implement validation
    return "", ""


def validate_cvv(cvv: str) -> Tuple[str, str]:
    if any(c.isalpha() for c in cvv):
        return ("","Must contain only digits")
    if len(cvv)<3 or len(cvv)>4:
        return ("", "Must be 3 or 4 digits")

    return("","")    
    """
    Validate CVV.

    Requirements:
    - Must contain only digits
    - Must be exactly 3 or 4 digits
    - Should NOT return the CVV value for storage

    Input:
        cvv (str)

    Returns:
        ("", error_message)
        (always return empty clean value for security reasons)
    """
    # TODO: Implement validation
    return "", ""


def validate_billing_email(billing_email: str) -> Tuple[str, str]:
    billing_email=normalize_basic(billing_email)
    billing_email.lower()
    list = billing_email.split("@")
    if len(billing_email)>254:
        return("", "Maximum length is 254")
    if len(list) != 2 or list[0] == "" or list[1] == "":
        return ("","email must follow the following format juan@prueba.com")

    if len(list[1].split(".")) != 2:
        return ("", "email must follow the following format juan@prueba.com")

    return (billing_email, "")
    """
    Validate billing email.

    Requirements:
    - Normalize (strip + lowercase)
    - Max length 254
    - Must match basic email pattern

    Input:
        billing_email (str)

    Returns:
        (normalized_email, error_message)
    """
    # TODO: Implement validation
    return "", ""


def validate_name_on_card(name_on_card: str) -> Tuple[str, str]:
    name_on_card=normalize_basic(name_on_card)
    if len(name_on_card)<2 or len(name_on_card)>60:
        return("", "Length must be between 2 and 60")
    
    if not (any(c.isalpha() or c =="-" or c =="'" or c ==" " for c in name_on_card)):
        return ("", "Only letters (including accents), spaces, apostrophes, hyphens")
    name_on_card.replace(" ","")

    return (name_on_card, "")

    """
    Validate name on card.

    Requirements:
    - Normalize input
    - Collapse multiple spaces
    - Length between 2 and 60 characters
    - Only letters (including accents), spaces, apostrophes, hyphens

    Input:
        name_on_card (str)

    Returns:
        (normalized_name, error_message)
    """
    # TODO: Implement validation
    return "", ""


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
    """
    Orchestrates all field validations.

    Returns:
        clean (dict)  -> sanitized values safe for storage/use
        errors (dict) -> field_name -> error_message
    """

    clean = {}
    errors = {}

    card, err = validate_card_number(card_number)
    if err:
        errors["card_number"] = err
    clean["card"] = card

    exp_clean, err = validate_exp_date(exp_date)
    if err:
        errors["exp_date"] = err
    clean["exp_date"] = exp_clean

    _, err = validate_cvv(cvv)
    if err:
        errors["cvv"] = err

    name_clean, err = validate_name_on_card(name_on_card)
    if err:
        errors["name_on_card"] = err
    clean["name_on_card"] = name_clean

    email_clean, err = validate_billing_email(billing_email)
    if err:
        errors["billing_email"] = err
    clean["billing_email"] = email_clean

    return clean, errors
