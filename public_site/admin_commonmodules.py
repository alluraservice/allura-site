"""Admin navbar: logo on the far left, section links in the middle, My Account + Logout on the far right
(same arrangement as the public navbar in commonmodules.py)."""
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from app import app

ADMIN_LINKS = [('Home', '/admin/dashboard'), ('Inquiries', '/admin/inquiries'), ('Items', '/admin/items'),
               ('Accounts', '/admin/accounts'), ('Reports & Analytics', '/admin/analytics')]

# --- ADMIN NAVBAR COMPONENT ---
admin_navbar = [
    # Session stores live in app.layout (index.py)

    # 1. MAIN STICKY ADMIN NAVIGATION BAR
    html.Header(
        dbc.Navbar(
            dbc.Container(
                [
                    # Left end: logo
                    html.A(
                        html.Img(src=app.get_asset_url('logos/alluralogo1.png'), height='45px', alt='Allura Enterprise Admin'),
                        href='/admin/dashboard',
                        className='navbar-brand d-flex align-items-center me-0 gap-3'
                    ),

                    # Middle: sections (Menu button on small screens, see the right end)
                    html.Div(
                        [dbc.NavLink(label, href=href, className='btn-nav') for label, href in ADMIN_LINKS],
                        className='nav-container d-none d-md-flex align-items-center justify-content-center gap-3'
                    ),

                    # Right end: My Account (icon button, brand green) + Logout
                    html.Div(
                        [
                            dbc.DropdownMenu(
                                [dbc.DropdownMenuItem(label, href=href) for label, href in ADMIN_LINKS],
                                label="Menu", align_end=True, className='nav-menu d-md-none', toggleClassName='btn-nav',
                            ),
                            dcc.Link(
                                html.Img(src=app.get_asset_url('icons/accounts.svg'), alt='My Account'),
                                href='/admin/my-account', title='My Account', className='btn-nav-icon'
                            ),
                            dbc.Button("Logout", id='btn-open-logout-modal',
                                       className='btn btn-green rounded-pill fw-semibold text-white'),
                        ],
                        className='nav-actions'
                    )
                ],
                fluid=True,
                className='d-flex align-items-center justify-content-between w-100 px-4 gap-3'
            ),
            color='white',
            className='main-nav-bar shadow-sm py-2'
        ),
        style={'position': 'sticky', 'top': '0', 'zIndex': '1030', 'backgroundColor': 'white'}
    ),

    # 2. CONFIRM LOGOUT POP-UP MODAL
    dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Confirm Logout", className="fw-bold px-2", style={'color': 'var(--dark-green)'}),
                close_button=True, id='btn-close-logout-modal', className="border-0 pb-0"
            ),
            dbc.ModalBody(
                html.Div([
                    html.P("Are you sure you want to logout?", className="text-muted mb-4 px-2 fs-6"),
                    html.Div([
                        dbc.Button("YES", id='btn-logout-yes',
                                   className="btn btn-green rounded-pill fw-semibold px-5 py-2 text-white shadow-sm me-3"),
                        dbc.Button("NO", id='btn-logout-no',
                                   className="btn btn-green rounded-pill fw-semibold px-5 py-2 text-white shadow-sm"),
                    ], className="d-flex justify-content-center align-items-center gap-3 mt-2 mb-2"),
                ], className="px-3 py-3 text-center")
            ),
        ],
        id='logout-confirm-modal', is_open=False, centered=True, backdrop=True, className="a-modal"
    ),

    # Location component to handle redirection upon logout
    dcc.Location(id='admin-logout-redirect', refresh=True)
]


# ==========================================
# CALLBACK: LOGOUT MODAL TOGGLE & REDIRECT
# (YES also clears the session so the admin pages can't be reopened with Back)
# ==========================================
@callback(
    [
        Output('logout-confirm-modal', 'is_open'),
        Output('admin-logout-redirect', 'href'),
        Output('session-admin-name', 'data', allow_duplicate=True),
        Output('session-admin-email', 'data', allow_duplicate=True),
    ],
    [
        Input('btn-open-logout-modal', 'n_clicks'),
        Input('btn-close-logout-modal', 'n_clicks'),
        Input('btn-logout-no', 'n_clicks'),
        Input('btn-logout-yes', 'n_clicks')
    ],
    [State('logout-confirm-modal', 'is_open')],
    prevent_initial_call=True
)
def handle_logout_modal(open_clicks, close_clicks, no_clicks, yes_clicks, is_open):
    ctx = dash.callback_context
    keep = (dash.no_update, dash.no_update, dash.no_update)
    if not ctx.triggered:
        return (is_open,) + keep

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'btn-open-logout-modal' and (open_clicks or 0) > 0:
        return (True,) + keep
    if trigger_id in ['btn-close-logout-modal', 'btn-logout-no']:
        return (False,) + keep
    if trigger_id == 'btn-logout-yes':
        return False, '/home', None, None
    return (is_open,) + keep
