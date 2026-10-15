"""
Outgoing email: admin invites, password emails, inquiry acknowledgements and replies.

Configure with environment variables, or put them in a `.env` file in the project root
(see `.env.example`; that file is read automatically, no extra package needed):
    SMTP_HOST        e.g. smtp.gmail.com  /  smtp.office365.com  /  your host's SMTP server
    SMTP_PORT        587 (STARTTLS, default) or 465 (SSL)
    SMTP_USER        the mailbox that sends, e.g. info@alluraenterpriseph.com
    SMTP_PASSWORD    that mailbox's password (for Gmail/Google Workspace: an App Password)
    SMTP_FROM        optional, defaults to SMTP_USER
    SMTP_FROM_NAME   optional, defaults to "Allura Enterprise"
    SITE_URL         the public address of the website, used in links (e.g. https://allura.onrender.com)

If SMTP isn't configured, nothing is sent: the message is saved as an .eml file in /outbox
so you can open it and see exactly what would have gone out, and the caller is told it was not sent.
"""
import html as _html
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTBOX_DIR = os.path.join(ROOT, 'outbox')

BRAND_GREEN = "#006400"
BRAND_DARK = "#084008"
BRAND_LIGHT = "#eef3e4"


def _load_dotenv():
    """Reads KEY=VALUE lines from <project>/.env (or site/.env) without overriding real env vars."""
    for path in (os.path.join(ROOT, '.env'), os.path.join(ROOT, 'site', '.env')):
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        except OSError as e:
            print(f"[mailer] Could not read {path}: {e}")


_load_dotenv()


