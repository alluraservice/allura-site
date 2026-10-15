"""
Add / edit an item.   /admin/items/add          -> new item
                      /admin/items/add?id=12   -> edit item 12
                      /admin/items/add?modality=3 -> new item with the modality pre-selected

Photos are uploaded as files (drag & drop or browse). On save they're resized, stored in the
database and the item's image_url becomes '/media/<id>' (see utils/media.py).
The right-hand column previews the item exactly as visitors will see it on the product list.
"""
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

import admin_ui as ui
from database.db_handler import (DEFAULT_ITEM_IMAGE, create_item, delete_item, get_categories_with_types,
                                 get_item_by_id, save_uploaded_image, update_item_full)
from utils.media import MAX_UPLOAD_BYTES, process_upload, validate_upload

dash.register_page(__name__, path='/admin/items/add')

NONE = '_'   # dbc.Select can't show an option whose value is ''


def _product_categories():
    cats = [c for c in (get_categories_with_types() or []) if 'service' not in str(c.get('name', '')).lower()]
    for c in cats:
        c['types'] = [t for t in (c.get('types') or []) if 'service' not in str(t.get('name', '')).lower()]
    return cats


def _field(label, component, help_text=None, required=False):
    return html.Div([
        html.Label([label, html.Span(" *", style={'color': 'var(--st-urgent)'}) if required else None], className="a-label"),
        component,
        html.Div(help_text, className="a-help") if help_text else None,
    ])


