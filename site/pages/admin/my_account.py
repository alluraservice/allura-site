"""
My Account — the signed-in user's own profile and password.

Profile: name, personal email and contact number are editable; login email, role and status are
managed by an administrator on the Accounts page.
Password: change it by confirming the current one (standard practice), with a live strength meter
and rule checklist. People signing in with a temporary password are sent here first.
"""
import re

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

import admin_ui as ui
from database.db_handler import get_account_by_email, set_account_password, update_account_profile
from utils.mailer import send_password_changed_notice
from utils.security import check_password, hash_password, password_rules, password_strength

dash.register_page(__name__, path='/admin/my-account')

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
METER_COLORS = ['#b42318', '#b42318', '#c99700', '#5a9a2f', '#006400']


def _field(label, component, help_text=None, full=False):
    return html.Div([html.Label(label, className="a-label"), component,
                     html.Div(help_text, className="a-help") if help_text else None],
                    className="full" if full else None)


def layout():
    profile_form = html.Div([
        html.Div(html.H6("Personal information"), className="a-card-head"),
        html.Div([
            html.Div([
                _field("Full name", dbc.Input(id='me-name', className="a-input"), full=True),
                _field("Login email", dbc.Input(id='me-allura-email', className="a-input", disabled=True),
                       "Ask an administrator if this needs to change."),
                _field("Personal email", dbc.Input(id='me-personal-email', type='email', className="a-input"),
                       "Used for password resets and security notices."),
                _field("Contact number", dbc.Input(id='me-contact', className="a-input", placeholder="+63 9XX XXX XXXX")),
                _field("Role", dbc.Input(id='me-role', className="a-input", disabled=True)),
            ], className="form-grid"),
            html.Div(id='me-profile-feedback', className="mt-3"),
            html.Div(html.Button("Save changes", id='me-save-profile', n_clicks=0, className="a-btn a-btn-primary"),
                     className="d-flex justify-content-end mt-3"),
        ], className="a-card-body"),
    ], className="a-card mb-3")

    password_form = html.Div([
        html.Div([html.H6("Password"), html.Span(id='me-pw-last', className="text-muted", style={'fontSize': '.8rem'})],
                 className="a-card-head"),
        html.Div([
            html.Div(id='me-pw-banner'),
            # Hidden username field so browsers/password managers save the new password against the right login
            dcc.Input(id='me-pw-username', type='email', autoComplete='username', style={'display': 'none'}),
            html.Div([
                _field("Current password", dbc.Input(id='me-pw-current', type='password', className="a-input",
                                                     autoComplete='current-password'), full=True),
                _field("New password", dbc.Input(id='me-pw-new', type='password', className="a-input",
                                                 autoComplete='new-password')),
                _field("Confirm new password", dbc.Input(id='me-pw-confirm', type='password', className="a-input",
                                                         autoComplete='new-password')),
            ], className="form-grid"),
            html.Div([
                html.Div(html.Div(id='me-pw-meter-bar', style={'width': '0%'}), className="pw-meter", style={'flex': 1}),
                html.Span(id='me-pw-meter-label', style={'fontSize': '.78rem', 'minWidth': '70px', 'textAlign': 'right'}),
            ], className="d-flex align-items-center gap-2 mt-2"),
            html.Ul(id='me-pw-rules', className="pw-rules"),
            dbc.Checkbox(id='me-pw-show', label="Show passwords", value=False, className="mt-2", style={'fontSize': '.82rem'}),
            html.Div(id='me-pw-feedback', className="mt-3"),
            html.Div(html.Button("Update password", id='me-pw-save', n_clicks=0, className="a-btn a-btn-primary", disabled=True),
                     className="d-flex justify-content-end mt-3"),
        ], className="a-card-body"),
    ], className="a-card")

    return html.Div([
        dcc.Store(id='me-refresh', data=0),
        ui.page_header("My Account", "Your profile and sign-in security.", crumbs="Admin  /  My Account"),
        html.Div([
            html.Div([
                html.H5("You're not signed in"),
                html.P("Sign in from the Login icon on the website to manage your account.", className="text-muted mb-3"),
                dcc.Link("Go to the website", href='/home', className="a-btn a-btn-primary"),
            ], id='me-signed-out', className="a-card a-card-body text-center", style={'display': 'none'}),
            html.Div([
                html.Div(id='me-profile', className="a-card profile-card"),
                html.Div([profile_form, password_form]),
            ], id='me-content', className="acc-grid", style={'display': 'none'}),
        ], className="admin-container"),
    ], className="admin-shell")


