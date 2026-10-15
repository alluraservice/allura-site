"""
Inquiries inbox — a Gmail-style workspace for every inquiry sent from the website.

Layout:  [ folders ]  [ message list ]  [ reading pane + reply composer ]
Every inquiry shows WHERE it came from (its channel) and its REFERENCE NUMBER:
    Product Page  - "Contact Sales" on a product (the product name is shown with it)
    Service Page  - the Service Inquiry form on the Services page
    Contact Us    - the inquiry form on the Contact Us page
The folder rail has a "Channels" section for each one, and the Source filter narrows any view.
The reference number appears in the list, the reading pane, search, CSV export, and in every reply
emailed to the customer (subject line and message).

Other features: folders with counts (unread, starred, assigned to me, by status, archived, labels),
search + filters + sort, star / read / archive, bulk actions, status / priority / assignee / labels
per inquiry (autosaved), reply by email with templates, internal notes, activity thread, CSV export.
/admin/inquiries?open=<id> opens that inquiry directly (used by the dashboard).
"""
import re
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update

import admin_ui as ui
from database.db_handler import (INQUIRY_LABELS, INQUIRY_PRIORITIES, INQUIRY_SOURCES, INQUIRY_STATUSES,
                                 SOURCE_DESCRIPTIONS, add_inquiry_message, bulk_update_inquiries,
                                 get_account_by_email, get_all_accounts, get_inquiries_by_ids, get_inquiry_detail,
                                 get_inquiry_folder_counts, get_inquiry_messages, search_inquiries,
                                 update_inquiry_fields)
from utils.mailer import send_inquiry_reply

dash.register_page(__name__, path='/admin/inquiries')

ANY = '_'
FOLDERS_MAIN = [('inbox', 'Inbox', '✉'), ('unread', 'Unread', '●'), ('starred', 'Starred', '★'), ('mine', 'Assigned to me', '◎')]
FOLDERS_SOURCE = [('source:Product Page', 'Product Page', html.Span(className="dot dot-product")),
                  ('source:Service Page', 'Service Page', html.Span(className="dot dot-service")),
                  ('source:Contact Us', 'Contact Us', html.Span(className="dot dot-contact"))]
FOLDERS_STATUS = [('New', 'New', '◆'), ('Urgent', 'Urgent', '!'), ('In Progress', 'In Progress', '◐'), ('Resolved', 'Resolved', '✓')]
FOLDERS_OTHER = [('archived', 'Archived', '▤')]
FOLDER_TITLES = {f: t for f, t, _ in FOLDERS_MAIN + FOLDERS_SOURCE + FOLDERS_STATUS + FOLDERS_OTHER}
FOLDER_TITLES.update({f'source:{s}': f"From the {s}" if s != 'Contact Us' else "From Contact Us" for s in INQUIRY_SOURCES})

SIGNATURE_TAIL = "Allura Enterprise\ninfo@alluraenterpriseph.com  |  +63 917 770 1820"
TEMPLATES = {
    'ack': ("Acknowledge receipt",
            "Dear {contact},\n\nThank you for reaching out to Allura Enterprise regarding {topic} (reference no. {ref}). "
            "We have received your inquiry and a member of our team will get back to you within one (1) business day."),
    'quote': ("Quotation to follow",
              "Dear {contact},\n\nThank you for your interest in {topic}. We are preparing a formal quotation for "
              "{customer} and will send it to you shortly. It will include pricing, lead time, installation "
              "requirements and warranty coverage."),
    'details': ("Ask for more details",
                "Dear {contact},\n\nThank you for your inquiry regarding {topic}. So we can recommend the right "
                "configuration, could you share the following:\n\n  • Intended clinical use / department\n"
                "  • Expected patient volume per day\n  • Target delivery date and budget range\n"
                "  • Room dimensions or site layout, if available"),
    'visit': ("Schedule a site visit",
              "Dear {contact},\n\nFollowing your inquiry about {topic}, we would like to schedule a site visit at "
              "{customer} to assess the installation area and power requirements. Please let us know two or three "
              "dates and times that work for your team."),
    'service': ("Service request received",
                "Dear {contact},\n\nWe have logged your service request regarding {topic} under reference no. {ref}. "
                "Our field engineer will contact you to confirm the visit schedule. For urgent concerns, call us at "
                "+63 917 770 1820 and mention your reference number."),
    'close': ("Close the inquiry",
              "Dear {contact},\n\nThank you again for considering Allura Enterprise. We're marking inquiry {ref} as "
              "resolved, but please don't hesitate to reply to this email if you need anything else."),
}


def _folder_button(key, label, icon):
    return html.Button([
        html.Span(icon, className="ico"),
        html.Span(label),
        html.Span("", id={'type': 'inq-count', 'folder': key}, className="count"),
    ], id={'type': 'inq-folder', 'folder': key}, n_clicks=0, className="folder" + (" active" if key == 'inbox' else ""),
        title=SOURCE_DESCRIPTIONS.get(key[7:]) if key.startswith('source:') else None)