def layout():
    cats = _product_categories()
    modality_map = {str(c['id']): [{'label': t['name'], 'value': str(t['id'])} for t in c['types']] for c in cats}

    details = html.Div([
        html.Div(html.H6("Item details"), className="a-card-head"),
        html.Div([
            _field("Item name", dbc.Input(id='item-f-name', className="a-input", placeholder="e.g. Affiniti 70",
                                          maxLength=150), required=True),
            html.Div([
                _field("Category", dbc.Select(id='item-f-category', className="a-input", value=NONE,
                                              options=[{'label': 'Choose a category', 'value': NONE}] +
                                                      [{'label': c['name'], 'value': str(c['id'])} for c in cats]),
                       required=True),
                _field("Modality", dbc.Select(id='item-f-modality', className="a-input", value=NONE,
                                              options=[{'label': 'Choose a category first', 'value': NONE}]),
                       "The product list groups items by modality.", required=True),
            ], className="form-grid mt-3"),
            html.Div(_field("Description", dbc.Textarea(id='item-f-desc', className="a-input", style={'height': '150px'},
                                                        placeholder="What it is, key features, typical use. Shown under the item name on the product page."),
                            html.Span(id='item-f-desc-count')), className="mt-3"),
        ], className="a-card-body"),
    ], className="a-card mb-3")

    photo = html.Div([
        html.Div([html.H6("Photo"), html.Span("JPG, PNG, WEBP or GIF · up to "
                                              f"{MAX_UPLOAD_BYTES // 1048576} MB", className="text-muted", style={'fontSize': '.78rem'})],
                 className="a-card-head"),
        html.Div([
            # No 'accept' filter on purpose: the browser would silently ignore a wrong file;
            # instead every file is checked and the admin gets a clear message.
            dcc.Upload(id='item-f-upload', children=html.Div(id='item-photo-drop-inner'), multiple=False,
                       className="photo-drop", className_active="photo-drop dragging",
                       max_size=-1),
            html.Div([
                html.Button("Remove photo", id='item-photo-remove', n_clicks=0, className="a-btn a-btn-outline a-btn-sm"),
                html.Span("Tip: a product on a plain white or transparent background looks best on the cards.",
                          className="a-help m-0"),
            ], id='item-photo-tools', className="d-flex align-items-center gap-3 mt-2 flex-wrap", style={'display': 'none'}),
            html.Div(id='item-photo-error', className="mt-2"),
        ], className="a-card-body"),
    ], className="a-card mb-3")

    visibility = html.Div([
        html.Div(html.H6("Visibility"), className="a-card-head"),
        html.Div([
            html.Div([html.Div([html.B("Show on website"), html.Span("When off, the item is hidden from the public product list.")], className="t"),
                      dbc.Switch(id='item-f-active', value=True)], className="switch-row"),
            html.Div([html.Div([html.B("Featured"), html.Span("Mark as a highlighted product.")], className="t"),
                      dbc.Switch(id='item-f-featured', value=False)], className="switch-row"),
        ], className="a-card-body py-1"),
    ], className="a-card mb-3")

    danger = html.Div([
        html.Div(html.H6("Delete item"), className="a-card-head"),
        html.Div([
            html.Span("Permanently removes the item and its uploaded photo. This can't be undone. "
                      "To take it off the website temporarily, turn off “Show on website” instead.",
                      className="text-muted", style={'fontSize': '.84rem'}),
            dcc.ConfirmDialogProvider(html.Button("Delete item", className="a-btn a-btn-danger"),
                                      id='item-f-delete', message="Delete this item permanently? This can't be undone."),
        ], className="a-card-body d-flex justify-content-between align-items-center gap-3 flex-wrap"),
    ], id='item-danger-zone', className="a-card danger-zone mb-3", style={'display': 'none'})

    preview = html.Div([
        html.Div([
            html.Div([html.H6("Preview"), html.Span("How visitors will see it", className="text-muted", style={'fontSize': '.78rem'})],
                     className="a-card-head"),
            html.Div([
                html.Div("Product list", className="a-section-title"),
                html.Div(id='item-preview-card', className="preview-card-wrap mb-3"),
                html.Div("Product page", className="a-section-title"),
                html.Div(id='item-preview-detail'),
            ], className="a-card-body"),
        ], className="a-card"),
    ], className="preview-col")

    return html.Div([
        dcc.Location(id='item-f-url', refresh=False),
        dcc.Location(id='item-f-redirect', refresh=True),
        dcc.Store(id='item-f-id'),
        dcc.Store(id='item-f-modality-map', data=modality_map),
        dcc.Store(id='item-photo-current'),            # existing image_url when editing
        dcc.Store(id='item-photo-new'),                 # {'contents': data-uri, 'filename': ...} not yet saved

        ui.page_header("Add item", "Add a product to the catalog.", crumbs="Admin  /  Items  /  Add item",
                       title_id='item-f-title', crumbs_id='item-f-crumbs',
                       actions=[dcc.Link("← Back to items", id='item-f-back', href='/admin/items', className="a-btn a-btn-light")]),
        html.Div([
            html.Div([
                html.Div([
                    details, photo, visibility, danger,
                    html.Div(id='item-f-feedback'),
                    html.Div([
                        dcc.Link("Cancel", id='item-f-cancel', href='/admin/items', className="a-btn a-btn-outline"),
                        html.Button("Save item", id='item-f-save', n_clicks=0, className="a-btn a-btn-primary"),
                    ], className="editor-actions"),
                ]),
                preview,
            ], className="item-editor"),
        ], className="admin-container"),
    ], className="admin-shell")


