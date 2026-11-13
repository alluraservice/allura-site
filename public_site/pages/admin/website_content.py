"""
Admin › Website Content   (/admin/website)

Lets Allura staff change the website's words and photos without editing code:

    Site settings  - phone, email, offices, map links, social links, footer text.
                     Used everywhere: top bar, footer, Contact Us, AlluBot, printed letterhead, email footers.
    Home           - hero, section titles, "What we do" cards, stats, "Why Allura", steps, bottom cards
    About Us       - banner, stats, "Who we are", capabilities, timeline, leaders (with photos)
    Services       - banner, the three service areas (with photos), steps, closing band
    AlluBot        - greeting and the wording of every question and answer

How the editor works
- Each tab edits one section. Edits are kept while switching tabs, but only "Save changes" puts them
  on the website (the public pages read utils/site_content.py, cached for up to 20 seconds).
- Lists (stats, timeline, leaders…) have "+ Add" and "Remove" buttons, except lists with a fixed
  layout (the three Home cards, the three service areas and the AlluBot questions).
- "Undo last save" goes back one save. "Restore original" brings back the content the website had
  before this editor existed. Every save is kept in site_content_history.
"""
import copy

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update

import admin_ui as ui
from database.db_handler import get_account_by_email, save_uploaded_image
from utils.media import process_upload, validate_upload
from utils.site_content import (DEFAULTS, get_content, last_saved, restore_defaults, save_content,
                                undo_last_save)

dash.register_page(__name__, path='/admin/website')

TABS = [('settings', 'Site settings'), ('home', 'Home'), ('about', 'About Us'), ('services', 'Services'),
        ('allubot', 'AlluBot')]
TAB_NAMES = dict(TABS)
VIEW_LINKS = {'settings': '/contact_us', 'home': '/home', 'about': '/about_us', 'services': '/services', 'allubot': '/home'}

# ---------------------------------------------------------------------------------------------
# What each tab shows. Entries:
#   ('head', title, note)                               - a card title for the fields below it
#   ('text' | 'area', key, label, help)                 - one field ('area' = several lines)
#   ('list', key, label, help, item_fields, options)    - repeated rows; item_fields use the same shapes
#        options: fixed=True (no add/remove), item='Leader' (row name), max=n, min=n
#   ('photo', key, label, help)                         - only inside lists
# ---------------------------------------------------------------------------------------------
STAT = [('text', 'k', 'Small label', None), ('text', 'v', 'Big value', None), ('text', 's', 'Caption', None)]
TITLE_TEXT = [('text', 'title', 'Title', None), ('area', 'text', 'Text', None)]
POINTS_HELP = "One point per line."