def _select(id_, options, placeholder=None, value=None, cls="a-input"):
    # dbc.Select hides an option whose value is '' so the "any / none" choice uses ANY ('_') instead
    opts = ([{'label': placeholder, 'value': ANY}] if placeholder is not None else []) + \
           [o if isinstance(o, dict) else {'label': o, 'value': o} for o in options]
    if value is None:
        value = ANY if placeholder is not None else opts[0]['value']
    return dbc.Select(id=id_, options=opts, value=value, className=cls)


def _v(x):
    """Select value -> None when it's the "any / none" choice."""
    return None if x in (None, '', ANY) else x


def layout():
    accounts = [a for a in get_all_accounts() if (a.get('status') or 'Active') == 'Active']
    assignee_opts = [{'label': 'Unassigned', 'value': 'unassigned'}] + \
                    [{'label': a['name'], 'value': str(a['id'])} for a in accounts]

    folders = html.Div([
        html.Div("Mailbox", className="a-section-title"),
        *[_folder_button(*f) for f in FOLDERS_MAIN],
        html.Div(className="folder-divider"),
        html.Div("Channels", className="a-section-title"),
        *[_folder_button(*f) for f in FOLDERS_SOURCE],
        html.Div(className="folder-divider"),
        html.Div("Status", className="a-section-title"),
        *[_folder_button(*f) for f in FOLDERS_STATUS],
        html.Div(className="folder-divider"),
        *[_folder_button(*f) for f in FOLDERS_OTHER],
        html.Div(className="folder-divider"),
        html.Div("Labels", className="a-section-title"),
        *[_folder_button(f"label:{lb}", lb, '#') for lb in INQUIRY_LABELS],
    ], className="a-card folders")

    filters = html.Div([
        html.Div(dbc.Input(id='inq-search', type='search', debounce=True, className="a-input",
                           placeholder="Search reference no., customer, contact, email, phone, product or message…"),
                 className="a-search grow"),
        html.Div(_select('inq-f-source', [{'label': f"From {s}", 'value': s} for s in INQUIRY_SOURCES], 'All channels'),
                 className="fit"),
        html.Div(_select('inq-f-priority', INQUIRY_PRIORITIES, 'Any priority'), className="fit"),
        html.Div(_select('inq-f-assignee', assignee_opts, 'Anyone'), className="fit"),
        html.Div(_select('inq-f-period', [{'label': 'Today', 'value': 'today'}, {'label': 'Last 7 days', 'value': '7d'},
                                          {'label': 'Last 30 days', 'value': '30d'}, {'label': 'Last 90 days', 'value': '90d'},
                                          {'label': 'This year', 'value': 'year'}], 'Any time'), className="fit"),
        html.Div(_select('inq-sort', [{'label': 'Newest first', 'value': 'newest'}, {'label': 'Oldest first', 'value': 'oldest'},
                                      {'label': 'Recently updated', 'value': 'updated'}, {'label': 'Priority', 'value': 'priority'},
                                      {'label': 'Status', 'value': 'status'}, {'label': 'Customer A–Z', 'value': 'customer'}],
                         None, value='newest'), className="fit"),
    ], className="a-toolbar mb-3")

    message_list = html.Div([
        html.Div([
            html.Div([
                html.Div([
                    dbc.Checkbox(id='inq-select-all', value=False, className="me-1"),
                    html.Span(id='inq-list-title', className="fw-bold", style={'color': 'var(--dark-green)'}),
                ], className="d-flex align-items-center gap-1"),
                html.Span(id='inq-list-count'),
            ], className="inq-list-meta"),
        ], className="inq-list-tools"),
        html.Div([
            html.Span(id='inq-bulk-count', className="fw-bold me-1", style={'fontSize': '.8rem'}),
            html.Button("Mark read", id='inq-bulk-read', n_clicks=0, className="a-btn a-btn-outline a-btn-sm"),
            html.Button("Unread", id='inq-bulk-unread', n_clicks=0, className="a-btn a-btn-outline a-btn-sm"),
            html.Button("Star", id='inq-bulk-star', n_clicks=0, className="a-btn a-btn-outline a-btn-sm"),
            html.Button("Archive", id='inq-bulk-archive', n_clicks=0, className="a-btn a-btn-outline a-btn-sm"),
            _select('inq-bulk-status', INQUIRY_STATUSES, 'Set status…', cls="a-input form-select-sm"),
            _select('inq-bulk-assign', assignee_opts, 'Assign to…', cls="a-input form-select-sm"),
        ], id='inq-bulkbar', className="inq-bulkbar", style={'display': 'none'}),
        dcc.Loading(html.Div(id='inq-list'), type='dot', color='#006400', parent_className="inq-list",
                    overlay_style={'visibility': 'visible', 'opacity': .6}),
    ], className="a-card inq-list-card")

    reader = html.Div([
        html.Div([
            html.Img(src='/assets/icons/inquiries.svg'),
            html.H5("Select an inquiry to read it", className="mb-1"),
            html.Div("Replies, notes and status changes all live here.", style={'fontSize': '.85rem'}),
        ], id='inq-reader-empty', className="reader-empty"),

        html.Div([
            html.Div([
                html.Div([
                    html.Div(id='inq-reader-head', style={'minWidth': 0}),
                    html.Div([
                        html.Button("☆", id='inq-act-star', n_clicks=0, className="a-icon-btn", title="Star"),
                        html.Button("✉", id='inq-act-unread', n_clicks=0, className="a-icon-btn", title="Mark as unread"),
                        html.Button("▤", id='inq-act-archive', n_clicks=0, className="a-icon-btn", title="Archive"),
                    ], className="reader-actions"),
                ], className="d-flex justify-content-between gap-3"),
            ], className="reader-head"),

            # Everything below the header scrolls together: controls, thread, then the reply box (Gmail-style)
            html.Div([
                html.Div([
                    html.Div([html.Label("Status", className="a-label"),
                              _select('inq-ctl-status', INQUIRY_STATUSES, None, value='New', cls="a-input")]),
                    html.Div([html.Label("Priority", className="a-label"),
                              _select('inq-ctl-priority', INQUIRY_PRIORITIES, None, value='Normal', cls="a-input")]),
                    html.Div([html.Label("Assigned to", className="a-label"),
                              _select('inq-ctl-assignee', [{'label': a['name'], 'value': str(a['id'])} for a in accounts],
                                      'Unassigned', cls="a-input")]),
                    html.Div([html.Label("Labels", className="a-label"),
                              dcc.Dropdown(id='inq-ctl-labels', options=INQUIRY_LABELS, multi=True, value=[],
                                           placeholder="Add labels", clearable=True, searchable=True)]),
                ], className="reader-controls"),

                html.Div(id='inq-reader-body', className="reader-body"),

                html.Div([
                    html.Div([
                        html.Button("Reply by email", id='inq-mode-reply', n_clicks=0, className="nav-link active"),
                        html.Button("Internal note", id='inq-mode-note', n_clicks=0, className="nav-link"),
                    ], className="nav nav-tabs"),
                    html.Div([
                        html.Div([
                            dbc.Input(id='inq-reply-subject', className="a-input", placeholder="Subject", style={'flex': '1 1 260px'}),
                            html.Div(_select('inq-template', [{'label': v[0], 'value': k} for k, v in TEMPLATES.items()],
                                             'Insert template…', cls="a-input"), style={'flex': '0 0 200px'}),
                        ], className="composer-row mb-2"),
                        dbc.Textarea(id='inq-reply-body', className="a-input", style={'height': '110px'},
                                     placeholder="Write your reply to the client. It is emailed from Allura (with the reference "
                                                 "number) and saved to this thread."),
                        html.Div([
                            html.Span("After sending:", className="a-label mb-0"),
                            html.Div(_select('inq-reply-then', [{'label': 'Set to In Progress', 'value': 'In Progress'},
                                                                {'label': 'Set to Resolved', 'value': 'Resolved'}],
                                             'Keep current status', cls="a-input form-select-sm"), style={'width': '190px'}),
                            html.Button("Send reply", id='inq-send', n_clicks=0, className="a-btn a-btn-primary ms-auto"),
                        ], className="composer-row mt-2"),
                    ], id='inq-compose-reply'),
                    html.Div([
                        dbc.Textarea(id='inq-note-body', className="a-input", style={'height': '90px'},
                                     placeholder="Notes are visible only to the Allura team (e.g. called the client, waiting for PO)."),
                        html.Div(html.Button("Add note", id='inq-add-note', n_clicks=0, className="a-btn a-btn-primary ms-auto"),
                                 className="composer-row mt-2"),
                    ], id='inq-compose-note', style={'display': 'none'}),
                    html.Div(id='inq-compose-status', className="composer-status"),
                ], className="composer"),
            ], id='inq-reader-scroll', className="reader-scroll"),
        ], id='inq-reader-main', className="d-flex flex-column", style={'display': 'none', 'height': '100%', 'minHeight': 0}),
    ], className="a-card reader")

    return html.Div([
        dcc.Store(id='inq-folder', data='inbox'),
        dcc.Store(id='inq-active', data=None),
        dcc.Store(id='inq-refresh', data=0),
        dcc.Store(id='inq-visible-ids', data=[]),
        dcc.Download(id='inq-download'),

        ui.page_header(
            "Inquiries",
            "Every quote and service request from the website, filed by the page it came from.",
            crumbs="Admin  /  Inquiries",
            actions=[html.Button("Export CSV", id='inq-export', n_clicks=0, className="a-btn a-btn-light")],
        ),
        html.Div([
            dbc.Alert(id='inq-toast', is_open=False, duration=5000, dismissable=True,
                      className="a-alert a-alert-ok mb-3"),
            filters,
            html.Div([folders, message_list, reader], className="inbox"),
        ], className="admin-container"),
    ], className="admin-shell")


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------
def _me(session_email):
    return get_account_by_email(session_email) if session_email else None


