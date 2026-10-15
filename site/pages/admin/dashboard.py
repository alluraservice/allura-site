"""
Admin home. Same admin branding as the other pages, keeping the dashboard's neutral grey header.
Shows what needs attention (unread / urgent / unassigned inquiries), quick links to every section,
and the latest inquiries (each opens straight into the inbox).
Signed-out visitors are sent back to /home, as before.
"""
from datetime import datetime

import dash
from dash import Input, Output, State, callback, dcc, html

import admin_ui as ui
from app import app
from database.db_handler import (get_account_by_email, get_all_accounts, get_inquiry_folder_counts,
                                 get_item_counts, search_inquiries)

dash.register_page(__name__, path='/admin/dashboard')

layout = html.Div([
    # Location component to handle forced redirects if unauthorized
    dcc.Location(id='admin-auth-redirect', refresh=True),
    # Dynamic container that will hold the protected page content
    html.Div(id='admin-page-protected-content'),
])


def _greeting():
    h = datetime.now().hour
    return "Good morning" if h < 12 else ("Good afternoon" if h < 18 else "Good evening")


def _stat(href, k, v, s=None, cls=''):
    return dcc.Link(html.Div([html.Div(k, className="k"), html.Div(v, className="v"),
                              html.Div(s, className="s") if s else None], className=f"stat {cls}"),
                    href=href, className="stat-link")


def _quick(href, icon, title, sub, bg):
    return dcc.Link(html.Div([
        html.Img(src=app.get_asset_url(icon), className='admin-card-icon'),
        html.H5(title, className='admin-card-title'),
        html.Div(sub, className="sub"),
    ], className='admin-card-body'), href=href, className=f'admin-card {bg} text-decoration-none')


@callback(
    [
        Output('admin-page-protected-content', 'children'),
        Output('admin-auth-redirect', 'href')
    ],
    Input('session-admin-name', 'data'),
    State('session-admin-email', 'data'),
)
def protect_and_render_dashboard(first_name, session_email):
    # If no session data exists, force redirect to home/login
    if not first_name:
        return dash.no_update, '/home'

    me = get_account_by_email(session_email) if session_email else None
    counts = get_inquiry_folder_counts(me['id'] if me else None)
    items = get_item_counts()
    accounts = get_all_accounts()
    active_accounts = sum(1 for a in accounts if (a.get('status') or 'Active') == 'Active')
    pending = sum(1 for a in accounts if a.get('must_change_password'))
    open_count = counts.get('New', 0) + counts.get('Urgent', 0) + counts.get('In Progress', 0)
    recent = search_inquiries('inbox', sort='newest', limit=6)

    header = ui.page_header(
        f"{_greeting()}, {first_name}!",
        "Here's what's happening with inquiries, the catalog and your team today.",
        crumbs=datetime.now().strftime('%A, %B %d, %Y').replace(' 0', ' '),
        variant='grey',
        actions=[html.A("View website ↗", href='/home', target='_blank', className="a-btn a-btn-light")],
    )

    stats = html.Div([
        _stat('/admin/inquiries', "Unread inquiries", counts.get('unread', 0), "Waiting in the inbox",
              'amber' if counts.get('unread') else ''),
        _stat('/admin/inquiries', "Urgent", counts.get('Urgent', 0), "Marked urgent, not resolved",
              'warn' if counts.get('Urgent') else ''),
        _stat('/admin/inquiries', "Open inquiries", open_count,
              f"{counts.get('mine', 0)} assigned to you" if me else "New, urgent or in progress"),
        _stat('/admin/items', "Items on website", int(items.get('visible') or 0),
              f"{int(items['hidden'])} hidden" if items.get('hidden') else f"{int(items.get('total') or 0)} in the catalog"),
        _stat('/admin/accounts', "Active accounts", active_accounts,
              f"{pending} awaiting first login" if pending else "Admin users"),
    ], className="stat-row mb-3")

    quick = html.Div([
        html.Div(html.H6("Quick access"), className="a-card-head"),
        html.Div(html.Div([
            _quick('/admin/inquiries', 'icons/inquiries.svg', "Inquiries", f"{counts.get('unread', 0)} unread", 'inquiries-bg'),
            _quick('/admin/items', 'icons/items.svg', "Items", f"{int(items.get('total') or 0)} products", 'items-bg'),
            _quick('/admin/accounts', 'icons/accounts.svg', "Accounts", f"{active_accounts} active", 'accounts-bg'),
            _quick('/admin/analytics', 'icons/analytics.svg', "Reports & Analytics", "Print a one-page report", 'reports-bg'),
        ], className="quick-grid"), className="a-card-body"),
    ], className="a-card mb-3")

    attention = []
    if counts.get('Urgent'):
        attention.append(html.Li([html.B(f"{counts['Urgent']} urgent"), " inquir", "y" if counts['Urgent'] == 1 else "ies", " still open."]))
    if counts.get('unread'):
        attention.append(html.Li([html.B(f"{counts['unread']} unread"), " in the inbox."]))
    if items.get('hidden'):
        attention.append(html.Li([html.B(f"{int(items['hidden'])} item{'s' if items['hidden'] != 1 else ''}"), " hidden from the website."]))
    if pending:
        attention.append(html.Li([html.B(f"{pending} account{'s' if pending != 1 else ''}"),
                                  " haven't" if pending != 1 else " hasn't", " signed in to set a password yet."]))
    if me and me.get('must_change_password'):
        attention.insert(0, html.Li([html.B("You're on a temporary password. "), dcc.Link("Set your own", href='/admin/my-account')]))

    attention_card = html.Div([
        html.Div(html.H6("Needs attention"), className="a-card-head"),
        html.Div(html.Ul(attention, className="highlights") if attention else
                 html.Div("All caught up.", className="text-muted"), className="a-card-body"),
    ], className="a-card")

    rows = []
    for iq in recent:
        rows.append(dcc.Link([
            html.Span(className="unread-dot" + ("" if not iq['is_read'] else " read")),
            html.Div([html.Div(iq.get('customer_name') or '(no name)', className="n"),
                      html.Div((iq.get('machine_inquiry') or '').split('\n')[0], className="s")], style={'minWidth': 0}),
            html.Div([ui.status_chip(iq['status']), html.Div(ui.short_when(iq.get('created_at')), className="mt-1")], className="w"),
        ], href=f"/admin/inquiries?open={iq['id']}", className="recent-row"))
    recent_card = html.Div([
        html.Div([html.H6("Latest inquiries"), dcc.Link("Open inbox →", href='/admin/inquiries', className="a-btn a-btn-outline a-btn-sm")],
                 className="a-card-head"),
        html.Div(rows or [html.Div("No inquiries yet.", className="a-card-body text-muted")], className="recent-list"),
    ], className="a-card mb-3")

    content = html.Div([
        header,
        html.Div([
            stats,
            html.Div([
                html.Div([quick, attention_card]),
                html.Div([recent_card]),
            ], className="dash-grid"),
        ], className="admin-container"),
    ], className="admin-shell")
    return content, dash.no_update