SCHEMA = {
    'settings': [
        ('head', "Contact details", "Shown in the top green bar, the footer, Contact Us, AlluBot, printed "
                                    "quotations and inquiry records, reply signatures and email footers."),
        ('text', 'company_name', "Company name", "Footer copyright line, letterhead and signatures."),
        ('text', 'phone', "Phone number", "Write it the way visitors should read it, e.g. +63 917 770 1820."),
        ('text', 'email', "Email address", None),
        ('text', 'website', "Website address", "Printed on quotations, without https://."),
        ('text', 'location_short', "Short location", "Top green bar and footer, e.g. “BGC, Taguig City, Philippines”."),
        ('head', "Offices and maps", "Shown on Contact Us. The main office address is also the letterhead address."),
        ('area', 'main_office', "Main office address", None),
        ('text', 'main_office_label', "Main office map title", "e.g. Legazpi City"),
        ('area', 'main_map_url', "Main office map link (embed)",
         "Google Maps › Share › Embed a map › copy only the link inside src=\"…\"."),
        ('area', 'satellite_office', "Satellite office address", "Leave empty to hide the satellite office."),
        ('text', 'satellite_office_label', "Satellite office map title", "e.g. Bacoor, Cavite"),
        ('area', 'satellite_map_url', "Satellite office map link (embed)", None),
        ('head', "Social media and footer", None),
        ('text', 'facebook_url', "Facebook page link", None),
        ('text', 'linkedin_url', "LinkedIn page link", None),
        ('area', 'footer_text', "Footer description", "The short paragraph under the logo in the footer."),
    ],
    'home': [
        ('head', "Top banner and introduction", None),
        ('text', 'hero_eyebrow', "Banner small text", None),
        ('area', 'hero_title', "Banner headline", "Keep it short; it is the largest text on the website."),
        ('area', 'hero_lead', "Banner sentence", None),
        ('text', 'intro_title', "Introduction title", None),
        ('area', 'intro_text', "Introduction text", None),
        ('head', "What we do", "The three cards keep their photos, icons and buttons; their words can change."),
        ('text', 'recap_title', "Section title", None),
        ('area', 'recap_text', "Section text", None),
        ('list', 'recap', "Cards", None,
         [('text', 'tag', 'Tag', None), ('text', 'title', 'Title', None), ('area', 'text', 'Text', None),
          ('area', 'points', 'Checklist points', POINTS_HELP)], {'fixed': True, 'item': 'Card'}),
        ('head', "Imaging & radiology carousel", "The cards in the carousel come from the product catalog (Items)."),
        ('text', 'featured_title', "Section title", None),
        ('area', 'featured_text', "Section text", None),
        ('head', "Why Allura", None),
        ('text', 'why_title', "Section title", None),
        ('area', 'why_text', "Section text", None),
        ('list', 'stats', "Stat boxes", "Four fit best on one row.", STAT, {'item': 'Stat', 'max': 6}),
        ('list', 'why', "Reasons", None, TITLE_TEXT, {'item': 'Reason', 'max': 8}),
        ('head', "How working with us works", None),
        ('text', 'steps_title', "Section title", None),
        ('area', 'steps_text', "Section text", None),
        ('list', 'steps', "Steps", None, TITLE_TEXT, {'item': 'Step', 'max': 6}),
        ('head', "Bottom cards", None),
        ('text', 'contact_title', "Contact card title", None),
        ('area', 'contact_text', "Contact card text", None),
        ('text', 'follow_title', "Social media card title", None),
        ('area', 'follow_text', "Social media card text", None),
        ('text', 'allubot_title', "AlluBot card title", None),
        ('area', 'allubot_text', "AlluBot card text", None),
    ],
    'about': [
        ('head', "Banner", None),
        ('area', 'header_title', "Headline", None),
        ('area', 'header_lead', "Sentence under the headline", None),
        ('list', 'stats', "Stat boxes", "Four fit best on one row.", STAT, {'item': 'Stat', 'max': 6}),
        ('head', "Who we are", None),
        ('text', 'who_title', "Title", None),
        ('area', 'who_text', "Text", "Leave an empty line between paragraphs."),
        ('list', 'capabilities', "Strategic capabilities", None, TITLE_TEXT, {'item': 'Capability', 'max': 6}),
        ('head', "History", None),
        ('text', 'timeline_title', "Title", None),
        ('list', 'timeline', "Timeline", "Oldest first.",
         [('text', 'years', 'Years', None), ('text', 'title', 'Title', None), ('area', 'text', 'Text', None)],
         {'item': 'Phase', 'max': 10}),
        ('head', "Leadership", "Photos: a clear, front-facing portrait, at least 600 px wide. Without a photo, "
                               "the person's initials are shown."),
        ('text', 'leaders_title', "Title", None),
        ('list', 'leaders', "Leaders", None,
         [('text', 'name', 'Full name', None), ('text', 'role', 'Position', None), ('photo', 'photo', 'Photo', None)],
         {'item': 'Leader', 'max': 12}),
    ],
    'services': [
        ('head', "Banner", None),
        ('area', 'header_lead', "Sentence under “Services”", None),
        ('text', 'banner_title', "Service inquiry card title", "The card with the Service Inquiry button."),
        ('area', 'banner_text', "Service inquiry card text", None),
        ('head', "What we service", "Three service areas. The first photo is also the background of the "
                                    "Service inquiry card. Use real Allura photos where possible."),
        ('text', 'areas_title', "Section title", None),
        ('area', 'areas_text', "Section text", None),
        ('list', 'areas', "Service areas", None,
         [('text', 'title', 'Title', None), ('area', 'text', 'Text', None), ('area', 'points', 'Checklist points', POINTS_HELP),
          ('photo', 'photo', 'Photo', None)], {'fixed': True, 'item': 'Service area'}),
        ('head', "How it works", None),
        ('text', 'steps_title', "Title", None),
        ('list', 'steps', "Steps", None, TITLE_TEXT, {'item': 'Step', 'max': 6}),
        ('head', "Closing band", None),
        ('text', 'lifecycle_title', "Title", None),
        ('area', 'lifecycle_text', "Text", None),
    ],
    'allubot': [
        ('head', "Greeting", "AlluBot's first message. You can write {phone}, {email}, {main_office} or "
                             "{satellite_office}; they are replaced with the details in Site settings."),
        ('area', 'greeting', "Greeting", None),
        ('head', "Questions and answers", "Change the words only. Adding a new question or changing which questions "
                                          "follow each other is done in the code (SOP-12). Clear a field to go back "
                                          "to the original wording."),
        ('list', 'questions', "Questions", None,
         [('text', 'label', 'Question (button text)', None), ('area', 'answer', 'Answer', None)],
         {'fixed': True, 'item': 'Question', 'show_key': True}),
    ],
}