def is_configured():
    return bool(os.environ.get('SMTP_HOST') and os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASSWORD'))


def site_url(fallback=None):
    """Base address for links in emails: SITE_URL, else the address the request came in on."""
    url = os.environ.get('SITE_URL') or fallback
    if not url:
        try:
            from flask import request
            url = request.host_url
        except Exception:
            url = 'http://127.0.0.1:8050/'
    return url.rstrip('/')


def _branded_html(title, body_html, footer_note="This message was sent by Allura Enterprise."):
    return f"""<!doctype html>
<html><body style="margin:0;padding:0;background:#f4f6f1;font-family:Arial,Helvetica,sans-serif;color:{BRAND_DARK};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f1;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e3e9da;">
        <tr><td style="background:{BRAND_GREEN};padding:18px 28px;color:#ffffff;font-size:18px;font-weight:bold;letter-spacing:.5px;">ALLURA ENTERPRISE</td></tr>
        <tr><td style="padding:28px;">
          <h2 style="margin:0 0 16px 0;font-size:20px;color:{BRAND_DARK};">{_html.escape(title)}</h2>
          <div style="font-size:15px;line-height:1.6;color:#2b3a2b;">{body_html}</div>
        </td></tr>
        <tr><td style="background:{BRAND_LIGHT};padding:14px 28px;font-size:12px;color:#5b6b5b;">
          {_html.escape(footer_note)}<br>info@alluraenterpriseph.com &middot; +63 917 770 1820
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def _button(label, href):
    return (f'<p style="margin:22px 0;"><a href="{_html.escape(href)}" style="background:{BRAND_GREEN};color:#ffffff;'
            f'text-decoration:none;font-weight:bold;padding:12px 24px;border-radius:999px;display:inline-block;">'
            f'{_html.escape(label)}</a></p>')


def _ref_box(reference_no):
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="background:{BRAND_LIGHT};border-radius:10px;'
            f'padding:12px 18px;margin:0 0 18px 0;"><tr><td style="color:#5b6b5b;font-size:12px;">Reference no.</td></tr>'
            f'<tr><td style="font-size:18px;font-weight:bold;font-family:Consolas,Menlo,monospace;letter-spacing:1px;">'
            f'{_html.escape(reference_no)}</td></tr></table>')


def text_to_html(text):
    """Escapes plain text and keeps its line breaks."""
    return _html.escape(text or "").replace("\n", "<br>")


def send_email(to, subject, text_body, html_body=None, reply_to=None):
    """Sends one email. Returns (ok: bool, message: str). Never raises."""
    if not to:
        return False, "No recipient email address."

    sender = os.environ.get('SMTP_FROM') or os.environ.get('SMTP_USER') or 'no-reply@alluraenterpriseph.com'
    sender_name = os.environ.get('SMTP_FROM_NAME', 'Allura Enterprise')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr((sender_name, sender))
    msg['To'] = to
    msg['Message-ID'] = make_msgid(domain=sender.split('@')[-1])
    if reply_to:
        msg['Reply-To'] = reply_to
    msg.set_content(text_body or "")
    if html_body:
        msg.add_alternative(html_body, subtype='html')

    if not is_configured():
        path = _save_to_outbox(msg, to)
        return False, f"Email is not set up on this server yet (SMTP settings missing). A copy was saved to {path}."

    host = os.environ['SMTP_HOST']
    port = int(os.environ.get('SMTP_PORT', 587))
    user = os.environ['SMTP_USER']
    password = os.environ['SMTP_PASSWORD']
    try:
        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls(context=context)
                server.login(user, password)
                server.send_message(msg)
        return True, f"Sent to {to}."
    except Exception as e:
        print(f"[mailer] Failed to send to {to}: {e}")
        return False, f"Could not send email to {to}: {e}"


def _save_to_outbox(msg, to):
    os.makedirs(OUTBOX_DIR, exist_ok=True)
    safe_to = ''.join(c if c.isalnum() else '_' for c in to)[:40]
    name = f"{datetime.now():%Y%m%d-%H%M%S}-{safe_to}.eml"
    path = os.path.join(OUTBOX_DIR, name)
    with open(path, 'wb') as f:
        f.write(bytes(msg))
    return os.path.join('outbox', name)


def _first(full_name):
    return (full_name or '').split(' ')[0] or 'there'


# ------------------------------------------------------------------
# Admin accounts
# ------------------------------------------------------------------
def send_admin_invite(to, full_name, temp_password, role, invited_by=None, login_url=None):
    """New admin: invite sent to the email that was typed in, with that email + a temporary password."""
    url = site_url(login_url)
    first = _first(full_name)
    phrase = f"{invited_by} has invited you" if invited_by else "You've been invited"
    title = "You're invited to manage the Allura Enterprise website"
    text = (
        f"Hi {first},\n\n"
        f"{phrase} to be an admin of the Allura Enterprise website"
        f"{f' as {role}' if role else ''}.\n\n"
        f"Sign in with:\n  Email: {to}\n  Temporary password: {temp_password}\n\n"
        f"Go to {url}/home?login=1 and use the Login icon at the top right. "
        f"You'll be asked to choose your own password right after signing in.\n\n"
        f"If you weren't expecting this invitation, you can ignore this email.\n\n- Allura Enterprise"
    )
    body = f"""
      <p>Hi {_html.escape(first)},</p>
      <p>{_html.escape(phrase)} to be an <b>admin of the Allura Enterprise website</b>{
        f' as <b>{_html.escape(role)}</b>' if role else ''}.</p>
      <table role="presentation" cellpadding="0" cellspacing="0" style="background:{BRAND_LIGHT};border-radius:10px;padding:16px 20px;margin:18px 0;width:100%;">
        <tr><td style="padding:4px 0;color:#5b6b5b;font-size:13px;">Email</td></tr>
        <tr><td style="padding:0 0 10px 0;font-size:16px;font-weight:bold;">{_html.escape(to)}</td></tr>
        <tr><td style="padding:4px 0;color:#5b6b5b;font-size:13px;">Temporary password</td></tr>
        <tr><td style="padding:0;font-size:18px;font-weight:bold;font-family:Consolas,Menlo,monospace;letter-spacing:1px;">{_html.escape(temp_password)}</td></tr>
      </table>
      {_button("Accept invite & sign in", f"{url}/home?login=1")}
      <p>For your security you'll be asked to choose your own password right after signing in.</p>
      <p style="color:#5b6b5b;font-size:13px;">If you weren't expecting this invitation, you can ignore this email.</p>
    """
    return send_email(to, title, text, _branded_html(title, body,
                      "You received this because an Allura Enterprise administrator invited this email address."))


def send_account_credentials(to, full_name, allura_email, temp_password, role, login_url=None, is_reset=False):
    """Temporary password email (used when an administrator resets someone's password)."""
    url = site_url(login_url)
    first = _first(full_name)
    if is_reset:
        title = "Your Allura account password was reset"
        intro = "An administrator reset the password for your Allura Enterprise admin account."
    else:
        title = "Your Allura Enterprise admin account"
        intro = f"An account has been created for you on the Allura Enterprise admin site with the role <b>{_html.escape(role or '')}</b>."
    text = (f"Hi {first},\n\n{'An administrator reset your Allura Enterprise account password.' if is_reset else 'An Allura Enterprise admin account has been created for you.'}\n\n"
            f"Login email: {allura_email}\nTemporary password: {temp_password}\n\n"
            f"Sign in at {url}/home?login=1. You will be asked to choose your own password right after signing in.\n\n"
            f"If you weren't expecting this email, contact your administrator.\n\n- Allura Enterprise")
    body = f"""
      <p>Hi {_html.escape(first)},</p><p>{intro}</p>
      <table role="presentation" cellpadding="0" cellspacing="0" style="background:{BRAND_LIGHT};border-radius:10px;padding:16px 20px;margin:18px 0;width:100%;">
        <tr><td style="padding:4px 0;color:#5b6b5b;font-size:13px;">Login email</td></tr>
        <tr><td style="padding:0 0 10px 0;font-size:16px;font-weight:bold;">{_html.escape(allura_email)}</td></tr>
        <tr><td style="padding:4px 0;color:#5b6b5b;font-size:13px;">Temporary password</td></tr>
        <tr><td style="padding:0;font-size:18px;font-weight:bold;font-family:Consolas,Menlo,monospace;letter-spacing:1px;">{_html.escape(temp_password)}</td></tr>
      </table>
      {_button("Sign in", f"{url}/home?login=1")}
      <p style="color:#5b6b5b;font-size:13px;">If you weren't expecting this email, please contact your administrator.</p>
    """
    return send_email(to, title, text, _branded_html(title, body))


def send_password_reset_link(to, full_name, link, minutes=60):
    first = _first(full_name)
    title = "Reset your Allura password"
    text = (f"Hi {first},\n\nWe received a request to reset the password for your Allura Enterprise admin account.\n\n"
            f"Open this link to choose a new password (it works once and expires in {minutes} minutes):\n{link}\n\n"
            f"If you didn't ask for this, you can ignore this email; your password won't change.\n\n- Allura Enterprise")
    body = (f"<p>Hi {_html.escape(first)},</p>"
            f"<p>We received a request to reset the password for your Allura Enterprise admin account.</p>"
            f"{_button('Choose a new password', link)}"
            f"<p style='color:#5b6b5b;font-size:13px;'>This link works once and expires in {minutes} minutes. "
            f"If the button doesn't work, copy this address into your browser:<br>{_html.escape(link)}</p>"
            f"<p style='color:#5b6b5b;font-size:13px;'>If you didn't ask for this, you can ignore this email; your password won't change.</p>")
    return send_email(to, title, text, _branded_html(title, body, "Account recovery for the Allura Enterprise website."))


def send_password_changed_notice(to, full_name):
    first = _first(full_name)
    when = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    title = "Your Allura password was changed"
    text = (f"Hi {first},\n\nThe password for your Allura Enterprise admin account was changed on {when}.\n"
            f"If this was you, no action is needed. If it wasn't, contact your administrator right away.\n\n- Allura Enterprise")
    body = (f"<p>Hi {_html.escape(first)},</p><p>The password for your Allura Enterprise admin account was changed on "
            f"<b>{when}</b>.</p><p>If this was you, no action is needed. If it wasn't, contact your administrator right away.</p>")
    return send_email(to, title, text, _branded_html(title, body))


# ------------------------------------------------------------------
# Inquiries
# ------------------------------------------------------------------
def send_inquiry_acknowledgement(to, contact_name, reference_no, source, summary):
    """Sent to the customer right after they submit a form, so they have the reference number."""
    first = (contact_name or '').strip() or 'Sir/Madam'
    title = f"We received your inquiry [{reference_no}]"
    text = (f"Dear {first},\n\nThank you for contacting Allura Enterprise. We received your inquiry "
            f"({source}) and our team will get back to you within one business day.\n\n"
            f"Reference no.: {reference_no}\n\nYour message:\n{summary}\n\n"
            f"Please mention the reference number if you call or email us about this request.\n\n- Allura Enterprise")
    body = (f"<p>Dear {_html.escape(first)},</p>"
            f"<p>Thank you for contacting Allura Enterprise. We received your inquiry and our team will get back to you "
            f"within one business day.</p>{_ref_box(reference_no)}"
            f"<p style='color:#5b6b5b;font-size:13px;margin-bottom:4px;'>Your message</p>"
            f"<div style='border-left:3px solid #d6e3c6;padding-left:12px;'>{text_to_html(summary)}</div>"
            f"<p style='margin-top:18px;'>Please mention the reference number if you call or email us about this request.</p>")
    return send_email(to, title, text, _branded_html(title, body, f"Inquiry received via {source}."))


def send_inquiry_reply(to, subject, reply_text, agent_name=None, reply_to=None, reference_no=None):
    """reply_to = the agent's Allura email, so when the client hits Reply it reaches the team."""
    if reference_no and reference_no not in (subject or ''):
        subject = f"[{reference_no}] {subject}"
    body = (_ref_box(reference_no) if reference_no else "") + f"<div>{text_to_html(reply_text)}</div>"
    text = (f"Reference no.: {reference_no}\n\n" if reference_no else "") + (reply_text or "")
    return send_email(to, subject, text, _branded_html(subject, body,
                      f"Reply from {agent_name or 'Allura Enterprise'} regarding your inquiry"
                      + (f" {reference_no}." if reference_no else ".")), reply_to=reply_to)
