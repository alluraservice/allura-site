"""Password helpers: temporary passwords, hashing, verification, strength rules and reset tokens."""
import hashlib
import re
import secrets
import string

import bcrypt

MIN_LENGTH = 8


def generate_temp_password(length=12):
    """Random password that always satisfies the strength rules (upper, lower, digit, symbol)."""
    symbols = "!@#$%&*?"
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, symbols]
    # Avoid look-alike characters so it's easy to type from an email
    pools = [''.join(c for c in p if c not in "O0Il1") for p in pools]
    chars = [secrets.choice(p) for p in pools]
    everything = ''.join(pools)
    chars += [secrets.choice(everything) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return ''.join(chars)


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(password, stored_hash):
    if not password or not stored_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except ValueError:
        return False


def password_rules(password):
    """Returns a list of (label, passed) used by both the live checklist and server-side validation."""
    p = password or ""
    return [
        (f"At least {MIN_LENGTH} characters", len(p) >= MIN_LENGTH),
        ("An uppercase letter", bool(re.search(r"[A-Z]", p))),
        ("A lowercase letter", bool(re.search(r"[a-z]", p))),
        ("A number", bool(re.search(r"\d", p))),
        ("A symbol (e.g. ! @ # $)", bool(re.search(r"[^A-Za-z0-9]", p))),
    ]


def password_strength(password):
    """0-4 score plus a label, for the strength meter."""
    if not password:
        return 0, ""
    passed = sum(ok for _, ok in password_rules(password))
    score = max(0, passed - 1)               # 5 rules -> 0..4
    if len(password) >= 14 and passed == 5:
        score = 4
    labels = {0: "Very weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong"}
    return score, labels[score]


def new_reset_token():
    """Returns (token for the emailed link, hash to store). Only the hash is saved in the database."""
    token = secrets.token_urlsafe(32)
    return token, hash_reset_token(token)


def hash_reset_token(token):
    return hashlib.sha256((token or '').encode('utf-8')).hexdigest()
