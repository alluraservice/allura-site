"""
Admin sign-in page: alluraenterpriseph.com/admin/login (also /login).

A page of its own (not only the Login pop-up on Home) so admins can bookmark it and the browser can
save the password for it. Opening any admin page while signed out also comes here, and after signing in
the admin goes back to the page they asked for.

(The module is called sign_in, not admin_login: modules named pages.admin* are treated as admin-only
by utils/auth.py, and this page must work before anyone is signed in.)
"""
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

from app import app
from commonmodules import attempt_sign_in, recovery_message


def layout(search=None):
    nxt = (parse_qs((search or '').lstrip('?')).get('next') or [''])[0]
    return html.Div([
        dcc.Store(id='signin-next', data=nxt),
        dcc.Location(id='signin-redirect', refresh=True),
        html.Div([
            html.A(html.Img(src=app.get_asset_url('logos/alluralogo1.png'), alt='Allura Enterprise',
                            className="signin-logo"), href='/home'),

            # ---- Sign in ----
            html.Div([
                html.H1("Admin sign-in", className="signin-title"),
                html.P("For Allura staff who manage inquiries, products and website content. Tip: bookmark this "
                       "page and let your browser save your password to sign in faster next time.",
                       className="signin-lead"),
                html.Form([
                    html.Label("Email", htmlFor='signin-email', className="a-label"),
                    dbc.Input(id='signin-email', type='email', name='username', autoComplete='username',
                              placeholder="name@alluraenterpriseph.com", className="input-box mb-3", autoFocus=True),
                    html.Label("Password", htmlFor='signin-password', className="a-label"),
                    dbc.Input(id='signin-password', type='password', name='password', autoComplete='current-password',
                              placeholder="Your password", className="input-box", n_submit=0),
                    html.Div(html.Button("Forgot password?", id='signin-show-forgot', n_clicks=0, type='button',
                                         className="a-link small"), className="text-end mt-2 mb-3"),
                    html.Div(id='signin-feedback'),
                    html.Button("Sign in", id='signin-submit', n_clicks=0, type='button',
                                className="a-btn a-btn-primary a-btn-lg w-100 mt-2"),
                ], id='signin-form', autoComplete='on', className="signin-form",
                    # the browser offers to save the password only for a real form; Dash handles the submit
                    action='javascript:void(0)'),
            ], id='signin-view'),

            # ---- Forgot password ----
            html.Div([
                html.H1("Forgot password", className="signin-title"),
                html.P("Enter the email address of your admin account. We'll send a link so you can choose a new "
                       "password.", className="signin-lead"),
                html.Label("Email", htmlFor='signin-forgot-email', className="a-label"),
                dbc.Input(id='signin-forgot-email', type='email', placeholder="name@example.com",
                          className="input-box mb-3", n_submit=0),
                html.Div(id='signin-forgot-feedback'),
                html.Button("Send recovery email", id='signin-send-recovery', n_clicks=0, type='button',
                            className="a-btn a-btn-primary a-btn-lg w-100 mt-2"),
                html.Div(html.Button("← Back to sign-in", id='signin-show-login', n_clicks=0, type='button',
                                     className="a-link small"), className="text-center mt-3"),
            ], id='signin-forgot-view', style={'display': 'none'}),

            html.Div(dcc.Link("← Back to the Allura website", href='/home'), className="signin-back"),
        ], className="signin-card"),
    ], className="signin-page")


@callback(
    Output('signin-view', 'style'),
    Output('signin-forgot-view', 'style'),
    Input('signin-show-forgot', 'n_clicks'),
    Input('signin-show-login', 'n_clicks'),
    prevent_initial_call=True,
)
def switch_view(_forgot, _login):
    if ctx.triggered_id == 'signin-show-forgot':
        return {'display': 'none'}, {}
    return {}, {'display': 'none'}


@callback(
    Output('signin-redirect', 'href'),
    Output('session-admin-name', 'data', allow_duplicate=True),
    Output('session-admin-email', 'data', allow_duplicate=True),
    Output('signin-feedback', 'children'),
    Input('signin-submit', 'n_clicks'),
    Input('signin-password', 'n_submit'),
    State('signin-email', 'value'),
    State('signin-password', 'value'),
    State('signin-next', 'data'),
    running=[(Output('signin-submit', 'disabled'), True, False),
             (Output('signin-submit', 'children'), "Signing in…", "Sign in")],
    prevent_initial_call=True,
)
def sign_in_page(_clicks, _enter, email, password, nxt):
    if not ctx.triggered or not ctx.triggered[0].get('value'):
        raise dash.exceptions.PreventUpdate
    ok, result = attempt_sign_in(email, password, next_path=nxt)
    if not ok:
        return no_update, no_update, no_update, result
    return result['target'], result['first_name'], result['email'], None


@callback(
    Output('signin-forgot-feedback', 'children'),
    Input('signin-send-recovery', 'n_clicks'),
    Input('signin-forgot-email', 'n_submit'),
    State('signin-forgot-email', 'value'),
    prevent_initial_call=True,
)
def send_recovery_page(_clicks, _enter, email):
    if not ctx.triggered or not ctx.triggered[0].get('value'):
        raise dash.exceptions.PreventUpdate
    return recovery_message(email)