# =====================================================================
# Draft <-> stored content
# =====================================================================
def _allubot_tree():
    import allubot
    return allubot.TREE


def _load(section):
    """The section as the editor shows it."""
    data = get_content(section)
    if section == 'allubot':
        saved = data.get('answers') or {}
        data = {'greeting': data.get('greeting') or '', 'questions': [
            {'key': k, 'label': (saved.get(k) or {}).get('label') or node['label'],
             'answer': (saved.get(k) or {}).get('answer') or node['answer']}
            for k, node in _allubot_tree().items()]}
    return data


def _to_store(section, data):
    """The editor's data as it is saved (AlluBot keeps only what differs from the code)."""
    if section != 'allubot':
        return data
    tree = _allubot_tree()
    answers = {}
    for q in data.get('questions') or []:
        node = tree.get(q.get('key'))
        if not node:
            continue
        diff = {}
        if (q.get('label') or '').strip() and q['label'].strip() != node['label']:
            diff['label'] = q['label'].strip()
        if (q.get('answer') or '').strip() and q['answer'].strip() != node['answer']:
            diff['answer'] = q['answer'].strip()
        if diff:
            answers[q['key']] = diff
    return {'greeting': (data.get('greeting') or '').strip(), 'answers': answers}


def _set_path(data, path, value):
    parts = path.split('.')
    obj = data
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    last = parts[-1]
    if isinstance(obj, list):
        obj[int(last)] = value
    else:
        obj[last] = value


def _get_path(data, path):
    obj = data
    for p in path.split('.'):
        obj = obj[int(p)] if isinstance(obj, list) else obj.get(p)
    return obj


def _apply_inputs(data, ids, values):
    """Copies what is typed in the form into the draft."""
    for id_, val in zip(ids or [], values or []):
        try:
            _set_path(data, id_['path'], val if val is not None else '')
        except (KeyError, IndexError, ValueError, TypeError, AttributeError):
            pass
    return data


