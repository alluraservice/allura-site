"""Public navbar (with the Login / Forgot password pop-up) and the site footer."""
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

from app import app
from database.db_handler import authenticate, create_password_reset, find_account_for_recovery
from utils.mailer import send_password_reset_link, site_url
from utils.security import new_reset_token

RESET_MINUTES = 60
NAV_LINKS = [('Home', '/home'), ('About Us', '/about_us'), ('Products', '/products'),
             ('Services', '/services'), ('Contact Us', '/contact_us')]


def _label(text):
    return html.Label(text, className="a-label")


# --- NAVBAR COMPONENT ---
navbar = [
    # 1. TOP GREEN BAR (scrolls away normally)
    html.Div(
        dbc.Container(
            html.Div([
                html.Span([html.Img(src=app.get_asset_url('icons/office.svg'), className='top-bar-icon'),
                           "BGC, Taguig City, Philippines"], className='top-bar-item'),
                html.Span([html.Img(src=app.get_asset_url('icons/call.svg'), className='top-bar-icon'),
                           "+63 917 770 1820"], className='top-bar-item'),
                html.Span([html.Img(src=app.get_asset_url('icons/email.svg'), className='top-bar-icon'),
                           "info@alluraenterpriseph.com"], className='top-bar-item'),
            ], className='d-flex justify-content-end align-items-center w-100'),
            fluid=True, className='px-5'
        ),
        className='top-green-bar py-1'
    ),

    # 2. MAIN NAVIGATION BAR (sticky)
    html.Header(
        dbc.Navbar(
            dbc.Container([
                html.A(html.Img(src=app.get_asset_url('logos/alluralogo1.png'), height='45px', alt='Allura Enterprise'),
                       href='/home', className='navbar-brand d-flex align-items-center me-0 gap-3'),

                html.Div([dbc.NavLink(label, href=href, className='btn-nav') for label, href in NAV_LINKS], className='nav-container d-none d-md-flex align-items-center justify-content-center gap-3'),

                html.Div([
                    # Small screens: the same links in a Menu button
                    dbc.DropdownMenu(
                        [dbc.DropdownMenuItem(label, href=href) for label, href in NAV_LINKS],
                        label="Menu", nav=False, align_end=True, className='nav-menu d-md-none',
                        toggleClassName='btn-nav',
                    ),
                    html.A(html.Img(src=app.get_asset_url('icons/quote.svg'), alt='Login'),
                           href='#', id='btn-open-login-modal', title='Login', className='btn-nav-icon'),
                    html.A(html.Img(src=app.get_asset_url('icons/allubot1.svg'), alt='AlluBot'),
                           href='#', id='open_allubot_btn', title='AlluBot', className='btn-nav-icon'),
                ], className='nav-actions'),
            ], fluid=True, className='d-flex align-items-center justify-content-between w-100 px-4 gap-3'),
            color='white', className='main-nav-bar shadow-sm py-2'
        ),
        style={'position': 'sticky', 'top': '0', 'zIndex': '1030', 'backgroundColor': 'white'}
    ),

    # 3. LOGIN / FORGOT PASSWORD POP-UP
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Account Login", id='login-modal-title', className="fw-bold px-2",
                                       style={'color': 'var(--dark-green)'}),
                        close_button=True, id='btn-close-login-modal', className="border-0 pb-0"),
        dbc.ModalBody([
            # ---- Login view ----
            html.Div([
                html.Div([_label("Email"),
                          dbc.Input(type="email", placeholder="Enter your email here", id="login-email-input",
                                    className="input-box", autoComplete="username")], className="mb-3"),
                html.Div([_label("Password"),
                          dbc.Input(type="password", placeholder="Enter your password here", id="login-password-input",
                                    className="input-box", autoComplete="current-password", n_submit=0)], className="mb-3"),
                html.Div([
                    dbc.Checkbox(label="Remember me", id="login-remember-me", className="small text-muted"),
                    html.Button("Forgot password?", id="login-forgot-password", n_clicks=0, type="button", className="a-link small"),
                ], className="d-flex justify-content-between align-items-center mb-3 px-1"),
                html.Div(id='login-feedback'),
                html.Div(dbc.Button("LOGIN", id="btn-submit-login", n_clicks=0,
                                    className="btn btn-green rounded-pill fw-semibold px-5 py-2 text-white shadow-sm"),
                         className="d-flex justify-content-center mt-4"),
            ], id='login-view', className="px-3 py-2"),

            # ---- Forgot password view ----
            html.Div([
                html.P("Enter the email address of your admin account. We'll send a link to that address so you can "
                       "choose a new password.", className="text-muted small mb-3"),
                html.Div([_label("Email"),
                          dbc.Input(type="email", placeholder="name@example.com", id="forgot-email-input",
                                    className="input-box", n_submit=0)], className="mb-3"),
                html.Div(id='forgot-feedback'),
                html.Div([
                    html.Button("← Back to login", id="forgot-back", n_clicks=0, type="button", className="a-link small"),
                    dbc.Button("Send recovery email", id="btn-send-recovery", n_clicks=0,
                               className="btn btn-green rounded-pill fw-semibold px-4 py-2 text-white shadow-sm"),
                ], className="d-flex justify-content-between align-items-center mt-4"),
            ], id='forgot-view', className="px-3 py-2", style={'display': 'none'}),
        ]),
    ], id='login-modal', is_open=False, centered=True, backdrop=True, className="a-modal"),

    dcc.Location(id='login-redirect', refresh=True),
]