def _clicked():
    """True only for a real click (ignores components that were just re-rendered)."""
    return bool(ctx.triggered_id) and bool(ctx.triggered and ctx.triggered[0].get('value'))


def _subject_line(text, n=70):
    first = (text or '').strip().split('\n')[0]
    return first if len(first) <= n else first[:n].rsplit(' ', 1)[0] + '…'


def _row(iq, active_id):
    labels = [lb for lb in (iq.get('labels') or '').split(',') if lb]
    cls = "inq-row" + ("" if iq['is_read'] else " unread") + (" active" if iq['id'] == active_id else "")
    tags = [ui.status_chip(iq['status']), ui.source_chip(iq['source'])]
    tags += [html.Span(lb, className="chip chip-label plain") for lb in labels[:2]]
    meta = []
    if iq.get('reply_count'):
        meta.append(f"↩ {iq['reply_count']}")
    if iq.get('assignee_name'):
        meta.append(iq['assignee_name'].split(' ')[0])
    if meta:
        tags.append(html.Span("  ·  ".join(meta), className="meta"))
    subject = _subject_line(iq.get('machine_inquiry'))
    if iq.get('source_detail'):
        subject = f"{iq['source_detail']} — {subject}"
    return html.Div([
        dbc.Checkbox(id={'type': 'inq-check', 'index': iq['id']}, value=False),
        html.Button("★" if iq['is_starred'] else "☆", id={'type': 'inq-star', 'index': iq['id']}, n_clicks=0,
                    className="star-btn" + (" on" if iq['is_starred'] else ""), title="Star"),
        html.Div([
            html.Div([
                html.Span(className=f"prio prio-{iq['priority']}", title=f"{iq['priority']} priority"),
                html.Span(iq.get('customer_name') or '(no name)', className="name"),
                html.Span(ui.short_when(iq.get('created_at')), className="when"),
            ], className="inq-row-top"),
            html.Div(iq.get('reference_no') or '', className="refline"),
            html.Div(subject, className="subject"),
            html.Div(tags, className="inq-row-tags"),
        ], id={'type': 'inq-open', 'index': iq['id']}, n_clicks=0, className="inq-row-main"),
    ], className=cls)


