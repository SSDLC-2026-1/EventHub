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


CARD_DIGITS_RE = re.compile(r"^[0-9_]{13,19}$")     # digits only
CVV_RE = re.compile(r"^[0-9_]{3,4}")             # 3 or 4 digits
EXP_RE = re.compile(r"^(0[1-9]|1[0-2])\/[0-9]{2}$")             # MM/YY format
EMAIL_BASIC_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")     # basic email structure
NAME_ALLOWED_RE = re.compile(r"^[a-zA-Z\s'\-]{2,60}$")    # allowed name characters


# =============================
# Utility Functions
# =============================

def normalize_basic(value: str) -> str:
    """
    Normalize input using NFKC and strip whitespace. # Eh creo que este ya está hecho 
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
    # Normalize input
    card_number = normalize_basic(card_number)
    # Remove spaces and hyphens
    card_number = card_number.replace(" ", "").replace("-", "")
    # Validate digits only and length
    ptrn = CARD_DIGITS_RE
    if not ptrn.match(card_number):
        return "", "Número de tarjeta inválido: debe contener solo dígitos y tener entre 13 y 19 caracteres."
    # BONUS: Validate Luhn algorithm
    if not luhn_is_valid(card_number):
        return "", "Número de tarjeta inválido: no pasa la validación de Luhn."

    return card_number, ""

def validate_exp_date(exp_date: str) -> Tuple[str, str]:
    #Normalize input
    exp_date = normalize_basic(exp_date)
    # Format & Month validation
    ptrn = EXP_RE
    if not ptrn.match(exp_date):
        return "", "Fecha de expiración inválida: formato debe ser MM/YY y mes entre 01 y 12."
    # Expiration validation
    try:
        exp_month, exp_year = exp_date.split("/")
        exp_year = int(exp_year)
        now = datetime.now(datetime.UTC)
        current_year = int(str(now.year)[-2:])  # Get last two digits of current year
        current_month = now.month
        if (exp_year < current_year) or (exp_year == current_year and int(exp_month) < current_month):
            return "", "La tarjeta ha expirado."
        if exp_year > current_year + 15:
            return "", "Fecha de expiración demasiado lejana."
    except Exception:
        return "", "Fecha de expiración inválida: formato debe ser MM/YY."

    return exp_date, ""

def validate_cvv(cvv: str) -> Tuple[str, str]:
    # Normalize input
    cvv = normalize_basic(cvv)
    # Digits and length validation
    ptrn = CVV_RE
    if not ptrn.match(cvv):
        return "", "CVV inválido: debe contener solo dígitos y tener 3 o 4 caracteres."

    return "", "" # CVV No retornado por seguridad


def validate_billing_email(billing_email: str) -> Tuple[str, str]:
    # Normalize input
    billing_email = normalize_basic(billing_email).lower()
    # Length validation
    if len(billing_email) > 254:
        return "", "Correo electrónico inválido: debe tener máximo 254 caracteres."
    # Basic email pattern validation
    ptrn = EMAIL_BASIC_RE
    if not ptrn.match(billing_email):
        return "", "Correo electrónico inválido: formato incorrecto."

    return billing_email, ""
    


def validate_name_on_card(name_on_card: str) -> Tuple[str, str]:
    # Normalize input
    name_on_card = normalize_basic(name_on_card)
    # Collapse multiple spaces
    name_on_card = re.sub(r"\s+", " ", name_on_card).strip() #Reemplaza todo \s+ (uno o más espacios) por " " (un solo espacio)
    # Length and character validation
    ptrn = NAME_ALLOWED_RE
    if not ptrn.match(name_on_card):
        return "", "Nombre en la tarjeta inválido: debe tener entre 2 y 60 caracteres y solo contener letras, espacios, apóstrofes o guiones."
    
    return name_on_card, ""

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

if __name__ == "__main__":
    print("--- Test 1: Valid input ---")
    print(validate_payment_form(
        card_number="4111 1111 1111 1111",
        exp_date="12/25",
        cvv="123",
        name_on_card="John O'Connor-Smith",
        billing_email="john.oconnor@example.com"
    ))
    print("\n--- Test 2: Invalid card - too short ---")
    print(validate_payment_form(
        card_number="123456",
        exp_date="12/25",
        cvv="123",
        name_on_card="John Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 3: Invalid card - contains letters ---")
    print(validate_payment_form(
        card_number="4111-1111-1111-111A",
        exp_date="12/25",
        cvv="123",
        name_on_card="John Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 4: Invalid expiration - month 00 ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="00/25",
        cvv="123",
        name_on_card="John Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 5: Invalid expiration - month 13 ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="13/25",
        cvv="123",
        name_on_card="John Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 6: Invalid expiration - format without slash ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="1229",
        cvv="123",
        name_on_card="John Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 7: Invalid CVV - too short ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="12/25",
        cvv="12",
        name_on_card="John Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 8: Invalid CVV - too long ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="12/25",
        cvv="12345",
        name_on_card="John Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 9: Invalid email - missing domain ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="12/25",
        cvv="123",
        name_on_card="John Doe",
        billing_email="test@"
    ))

    print("\n--- Test 10: Invalid email - missing local part ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="12/25",
        cvv="123",
        name_on_card="John Doe",
        billing_email="@example.com"
    ))

    print("\n--- Test 11: Invalid name - contains number ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="12/25",
        cvv="123",
        name_on_card="J0hn Doe",
        billing_email="john@example.com"
    ))

    print("\n--- Test 12: Invalid name - too short ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="12/25",
        cvv="123",
        name_on_card="A",
        billing_email="john@example.com"
    ))

    print("\n--- Test 13: Valid card - Visa alternative ---")
    print(validate_payment_form(
        card_number="5500000000000004",
        exp_date="12/29",
        cvv="123",
        name_on_card="Anne-Marie O'Connor",
        billing_email="anne.marie@example.com"
    ))

    print("\n--- Test 14: Valid name - with apostrophe and hyphen ---")
    print(validate_payment_form(
        card_number="4111111111111111",
        exp_date="12/25",
        cvv="123",
        name_on_card="Juan Pérez",
        billing_email="juan@example.com"
    ))