# ==========================================
# Open / close the pop-up and switch between Login and Forgot password
# ==========================================
@callback(
    Output('login-modal', 'is_open'),
    Output('login-view', 'style'),
    Output('forgot-view', 'style'),
    Output('login-modal-title', 'children'),
    Output('login-feedback', 'children'),
    Output('forgot-feedback', 'children'),
    Input('btn-open-login-modal', 'n_clicks'),
    Input('btn-close-login-modal', 'n_clicks'),
    Input('login-forgot-password', 'n_clicks'),
    Input('forgot-back', 'n_clicks'),
    prevent_initial_call=True,
)
def switch_login_views(_open, _close, _forgot, _back):
    if not ctx.triggered or not ctx.triggered[0].get('value'):
        raise dash.exceptions.PreventUpdate
    t = ctx.triggered_id
    show, hide = {}, {'display': 'none'}
    if t == 'btn-close-login-modal':
        return False, show, hide, "Account Login", None, None
    if t == 'login-forgot-password':
        return True, hide, show, "Forgot password", None, None
    return True, show, hide, "Account Login", None, None


# ==========================================
# Sign in (button or Enter in the password box)
# ==========================================
@callback(
    Output('login-modal', 'is_open', allow_duplicate=True),
    Output('login-redirect', 'href'),
    Output('session-admin-name', 'data'),
    Output('session-admin-email', 'data'),
    Output('login-feedback', 'children', allow_duplicate=True),
    Input('btn-submit-login', 'n_clicks'),
    Input('login-password-input', 'n_submit'),
    State('login-email-input', 'value'),
    State('login-password-input', 'value'),
    prevent_initial_call=True,
)
def sign_in(_clicks, _enter, email, password):
    if not ctx.triggered or not ctx.triggered[0].get('value'):
        raise dash.exceptions.PreventUpdate
    keep = (no_update, no_update, no_update, no_update)
    if not (email or '').strip() or not password:
        return keep + (html.Div("Please enter your email and password.", className="a-alert a-alert-warn"),)

    account, error = authenticate(email.strip(), password)
    if not account:
        return keep + (html.Div(error or "Incorrect email or password.", className="a-alert a-alert-err"),)

    first_name = (account.get('name') or email.split('@')[0]).split(' ')[0]
    # Store BOTH name and login email: every admin page (My Account, Inquiries, Accounts…) reads the email
    target = '/admin/my-account' if account.get('must_change_password') else '/admin/dashboard'
    return False, target, first_name, account['email'], None


