"""
Accounts — manage the admin users of the website.

Adding an account sends an INVITE to the email that was typed in: the email itself is their login,
and the invite contains a temporary password. They must choose their own password on first sign-in.

Account powers (stored per account):
    can_manage_accounts  - may add, edit, reset passwords for and delete accounts
    can_grant_access     - may give or remove these two powers for any account
Everyone else can only view the list. The checks are enforced in the callbacks, not just hidden in
the page. There must always be at least one active account that can grant access, and nobody can
delete or deactivate their own account.
"""
import re

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update

import admin_ui as ui
from database.db_handler import (ACCOUNT_ROLES, allura_email_exists, count_access_granters, create_account,
                                 delete_account, get_account_by_email, get_account_by_id, get_all_accounts,
                                 set_account_password, set_account_permissions, update_account_admin_fields)
from utils.mailer import send_account_credentials, send_admin_invite
from utils.security import generate_temp_password, hash_password

dash.register_page(__name__, path='/admin/accounts')

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HIDE = {'display': 'none'}


def _field(label, component, help_text=None, full=False):
    return html.Div([html.Label(label, className="a-label"), component,
                     html.Div(help_text, className="a-help") if help_text else None],
                    className="full" if full else None)


def _role_select(id_, value=None):
    return dbc.Select(id=id_, options=[{'label': r, 'value': r} for r in ACCOUNT_ROLES],
                      value=value or ACCOUNT_ROLES[1], className="a-input")


def _status_select(id_, value='Active'):
    return dbc.Select(id=id_, options=[{'label': s, 'value': s} for s in ('Active', 'Inactive')],
                      value=value, className="a-input")


def _perm_switches(prefix):
    return html.Div([
        html.Div([html.Div([html.B("Can manage accounts"),
                            html.Span("Add, edit, reset passwords for and delete admin accounts.")], className="t"),
                  dbc.Switch(id=f'{prefix}-manage', value=False)], className="switch-row"),
        html.Div([html.Div([html.B("Can grant access"),
                            html.Span("Give or remove these two powers for other accounts.")], className="t"),
                  dbc.Switch(id=f'{prefix}-grant', value=False)], className="switch-row"),
    ], className="perm-box")


def _me(session_email):
    me = get_account_by_email(session_email) if session_email else None
    if not me or (me.get('status') or 'Active') != 'Active':
        return None
    return me


