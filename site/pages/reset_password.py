"""
/reset-password?token=…  — opened from the "Forgot password?" email.
Checks the one-time token, lets the person choose a new password (same rules as My Account),
then marks the link used and emails a "password changed" notice.
"""
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update

import site_ui as ui
from database.db_handler import get_valid_password_reset, mark_password_reset_used, set_account_password
from utils.mailer import send_password_changed_notice
from utils.security import hash_password, hash_reset_token, password_rules, password_strength

METER_COLORS = ['#b42318', '#b42318', '#c99700', '#5a9a2f', '#006400']


def _token(search):
    return (parse_qs((search or '').lstrip('?')).get('token') or [''])[0]


def layout(*args, **kwargs):
    form = html.Div([
        html.Div(id='rp-who', className="mb-3"),
        dcc.Input(id='rp-username', type='email', autoComplete='username', style={'display': 'none'}),
        html.Div([html.Label("New password", className="a-label"),
                  dbc.Input(id='rp-new', type='password', className="input-box", autoComplete='new-password')], className="mb-3"),
        html.Div([html.Label("Confirm new password", className="a-label"),
                  dbc.Input(id='rp-confirm', type='password', className="input-box", autoComplete='new-password')]),
        html.Div([
            html.Div(html.Div(id='rp-meter-bar', style={'width': '0%'}), className="pw-meter", style={'flex': 1}),
            html.Span(id='rp-meter-label', style={'fontSize': '.78rem', 'minWidth': '70px', 'textAlign': 'right'}),
        ], className="d-flex align-items-center gap-2 mt-2"),
        html.Ul(id='rp-rules', className="pw-rules"),
        html.Div(id='rp-feedback', className="mt-3"),
        html.Div(html.Button("Set new password", id='rp-save', n_clicks=0, disabled=True, className="a-btn a-btn-primary a-btn-lg"),
                 className="d-flex justify-content-end mt-3"),
    ], id='rp-form', style={'display': 'none'})

    invalid = html.Div([
        html.H5("This link has expired or was already used"),
        html.P("Reset links work once and expire after an hour. Request a new one from the Login pop-up "
               "(“Forgot password?”).", className="text-muted"),
        dcc.Link("Go to login", href='/home?login=1', refresh=True, className="a-btn a-btn-primary"),
    ], id='rp-invalid', className="text-center", style={'display': 'none'})

    return html.Div([
        ui.page_header("Reset your password", "Choose a new password for your Allura admin account.",
                       crumbs=[("Home", "/home"), ("Reset password", None)]),
        html.Div(html.Div(html.Div([form, invalid], className="a-card-body", style={'padding': '24px 26px'}),
                          className="a-card reset-card"), className="site-container"),
    ], className="site-shell")


@callback(
    Output('rp-form', 'style'),
    Output('rp-invalid', 'style'),
    Output('rp-who', 'children'),
    Output('rp-username', 'value'),
    Input('url', 'search'),
)
def check_link(search):
    reset = get_valid_password_reset(hash_reset_token(_token(search))) if _token(search) else None
    if not reset:
        return {'display': 'none'}, {}, None, None
    return {}, {'display': 'none'}, html.Div(["Account: ", html.B(reset['email'])], className="text-muted"), reset['email']


@callback(
    Output('rp-meter-bar', 'style'),
    Output('rp-meter-label', 'children'),
    Output('rp-rules', 'children'),
    Output('rp-save', 'disabled'),
    Input('rp-new', 'value'),
    Input('rp-confirm', 'value'),
)
def live_checks(new, confirm):
    rules = password_rules(new)
    match = bool(new) and new == confirm
    items = [html.Li(label, className="ok" if ok else "") for label, ok in rules]
    items.append(html.Li("Both passwords match", className="ok" if match else ""))
    score, label = password_strength(new)
    bar = {'width': f"{(score + 1) * 20 if new else 0}%", 'background': METER_COLORS[score]}
    return bar, html.Span(label, style={'color': METER_COLORS[score], 'fontWeight': 700}), items, \
        not (all(ok for _, ok in rules) and match)


@callback(
    Output('rp-feedback', 'children'),
    Output('rp-save', 'disabled', allow_duplicate=True),
    Output('rp-new', 'value'),
    Output('rp-confirm', 'value'),
    Input('rp-save', 'n_clicks'),
    State('rp-new', 'value'),
    State('rp-confirm', 'value'),
    State('url', 'search'),
    prevent_initial_call=True,
)
def save_new_password(n, new, confirm, search):
    if not n:
        raise dash.exceptions.PreventUpdate
    reset = get_valid_password_reset(hash_reset_token(_token(search)))
    if not reset:
        return ui_alert("This link has expired or was already used. Request a new one from the Login pop-up.", 'err'), \
            True, no_update, no_update
    if not all(ok for _, ok in password_rules(new)) or new != confirm:
        return ui_alert("Please meet all the password requirements.", 'warn'), no_update, no_update, no_update

    set_account_password(reset['account_id'], hash_password(new), must_change=False)
    mark_password_reset_used(reset['id'])
    notify = reset.get('personal_email') or reset.get('email')
    if notify:
        send_password_changed_notice(notify, reset.get('name'))
    return html.Div([html.B("Your password was changed. "), "You can now sign in with it. ",
                     dcc.Link("Go to login", href='/home?login=1', refresh=True)],
                    className="a-alert a-alert-ok"), True, '', ''


def ui_alert(message, kind):
    return html.Div(message, className=f"a-alert a-alert-{kind}")