# =====================================================================
# Rendering
# =====================================================================
def _field_input(kind, path, label, help_text, value):
    if kind == 'area':
        rows = max(2, min(8, len(str(value or '')) // 70 + str(value or '').count('\n') + 1))
        comp = dbc.Textarea(id={'type': 'wc-in', 'path': path}, value=value or '', className="a-input",
                            style={'height': f'{rows * 26 + 18}px'})
    else:
        comp = dbc.Input(id={'type': 'wc-in', 'path': path}, value=value or '', className="a-input")
    return html.Div([html.Label(label, className="a-label"), comp,
                     html.Div(help_text, className="a-help") if help_text else None],
                    className="wc-field" + (" full" if kind == 'area' else ""))


def _photo_field(path, label, value):
    has = bool(str(value or '').strip())
    return html.Div([
        html.Label(label, className="a-label"),
        html.Div([
            html.Img(src=value, className="wc-photo-thumb") if has else html.Div("No photo", className="wc-photo-empty"),
            html.Div([
                dcc.Upload(html.Span("Upload a new photo", className="a-btn a-btn-outline a-btn-sm"),
                           id={'type': 'wc-upload', 'path': path}, multiple=False, accept="image/*", max_size=-1),
                html.Button("Remove photo", id={'type': 'wc-photo-del', 'path': path}, n_clicks=0,
                            className="a-btn a-btn-danger a-btn-sm") if has else None,
                html.Div("JPG, PNG or WEBP, up to 8 MB. Large photos are resized automatically.", className="a-help"),
            ], className="wc-photo-tools"),
        ], className="wc-photo"),
    ], className="wc-field full")


def _list_block(section, key, label, help_text, fields, opts, rows):
    rows = rows or []
    fixed = opts.get('fixed')
    blocks = []
    for i, row in enumerate(rows):
        base = f"{key}.{i}"
        head = [html.B(f"{opts.get('item', 'Row')} {i + 1}")]
        if opts.get('show_key'):
            head.append(html.Span(row.get('key'), className="chip plain chip-ref ms-2"))
        if not fixed:
            head.append(html.Div([
                html.Button("↑", id={'type': 'wc-up', 'path': base}, n_clicks=0, title="Move up",
                            className="a-btn a-btn-outline a-btn-sm", disabled=i == 0),
                html.Button("Remove", id={'type': 'wc-del', 'path': base}, n_clicks=0,
                            className="a-btn a-btn-danger a-btn-sm",
                            disabled=len(rows) <= opts.get('min', 1)),
            ], className="ms-auto d-flex gap-2"))
        inner = []
        for f in fields:
            if f[0] == 'photo':
                inner.append(_photo_field(f"{base}.{f[1]}", f[2], row.get(f[1])))
            else:
                inner.append(_field_input(f[0], f"{base}.{f[1]}", f[2], f[3], row.get(f[1])))
        blocks.append(html.Div([html.Div(head, className="wc-row-head"), html.Div(inner, className="form-row")],
                               className="wc-row"))
    add = None
    if not fixed and len(rows) < opts.get('max', 20):
        add = html.Button(f"+ Add {opts.get('item', 'row').lower()}", id={'type': 'wc-add', 'path': key}, n_clicks=0,
                          className="a-btn a-btn-outline a-btn-sm mt-2")
    return html.Div([
        html.Label(label, className="a-label"),
        html.Div(help_text, className="a-help mb-2") if help_text else None,
        html.Div(blocks, className="wc-rows" + (" wc-rows-scroll" if opts.get('show_key') else "")),
        add,
    ], className="wc-field full wc-list")


def _render_form(section, data):
    cards, current = [], None

    def flush():
        if current:
            cards.append(html.Div([
                html.Div([html.H6(current['title'])], className="a-card-head"),
                html.Div([html.Div(current['note'], className="a-help mb-3") if current['note'] else None,
                          html.Div(current['fields'], className="form-row")], className="a-card-body"),
            ], className="a-card mb-3"))

    for entry in SCHEMA[section]:
        kind = entry[0]
        if kind == 'head':
            flush()
            current = {'title': entry[1], 'note': entry[2], 'fields': []}
            continue
        if current is None:
            current = {'title': TAB_NAMES[section], 'note': None, 'fields': []}
        if kind == 'list':
            _, key, label, help_text, fields, opts = entry
            current['fields'].append(_list_block(section, key, label, help_text, fields, opts, data.get(key)))
        else:
            _, key, label, help_text = entry
            current['fields'].append(_field_input(kind, key, label, help_text, data.get(key)))
    flush()
    return cards


def _status(section):
    row = last_saved(section)
    if not row:
        return html.Span(["This section shows the ", html.B("original website content"), " (never changed here)."])
    who = row.get('updated_by') or 'an admin'
    return html.Span(["Last saved ", html.B(ui.fmt_date(row.get('updated_at'), with_time=True)), f" by {who}."])


def _empty_list_row(fields):
    return {f[1]: '' for f in fields}


def _list_spec(section, key):
    for e in SCHEMA[section]:
        if e[0] == 'list' and e[1] == key:
            return e
    return None


# =====================================================================
# Layout
# =====================================================================
def layout(*args, **kwargs):
    header = ui.page_header(
        "Website Content",
        "Change the words, contact details and photos on the public website. Products are managed in Items.",
        crumbs="Admin  /  Website Content",
        actions=[html.A("View website ↗", href='/home', target='_blank', className="a-btn a-btn-light")],
    )
    toolbar = html.Div([
        html.Div([dbc.Tabs([dbc.Tab(label=label, tab_id=key) for key, label in TABS], id='wc-tabs',
                           active_tab='settings', className="wc-tabs")]),
        html.Div([
            html.Div(id='wc-status', className="text-muted small"),
            html.Div([
                html.A("View page ↗", id='wc-view', href='/contact_us', target='_blank', className="a-btn a-btn-outline a-btn-sm"),
                html.Button("Undo last save", id='wc-undo', n_clicks=0, className="a-btn a-btn-outline a-btn-sm"),
                html.Button("Restore original", id='wc-restore-open', n_clicks=0, className="a-btn a-btn-danger a-btn-sm"),
                html.Button("Save changes", id='wc-save', n_clicks=0, className="a-btn a-btn-primary"),
            ], className="d-flex flex-wrap gap-2 align-items-center"),
        ], className="wc-toolbar"),
        html.Div(id='wc-feedback'),
    ], className="wc-sticky")

    restore_modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Restore the original content?", className="fw-bold"), close_button=True),
        dbc.ModalBody([
            html.P(id='wc-restore-text', className="text-muted"),
            html.Div([
                html.Button("Cancel", id='wc-restore-cancel', n_clicks=0, className="a-btn a-btn-outline"),
                html.Button("Restore original", id='wc-restore-yes', n_clicks=0, className="a-btn a-btn-danger"),
            ], className="d-flex justify-content-end gap-2"),
        ]),
    ], id='wc-restore-modal', is_open=False, centered=True, className="a-modal")

    return html.Div([
        dcc.Store(id='wc-drafts', data={}),
        dcc.Store(id='wc-current', data=None),
        header,
        html.Div([toolbar, html.Div(id='wc-form')], className="admin-container wc-shell"),
        restore_modal,
    ], className="admin-shell")