def layout():
    add_modal = dbc.Modal(dbc.ModalBody([
        html.Div([
            html.Div([html.H4("Invite a new admin"),
                      html.Button(id='acc-add-x', n_clicks=0, className="btn-close")],
                     className="d-flex justify-content-between align-items-center"),
            html.P("We'll email an invite to this address with their login (the same email) and a temporary password.",
                   className="modal-sub"),
            html.Div([
                _field("Full name", dbc.Input(id='acc-name', className="a-input", placeholder="e.g. Juan Dela Cruz"), full=True),
                _field("Email", dbc.Input(id='acc-email', type='email', className="a-input", placeholder="name@gmail.com"),
                       "The invite is sent here, and this is the email they'll sign in with.", full=True),
                _field("Contact number (optional)", dbc.Input(id='acc-contact', className="a-input", placeholder="+63 9XX XXX XXXX")),
                _field("Role", _role_select('acc-role')),
                _field("Status", _status_select('acc-status')),
            ], className="form-grid"),
            html.Div([
                html.Div("Account powers", className="a-section-title mt-4"),
                _perm_switches('acc-add'),
            ], id='acc-add-perms', style=HIDE),
            html.Div(id='acc-add-feedback', className="mt-3"),
            html.Div([
                html.Button("Cancel", id='acc-add-cancel', n_clicks=0, className="a-btn a-btn-outline"),
                html.Button("Send invite", id='acc-add-save', n_clicks=0, className="a-btn a-btn-primary"),
            ], className="modal-actions"),
        ], id='acc-add-form'),
        html.Div([
            html.Div(id='acc-add-result'),
            html.Div(html.Button("Done", id='acc-add-done', n_clicks=0, className="a-btn a-btn-primary"),
                     className="modal-actions"),
        ], id='acc-add-done-view', style=HIDE),
    ]), id='acc-add-modal', size='lg', centered=True, is_open=False, className="a-modal", backdrop='static')

    manage_modal = dbc.Modal(dbc.ModalBody([
        dcc.Store(id='acc-manage-id'),
        html.Div([html.Div(id='acc-manage-head'),
                  html.Button(id='acc-manage-x', n_clicks=0, className="btn-close")],
                 className="d-flex justify-content-between align-items-start mb-3"),
        html.Div([
            _field("Role", _role_select('acc-m-role')),
            _field("Status", _status_select('acc-m-status')),
            _field("Backup email (optional)", dbc.Input(id='acc-m-personal-email', type='email', className="a-input"),
                   "Where password notices are sent."),
            _field("Contact number", dbc.Input(id='acc-m-contact', className="a-input")),
        ], className="form-grid"),
        html.Div([
            html.Div("Account powers", className="a-section-title mt-4"),
            _perm_switches('acc-m'),
            html.Div(id='acc-m-perm-note', className="perm-note"),
        ]),
        html.Div([
            html.Div("Password", className="a-section-title mt-4"),
            html.Div([
                html.Div(id='acc-m-pw-info', className="text-muted", style={'fontSize': '.84rem'}),
                dcc.ConfirmDialogProvider(
                    html.Button("Reset & email a temporary password", className="a-btn a-btn-outline a-btn-sm"),
                    id='acc-m-reset', message="Generate a new temporary password for this user and email it to them? "
                                              "Their current password will stop working."),
            ], className="d-flex justify-content-between align-items-center gap-3 flex-wrap"),
            html.Div("Delete account", className="a-section-title mt-4"),
            html.Div([
                html.Div("Removes their access to the admin site. Inquiries assigned to them become unassigned.",
                         className="text-muted", style={'fontSize': '.84rem'}),
                dcc.ConfirmDialogProvider(
                    html.Button("Delete account", className="a-btn a-btn-danger a-btn-sm"),
                    id='acc-m-delete', message="Delete this account permanently? They will no longer be able to sign in. "
                                               "This can't be undone."),
            ], className="d-flex justify-content-between align-items-center gap-3 flex-wrap"),
        ], id='acc-m-manage-tools'),
        html.Div(id='acc-manage-feedback', className="mt-3"),
        html.Div([
            html.Button("Cancel", id='acc-manage-cancel', n_clicks=0, className="a-btn a-btn-outline"),
            html.Button("Save changes", id='acc-manage-save', n_clicks=0, className="a-btn a-btn-primary"),
        ], className="modal-actions"),
    ]), id='acc-manage-modal', size='lg', centered=True, is_open=False, className="a-modal")

    return html.Div([
        dcc.Store(id='acc-refresh', data=0),
        dcc.Store(id='acc-me', data={}),
        ui.page_header("Accounts", "Admin users, their roles, and who can manage access to this site.",
                       crumbs="Admin  /  Accounts",
                       actions=[html.Button("+  Invite admin", id='acc-add-open', n_clicks=0,
                                            className="a-btn a-btn-light", style=HIDE)]),
        html.Div([
            dbc.Alert(id='acc-toast', is_open=False, duration=5000, dismissable=True, className="a-alert a-alert-ok mb-3"),
            html.Div(id='acc-perm-banner'),
            html.Div(id='acc-stats', className="stat-row mb-3"),
            html.Div([
                html.Div([
                    html.Div(dbc.Input(id='acc-search', type='search', className="a-input", debounce=True,
                                       placeholder="Search name or email…"), className="a-search grow"),
                    html.Div(dbc.Select(id='acc-f-role', className="a-input", value='all',
                                        options=[{'label': 'All roles', 'value': 'all'}] + [{'label': r, 'value': r} for r in ACCOUNT_ROLES]),
                             className="fit"),
                    html.Div(dbc.Select(id='acc-f-status', className="a-input", value='all',
                                        options=[{'label': 'Any status', 'value': 'all'}, {'label': 'Active', 'value': 'Active'},
                                                 {'label': 'Inactive', 'value': 'Inactive'},
                                                 {'label': 'Awaiting first login', 'value': 'pending'},
                                                 {'label': 'Can manage accounts', 'value': 'managers'}]),
                             className="fit"),
                ], className="a-toolbar a-card-head"),
                html.Div(id='acc-table', className="a-table-wrap"),
            ], className="a-card"),
        ], className="admin-container"),
        add_modal,
        manage_modal,
    ], className="admin-shell")


