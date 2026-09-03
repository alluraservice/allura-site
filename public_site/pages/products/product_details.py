import dash
from dash import html, dcc, callback, Input, Output, State
from urllib.parse import parse_qs
import dash_bootstrap_components as dbc
from database.db_handler import get_item_by_id

dash.register_page(__name__, path='/product-details', title='Allura Enterprise - Product Details')


# ==========================================
# PAGE LAYOUT (URL LOCATION SHELL)
# ==========================================
def layout(id=None, **kwargs):
    return html.Div([
        html.Div(id='product-detail-content'),
        
        # Quote Modal Container (Closed by Default)
                dbc.Modal([
                    dbc.ModalBody([
                        # Top Row: Close Button
                        html.Div([
                            html.Button(
                                type="button",
                                id="btn-close-quote-modal",
                                className="btn-close ms-auto",
                            )
                        ], className="d-flex justify-content-end mb-2"),

                        # Header: Product Image + Product Name
                        html.Div([
                            html.Img(id='modal-product-img', src='', className='rounded-3 me-3', style={'width': '60px', 'height': '60px', 'objectFit': 'contain'}),
                            html.H3(id='modal-product-title', className='fw-bold mb-0', style={'color': 'var(--dark-green)'})
                        ], className='d-flex align-items-center mb-3'),

                        html.H5("INQUIRY FORM", className="fw-bold mb-4", style={'color': 'var(--dark-green)'}),

                        # Inquiry Form Grid
                        html.Div([
                            # Row 1
                            html.Div([
                                html.Div([
                                    html.Label("Customer/Hospital Name:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Input(id='inquiry-customer', type='text', placeholder='Enter your customer/hospital name here', className='input-box')
                                ], className="col-md-6 mb-3"),
                                html.Div([
                                    html.Label("Office Address:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Input(id='inquiry-address', type='text', placeholder='Enter your address here', className='input-box')
                                ], className="col-md-6 mb-3"),
                            ], className="row"),

                            # Row 2
                            html.Div([
                                html.Div([
                                    html.Label("Contact Person:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Input(id='inquiry-person', type='text', placeholder='Enter your contact person here', className='input-box')
                                ], className="col-md-6 mb-3"),
                                html.Div([
                                    html.Label("Department and title:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Input(id='inquiry-dept', type='text', placeholder='Enter your department and title here', className='input-box')
                                ], className="col-md-6 mb-3"),
                            ], className="row"),

                            # Row 3
                            html.Div([
                                html.Div([
                                    html.Label("Contact No.:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Input(id='inquiry-phone', type='text', placeholder='Enter your contact no. here', className='input-box')
                                ], className="col-md-6 mb-3"),
                                html.Div([
                                    html.Label("Email address:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Input(id='inquiry-email', type='email', placeholder='Enter your email address here', className='input-box')
                                ], className="col-md-6 mb-3"),
                            ], className="row"),

                            # Row 4 (Textareas)
                            html.Div([
                                html.Div([
                                    html.Label("Machine Inquiry:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Textarea(id='inquiry-machine', placeholder='Enter your machine inquiry here', className='input-box', style={'height': '110px'})
                                ], className="col-md-6 mb-3"),
                                html.Div([
                                    html.Label("Remarks (Optional):", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                                    dbc.Textarea(id='inquiry-remarks', placeholder='Enter your remarks here', className='input-box', style={'height': '110px'})
                                ], className="col-md-6 mb-3"),
                            ], className="row"),

                            # Submit Button
                            html.Div([
                                html.Button("Submit", id='btn-submit-inquiry', n_clicks=0, className='btn btn-green rounded-pill fw-semibold px-5 py-2 text-white shadow-sm')
                            ], className="mt-2")
                        ])
                    ], className='p-4')
                ], id='quote-inquiry-modal', size='lg', centered=True, is_open=False)
    ])


# ==========================================
# CALLBACK: RENDER PRODUCT DETAILS
# ==========================================
@callback(
    Output('product-detail-content', 'children'),
    Input('url', 'search')
)
def update_product_detail_page(search):
    item_id = None
    if search:
        raw_query = search.lstrip('?')
        query_params = parse_qs(raw_query)
        if 'id' in query_params:
            try:
                item_id = int(query_params['id'][0])
            except (ValueError, TypeError):
                item_id = None

    item = None
    if item_id:
        try:
            item = get_item_by_id(item_id)
        except Exception as e:
            print(f"Error loading item details: {e}")

    # Fallback view if item is not found
    if not item:
        return html.Div([
            html.Div([
                html.H3("Product Not Found", className="text-center text-muted py-5"),
                html.Div(
                    dcc.Link("Back to Product List", href="/products/all", className="btn btn-green rounded-pill px-4 py-2 text-white"),
                    className="text-center"
                )
            ], className="container py-5")
        ])

    # Extract dynamic properties
    item_name = item.get("name") or item.get("title") or "Product Details"
    short_desc = item.get("short_description") or item.get("description") or "No description available."
    long_desc = item.get("long_description", "")
    category_name = item.get("category_name", "Products")
    modality_name = item.get("modality_name", "General")
    
    raw_img = item.get("image_url") or item.get("image")
    image_path = f"/{str(raw_img).lstrip('/')}" if raw_img and str(raw_img).strip() != "" else "/assets/icons/product_icon.svg"
    is_fallback = "product_icon" in str(image_path)
    img_class = "img-fluid rounded-4 shadow-sm product-icon" if is_fallback else "img-fluid rounded-4 shadow-sm"

    # Back Button & Interactive Dynamic Breadcrumb Trail
    navigation_header = html.Div([
        dcc.Link(
            "← Back to Product List",
            href="/products/all",
            className="btn btn-outline-secondary rounded-pill btn-sm px-3 mb-3 fw-semibold text-decoration-none"
        ),
        html.P([
            dcc.Link("Home", href="/", className="text-decoration-none text-muted"),
            " / ",
            dcc.Link("Products", href="/products/all", className="text-decoration-none text-muted"),
            " / ",
            dcc.Link(f"{category_name}", href=f"/products/category/{category_name}", className="text-decoration-none text-muted"),
            " / ",
            dcc.Link(f"{modality_name}", href=f"/products/modality/{modality_name}", className="text-decoration-none text-muted"),
            " / ",
            html.Span(f"{item_name}", className="fw-semibold text-dark")
        ], className="text-muted mb-4 fs-6")
    ])

    # Main Details Block
    details_body = html.Div([
        html.Div([
            # Left: Product Image
            html.Div([
                html.Div([
                    html.Img(src=image_path, alt=item_name, className=img_class)
                ], className="p-3 bg-white rounded-4 border text-center")
            ], className="col-lg-5 col-md-6 mb-4 mb-md-0"),

            # Right: Product Information & Action Link
            html.Div([
                html.H2(item_name, className="fw-bold mb-3 text-dark"),
                html.P(short_desc, className="text-muted mb-4 fs-6", style={"lineHeight": "1.6"}),
                
                html.Div([
                    html.P([
                        html.Strong("Category: "), 
                        dcc.Link(category_name, href=f"/products/category/{category_name}", className="text-decoration-none text-secondary")
                    ], className="mb-1 text-secondary"),
                    html.P([
                        html.Strong("Modality: "), 
                        dcc.Link(modality_name, href=f"/products/modality/{modality_name}", className="text-decoration-none text-secondary")
                    ], className="mb-4 text-secondary"),
                ]),

                # Trigger Button for Modal
                html.Button(
                    "Contact Sales",
                    id="btn-open-quote-modal",
                    n_clicks=0,
                    className="btn btn-green rounded-pill fw-semibold px-4 py-2 text-white"
                )
            ], className="col-lg-7 col-md-6 ps-lg-5")
        ], className="row align-items-center")
    ])

    # Optional Long Description Section
    description_section = html.Div([
        html.H4("Description", className="fw-bold mb-3 mt-5 text-dark"),
        html.Div(
            dcc.Markdown(long_desc if long_desc else "No detailed description available.", mathjax=False),
            className="text-muted fs-6"
        )
    ]) if long_desc else None

    # Hidden stores to pass dynamic product metadata into the modal
    return html.Div([
        dcc.Store(id='modal-item-name-store', data=item_name),
        dcc.Store(id='modal-item-img-store', data=image_path),
        html.Div([
            navigation_header,
            details_body,
            description_section
        ], className="container py-5")
    ])


# ==========================================
# CALLBACK: STRICT CONTACT SALES CLICK MODAL TOGGLE
# ==========================================
@callback(
    [
        Output('quote-inquiry-modal', 'is_open'),
        Output('modal-product-title', 'children'),
        Output('modal-product-img', 'src')
    ],
    [
        Input('btn-open-quote-modal', 'n_clicks'),
        Input('btn-submit-inquiry', 'n_clicks'),
        Input('btn-close-quote-modal', 'n_clicks')  # <--- Added close button input
    ],
    [
        State('quote-inquiry-modal', 'is_open'),
        State('modal-item-name-store', 'data'),
        State('modal-item-img-store', 'data')
    ],
    prevent_initial_call=True
)
def toggle_quote_modal(open_clicks, submit_clicks, close_clicks, is_open, item_name, image_path):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Open ONLY when Contact Sales is clicked
    if trigger_id == 'btn-open-quote-modal' and (open_clicks or 0) > 0:
        return True, item_name or "Product Inquiry", image_path or "/assets/icons/product_icon.svg"
    
    # Close when Submit or X button is clicked
    if trigger_id in ['btn-submit-inquiry', 'btn-close-quote-modal']:
        return False, item_name or "Product Inquiry", image_path or "/assets/icons/product_icon.svg"

    return is_open, item_name or "", image_path or ""