"""
Public product page — same layout as the admin Item details page (admin/items/item_details.py):
page header, a bar with breadcrumbs, and the product card.
"Contact Sales" opens the quote form; submitted quotes are saved as Product Page inquiries
(with the product name), and the customer gets a reference number.
"""
from urllib.parse import parse_qs

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import SOURCE_PRODUCT, get_item_by_id
from inquiry_forms import submit_inquiry

dash.register_page(__name__, path='/product-details', title='Allura Enterprise - Product Details')

FIELD_IDS = ['inquiry-customer', 'inquiry-address', 'inquiry-person', 'inquiry-dept', 'inquiry-phone',
             'inquiry-email', 'inquiry-machine', 'inquiry-remarks']


def _label(text):
    return html.Label(text, className="a-label")


def _field(label, component):
    return html.Div([_label(label), component])


# ==========================================
# PAGE LAYOUT
# ==========================================
def layout(id=None, **kwargs):
    quote_modal = dbc.Modal([
        dbc.ModalBody([
            html.Div([
                html.Div([
                    html.Img(id='modal-product-img', src=''),
                    html.Div([
                        html.H4(id='modal-product-title'),
                        html.P("Send us your details and our sales team will prepare a quotation.", className="modal-sub mb-0"),
                    ]),
                ], className="modal-title-row"),
                html.Button(type="button", id="btn-close-quote-modal", className="btn-close ms-auto",
                            **{"aria-label": "Close"}),
            ], className="d-flex align-items-start gap-3 mb-3"),

            html.Div([
                _field("Customer / Hospital Name", dbc.Input(id='inquiry-customer', type='text', placeholder='Enter your customer/hospital name here', className='input-box')),
                _field("Office Address", dbc.Input(id='inquiry-address', type='text', placeholder='Enter your address here', className='input-box')),
                _field("Contact Person", dbc.Input(id='inquiry-person', type='text', placeholder='Enter your contact person here', className='input-box')),
                _field("Department and Title", dbc.Input(id='inquiry-dept', type='text', placeholder='Enter your department and title here', className='input-box')),
                _field("Contact No.", dbc.Input(id='inquiry-phone', type='text', placeholder='Enter your contact no. here', className='input-box')),
                _field("Email Address", dbc.Input(id='inquiry-email', type='email', placeholder='Enter your email address here', className='input-box')),
                _field("Machine Inquiry", dbc.Textarea(id='inquiry-machine', placeholder='What would you like to know? (leave blank for a standard quotation)', className='input-box', style={'height': '110px'})),
                _field("Remarks (Optional)", dbc.Textarea(id='inquiry-remarks', placeholder='Enter your remarks here', className='input-box', style={'height': '110px'})),
            ], className="form-row"),

            html.Div(id='quote-inquiry-feedback', className="mt-3"),
            html.Div([
                html.Button("Submit", id='btn-submit-inquiry', n_clicks=0, className='a-btn a-btn-primary a-btn-lg'),
            ], className="modal-actions"),
        ])
    ], id='quote-inquiry-modal', size='lg', centered=True, is_open=False, className="a-modal")

    return html.Div([
        ui.page_header("Product details", "Specifications and quotations from our sales team.",
                       crumbs=[("Home", "/home"), ("Products", "/products"), ("Details", None)]),
        html.Div([
            html.Div(id='quote-inquiry-toast'),
            html.Div(id='product-detail-content'),
        ], className="site-container narrow"),
        quote_modal,
    ], className="site-shell")


def _item_id(search):
    q = parse_qs((search or '').lstrip('?'))
    try:
        return int(q.get('id', [None])[0])
    except (TypeError, ValueError):
        return None