# ---------------------------------------------------------------------
# What can the signed-in user do here?
# ---------------------------------------------------------------------
@callback(
    Output('acc-me', 'data'),
    Output('acc-add-open', 'style'),
    Output('acc-add-perms', 'style'),
    Output('acc-perm-banner', 'children'),
    Input('session-admin-email', 'data'),
    Input('acc-refresh', 'data'),
)
def load_me(session_email, _):
    me = _me(session_email)
    if not me:
        return {}, HIDE, HIDE, ui.alert("Sign in again to manage accounts.", 'warn')
    data = {'id': me['id'], 'manage': bool(me.get('can_manage_accounts')), 'grant': bool(me.get('can_grant_access'))}
    banner = None
    if not data['manage'] and not data['grant']:
        banner = html.Div([html.B("View only. "), "Ask an admin who can manage accounts if someone needs to be added, "
                           "changed or removed."], className="a-alert a-alert-info mb-3")
    return data, ({} if data['manage'] else HIDE), ({} if data['grant'] else HIDE), banner


# ---------------------------------------------------------------------
# Table + stats
# ---------------------------------------------------------------------
@callback(
    Output('acc-table', 'children'),
    Output('acc-stats', 'children'),
    Input('acc-refresh', 'data'),
    Input('acc-search', 'value'),
    Input('acc-f-role', 'value'),
    Input('acc-f-status', 'value'),
    Input('acc-me', 'data'),
)
def render_accounts(_, search, role, status, me):
    me = me or {}
    accounts = get_all_accounts()

    def stat(k, v, s=None, cls=''):
        return html.Div([html.Div(k, className="k"), html.Div(v, className="v"),
                         html.Div(s, className="s") if s else None], className=f"stat {cls}")
    active = sum(1 for a in accounts if (a.get('status') or 'Active') == 'Active')
    pending = sum(1 for a in accounts if a.get('must_change_password'))
    managers = sum(1 for a in accounts if a.get('can_manage_accounts'))
    stats = [stat("Total accounts", len(accounts)),
             stat("Active", active, "Can sign in"),
             stat("Inactive", len(accounts) - active, "Sign-in blocked", 'warn' if len(accounts) - active else ''),
             stat("Awaiting first login", pending, "Still on a temporary password", 'amber' if pending else ''),
             stat("Can manage accounts", managers, f"{sum(1 for a in accounts if a.get('can_grant_access'))} can grant access")]

    rows = accounts
    if search and search.strip():
        q = search.strip().lower()
        rows = [a for a in rows if q in (a.get('name') or '').lower() or q in (a.get('email') or '').lower()
                or q in (a.get('personal_email') or '').lower()]
    if role and role != 'all':
        rows = [a for a in rows if a.get('role') == role]
    if status == 'pending':
        rows = [a for a in rows if a.get('must_change_password')]
    elif status == 'managers':
        rows = [a for a in rows if a.get('can_manage_accounts') or a.get('can_grant_access')]
    elif status and status != 'all':
        rows = [a for a in rows if (a.get('status') or 'Active') == status]

    if not rows:
        return html.Div("No accounts match these filters.", className="inq-empty"), stats

    can_open = me.get('manage') or me.get('grant')
    body = []
    for a in rows:
        st = a.get('status') or 'Active'
        chips = [html.Span(st, className=f"chip chip-{st.lower()}")]
        if a.get('must_change_password'):
            chips.append(html.Span("Temp password", className="chip chip-pending ms-1", title="Hasn't set their own password yet"))
        powers = []
        if a.get('can_manage_accounts'):
            powers.append(html.Span("Manages accounts", className="chip plain chip-power"))
        if a.get('can_grant_access'):
            powers.append(html.Span("Grants access", className="chip plain chip-power ms-1"))
        is_me = a['id'] == me.get('id')
        body.append(html.Tr([
            html.Td(html.Div([ui.avatar(a.get('name')),
                              html.Div([html.B([a.get('name'), html.Span("  (you)", className="you text-muted") if is_me else None]),
                                        html.Span(a.get('email'))], className="who")], className="person")),
            html.Td(a.get('contact_number') or '—', className="muted nowrap"),
            html.Td(a.get('role') or '—', className="nowrap"),
            html.Td(chips, className="nowrap"),
            html.Td(powers or html.Span("View only", className="text-muted"), className="nowrap"),
            html.Td(ui.time_ago(a.get('last_login')) if a.get('last_login') else 'Never', className="muted nowrap"),
            html.Td(html.Button("Manage", id={'type': 'acc-manage-open', 'index': a['id']}, n_clicks=0,
                                className="a-btn a-btn-outline a-btn-sm") if can_open else None, className="num"),
        ]))
    table = html.Table([
        html.Thead(html.Tr([html.Th("Name"), html.Th("Contact"), html.Th("Role"), html.Th("Status"),
                            html.Th("Account powers"), html.Th("Last login"), html.Th("", className="num")])),
        html.Tbody(body),
    ], className="a-table")
    return table, stats


