"""
Admin sign-in security (tracker item C-01).

1. Server-side signed session
   Signing in now also stores the account in a signed, HttpOnly Flask session cookie that expires
   after SESSION_HOURS without use. The browser can no longer "sign itself in" by editing the
   session-admin-email value: every request to an admin-page callback is checked against the
   signed session, and admin pages are only shown when it is valid.

2. Login lockout
   After MAX_FAILED_LOGINS wrong passwords in a row, the account is locked for LOCK_MINUTES.
   A correct password (after the lock ends) or a password reset by an admin clears the counter.

3. Default password check
   On start-up, any account still using the default password from the Milestone 3 report is marked
   "must change password", so its next sign-in goes straight to My Account.

Settings: SECRET_KEY (environment variable on Render). If it is missing, a key is derived from
DATABASE_URL so every server worker uses the same key; set SECRET_KEY to log everyone out at once.
"""
import hashlib
import json
import os
from datetime import timedelta

from flask import abort, request, session

SESSION_HOURS = 12
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15

# Modules whose callbacks only signed-in admins may run
ADMIN_MODULE_PREFIXES = ('pages.admin', 'admin_commonmodules')
# Admin callbacks that must still work after the session expired (so Logout always works)
ALWAYS_ALLOWED_OUTPUT_IDS = ('logout-confirm-modal',)

_admin_outputs = set()


# ------------------------------------------------------------------ set-up
def _secret_key():
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    seed = os.environ.get('DATABASE_URL', '') + '|allura-admin-session|v1'
    return hashlib.sha256(seed.encode('utf-8')).hexdigest()


def configure(app):
    """Call once after all pages are imported (index.py)."""
    server = app.server
    server.secret_key = _secret_key()
    server.config.update(
        PERMANENT_SESSION_LIFETIME=timedelta(hours=SESSION_HOURS),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=bool(os.environ.get('RENDER') or os.environ.get('SESSION_COOKIE_SECURE')),
        SESSION_REFRESH_EACH_REQUEST=True,
    )
    _collect_admin_outputs(app)

    @server.before_request
    def _guard_admin_callbacks():
        if not request.path.endswith('/_dash-update-component'):
            return None
        body = request.get_json(silent=True) or {}
        output = body.get('output') or ''
        if output not in _admin_outputs or any(x in output for x in ALWAYS_ALLOWED_OUTPUT_IDS):
            return None
        if not current_email():
            abort(401)
        # The page's own copy of the email must match the signed session
        for item in (body.get('inputs') or []) + (body.get('state') or []):
            if isinstance(item, dict) and item.get('id') == 'session-admin-email':
                value = item.get('value')
                if value and str(value).lower() != current_email().lower():
                    abort(401)
        return None


def _collect_admin_outputs(app):
    from dash._callback import GLOBAL_CALLBACK_MAP
    for output, spec in list(GLOBAL_CALLBACK_MAP.items()) + list(app.callback_map.items()):
        fn = spec.get('callback')
        module = getattr(fn, '__module__', '') or getattr(getattr(fn, '__wrapped__', None), '__module__', '') or ''
        if module.startswith(ADMIN_MODULE_PREFIXES):
            _admin_outputs.add(output)


# ------------------------------------------------------------------ session
def start_session(account):
    session.clear()
    session.permanent = True
    session['aid'] = account.get('id')
    session['email'] = account.get('email')


def end_session():
    session.clear()


def current_email():
    try:
        return session.get('email')
    except RuntimeError:      # outside a request
        return None


def session_matches(store_email):
    """True if the signed session belongs to the email the page holds."""
    email = current_email()
    return bool(email and store_email and email.lower() == str(store_email).lower())


# ------------------------------------------------------------------ lockout
def lock_message(minutes_left):
    m = max(1, int(minutes_left + 0.999))
    return (f"Too many incorrect attempts. This account is locked for {m} more minute{'s' if m != 1 else ''}. "
            "Try again later, or ask an admin with “Can manage accounts” to reset your password.")


# ------------------------------------------------------------------ default password

def flag_default_password():
    """Mark accounts that still use the Milestone 3 default password as 'must change password'."""
    try:
        from database.db_handler import _run
        from utils.security import check_password
        # The default password was published in the Milestone 3 report (and in generate_hash.py, now removed)
        default = os.environ.get('LEGACY_DEFAULT_PASSWORD', 'Admin2026!')
        rows = _run("SELECT id, password_hash FROM accounts WHERE password_hash IS NOT NULL "
                    "AND COALESCE(must_change_password, FALSE) = FALSE;", fetch='all') or []
        flagged = 0
        for r in rows:
            if check_password(default, r['password_hash']):
                _run("UPDATE accounts SET must_change_password = TRUE WHERE id = %s;", [r['id']],
                     fetch='none', commit=True)
                flagged += 1
        if flagged:
            print(f"[auth] {flagged} account(s) still used the default password; they must change it at next sign-in.")
    except Exception as e:   # never stop the site from starting
        print(f"[auth] default password check skipped: {e}")