# ---------------------------------------------------------------------
# Load the signed-in account
# ---------------------------------------------------------------------
@callback(
    Output('me-signed-out', 'style'),
    Output('me-content', 'style'),
    Output('me-profile', 'children'),
    Output('me-name', 'value'),
    Output('me-allura-email', 'value'),
    Output('me-personal-email', 'value'),
    Output('me-contact', 'value'),
    Output('me-role', 'value'),
    Output('me-pw-banner', 'children'),
    Output('me-pw-last', 'children'),
    Output('me-pw-username', 'value'),
    Input('session-admin-email', 'data'),
    Input('me-refresh', 'data'),
)
def load_account(session_email, _):
    a = get_account_by_email(session_email) if session_email else None
    if not a:
        return ({}, {'display': 'none'}) + (no_update,) * 9

    status = a.get('status') or 'Active'
    profile = [
        ui.avatar(a['name'], 'lg'),
        html.H4(a['name']),
        html.Div(a.get('role') or '—', className="role"),
        html.Div(html.Span(status, className=f"chip chip-{status.lower()}"), className="mt-2"),
        html.Div([
            html.Div([html.Div("Login email", className="k"), html.Div(a['email'], className="v")]),
            html.Div([html.Div("Member since", className="k"), html.Div(ui.fmt_date(a.get('created_at')), className="v")]),
            html.Div([html.Div("Last sign-in", className="k"), html.Div(ui.fmt_date(a.get('last_login'), True), className="v")]),
        ], className="profile-facts"),
    ]
    banner = None
    if a.get('must_change_password'):
        banner = html.Div([html.B("You're signed in with a temporary password. "),
                           "Choose a new password below to finish setting up your account. "
                           "The current password is the one from your welcome email."],
                          className="a-alert a-alert-warn mb-3")
    last = (f"Last changed {ui.time_ago(a['password_changed_at'])}" if a.get('password_changed_at') else "")
    if ctx.triggered_id == 'me-refresh':
        # A save elsewhere on the page: refresh the card/banner but don't overwrite unsaved form edits
        return ({'display': 'none'}, {}, profile, no_update, no_update, no_update, no_update, no_update,
                banner, last, no_update)
    return ({'display': 'none'}, {}, profile, a['name'], a['email'], a.get('personal_email') or '',
            a.get('contact_number') or '', a.get('role') or '', banner, last, a['email'])


# ---------------------------------------------------------------------
# Save profile
# ---------------------------------------------------------------------
@callback(
    Output('me-profile-feedback', 'children'),
    Output('me-refresh', 'data', allow_duplicate=True),
    Output('session-admin-name', 'data', allow_duplicate=True),
    Input('me-save-profile', 'n_clicks'),
    State('me-name', 'value'),
    State('me-personal-email', 'value'),
    State('me-contact', 'value'),
    State('session-admin-email', 'data'),
    State('me-refresh', 'data'),
    prevent_initial_call=True,
)
def save_profile(n, name, personal_email, contact, session_email, refresh):
    if not n:
        raise dash.exceptions.PreventUpdate
    a = get_account_by_email(session_email)
    if not a:
        raise dash.exceptions.PreventUpdate
    name = (name or '').strip()
    personal_email = (personal_email or '').strip()
    if not name:
        return ui.alert("Your name can't be empty.", 'warn'), no_update, no_update
    if personal_email and not EMAIL_RE.match(personal_email):
        return ui.alert("That personal email doesn't look right.", 'warn'), no_update, no_update
    update_account_profile(a['id'], name, personal_email or None, (contact or '').strip() or None)
    return ui.alert("Profile saved.", 'ok'), (refresh or 0) + 1, name.split(' ')[0]


# ---------------------------------------------------------------------
# Password: live checks, show/hide, save
# ---------------------------------------------------------------------
@callback(
    Output('me-pw-meter-bar', 'style'),
    Output('me-pw-meter-label', 'children'),
    Output('me-pw-rules', 'children'),
    Output('me-pw-save', 'disabled'),
    Input('me-pw-current', 'value'),
    Input('me-pw-new', 'value'),
    Input('me-pw-confirm', 'value'),
)
def live_password_checks(current, new, confirm):
    rules = password_rules(new)
    match = bool(new) and new == confirm
    items = [html.Li(label, className="ok" if ok else "") for label, ok in rules]
    items.append(html.Li("Both new passwords match", className="ok" if match else ""))
    score, label = password_strength(new)
    bar = {'width': f"{(score + 1) * 20 if new else 0}%", 'background': METER_COLORS[score]}
    ready = bool(current) and all(ok for _, ok in rules) and match
    return bar, html.Span(label, style={'color': METER_COLORS[score], 'fontWeight': 700}), items, not ready


@callback(
    Output('me-pw-current', 'type'),
    Output('me-pw-new', 'type'),
    Output('me-pw-confirm', 'type'),
    Input('me-pw-show', 'value'),
)
def toggle_show(show):
    t = 'text' if show else 'password'
    return t, t, t


@callback(
    Output('me-pw-feedback', 'children'),
    Output('me-pw-current', 'value'),
    Output('me-pw-new', 'value'),
    Output('me-pw-confirm', 'value'),
    Output('me-refresh', 'data', allow_duplicate=True),
    Input('me-pw-save', 'n_clicks'),
    State('me-pw-current', 'value'),
    State('me-pw-new', 'value'),
    State('me-pw-confirm', 'value'),
    State('session-admin-email', 'data'),
    State('me-refresh', 'data'),
    prevent_initial_call=True,
)
def change_password(n, current, new, confirm, session_email, refresh):
    if not n:
        raise dash.exceptions.PreventUpdate
    keep = (no_update,) * 4
    a = get_account_by_email(session_email)
    if not a:
        return (ui.alert("You're not signed in.", 'err'),) + keep
    if not check_password(current, a.get('password_hash')):
        return (ui.alert("Your current password is incorrect.", 'err'), '', no_update, no_update, no_update)
    if not all(ok for _, ok in password_rules(new)):
        return (ui.alert("The new password doesn't meet all the requirements.", 'warn'),) + keep
    if new != confirm:
        return (ui.alert("The new passwords don't match.", 'warn'),) + keep
    if new == current:
        return (ui.alert("Choose a password different from your current one.", 'warn'),) + keep

    set_account_password(a['id'], hash_password(new), must_change=False)
    note = ""
    if a.get('personal_email'):
        sent, _ = send_password_changed_notice(a['personal_email'], a['name'])
        note = f" A confirmation was sent to {a['personal_email']}." if sent else ""
    return ui.alert("Password updated." + note, 'ok'), '', '', '', (refresh or 0) + 1