# ---------------------------------------------------------------------
# Invite (add) an account
# ---------------------------------------------------------------------
@callback(
    Output('acc-add-modal', 'is_open'),
    Output('acc-add-form', 'style'),
    Output('acc-add-done-view', 'style'),
    Output('acc-add-feedback', 'children'),
    Output('acc-name', 'value'),
    Output('acc-email', 'value'),
    Output('acc-contact', 'value'),
    Output('acc-add-manage', 'value'),
    Output('acc-add-grant', 'value'),
    Input('acc-add-open', 'n_clicks'),
    Input('acc-add-cancel', 'n_clicks'),
    Input('acc-add-x', 'n_clicks'),
    Input('acc-add-done', 'n_clicks'),
    State('acc-me', 'data'),
    prevent_initial_call=True,
)
def toggle_add_modal(_o, _c, _x, _d, me):
    opening = ctx.triggered_id == 'acc-add-open' and (me or {}).get('manage')
    return bool(opening), {}, HIDE, None, '', '', '', False, False


@callback(
    Output('acc-add-feedback', 'children', allow_duplicate=True),
    Output('acc-add-form', 'style', allow_duplicate=True),
    Output('acc-add-done-view', 'style', allow_duplicate=True),
    Output('acc-add-result', 'children'),
    Output('acc-refresh', 'data', allow_duplicate=True),
    Input('acc-add-save', 'n_clicks'),
    State('acc-name', 'value'),
    State('acc-email', 'value'),
    State('acc-contact', 'value'),
    State('acc-role', 'value'),
    State('acc-status', 'value'),
    State('acc-add-manage', 'value'),
    State('acc-add-grant', 'value'),
    State('acc-refresh', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def create_new_account(n, name, email, contact, role, status, can_manage, can_grant, refresh, session_email):
    if not n:
        raise dash.exceptions.PreventUpdate
    nope = (no_update,) * 4
    me = _me(session_email)
    if not me or not me.get('can_manage_accounts'):
        return (ui.alert("You don't have permission to add accounts.", 'err'),) + nope

    name, email = (name or '').strip(), (email or '').strip().lower()
    problems = []
    if not name:
        problems.append("enter the full name")
    if not EMAIL_RE.match(email):
        problems.append("enter a valid email address")
    elif allura_email_exists(email):
        problems.append(f"{email} already has an account")
    if problems:
        return (ui.alert("Please " + "; ".join(problems) + ".", 'warn'),) + nope

    # Only someone who can grant access may hand out account powers
    give_manage = bool(can_manage) and bool(me.get('can_grant_access'))
    give_grant = bool(can_grant) and bool(me.get('can_grant_access'))

    temp_pw = generate_temp_password()
    new_id = create_account(name, email, email, (contact or '').strip() or None, role, status or 'Active',
                            hash_password(temp_pw), give_manage, give_grant)
    if not new_id:
        return (ui.alert("The account couldn't be saved. Check the database connection and try again.", 'err'),) + nope

    sent, info = send_admin_invite(email, name, temp_pw, role, invited_by=me.get('name'))
    if sent:
        result = html.Div([
            html.H4("Invite sent"),
            html.P(["An invite for ", html.B(name), " was emailed to ", html.B(email), "."], className="modal-sub"),
            html.Div([html.Div(["They sign in with: ", html.Code(email)]),
                      html.Div("The email contains their temporary password. They'll choose their own the first time "
                               "they sign in.", className="mt-2 text-muted")], className="cred-box"),
        ])
    else:
        result = html.Div([
            html.H4("Account created, but the invite wasn't sent"),
            html.P(info, className="modal-sub"),
            html.Div([html.Div(["Email: ", html.Code(email)]),
                      html.Div(["Temporary password: ", html.Code(temp_pw)], className="mt-2"),
                      html.Div("Share these with them securely. This password is shown only once.",
                               className="mt-2 text-muted")], className="cred-box"),
        ])
    return None, HIDE, {}, result, (refresh or 0) + 1


# ---------------------------------------------------------------------
# Manage an account
# ---------------------------------------------------------------------
@callback(
    Output('acc-manage-modal', 'is_open'),
    Output('acc-manage-id', 'data'),
    Output('acc-manage-head', 'children'),
    Output('acc-m-role', 'value'),
    Output('acc-m-status', 'value'),
    Output('acc-m-personal-email', 'value'),
    Output('acc-m-contact', 'value'),
    Output('acc-m-manage', 'value'),
    Output('acc-m-grant', 'value'),
    Output('acc-m-pw-info', 'children'),
    Output('acc-manage-feedback', 'children'),
    # what this admin is allowed to change
    Output('acc-m-role', 'disabled'),
    Output('acc-m-status', 'disabled'),
    Output('acc-m-personal-email', 'disabled'),
    Output('acc-m-contact', 'disabled'),
    Output('acc-m-manage', 'disabled'),
    Output('acc-m-grant', 'disabled'),
    Output('acc-m-manage-tools', 'style'),
    Output('acc-m-perm-note', 'children'),
    Input({'type': 'acc-manage-open', 'index': ALL}, 'n_clicks'),
    Input('acc-manage-x', 'n_clicks'),
    Input('acc-manage-cancel', 'n_clicks'),
    State('acc-me', 'data'),
    prevent_initial_call=True,
)
def open_manage(_o, _x, _c, me):
    me = me or {}
    t = ctx.triggered_id
    if isinstance(t, dict):
        if not (ctx.triggered and ctx.triggered[0].get('value')):
            raise dash.exceptions.PreventUpdate
        a = get_account_by_id(t['index'])
        if not a or not (me.get('manage') or me.get('grant')):
            raise dash.exceptions.PreventUpdate
        head = html.Div([ui.avatar(a['name']),
                         html.Div([html.B(a['name'], style={'fontSize': '1.05rem'}), html.Span(a['email'])], className="who")],
                        className="person")
        if a.get('must_change_password'):
            pw = "Using a temporary password (hasn't signed in and changed it yet)."
        elif a.get('password_changed_at'):
            pw = f"Password last changed {ui.time_ago(a['password_changed_at'])}."
        elif a.get('password_hash'):
            pw = "Password set."
        else:
            pw = "No password yet: this account can't sign in until you reset it."
        no_manage = not me.get('manage')
        no_grant = not me.get('grant')
        note = ("Only an admin who can grant access can change these." if no_grant
                else "There must always be at least one active account that can grant access.")
        return (True, a['id'], head, a.get('role') or ACCOUNT_ROLES[0], a.get('status') or 'Active',
                a.get('personal_email') or '', a.get('contact_number') or '',
                bool(a.get('can_manage_accounts')), bool(a.get('can_grant_access')), pw, None,
                no_manage, no_manage, no_manage, no_manage, no_grant, no_grant,
                HIDE if no_manage else {}, note)
    return (False,) + (no_update,) * 9 + (None,) + (no_update,) * 8


@callback(
    Output('acc-manage-modal', 'is_open', allow_duplicate=True),
    Output('acc-manage-feedback', 'children', allow_duplicate=True),
    Output('acc-refresh', 'data', allow_duplicate=True),
    Output('acc-toast', 'children'),
    Output('acc-toast', 'is_open'),
    Input('acc-manage-save', 'n_clicks'),
    State('acc-manage-id', 'data'),
    State('acc-m-role', 'value'),
    State('acc-m-status', 'value'),
    State('acc-m-personal-email', 'value'),
    State('acc-m-contact', 'value'),
    State('acc-m-manage', 'value'),
    State('acc-m-grant', 'value'),
    State('acc-refresh', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def save_manage(n, account_id, role, status, personal_email, contact, can_manage, can_grant, refresh, session_email):
    if not n or not account_id:
        raise dash.exceptions.PreventUpdate

    def stop(msg, kind='warn'):
        return no_update, ui.alert(msg, kind), no_update, no_update, no_update

    me = _me(session_email)
    a = get_account_by_id(account_id)
    if not me or not a:
        return stop("Sign in again to continue.", 'err')
    may_manage, may_grant = bool(me.get('can_manage_accounts')), bool(me.get('can_grant_access'))
    if not (may_manage or may_grant):
        return stop("You don't have permission to change accounts.", 'err')
    is_self = a['id'] == me['id']

    changes = []
    if may_manage:
        if is_self and status != 'Active':
            return stop("You can't deactivate your own account.")
        if personal_email and not EMAIL_RE.match(personal_email.strip()):
            return stop("That backup email doesn't look right.")
        if a.get('can_grant_access') and status != 'Active' and count_access_granters(exclude_id=a['id']) == 0:
            return stop("This is the only active account that can grant access, so it can't be deactivated.")
        update_account_admin_fields(account_id, role, status, (personal_email or '').strip() or None,
                                    (contact or '').strip() or None)
        changes.append("details")

    if may_grant:
        new_manage, new_grant = bool(can_manage), bool(can_grant)
        if (new_manage, new_grant) != (bool(a.get('can_manage_accounts')), bool(a.get('can_grant_access'))):
            if a.get('can_grant_access') and not new_grant and count_access_granters(exclude_id=a['id']) == 0:
                return stop("At least one active account must be able to grant access. Give this power to someone "
                            "else first, then remove it here.")
            set_account_permissions(account_id, new_manage, new_grant)
            changes.append("account powers")

    if not changes:
        return False, None, no_update, no_update, no_update
    return False, None, (refresh or 0) + 1, f"Saved {' and '.join(changes)} for {a['name']}.", True


@callback(
    Output('acc-manage-feedback', 'children', allow_duplicate=True),
    Output('acc-refresh', 'data', allow_duplicate=True),
    Input('acc-m-reset', 'submit_n_clicks'),
    State('acc-manage-id', 'data'),
    State('acc-refresh', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def reset_password(n, account_id, refresh, session_email):
    if not n or not account_id:
        raise dash.exceptions.PreventUpdate
    me = _me(session_email)
    if not me or not me.get('can_manage_accounts'):
        return ui.alert("You don't have permission to reset passwords.", 'err'), no_update
    a = get_account_by_id(account_id)
    if not a:
        raise dash.exceptions.PreventUpdate
    temp_pw = generate_temp_password()
    set_account_password(account_id, hash_password(temp_pw), must_change=True)
    to = a.get('personal_email') or a['email']
    sent, info = send_account_credentials(to, a['name'], a['email'], temp_pw, a.get('role'), is_reset=True)
    if sent:
        return ui.alert(f"Password reset. A temporary password was emailed to {to}.", 'ok'), (refresh or 0) + 1
    return ui.alert([f"Password reset, but the email failed ({info}). Temporary password: ",
                     html.Code(temp_pw), " (shown once)."], 'err'), (refresh or 0) + 1


@callback(
    Output('acc-manage-modal', 'is_open', allow_duplicate=True),
    Output('acc-manage-feedback', 'children', allow_duplicate=True),
    Output('acc-refresh', 'data', allow_duplicate=True),
    Output('acc-toast', 'children', allow_duplicate=True),
    Output('acc-toast', 'is_open', allow_duplicate=True),
    Input('acc-m-delete', 'submit_n_clicks'),
    State('acc-manage-id', 'data'),
    State('acc-refresh', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def remove_account(n, account_id, refresh, session_email):
    if not n or not account_id:
        raise dash.exceptions.PreventUpdate
    keep = (no_update, no_update, no_update)
    me = _me(session_email)
    a = get_account_by_id(account_id)
    if not me or not me.get('can_manage_accounts'):
        return (no_update, ui.alert("You don't have permission to delete accounts.", 'err')) + keep
    if not a:
        raise dash.exceptions.PreventUpdate
    if a['id'] == me['id']:
        return (no_update, ui.alert("You can't delete your own account.", 'warn')) + keep
    if a.get('can_grant_access') and count_access_granters(exclude_id=a['id']) == 0:
        return (no_update, ui.alert("This is the only account that can grant access, so it can't be deleted.", 'warn')) + keep
    if not delete_account(account_id):
        return (no_update, ui.alert("The account couldn't be deleted. Check the database connection.", 'err')) + keep
    return False, None, (refresh or 0) + 1, f"Deleted the account for {a['name']}.", True