# ==========================================
# CALLBACK: RENDER PRODUCT DETAILS
# ==========================================
@callback(
    Output('product-detail-content', 'children'),
    Input('url', 'search')
)
def update_product_detail_page(search):
    item_id = _item_id(search)
    item = None
    if item_id:
        try:
            item = get_item_by_id(item_id)
        except Exception as e:
            print(f"Error loading item details: {e}")

    # Hidden items are treated as not found on the public site
    if not item or not ui.is_visible(item):
        return html.Div([
            html.H3("Product Not Found", className="text-muted mb-2"),
            html.P("This product may have been moved or is no longer listed.", className="text-muted"),
            dcc.Link("Back to Product List", href="/products/all", className="a-btn a-btn-primary a-btn-lg mt-2"),
        ], className="a-card site-card-pad text-center py-5")

    item_name = item.get("name") or item.get("title") or "Product Details"
    short_desc = item.get("short_description") or item.get("description") or "No description available."
    long_desc = item.get("long_description") or ""
    category_name = item.get("category_name") or "Products"
    modality_name = item.get("modality_name") or "General"
    image_path = ui.item_image_src(item.get("image_url") or item.get("image"))
    is_fallback = "product_icon" in image_path
    img_class = "img-fluid rounded-4 shadow-sm product-icon" if is_fallback else "img-fluid rounded-4 shadow-sm"

    cat_href = ui.catalog_href('category', item.get('category_id'))
    mod_href = ui.catalog_href('modality', item.get('modality_id'))

    detail_bar = html.Div([
        dcc.Link("Products", href="/products/all", className="crumb"), html.Span("/", className="sep"),
        dcc.Link(category_name, href=cat_href, className="crumb"), html.Span("/", className="sep"),
        dcc.Link(modality_name, href=mod_href, className="crumb"), html.Span("/", className="sep"),
        html.Span(item_name, className="here"),
        html.Div(className="grow"),
        html.Span("Featured", className="chip chip-pending plain") if item.get('is_featured') else None,
        dcc.Link("← Back to Product List", href=mod_href if item.get('modality_id') else "/products/all",
                 className="a-btn a-btn-outline a-btn-sm"),
    ], className="detail-bar")

    details_body = html.Div([
        html.Div([
            html.Div([
                html.Div([html.Img(src=image_path, alt=item_name, className=img_class)],
                         className="p-3 bg-white rounded-4 border text-center")
            ], className="col-lg-5 col-md-6 mb-4 mb-md-0"),
            html.Div([
                html.H2(item_name, className="fw-bold mb-3"),
                html.P(short_desc, className="text-muted mb-4 fs-6", style={"lineHeight": "1.65"}),
                html.Div([
                    html.Div([html.Div("Category", className="k"),
                              html.Div(dcc.Link(category_name, href=cat_href), className="v")]),
                    html.Div([html.Div("Modality", className="k"),
                              html.Div(dcc.Link(modality_name, href=mod_href), className="v")]),
                ], className="detail-facts"),
                html.Button("Contact Sales", id="btn-open-quote-modal", n_clicks=0,
                            className="btn btn-green rounded-pill fw-semibold px-4 py-2 text-white"),
                html.Div([
                    "Need installation, maintenance or power protection for this equipment? ",
                    dcc.Link("See our services →", href="/services"),
                ], className="service-note"),
            ], className="col-lg-7 col-md-6 ps-lg-5"),
        ], className="row align-items-center"),
    ])

    description_section = html.Div([
        html.H4("Description", className="fw-bold mb-3 mt-5"),
        html.Div(dcc.Markdown(long_desc, mathjax=False), className="text-muted fs-6"),
    ]) if long_desc else None

    return html.Div([
        dcc.Store(id='modal-item-name-store', data=item_name),
        dcc.Store(id='modal-item-img-store', data=image_path),
        detail_bar,
        html.Div([details_body, description_section], className="a-card site-card-pad p-4 p-lg-5"),
    ])


# ==========================================
# CALLBACK: CONTACT SALES MODAL OPEN / CLOSE
# ==========================================
@callback(
    Output('quote-inquiry-modal', 'is_open'),
    Output('modal-product-title', 'children'),
    Output('modal-product-img', 'src'),
    Output('quote-inquiry-feedback', 'children'),
    Input('btn-open-quote-modal', 'n_clicks'),
    Input('btn-close-quote-modal', 'n_clicks'),
    State('modal-item-name-store', 'data'),
    State('modal-item-img-store', 'data'),
    prevent_initial_call=True
)
def toggle_quote_modal(open_clicks, close_clicks, item_name, image_path):
    ctx = dash.callback_context
    if not ctx.triggered or not ctx.triggered[0].get('value'):
        raise dash.exceptions.PreventUpdate
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    opening = trigger_id == 'btn-open-quote-modal'
    return opening, item_name or "Product Inquiry", image_path or ui.FALLBACK_IMG, None


# ==========================================
# CALLBACK: SAVE THE QUOTE REQUEST (channel = Product Page)
# ==========================================
@callback(
    Output('quote-inquiry-modal', 'is_open', allow_duplicate=True),
    Output('quote-inquiry-feedback', 'children', allow_duplicate=True),
    Output('quote-inquiry-toast', 'children'),
    *[Output(i, 'value') for i in FIELD_IDS],
    Input('btn-submit-inquiry', 'n_clicks'),
    *[State(i, 'value') for i in FIELD_IDS],
    State('modal-item-name-store', 'data'),
    prevent_initial_call=True,
)
def submit_quote_inquiry(n, customer, address, person, dept, phone, email, machine, remarks, item_name):
    if not n:
        raise dash.exceptions.PreventUpdate
    product = item_name or "a product"
    text = (machine or '').strip() or f"Requesting a quotation for {product}."
    ok, message, _ref = submit_inquiry(SOURCE_PRODUCT, customer, address, person, dept, phone, email, text, remarks,
                                       source_detail=item_name)
    if ok:
        return (False, None, html.Div(message, className="mb-3")) + ('',) * len(FIELD_IDS)
    return (no_update, message, no_update) + (no_update,) * len(FIELD_IDS)
