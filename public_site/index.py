import sys
import os
import webbrowser

# Fix sys.path before importing local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# Explicitly import BOTH app and server from app.py
from app import app, server

# Add the columns/tables the admin pages need (safe to run every start)
from database.admin_schema import ensure_admin_schema
ensure_admin_schema()

# Serve uploaded item photos at /media/<id> (stored in the database, see utils/media.py)
from utils.media import register_media_routes
register_media_routes(server)

# Importing commonmodules and pages
import commonmodules as cm
import admin_commonmodules as admin_cm
import allubot
from pages import home
from pages import about_us
from pages import contact_us
from pages import reset_password
from pages.products import products
from pages.products import product_list
from pages.products import product_details
from pages.services import services
from pages.services import service_list
from pages.services import service_details
from pages.admin import dashboard
from pages.admin import analytics
from pages.admin import inquiries
from pages.admin.items import items
from pages.admin.items import item_details
from pages.admin.items import add_item
from pages.admin import accounts
from pages.admin import my_account

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        # Signed-in admin session (kept here, not in the navbars, so it always exists before any page reads it)
        dcc.Store(id='session-admin-name', storage_type='session'),
        dcc.Store(id='session-admin-email', storage_type='session'),
        html.Div(id='navbar-container'),
        html.Div(id='page_content'),
        # Footer: public pages only (index.update_navbar fills it)
        html.Div(id='footer-container'),
        # Floating AlluBot chat (public pages only; hidden on admin pages by 70_allubot.css)
        allubot.widget(),
    ]
)


def _render(module, *args):
    lay = getattr(module, 'layout', None)
    return lay(*args) if callable(lay) else lay


def _signed_out():
    """Admin pages need a signed-in account: send visitors to Home and open the Login pop-up."""
    return html.Div([
        dcc.Location(id='admin-guard-redirect', href='/home?login=1', refresh=True),
        html.Div("Please sign in to continue…", className="site-container text-center text-muted"),
    ])


@app.callback(
    [Output('page_content', 'children')],
    [Input('url', 'pathname')],
    [State('session-admin-email', 'data')]
)
def displaypage(pathname, session_email):
    ctx = dash.callback_context
    if not ctx.triggered or not pathname:
        raise PreventUpdate

    if pathname.startswith('/admin') and not session_email:
        return [_signed_out()]

    if pathname in ('/', '/home'):
        returnlayout = _render(home)
    elif pathname in ('/about_us', '/about-us'):
        returnlayout = _render(about_us)
    elif pathname == '/contact_us':
        returnlayout = _render(contact_us)
    elif pathname == '/reset-password':
        returnlayout = _render(reset_password)

    elif pathname == '/products':
        returnlayout = _render(products)
    elif pathname in ['/product-details', '/products/details', '/products/detail']:
        returnlayout = _render(product_details)
    elif pathname.startswith('/products/'):
        parts = pathname.strip('/').split('/')
        returnlayout = product_list.layout(parts[1] if len(parts) > 1 else None)

    elif pathname == '/services':
        returnlayout = _render(services)
    elif pathname in ['/service-details', '/services/details', '/services/detail']:
        returnlayout = _render(service_details)
    elif pathname.startswith('/services/'):
        parts = pathname.strip('/').split('/')
        returnlayout = service_list.layout(parts[1] if len(parts) > 1 else None)

    # Admin Routes
    elif pathname in ['/admin/dashboard', '/admin', '/dashboard']:
        returnlayout = _render(dashboard)
    elif pathname == '/admin/analytics':
        returnlayout = _render(analytics)
    elif pathname == '/admin/inquiries':
        returnlayout = _render(inquiries)
    elif pathname == '/admin/items':
        returnlayout = _render(items)
    elif pathname == '/admin/accounts':
        returnlayout = _render(accounts)
    elif pathname in ['/admin/my-account', '/admin/my_account']:
        returnlayout = _render(my_account)
    elif pathname == '/admin/items/add':
        returnlayout = _render(add_item)
    elif pathname in ['/admin/item-details', '/admin/items/details']:
        returnlayout = _render(item_details)
    else:
        returnlayout = 'error404'

    return [returnlayout]


@app.callback(
    Output('navbar-container', 'children'),
    Output('footer-container', 'children'),
    Input('url', 'pathname')
)
def update_navbar(pathname):
    if pathname and pathname.startswith('/admin'):
        return admin_cm.admin_navbar, None          # no footer on the admin pages
    return cm.navbar, cm.get_footer()


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:8050/', new=0, autoraise=True)
    app.run(debug=False)