def _detail_item(label, value):
    return html.Div([html.Div(label, className="k"), html.Div(value or '—', className="v")])


def _thread(iq, messages):
    items = [html.Div([
        html.Div([html.Span([html.B(iq.get('contact_person') or iq.get('customer_name')), f"  <{iq.get('email') or 'no email'}>"]),
                  html.Span(ui.fmt_date(iq.get('created_at'), True))], className="mc-head"),
        html.Div(iq.get('machine_inquiry') or '', className="mc-body"),
        html.Div([html.Hr(className="my-2"), html.Div("Remarks", className="a-label"),
                  html.Div(iq.get('remarks'), className="mc-body")]) if (iq.get('remarks') or '').strip() else None,
    ], className="message-card from-client")]

    for m in messages:
        when = ui.fmt_date(m.get('created_at'), True)
        if m['kind'] == 'event':
            items.append(html.Div(f"{m.get('author') or 'System'} {m['body']}  ·  {when}", className="thread-event"))
        elif m['kind'] == 'note':
            items.append(html.Div([
                html.Div([html.Span([html.B(m.get('author') or 'Team'), "  added an internal note"]), html.Span(when)], className="mc-head"),
                html.Div(m['body'], className="mc-body"),
            ], className="message-card note"))
        else:
            status = "replied by email" if m.get('sent_ok') else "reply NOT delivered (saved only)"
            items.append(html.Div([
                html.Div([html.Span([html.B(m.get('author') or 'Allura'), f"  {status}"]), html.Span(when)], className="mc-head"),
                html.Div(m.get('subject') or '', className="fw-bold mb-1", style={'fontSize': '.84rem'}) if m.get('subject') else None,
                html.Div(m['body'], className="mc-body"),
            ], className="message-card reply" + ("" if m.get('sent_ok') else " failed")))
    return items


# ---------------------------------------------------------------------
# Folder selection
# ---------------------------------------------------------------------
@callback(
    Output('inq-folder', 'data'),
    Output({'type': 'inq-folder', 'folder': ALL}, 'className'),
    Input({'type': 'inq-folder', 'folder': ALL}, 'n_clicks'),
    State({'type': 'inq-folder', 'folder': ALL}, 'id'),
    prevent_initial_call=True,
)
def choose_folder(_, ids):
    if not _clicked():
        raise dash.exceptions.PreventUpdate
    chosen = ctx.triggered_id['folder']
    return chosen, ["folder" + (" active" if i['folder'] == chosen else "") for i in ids]


