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
from datetime import datetime
from typing import Tuple, Dict


# =============================
# Regular Patterns
# =============================


CARD_DIGITS_RE = re.compile(r"[0-9]")     # digits only
CVV_RE = re.compile(r"[0-9][0-9][0-9][0-9]")             # 3 or 4 digits
EXP_RE = re.compile(r"^[0-1][0-9][2-3][0-9]")             # MM/YY format
EMAIL_BASIC_RE = re.compile(r"^[a-zA-Z0-9_@.\-]*$")     # basic email structure
NAME_ALLOWED_RE = re.compile(r"[a-zA-z]*$")    # allowed name characters


# =============================
# Utility Functions
# =============================

def normalize_basic(value: str) -> str:
    """
    Normalize input using NFKC and strip whitespace.
    """
    return unicodedata.normalize("NFKC", (value or "")).strip()



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



# =============================
# Field Validations
# =============================

def validate_card_number(card_number: str) -> Tuple[str, str]:
    """
    Validate credit card number.

    Requirements:
    - Normalize input """
   
    if not luhn_is_valid(card_number):
       return "", "Card number is not valid according to Luhn algorithm"
    
    
    
    # TODO: Implement validation

    card_number = unicodedata.normalize("NFKC", card_number)
    card_number = card_number.split()
    card_number = "".join(card_number)
    print(card_number)
    card_number = card_number.split("-")
    card_number = "".join(card_number)
    print(card_number)
    if not CARD_DIGITS_RE.match(card_number):
        return "", "Numero de tarjeta no valido"
    if len(card_number) >= 13 and len(card_number) <= 19:
        return f"{card_number}", ""
    else:
        return "", "Numero de tarjeta no valido"


def validate_exp_date(exp_date: str) -> Tuple[str, str]:
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
    try:
        for i in cvv:
            a = int(i)
    except: 
        return "", "CVV no valido"

    if len(cvv) == 3 or len(cvv) == 4:
        return "", ""
    else:
        return "", "CVV no valido"


def validate_billing_email(billing_email: str) -> Tuple[str, str]:
    """
    Validate billing email.

    Requirements:
    - Normalize (strip + lowercase)
    billing_email = billing_email.strip().lower()
    
    - Max length 254
    if len(billing_email) > 254:
        return "", "Email is too long"
    
    - Must match basic email pattern
    if not EMAIL_BASIC_RE.match(billing_email):
        return "", "Email format is invalid"

    if normalized_email != billing_email:
        return "", "Email normalization error"
    else: 
        return billing_email, ""

    Input:
        billing_email (str)
        

    Returns:
        (normalized_email, error_message)
    """
    # TODO: Implement validation
    billing_email = unicodedata.normalize("NFKC", billing_email)
    billing_email = billing_email.strip().lower()
    if len(billing_email) > 254:
        return "", "Email no valido"
    if not EMAIL_BASIC_RE.match(billing_email):
        return "", "Email no valido"
    return billing_email, ""


def validate_name_on_card(name_on_card: str) -> Tuple[str, str]:
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
    name_on_card = unicodedata.normalize("NFKC", name_on_card)
    name_on_card = name_on_card.strip()
    if len(name_on_card) < 2 or len(name_on_card) > 60:
        return "", "Nombre no valido"
    if not NAME_ALLOWED_RE.match(name_on_card):
        return "", "Nombre no valido"
    return f"{name_on_card}", ""


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