# =====================================================================
# Callbacks
# =====================================================================
@callback(
    Output('wc-restore-modal', 'is_open'),
    Output('wc-restore-text', 'children'),
    Input('wc-restore-open', 'n_clicks'),
    Input('wc-restore-cancel', 'n_clicks'),
    Input('wc-restore-yes', 'n_clicks'),
    State('wc-tabs', 'active_tab'),
    prevent_initial_call=True,
)
def toggle_restore(_o, _c, _y, tab):
    if ctx.triggered_id == 'wc-restore-open' and _o:
        return True, (f"The {TAB_NAMES.get(tab, '')} section goes back to the content the website had before the "
                      "Website Content editor was added. Unsaved edits on this tab are discarded. "
                      "Earlier saves stay in the history, so “Undo last save” can bring the latest one back.")
    return False, no_update


@callback(
    Output('wc-form', 'children'),
    Output('wc-drafts', 'data'),
    Output('wc-current', 'data'),
    Output('wc-status', 'children'),
    Output('wc-feedback', 'children'),
    Output('wc-view', 'href'),
    Input('wc-tabs', 'active_tab'),
    Input('wc-save', 'n_clicks'),
    Input('wc-undo', 'n_clicks'),
    Input('wc-restore-yes', 'n_clicks'),
    Input({'type': 'wc-add', 'path': ALL}, 'n_clicks'),
    Input({'type': 'wc-del', 'path': ALL}, 'n_clicks'),
    Input({'type': 'wc-up', 'path': ALL}, 'n_clicks'),
    Input({'type': 'wc-upload', 'path': ALL}, 'contents'),
    Input({'type': 'wc-photo-del', 'path': ALL}, 'n_clicks'),
    State({'type': 'wc-upload', 'path': ALL}, 'filename'),
    State({'type': 'wc-in', 'path': ALL}, 'value'),
    State({'type': 'wc-in', 'path': ALL}, 'id'),
    State('wc-drafts', 'data'),
    State('wc-current', 'data'),
    State('session-admin-email', 'data'),
    State('session-admin-name', 'data'),
)
def editor(tab, _save, _undo, _restore, _add, _del, _up, uploads, _pdel, filenames, values, ids,
           drafts, current, email, name):
    tab = tab or 'settings'
    drafts = drafts or {}
    trig = ctx.triggered_id
    trig_value = ctx.triggered[0].get('value') if ctx.triggered else None
    # New buttons being drawn (n_clicks 0 / no file) are not clicks
    if isinstance(trig, dict) and not trig_value:
        raise dash.exceptions.PreventUpdate

    # 1. Keep what was typed on the tab that was open
    if current and current in SCHEMA:
        base = drafts.get(current) or _load(current)
        drafts[current] = _apply_inputs(copy.deepcopy(base), ids, values)

    if tab not in drafts:
        drafts[tab] = _load(tab)
    data = drafts[tab]
    feedback = no_update
    who = name or email or 'admin'
    if email:
        me = get_account_by_email(email) or {}
        who = me.get('name') or who

    if trig == 'wc-save' and _save:
        problems = _validate(tab, data)
        if problems:
            feedback = ui.alert(["Not saved: ", ", ".join(problems), "."], 'warn')
        elif save_content(tab, _to_store(tab, data), saved_by=who):
            feedback = ui.alert([html.B("Saved. "), "The website shows the change within a minute. ",
                                 html.A("View page ↗", href=VIEW_LINKS[tab], target='_blank')], 'ok')
            drafts[tab] = _load(tab)
        else:
            feedback = ui.alert("The changes couldn't be saved. Check the database connection and try again.", 'err')

    elif trig == 'wc-undo' and _undo:
        if undo_last_save(tab, saved_by=who):
            drafts[tab] = _load(tab)
            feedback = ui.alert("The last save was undone. The website shows the previous version.", 'ok')
        else:
            feedback = ui.alert("There is no earlier save to go back to.", 'warn')

    elif trig == 'wc-restore-yes' and _restore:
        restore_defaults(tab, saved_by=who)
        drafts[tab] = _load(tab)
        feedback = ui.alert("The original content is back on the website for this section.", 'ok')

    elif isinstance(trig, dict):
        kind, path = trig['type'], trig['path']
        if kind == 'wc-add':
            spec = _list_spec(tab, path)
            if spec:
                data.setdefault(path, []).append(_empty_list_row(spec[4]))
        elif kind in ('wc-del', 'wc-up'):
            key, idx = path.rsplit('.', 1)
            rows, idx = data.get(key) or [], int(idx)
            if kind == 'wc-del' and 0 <= idx < len(rows):
                rows.pop(idx)
            elif kind == 'wc-up' and 0 < idx < len(rows):
                rows[idx - 1], rows[idx] = rows[idx], rows[idx - 1]
        elif kind == 'wc-photo-del':
            _set_path(data, path, '')
            feedback = ui.alert("Photo removed. Click “Save changes” to update the website.", 'ok')
        elif kind == 'wc-upload':
            all_ids = [i['id']['path'] for i in ctx.inputs_list[7]]
            pos = all_ids.index(path) if path in all_ids else -1
            contents = uploads[pos] if pos >= 0 else None
            fname = (filenames[pos] if pos >= 0 and filenames else None) or 'photo'
            error = validate_upload(contents, fname)
            if error:
                feedback = ui.alert(error, 'err')
            else:
                mime, blob, w, h = process_upload(contents)
                image_id = save_uploaded_image(fname, mime, blob, w, h)
                if image_id:
                    _set_path(data, path, f"/media/{image_id}")
                    feedback = ui.alert("Photo uploaded. Click “Save changes” to put it on the website.", 'ok')
                else:
                    feedback = ui.alert("The photo couldn't be saved. Please try a different file.", 'err')

    drafts[tab] = data
    if trig == 'wc-tabs':
        feedback = None
    return _render_form(tab, data), drafts, tab, _status(tab), feedback, VIEW_LINKS[tab]


def _validate(section, data):
    problems = []
    if section == 'settings':
        for key, label in (('company_name', 'company name'), ('phone', 'phone number'), ('email', 'email address'),
                           ('main_office', 'main office address')):
            if not str(data.get(key) or '').strip():
                problems.append(f"fill in the {label}")
        if data.get('email') and '@' not in data['email']:
            problems.append("check the email address")
        for key, label in (('facebook_url', 'Facebook'), ('linkedin_url', 'LinkedIn'),
                           ('main_map_url', 'main office map'), ('satellite_map_url', 'satellite office map')):
            v = str(data.get(key) or '').strip()
            if v and not v.startswith('https://'):
                problems.append(f"the {label} link must start with https://")
    if section == 'about':
        if not any(str(r.get('name') or '').strip() for r in data.get('leaders') or []):
            problems.append("add at least one leader")
    for entry in SCHEMA[section]:
        if entry[0] in ('text', 'area') and section != 'allubot' and entry[1] in DEFAULTS.get(section, {}):
            if entry[1].endswith('_title') and not str(data.get(entry[1]) or '').strip():
                problems.append(f"fill in “{entry[2]}”")
    return problems