# ==========================================
# Forgot password: email a one-time reset link
# ==========================================
@callback(
    Output('forgot-feedback', 'children', allow_duplicate=True),
    Input('btn-send-recovery', 'n_clicks'),
    Input('forgot-email-input', 'n_submit'),
    State('forgot-email-input', 'value'),
    prevent_initial_call=True,
)
def send_recovery(_clicks, _enter, email):
    if not ctx.triggered or not ctx.triggered[0].get('value'):
        raise dash.exceptions.PreventUpdate
    email = (email or '').strip()
    if '@' not in email or '.' not in email.split('@')[-1]:
        return html.Div("Please enter a valid email address.", className="a-alert a-alert-warn")

    account = find_account_for_recovery(email)
    if account:
        token, token_hash = new_reset_token()
        create_password_reset(account['id'], token_hash, email, RESET_MINUTES)
        link = f"{site_url()}/reset-password?token={token}"
        sent, info = send_password_reset_link(email, account.get('name'), link, RESET_MINUTES)
        if not sent:
            print(f"[recovery] {info}")
            return html.Div("We couldn't send the recovery email right now. Please try again later or contact your "
                            "administrator.", className="a-alert a-alert-err")
    # Same answer whether or not the email exists, so the form can't be used to discover accounts
    return html.Div([html.B("Check your inbox. "),
                     f"If {email} belongs to an admin account, a password reset link is on its way. "
                     f"The link works once and expires in {RESET_MINUTES} minutes."],
                    className="a-alert a-alert-ok")


# --- FOOTER COMPONENT ---
def get_footer():
    return html.Footer(
        html.Div([
            html.Div([
                html.Div([
                    html.Img(src=app.get_asset_url('logos/alluralogo1.png'), alt='Allura Enterprise Logo', className='footer-logo mb-3'),
                    html.P("Allura Enterprise is a premier Philippine medical equipment distributor and service provider, "
                           "delivering reliable radiology, imaging, and hospital infrastructure solutions nationwide.",
                           className='small text-muted pe-lg-4', style={'lineHeight': '1.6', 'maxWidth': '300px'}),
                ], className='col-lg-4 col-md-12 mb-4 mb-lg-0'),
                html.Div([
                    html.H6("Company", className="fw-bold mb-3"),
                    html.Ul([
                        html.Li(html.A("Home", href="/home")),
                        html.Li(html.A("About Us", href="/about_us")),
                        html.Li(html.A("Products", href="/products")),
                        html.Li(html.A("Services", href="/services")),
                        html.Li(html.A("Contact Us", href="/contact_us")),
                    ], className="footer-links-list small"),
                ], className='col-lg-3 col-md-6 mb-4 mb-lg-0'),
                html.Div([
                    html.H6("Get in Touch", className="fw-bold mb-3"),
                    html.Div([
                        html.Div([html.Img(src=app.get_asset_url('icons/call.svg'), className='me-2 footer-icon', style={'width': '16px'}),
                                  html.Span("+63 917 770 1820", className="small")], className="footer-contact-item"),
                        html.Div([html.Img(src=app.get_asset_url('icons/email.svg'), className='me-2 footer-icon', style={'width': '16px'}),
                                  html.A("info@alluraenterpriseph.com", href="mailto:info@alluraenterpriseph.com",
                                         className="small text-decoration-none text-reset")], className="footer-contact-item"),
                        html.Div([html.Img(src=app.get_asset_url('icons/office.svg'), className='me-2 footer-icon', style={'width': '16px'}),
                                  html.Span("BGC, Taguig City, Philippines", className="small")], className="footer-contact-item"),
                    ]),
                ], className='col-lg-4 col-md-6'),
            ], className='row justify-content-between'),
            html.Div(html.P("© 2026 Allura Enterprise. All Rights Reserved.", className="text-center small mb-0 opacity-75"),
                     className="footer-bottom"),
        ], className="container"),
        className="site-footer"
    )