# ---------------------------------------------------------------------
# Load (edit mode) or prefill (new item)
# ---------------------------------------------------------------------
@callback(
    Output('item-f-id', 'data'),
    Output('item-f-title', 'children'),
    Output('item-f-crumbs', 'children'),
    Output('item-f-name', 'value'),
    Output('item-f-category', 'value'),
    Output('item-f-modality', 'value'),
    Output('item-f-desc', 'value'),
    Output('item-photo-current', 'data'),
    Output('item-f-active', 'value'),
    Output('item-f-featured', 'value'),
    Output('item-danger-zone', 'style'),
    Output('item-f-cancel', 'href'),
    Output('item-f-back', 'href'),
    Input('item-f-url', 'search'),
    State('item-f-modality-map', 'data'),
)
def load_item(search, modality_map):
    q = parse_qs((search or '').lstrip('?'))
    item_id = q.get('id', [None])[0]
    if item_id and str(item_id).isdigit():
        it = get_item_by_id(int(item_id))
        if it:
            back = f"/admin/item-details?id={it['id']}"
            current = it.get('image_url')
            if not current or str(current).strip() in ('', 'None', DEFAULT_ITEM_IMAGE):
                current = None
            return (it['id'], "Edit item", f"Admin  /  Items  /  {it['name']}", it['name'],
                    str(it['category_id']) if it.get('category_id') else NONE,
                    str(it['modality_id']) if it.get('modality_id') else NONE,
                    it.get('description') or '', current, bool(it.get('is_active', True)), bool(it.get('is_featured')),
                    {}, back, back)

    # New item: optionally pre-select the modality the admin was browsing
    cat_val, mod_val = NONE, NONE
    mod = q.get('modality', [None])[0]
    if mod:
        for cid, mods in (modality_map or {}).items():
            if any(m['value'] == str(mod) for m in mods):
                cat_val, mod_val = cid, str(mod)
    cat = q.get('category', [None])[0]
    if cat and cat_val == NONE and str(cat) in (modality_map or {}):
        cat_val = str(cat)
    return (None, "Add item", "Admin  /  Items  /  Add item", '', cat_val, mod_val, '', None, True, False,
            {'display': 'none'}, '/admin/items', '/admin/items')


@callback(
    Output('item-f-modality', 'options'),
    Output('item-f-modality', 'value', allow_duplicate=True),
    Input('item-f-category', 'value'),
    State('item-f-modality', 'value'),
    State('item-f-modality-map', 'data'),
    prevent_initial_call='initial_duplicate',
)
def modality_options(category, current, modality_map):
    mods = (modality_map or {}).get(category or '', [])
    if not mods:
        placeholder = 'Choose a category first' if category in (None, NONE) else 'No modalities in this category'
        return [{'label': placeholder, 'value': NONE}], NONE
    opts = [{'label': 'Choose a modality', 'value': NONE}] + mods
    keep = current if any(m['value'] == current for m in mods) else NONE
    return opts, keep


@callback(Output('item-f-desc-count', 'children'), Input('item-f-desc', 'value'))
def desc_count(text):
    n = len(text or '')
    return f"{n} characters" if n else "Plain text."


# ---------------------------------------------------------------------
# Photo: upload / remove
# ---------------------------------------------------------------------
@callback(
    Output('item-photo-new', 'data'),
    Output('item-photo-error', 'children'),
    Output('item-f-upload', 'contents'),
    Input('item-f-upload', 'contents'),
    State('item-f-upload', 'filename'),
    prevent_initial_call=True,
)
def receive_upload(contents, filename):
    if not contents:
        raise dash.exceptions.PreventUpdate
    err = validate_upload(contents, filename or 'This file')
    if err:
        return no_update, ui.alert(err, 'err'), None
    # Clear the Upload's own copy so picking the same file again still triggers
    return {'contents': contents, 'filename': filename}, None, None


@callback(
    Output('item-photo-new', 'data', allow_duplicate=True),
    Output('item-photo-current', 'data', allow_duplicate=True),
    Input('item-photo-remove', 'n_clicks'),
    prevent_initial_call=True,
)
def remove_photo(n):
    if not n:
        raise dash.exceptions.PreventUpdate
    return None, None