# ---------------------------------------------------------------------
# Message list + folder counts
# ---------------------------------------------------------------------
@callback(
    Output('inq-list', 'children'),
    Output('inq-list-title', 'children'),
    Output('inq-list-count', 'children'),
    Output({'type': 'inq-count', 'folder': ALL}, 'children'),
    Output('inq-visible-ids', 'data'),
    Output('inq-select-all', 'value'),
    Output('inq-bulk-archive', 'children'),
    Input('inq-folder', 'data'),
    Input('inq-search', 'value'),
    Input('inq-f-source', 'value'),
    Input('inq-f-priority', 'value'),
    Input('inq-f-assignee', 'value'),
    Input('inq-f-period', 'value'),
    Input('inq-sort', 'value'),
    Input('inq-refresh', 'data'),
    State('inq-active', 'data'),
    State('session-admin-email', 'data'),
)
def render_list(folder, search, source, priority, assignee, period, sort, _refresh, active_id, session_email):
    me = _me(session_email)
    me_id = me['id'] if me else None
    rows = search_inquiries(folder or 'inbox', search, _v(source), _v(priority), _v(assignee),
                            _v(period), _v(sort) or 'newest', me_id)
    counts = get_inquiry_folder_counts(me_id)

    count_out = []
    for out in ctx.outputs_list[3]:
        n = counts.get(out['id']['folder'])
        # Inbox/Unread show unread; channels, status folders and others show totals; labels show nothing
        count_out.append(str(n) if n else "")

    title = FOLDER_TITLES.get(folder, folder.replace('label:', 'Label: ') if folder else 'Inbox')
    if rows:
        body = [_row(r, active_id) for r in rows]
    else:
        body = html.Div([html.Div("✉", className="big"),
                         html.Div("Nothing here.", className="fw-bold mt-1"),
                         html.Div("Try another folder or clear the filters.", style={'fontSize': '.82rem'})],
                        className="inq-empty")
    count_txt = f"{len(rows)} {'inquiry' if len(rows) == 1 else 'inquiries'}"
    return (body, title, count_txt, count_out, [r['id'] for r in rows], False,
            "Move to inbox" if folder == 'archived' else "Archive")


# ---------------------------------------------------------------------
# Open an inquiry (marks it read) — from the list, or from ?open=<id>
# ---------------------------------------------------------------------
@callback(
    Output('inq-active', 'data'),
    Output('inq-refresh', 'data', allow_duplicate=True),
    Input({'type': 'inq-open', 'index': ALL}, 'n_clicks'),
    State('inq-refresh', 'data'),
    prevent_initial_call=True,
)
def open_inquiry(_, refresh):
    if not _clicked():
        raise dash.exceptions.PreventUpdate
    iid = ctx.triggered_id['index']
    update_inquiry_fields(iid, is_read=True)
    return iid, (refresh or 0) + 1


@callback(
    Output('inq-active', 'data', allow_duplicate=True),
    Output('inq-refresh', 'data', allow_duplicate=True),
    Input('url', 'search'),
    State('inq-refresh', 'data'),
    prevent_initial_call='initial_duplicate',
)
def open_from_link(search, refresh):
    value = (parse_qs((search or '').lstrip('?')).get('open') or [None])[0]
    if not value or not str(value).isdigit():
        raise dash.exceptions.PreventUpdate
    update_inquiry_fields(int(value), is_read=True)
    return int(value), (refresh or 0) + 1


@callback(
    Output('inq-refresh', 'data', allow_duplicate=True),
    Input({'type': 'inq-star', 'index': ALL}, 'n_clicks'),
    State('inq-refresh', 'data'),
    prevent_initial_call=True,
)
def star_from_list(_, refresh):
    if not _clicked():
        raise dash.exceptions.PreventUpdate
    iid = ctx.triggered_id['index']
    iq = get_inquiry_detail(iid)
    if iq:
        update_inquiry_fields(iid, is_starred=not bool(iq.get('is_starred')))
    return (refresh or 0) + 1


# ---------------------------------------------------------------------
# Reading pane
# ---------------------------------------------------------------------
@callback(
    Output('inq-reader-empty', 'style'),
    Output('inq-reader-main', 'style'),
    Output('inq-reader-head', 'children'),
    Output('inq-reader-body', 'children'),
    Output('inq-ctl-status', 'value'),
    Output('inq-ctl-priority', 'value'),
    Output('inq-ctl-assignee', 'value'),
    Output('inq-ctl-labels', 'value'),
    Output('inq-act-star', 'children'),
    Output('inq-act-star', 'className'),
    Output('inq-act-archive', 'title'),
    Output('inq-reply-subject', 'value'),
    Input('inq-active', 'data'),
    Input('inq-refresh', 'data'),
)
def render_reader(active_id, _refresh):
    hidden = {'display': 'none'}
    shown = {'display': 'flex', 'height': '100%', 'minHeight': 0}
    iq = get_inquiry_detail(active_id) if active_id else None
    if not iq:
        return ({}, hidden, None, None, no_update, no_update, no_update, no_update,
                no_update, no_update, no_update, no_update)

    contact_bits = []
    if iq.get('email'):
        contact_bits += [html.A(iq['email'], href=f"mailto:{iq['email']}")]
    if iq.get('phone'):
        contact_bits += ["  ·  ", html.A(iq['phone'], href=f"tel:{iq['phone']}")]
    head = [
        html.H3(iq.get('customer_name') or '(no name)'),
        html.Div(contact_bits, className="sub"),
        html.Div([ui.ref_chip(iq.get('reference_no')),
                  ui.status_chip(iq.get('status')),
                  ui.source_chip(iq.get('source_v'), iq.get('source_detail')),
                  html.Span(f"{iq.get('priority_v')} priority", className="chip plain"),
                  html.Span(f"Received {ui.fmt_date(iq.get('created_at'), True)}", className="chip plain")],
                 className="d-flex flex-wrap gap-1 mt-2"),
    ]

    details = html.Div([
        _detail_item("Reference no.", iq.get('reference_no')),
        _detail_item("Came from", SOURCE_DESCRIPTIONS.get(iq.get('source_v'), iq.get('source_v'))
                     + (f" ({iq['source_detail']})" if iq.get('source_detail') else "")),
        _detail_item("Contact person", iq.get('contact_person')),
        _detail_item("Department & title", iq.get('department')),
        _detail_item("Office address", iq.get('address')),
        _detail_item("Assigned to", iq.get('assignee_name') or 'Unassigned'),
        _detail_item("First response", ui.fmt_date(iq.get('first_response_at'), True) if iq.get('first_response_at') else 'Not yet replied'),
        _detail_item("Resolved", ui.fmt_date(iq.get('resolved_at'), True) if iq.get('resolved_at') else '—'),
    ], className="detail-grid")
    body = [details, html.Div("Conversation", className="a-section-title mt-2"),
            *_thread(iq, get_inquiry_messages(iq['id']))]

    starred = bool(iq.get('is_starred'))
    labels = [lb for lb in (iq.get('labels') or '').split(',') if lb]
    subject = no_update
    if ctx.triggered_id == 'inq-active':
        topic = iq.get('source_detail') or _subject_line(iq.get('machine_inquiry'), 50)
        subject = f"Re: Your inquiry with Allura Enterprise – {topic}"
    return ({'display': 'none'}, shown, head, body,
            iq.get('status') or 'New', iq.get('priority_v') or 'Normal',
            str(iq['assigned_to']) if iq.get('assigned_to') else ANY, labels,
            "★" if starred else "☆", "a-icon-btn" + (" is-on" if starred else ""),
            "Move to inbox" if iq.get('is_archived') else "Archive", subject)


