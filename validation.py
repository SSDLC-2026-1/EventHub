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
from datetime import timezone


# =============================
# Regular Patterns
# =============================


CARD_DIGITS_RE = re.compile(r"^[0-9_]{13,19}$")     # digits only
CVV_RE = re.compile(r"^[0-9_]{3,4}")             # 3 or 4 digits
EXP_RE = re.compile(r"^(0[1-9]|1[0-2])\/[0-9]{2}$")             # MM/YY format
EMAIL_BASIC_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")     # basic email structure
NAME_ALLOWED_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'\-]{2,60}$")    # allowed name characters
MOBILE_RE = re.compile(r"^[0-9]{7,15}")
PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[.!@#$%^&*()\-_=\+\[\]{}<>?])[.A-Za-z\d!@#$%^&*()\-_=\+\[\]{}<>?]{8,64}$")

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
        now = datetime.now(timezone.utc)
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


def validate_email(billing_email: str) -> Tuple[str, str]:
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
    


def validate_name(name_on_card: str) -> Tuple[str, str]:
    # Normalize input
    name_on_card = normalize_basic(name_on_card)
    # Collapse multiple spaces
    name_on_card = re.sub(r"\s+", " ", name_on_card).strip() #Reemplaza todo \s+ (uno o más espacios) por " " (un solo espacio)
    # Length and character validation
    ptrn = NAME_ALLOWED_RE
    if not ptrn.match(name_on_card):
        return "", "Nombre inválido: debe tener entre 2 y 60 caracteres y solo contener letras, espacios, apóstrofes o guiones."
    
    return name_on_card, ""

def validate_mobile_number(mobile_number: str) -> Tuple[str, str]:
    # Normalize input
    mobile_number = normalize_basic(mobile_number)
    # Collapse multiple spaces
    mobile_number = re.sub(r"\s+", " ", mobile_number).strip()
    # Length and pattern validation
    ptrn = MOBILE_RE
    if not ptrn.match(mobile_number):
        return "", "Número inválido: debe tener entre 7 y 15 númers, sin identificador internacionales ni letras o caracteres especiales."
    
    return mobile_number, ""

def validate_password(password: str) -> Tuple[str, str]:
    # Normalize input
    password = normalize_basic(password)
    # Length and pattern validation
    ptrn = PASSWORD_RE
    if not ptrn.match(password):
        return "", "Contraseña inválida: debe tener entre 8 y 64 caracteres, contener al menos una letra mayúscula, una letra minúscula y un número, y no contener caracteres especiales."
    
    return password, ""
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

    name_clean, err = validate_name(name_on_card)
    if err:
        errors["name_on_card"] = err
    clean["name_on_card"] = name_clean

    email_clean, err = validate_email(billing_email)
    if err:
        errors["billing_email"] = err
    clean["billing_email"] = email_clean

    return clean, errors

if __name__ == "__main__":
    pass