# ---------------------------------------------------------------------
# Dropzone content + live preview
# ---------------------------------------------------------------------
@callback(
    Output('item-photo-drop-inner', 'children'),
    Output('item-photo-tools', 'style'),
    Output('item-preview-card', 'children'),
    Output('item-preview-detail', 'children'),
    Input('item-f-name', 'value'),
    Input('item-f-desc', 'value'),
    Input('item-f-category', 'value'),
    Input('item-f-modality', 'value'),
    Input('item-photo-new', 'data'),
    Input('item-photo-current', 'data'),
    State('item-f-category', 'options'),
    State('item-f-modality', 'options'),
)
def render_preview(name, desc, category, modality, new_photo, current, cat_opts, mod_opts):
    if new_photo:
        src, label, sub = new_photo['contents'], new_photo['filename'], "New photo · saved when you click Save item"
    elif current:
        src, label, sub = ui.item_image_src(current), "Current photo", "Drop a new file here to replace it"
    else:
        src = None

    if src:
        drop = html.Div([
            html.Div(html.Img(src=src, alt=''), className="thumb"),
            html.Div([html.B(label), html.Span(sub), html.Div("Click or drop another photo to replace", className="a-help")],
                     className="meta"),
        ], className="photo-current")
        tools = {'display': 'flex'}
    else:
        drop = html.Div([
            html.Div("⬆", className="big"),
            html.Div([html.B("Drag a photo here"), " or ", html.Span("browse your files", style={'color': 'var(--green)', 'textDecoration': 'underline'})]),
            html.Div("It's resized automatically, so phone photos are fine.", className="hint mt-1"),
        ])
        tools = {'display': 'none'}

    title = (name or '').strip() or "Item name"
    img = src or DEFAULT_ITEM_IMAGE
    card = html.Div([
        html.Div(html.Img(src=img, alt=title, className="item-card-img"), className="item-card-img-container"),
        html.P(title, className="item-card-title"),
    ], className="item-card")

    def label_of(opts, v):
        return next((o['label'] for o in (opts or []) if o['value'] == v and v != NONE), '—')
    text = (desc or '').strip() or "No description yet."
    detail = html.Div([
        html.Div(html.Img(src=img, alt=''), className="img"),
        html.Div([
            html.H5(title),
            html.P(text if len(text) <= 180 else text[:180].rsplit(' ', 1)[0] + '…'),
            html.Div([html.B("Category: "), label_of(cat_opts, category)], className="meta"),
            html.Div([html.B("Modality: "), label_of(mod_opts, modality)], className="meta"),
        ]),
    ], className="preview-detail")
    return drop, tools, card, detail


# ---------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------
@callback(
    Output('item-f-feedback', 'children'),
    Output('item-f-redirect', 'href'),
    Input('item-f-save', 'n_clicks'),
    State('item-f-id', 'data'),
    State('item-f-name', 'value'),
    State('item-f-modality', 'value'),
    State('item-f-desc', 'value'),
    State('item-photo-new', 'data'),
    State('item-photo-current', 'data'),
    State('item-f-active', 'value'),
    State('item-f-featured', 'value'),
    prevent_initial_call=True,
)
def save_item(n, item_id, name, modality, desc, new_photo, current, active, featured):
    if not n:
        raise dash.exceptions.PreventUpdate
    name = (name or '').strip()
    problems = []
    if not name:
        problems.append("enter the item name")
    if not modality or modality == NONE:
        problems.append("choose a category and modality")
    if problems:
        return ui.alert("Please " + " and ".join(problems) + ".", 'warn'), no_update

    image_url = current or DEFAULT_ITEM_IMAGE
    if new_photo:
        try:
            mime, data, w, h = process_upload(new_photo['contents'])
            img_id = save_uploaded_image(new_photo.get('filename'), mime, data, w, h)
        except Exception as e:
            print(f"[add_item] photo processing failed: {e}")
            img_id = None
        if not img_id:
            return ui.alert("The photo couldn't be saved. Please try a different file.", 'err'), no_update
        image_url = f"/media/{img_id}"

    desc = (desc or '').strip()
    if item_id:
        ok = update_item_full(item_id, name, int(modality), desc, image_url, bool(active), bool(featured))
        target = item_id if ok else None
    else:
        target = create_item(name, int(modality), desc, image_url, bool(active), bool(featured))
    if not target:
        return ui.alert("The item couldn't be saved. Check the database connection and try again.", 'err'), no_update
    return None, f"/admin/item-details?id={target}&saved=1"


@callback(
    Output('item-f-redirect', 'href', allow_duplicate=True),
    Input('item-f-delete', 'submit_n_clicks'),
    State('item-f-id', 'data'),
    prevent_initial_call=True,
)
def delete_from_editor(n, item_id):
    if not n or not item_id:
        raise dash.exceptions.PreventUpdate
    delete_item(item_id)
    return "/admin/items?deleted=1"