# ---------------------------------------------------------------------
# Autosave status / priority / assignee / labels from the reading pane
# ---------------------------------------------------------------------
@callback(
    Output('inq-refresh', 'data', allow_duplicate=True),
    Output('inq-toast', 'children', allow_duplicate=True),
    Output('inq-toast', 'is_open', allow_duplicate=True),
    Input('inq-ctl-status', 'value'),
    Input('inq-ctl-priority', 'value'),
    Input('inq-ctl-assignee', 'value'),
    Input('inq-ctl-labels', 'value'),
    State('inq-active', 'data'),
    State('inq-refresh', 'data'),
    State('session-admin-name', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def autosave_controls(status, priority, assignee, labels, active_id, refresh, s_name, s_email):
    iq = get_inquiry_detail(active_id) if active_id else None
    if not iq:
        raise dash.exceptions.PreventUpdate
    me = _me(s_email)
    author = (me or {}).get('name') or s_name or 'Admin'

    changes, events = {}, []
    if status and status != iq.get('status'):
        changes['status'] = status
        events.append(f"changed status to {status}")
    if priority and priority != iq.get('priority_v'):
        changes['priority'] = priority
        events.append(f"set priority to {priority}")
    new_assignee = int(assignee) if _v(assignee) else None
    if new_assignee != iq.get('assigned_to'):
        changes['assigned_to'] = new_assignee
        name = next((a['name'] for a in get_all_accounts() if a['id'] == new_assignee), None)
        events.append(f"assigned this to {name}" if name else "removed the assignee")
    new_labels = ','.join(labels or [])
    if new_labels != (iq.get('labels') or ''):
        changes['labels'] = new_labels
        events.append(f"set labels: {', '.join(labels)}" if labels else "cleared labels")
    if not changes:
        raise dash.exceptions.PreventUpdate

    update_inquiry_fields(active_id, **changes)
    for e in events:
        add_inquiry_message(active_id, 'event', e, author=author, author_email=s_email)
    return (refresh or 0) + 1, "Saved. " + "; ".join(e[0].upper() + e[1:] for e in events) + ".", True


# ---------------------------------------------------------------------
# Reading pane actions: star / mark unread / archive
# ---------------------------------------------------------------------
@callback(
    Output('inq-refresh', 'data', allow_duplicate=True),
    Output('inq-active', 'data', allow_duplicate=True),
    Input('inq-act-star', 'n_clicks'),
    Input('inq-act-unread', 'n_clicks'),
    Input('inq-act-archive', 'n_clicks'),
    State('inq-active', 'data'),
    State('inq-refresh', 'data'),
    prevent_initial_call=True,
)
def reader_actions(_s, _u, _a, active_id, refresh):
    iq = get_inquiry_detail(active_id) if active_id else None
    if not iq or not _clicked():
        raise dash.exceptions.PreventUpdate
    if ctx.triggered_id == 'inq-act-star':
        update_inquiry_fields(active_id, is_starred=not bool(iq.get('is_starred')))
        return (refresh or 0) + 1, no_update
    if ctx.triggered_id == 'inq-act-unread':
        update_inquiry_fields(active_id, is_read=False)
        return (refresh or 0) + 1, None
    update_inquiry_fields(active_id, is_archived=not bool(iq.get('is_archived')))
    return (refresh or 0) + 1, None


# ---------------------------------------------------------------------
# Selection + bulk actions
# ---------------------------------------------------------------------
@callback(
    Output({'type': 'inq-check', 'index': ALL}, 'value'),
    Input('inq-select-all', 'value'),
    State({'type': 'inq-check', 'index': ALL}, 'id'),
    prevent_initial_call=True,
)
def select_all(checked, ids):
    if ctx.triggered_id != 'inq-select-all':
        raise dash.exceptions.PreventUpdate
    return [bool(checked)] * len(ids)


@callback(
    Output('inq-bulkbar', 'style'),
    Output('inq-bulk-count', 'children'),
    Input({'type': 'inq-check', 'index': ALL}, 'value'),
)
def show_bulkbar(values):
    n = sum(1 for v in (values or []) if v)
    return ({'display': 'flex'} if n else {'display': 'none'}), f"{n} selected"


@callback(
    Output('inq-refresh', 'data', allow_duplicate=True),
    Output('inq-bulk-status', 'value'),
    Output('inq-bulk-assign', 'value'),
    Output('inq-toast', 'children', allow_duplicate=True),
    Output('inq-toast', 'is_open', allow_duplicate=True),
    Input('inq-bulk-read', 'n_clicks'),
    Input('inq-bulk-unread', 'n_clicks'),
    Input('inq-bulk-star', 'n_clicks'),
    Input('inq-bulk-archive', 'n_clicks'),
    Input('inq-bulk-status', 'value'),
    Input('inq-bulk-assign', 'value'),
    State({'type': 'inq-check', 'index': ALL}, 'value'),
    State({'type': 'inq-check', 'index': ALL}, 'id'),
    State('inq-folder', 'data'),
    State('inq-refresh', 'data'),
    State('session-admin-name', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def bulk_actions(_r, _u, _s, _a, status, assign, checks, ids, folder, refresh, s_name, s_email):
    if not _clicked():
        raise dash.exceptions.PreventUpdate
    selected = [i['index'] for i, v in zip(ids, checks) if v]
    if not selected:
        raise dash.exceptions.PreventUpdate

    t = ctx.triggered_id
    if t in ('inq-bulk-status', 'inq-bulk-assign') and not _v(ctx.triggered[0].get('value')):
        raise dash.exceptions.PreventUpdate
    me = _me(s_email)
    author = (me or {}).get('name') or s_name or 'Admin'
    n = len(selected)
    if t == 'inq-bulk-read':
        bulk_update_inquiries(selected, is_read=True); msg = f"Marked {n} as read."
    elif t == 'inq-bulk-unread':
        bulk_update_inquiries(selected, is_read=False); msg = f"Marked {n} as unread."
    elif t == 'inq-bulk-star':
        bulk_update_inquiries(selected, is_starred=True); msg = f"Starred {n}."
    elif t == 'inq-bulk-archive':
        to_archive = folder != 'archived'
        bulk_update_inquiries(selected, is_archived=to_archive)
        msg = f"{'Archived' if to_archive else 'Moved to inbox'}: {n}."
    elif t == 'inq-bulk-status':
        bulk_update_inquiries(selected, status=status)
        for iid in selected:
            add_inquiry_message(iid, 'event', f"changed status to {status}", author=author, author_email=s_email)
        msg = f"Set {n} to {status}."
    else:
        new_id = None if assign == 'unassigned' else int(assign)
        bulk_update_inquiries(selected, assigned_to=new_id)
        name = next((a['name'] for a in get_all_accounts() if a['id'] == new_id), None)
        for iid in selected:
            add_inquiry_message(iid, 'event', f"assigned this to {name}" if name else "removed the assignee",
                                author=author, author_email=s_email)
        msg = f"Assigned {n} to {name}." if name else f"Unassigned {n}."
    return (refresh or 0) + 1, ANY, ANY, msg, True


# ---------------------------------------------------------------------
# Composer: mode toggle, templates, send reply, add note
# ---------------------------------------------------------------------
@callback(
    Output('inq-compose-reply', 'style'),
    Output('inq-compose-note', 'style'),
    Output('inq-mode-reply', 'className'),
    Output('inq-mode-note', 'className'),
    Input('inq-mode-reply', 'n_clicks'),
    Input('inq-mode-note', 'n_clicks'),
    prevent_initial_call=True,
)
def compose_mode(_r, _n):
    note = ctx.triggered_id == 'inq-mode-note'
    return ({'display': 'none'} if note else {}), ({} if note else {'display': 'none'}), \
        "nav-link" + ("" if note else " active"), "nav-link" + (" active" if note else "")


@callback(
    Output('inq-reply-body', 'value', allow_duplicate=True),
    Output('inq-template', 'value'),
    Input('inq-template', 'value'),
    State('inq-active', 'data'),
    State('session-admin-name', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def apply_template(key, active_id, s_name, s_email):
    if not key or key not in TEMPLATES or not active_id:
        raise dash.exceptions.PreventUpdate
    iq = get_inquiry_detail(active_id) or {}
    me = _me(s_email) or {}
    # The product for Contact Sales quotes, otherwise the first sentence of the client's message
    first = re.split(r'(?<=[.!?])\s|\n', (iq.get('machine_inquiry') or '').strip(), maxsplit=1)[0]
    topic = iq.get('source_detail') or _subject_line(first, 80).rstrip('.!?…') or 'your request'
    text = TEMPLATES[key][1].format(contact=iq.get('contact_person') or iq.get('customer_name') or 'Sir/Madam',
                                    customer=iq.get('customer_name') or 'your facility',
                                    topic=topic, ref=iq.get('reference_no') or '')
    agent = me.get('name') or s_name or 'The Allura Team'
    role = f"{me['role']}\n" if me.get('role') else ""
    text += f"\n\nBest regards,\n{agent}\n{role}{SIGNATURE_TAIL}"
    return text, ANY


@callback(
    Output('inq-compose-status', 'children'),
    Output('inq-reply-body', 'value'),
    Output('inq-refresh', 'data', allow_duplicate=True),
    Output('inq-reply-then', 'value'),
    Input('inq-send', 'n_clicks'),
    State('inq-reply-body', 'value'),
    State('inq-reply-subject', 'value'),
    State('inq-reply-then', 'value'),
    State('inq-active', 'data'),
    State('inq-refresh', 'data'),
    State('session-admin-name', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def send_reply(_, body, subject, then_status, active_id, refresh, s_name, s_email):
    if not _clicked():
        raise dash.exceptions.PreventUpdate
    iq = get_inquiry_detail(active_id) if active_id else None
    if not iq:
        raise dash.exceptions.PreventUpdate
    if not body or not body.strip():
        return ui.alert("Write a reply before sending.", 'warn'), no_update, no_update, no_update
    if not iq.get('email'):
        return ui.alert("This inquiry has no email address to reply to.", 'err'), no_update, no_update, no_update

    me = _me(s_email) or {}
    author = me.get('name') or s_name or 'Admin'
    ref = iq.get('reference_no')
    subject = (subject or '').strip() or "Re: Your inquiry with Allura Enterprise"
    if ref and ref not in subject:
        subject = f"[{ref}] {subject}"     # the customer sees the reference number in the subject and the message
    ok, info = send_inquiry_reply(iq['email'], subject, body.strip(), agent_name=author, reply_to=me.get('email'),
                                  reference_no=ref)
    add_inquiry_message(active_id, 'reply', body.strip(), author=author, author_email=s_email, subject=subject, sent_ok=ok)

    then_status = _v(then_status)
    if then_status and then_status != iq.get('status'):
        update_inquiry_fields(active_id, status=then_status)
        add_inquiry_message(active_id, 'event', f"changed status to {then_status}", author=author, author_email=s_email)
    elif ok and iq.get('status') == 'New':
        update_inquiry_fields(active_id, status='In Progress')
        add_inquiry_message(active_id, 'event', "changed status to In Progress (first reply sent)", author=author, author_email=s_email)

    if ok:
        return ui.alert(f"Reply sent to {iq['email']} and saved to the thread.", 'ok'), '', (refresh or 0) + 1, ANY
    return ui.alert(["Reply was saved to the thread but NOT emailed. ", html.Span(info)], 'err'), no_update, (refresh or 0) + 1, ANY


@callback(
    Output('inq-compose-status', 'children', allow_duplicate=True),
    Output('inq-note-body', 'value'),
    Output('inq-refresh', 'data', allow_duplicate=True),
    Input('inq-add-note', 'n_clicks'),
    State('inq-note-body', 'value'),
    State('inq-active', 'data'),
    State('inq-refresh', 'data'),
    State('session-admin-name', 'data'),
    State('session-admin-email', 'data'),
    prevent_initial_call=True,
)
def add_note(_, body, active_id, refresh, s_name, s_email):
    if not _clicked() or not active_id:
        raise dash.exceptions.PreventUpdate
    if not body or not body.strip():
        return ui.alert("Write a note first.", 'warn'), no_update, no_update
    me = _me(s_email) or {}
    add_inquiry_message(active_id, 'note', body.strip(), author=me.get('name') or s_name or 'Admin', author_email=s_email)
    return ui.alert("Note added.", 'ok'), '', (refresh or 0) + 1


@callback(
    Output('inq-compose-status', 'children', allow_duplicate=True),
    Input('inq-active', 'data'),
    prevent_initial_call=True,
)
def clear_compose_status(_):
    return None


# ---------------------------------------------------------------------
# Export current view
# ---------------------------------------------------------------------
@callback(
    Output('inq-download', 'data'),
    Input('inq-export', 'n_clicks'),
    State('inq-visible-ids', 'data'),
    prevent_initial_call=True,
)
def export_csv(n, ids):
    if not n:
        raise dash.exceptions.PreventUpdate
    rows = get_inquiries_by_ids(ids or [])
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=['reference_no', 'id', 'created_at', 'customer_name', 'source'])
    stamp = pd.Timestamp.now().strftime('%Y%m%d-%H%M')
    return dcc.send_data_frame(df.to_csv, f"allura-inquiries-{stamp}.csv", index=False)
