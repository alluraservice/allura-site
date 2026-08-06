import dash
from dash import html, dcc
from database import db_handler

# ==============================================================================
# CONTACT / SOCIAL / OFFICE INFO
# All of this now comes live from the 'site_settings' table (contact_email,
# contact_phone, main_office_address, satellite_office_address, facebook_link,
# linkedin_link) via db_handler.get_site_settings() — nothing hardcoded here.
# ==============================================================================

def _map_embed_src(address):
    """Builds a Google Maps embed URL from an address string (no API key needed)."""
    return f"https://www.google.com/maps?q={address}&output=embed"


def render_social_icons_row():
    """
    Small circular Facebook/LinkedIn icon links, reused across About Us / News /
    Contact Us. If a link isn't set yet in site_settings (both are currently
    null), the icon still shows but greyed out and non-clickable so the layout
    doesn't jump once real links are added.
    """
    settings = db_handler.get_site_settings()
    facebook_url = settings.get('facebook_url')
    linkedin_url = settings.get('linkedin_url')

    def social_icon(icon_file, url, label):
        icon_img = html.Img(src=f'/assets/icons/{icon_file}', className='social-icon-img')
        if url:
            return html.A(
                icon_img, href=url, target='_blank', rel='noopener noreferrer',
                className='social-icon-circle', **{'aria-label': label}
            )
        # No link set yet: render as a disabled placeholder instead of a dead '#' link.
        return html.Span(
            icon_img, className='social-icon-circle disabled',
            title=f'{label} link not yet added', **{'aria-label': f'{label} (not yet available)'}
        )

    return html.Div(className='social-icons-row', children=[
        social_icon('facebook.svg', facebook_url, 'Facebook'),
        social_icon('linkedin.svg', linkedin_url, 'LinkedIn')
    ])


def render_contact_info_sidebar():
    """
    'CONTACT INFO' sidebar used on both About Us and Contact Us:
    Main Office / Satellite Office / Contact No. / Email + social links.
    Pulled live from the 'site_settings' table.
    """
    settings = db_handler.get_site_settings()

    def info_box(icon, label, value):
        return html.Div(className='contact-info-box', children=[
            html.Div(className='contact-info-icon-wrap', children=[
                html.Img(src=f'/assets/icons/{icon}', className='contact-info-icon')
            ]),
            html.Div(className='contact-info-text', children=[
                html.Span(label, className='contact-info-label'),
                html.P(value or '—', className='contact-info-value')
            ])
        ])

    return html.Div(className='contact-info-sidebar', children=[
        html.H3("CONTACT INFO", className='contact-info-heading'),
        info_box('office.svg', 'MAIN OFFICE', settings.get('main_office_address')),
        info_box('satellite.svg', 'SATELLITE OFFICE', settings.get('satellite_office_address')),
        info_box('call.svg', 'CONTACT NO.', settings.get('contact_phone')),
        info_box('email.svg', 'EMAIL', settings.get('contact_email')),
        html.H4("Follow us", className='follow-us-heading'),
        render_social_icons_row()
    ])


def render_office_maps():
    """Embedded Google Maps for the Main Office and Satellite Office, driven by 'site_settings'."""
    settings = db_handler.get_site_settings()
    main_address = settings.get('main_office_address')
    satellite_address = settings.get('satellite_office_address')

    def map_block(address, title_prefix):
        if not address:
            return None
        return html.Div(className='map-section', children=[
            html.H3([f'{title_prefix} Office ', html.Span('Address', className='map-heading-light')], className='map-heading'),
            html.Div(className='map-iframe-wrapper', children=[
                html.Iframe(
                    src=_map_embed_src(address),
                    className='map-iframe',
                    referrerPolicy='no-referrer-when-downgrade'
                )
            ])
        ])

    blocks = [b for b in [map_block(main_address, 'Main'), map_block(satellite_address, 'Satellite')] if b]
    return html.Div(className='office-maps-wrapper', children=blocks)


# ==============================================================================
# REQUEST-A-QUOTE / SERVICE-REQUEST MODAL
# Used on product_details.py and service_details.py. Each page wires its own
# module-level clientside_callback (open/close/submit) targeting the ids built
# here with a given `prefix` ('product' or 'service') so the two pages never
# collide on component ids.
# ==============================================================================

def _quote_modal_field(prefix, field_key, label, placeholder, input_type='text', is_textarea=False):
    input_id = f'{prefix}-quote-{field_key}'
    # Generic, non-descriptive `name` (no "name"/"address"/"email" substrings) +
    # autoComplete='off' stops Chrome from recognizing these as address-form
    # fields and covering them with its own autofill icon/dropdown.
    no_autofill_name = f'nf-{abs(hash(prefix + field_key)) % 100000}'
    field = (
        dcc.Textarea(
            id=input_id, className='quote-modal-textarea', placeholder=placeholder, rows=3,
            name=no_autofill_name
        )
        if is_textarea else
        dcc.Input(
            id=input_id, type=input_type, className='quote-modal-input', placeholder=placeholder,
            autoComplete='off', name=no_autofill_name
        )
    )
    return html.Div(className='quote-modal-field', children=[
        html.Label(label, className='quote-modal-label'),
        field
    ])


def render_quote_modal(prefix, item_name, item_image, item_subtitle=None, theme='product', submit_label='Send Quotation'):
    """
    Builds the hidden-by-default quote/service-request modal for a single item.
    `prefix` must be unique per page ('product' or 'service') since these ids
    are wired to a clientside_callback defined once at that page's module level.
    """
    # product_icon.svg / service_icon.svg are solid white (meant to sit on a
    # colored badge) - on the modal's white image box they'd be invisible, so
    # give the box a themed background whenever we're showing a fallback icon.
    is_fallback_icon = 'product_icon' in str(item_image) or 'service_icon' in str(item_image)
    img_class = 'quote-modal-img quote-modal-img-fallback' if is_fallback_icon else 'quote-modal-img'

    return html.Div(id=f'{prefix}-quote-modal-overlay', className='quote-modal-overlay', children=[
        html.Div(className=f'quote-modal-card theme-{theme}', children=[
            html.Button('\u00d7', id=f'{prefix}-quote-modal-close', n_clicks=0, className='quote-modal-close-btn', **{'aria-label': 'Close'}),

            dcc.Store(id=f'{prefix}-quote-item-store', data={'name': item_name}),

            html.Div(className='quote-modal-header', children=[
                html.Img(src=item_image, className=img_class),
                html.Div(className='quote-modal-header-text', children=[
                    html.H3(item_name, className='quote-modal-title'),
                    html.P(item_subtitle, className='quote-modal-subtitle')
                ] if item_subtitle else [
                    html.H3(item_name, className='quote-modal-title')
                ])
            ]),

            html.Div(className='quote-modal-body', children=[
                _quote_modal_field(prefix, 'cust-name', 'Customer/Hospital Name:', 'Enter your customer/hospital name here'),
                _quote_modal_field(prefix, 'office-address', 'Office Address:', 'Enter your address here'),
                _quote_modal_field(prefix, 'contact-person', 'Contact Person:', 'Enter your contact person here'),
                _quote_modal_field(prefix, 'dept-title', 'Department and title:', 'Enter your department and title here'),
                _quote_modal_field(prefix, 'contact-no', 'Contact No.:', 'Enter your contact no. here'),
                _quote_modal_field(prefix, 'email', 'Email address:', 'Enter your email address here', input_type='email'),
                _quote_modal_field(prefix, 'inquiry', 'Machine Inquiry:', 'Enter your machine inquiry here'),
                _quote_modal_field(prefix, 'remarks', 'Remarks (Optional):', 'Enter your remarks here', is_textarea=True),
                html.Button(submit_label, id=f'{prefix}-quote-submit-btn', n_clicks=0, className='quote-modal-submit-btn')
            ])
        ])
    ])


def register_quote_modal_callback(prefix, recipient_email):
    """
    Registers the ONE clientside callback (per prefix) that opens/closes the
    modal and, on submit, builds a mailto: to `recipient_email` from the form
    fields and closes the modal. Call this once at page-module import time
    (not inside the page's content callback) to avoid duplicate-output errors.
    """
    dash.clientside_callback(
        """
        function(openClicks, closeClicks, submitClicks, custName, officeAddress, contactPerson,
                  deptTitle, contactNo, email, inquiry, remarks, itemInfo) {
            const ctx = dash_clientside.callback_context;
            if (!ctx.triggered.length) { return window.dash_clientside.no_update; }
            const triggeredId = ctx.triggered[0].prop_id.split('.')[0];

            if (triggeredId === '%(open_id)s') {
                document.body.style.overflow = 'hidden';
                return 'quote-modal-overlay active';
            }

            if (triggeredId === '%(submit_id)s') {
                const itemName = (itemInfo && itemInfo.name) ? itemInfo.name : '';
                const subject = encodeURIComponent('Quote Request: ' + itemName);
                const bodyLines = [
                    'Item: ' + itemName,
                    'Customer/Hospital Name: ' + (custName || ''),
                    'Office Address: ' + (officeAddress || ''),
                    'Contact Person: ' + (contactPerson || ''),
                    'Department and title: ' + (deptTitle || ''),
                    'Contact No.: ' + (contactNo || ''),
                    'Email address: ' + (email || ''),
                    'Machine Inquiry: ' + (inquiry || ''),
                    'Remarks: ' + (remarks || '')
                ];
                const body = encodeURIComponent(bodyLines.join('\\n'));
                window.location.href = 'mailto:%(recipient)s?subject=' + subject + '&body=' + body;
                document.body.style.overflow = '';
                return 'quote-modal-overlay';
            }

            // closeClicks (or anything else): just close it and restore scrolling.
            document.body.style.overflow = '';
            return 'quote-modal-overlay';
        }
        """ % {
            'open_id': f'{prefix}-quote-open-btn',
            'submit_id': f'{prefix}-quote-submit-btn',
            'recipient': recipient_email
        },
        dash.Output(f'{prefix}-quote-modal-overlay', 'className'),
        dash.Input(f'{prefix}-quote-open-btn', 'n_clicks'),
        dash.Input(f'{prefix}-quote-modal-close', 'n_clicks'),
        dash.Input(f'{prefix}-quote-submit-btn', 'n_clicks'),
        dash.State(f'{prefix}-quote-cust-name', 'value'),
        dash.State(f'{prefix}-quote-office-address', 'value'),
        dash.State(f'{prefix}-quote-contact-person', 'value'),
        dash.State(f'{prefix}-quote-dept-title', 'value'),
        dash.State(f'{prefix}-quote-contact-no', 'value'),
        dash.State(f'{prefix}-quote-email', 'value'),
        dash.State(f'{prefix}-quote-inquiry', 'value'),
        dash.State(f'{prefix}-quote-remarks', 'value'),
        dash.State(f'{prefix}-quote-item-store', 'data'),
        prevent_initial_call=True
    )


# ==============================================================================
# ALLUBOT CHAT WIDGET
# A single persistent floating chat window (like a Messenger chat head) - lives
# once in the app shell (see index.py's app.layout) so it survives page
# navigation. Opened from any "Ask AlluBot" button across the site via
# ALLUBOT_TRIGGER_IDS. Static/sample content only for now - no real chat logic.
# ==============================================================================

ALLUBOT_TRIGGER_IDS = [
    'allubot-trigger',                        # header (always mounted)
    'allubot-trigger-home',
    'allubot-trigger-product-categories',
    'allubot-trigger-product-list',
    'allubot-trigger-product-details',
    'allubot-trigger-service-categories',
    'allubot-trigger-service-list',
    'allubot-trigger-service-details',
]

ALLUBOT_QUICK_REPLIES = [
    "What products do you supply?",
    "How do I request a quote?",
    "Can I book a repair/service?",
    "Do you offer quality audits?",
]


def render_allubot_widget():
    """The floating AlluBot chat window itself. Starts closed (className has no
    'open'); toggled by register_allubot_widget_callback below."""
    return html.Div(id='allubot-widget', className='allubot-widget', children=[
        # HEADER BAR
        html.Div(className='allubot-widget-header', children=[
            html.Img(src='/assets/icons/allubot1.svg', className='allubot-widget-header-icon', alt=''),
            html.Span('AlluBot', className='allubot-widget-header-title'),
            html.Div(className='allubot-widget-header-actions', children=[
                html.Button('\u2212', id='allubot-minimize-btn', n_clicks=0, className='allubot-widget-minimize-btn', **{'aria-label': 'Minimize'}),
                html.Button('\u00d7', id='allubot-close-btn', n_clicks=0, className='allubot-widget-close-btn', **{'aria-label': 'Close'})
            ])
        ]),

        # BODY (hidden while minimized)
        html.Div(className='allubot-widget-body', children=[
            html.Div(className='allubot-message-row', children=[
                html.Img(src='/assets/icons/allubot1.svg', className='allubot-message-avatar', alt=''),
                html.Div("Hi, I'm AlluBot! How may I help you?", className='allubot-message-bubble')
            ]),

            html.Div(className='allubot-quick-replies', children=[
                html.Button(reply, className='allubot-quick-reply-btn', n_clicks=0)
                for reply in ALLUBOT_QUICK_REPLIES
            ]),

            html.Div(className='allubot-widget-input-row', children=[
                dcc.Textarea(
                    id='allubot-chat-input', className='allubot-widget-input',
                    placeholder='Type your question here.', rows=2, name='nf-allubot'
                )
            ])
        ])
    ])


def register_allubot_widget_callback():
    """Registers the ONE global clientside callback that opens/closes/minimizes
    the AlluBot widget. Call once at app-startup time (see index.py) - not per
    page - to avoid duplicate-output errors."""
    trigger_inputs = ''.join(f'triggerClicks{i}, ' for i in range(len(ALLUBOT_TRIGGER_IDS)))

    dash.clientside_callback(
        """
        function(%s minimizeClicks, closeClicks) {
            const ctx = dash_clientside.callback_context;
            if (!ctx.triggered.length) { return window.dash_clientside.no_update; }
            const triggeredId = ctx.triggered[0].prop_id.split('.')[0];

            if (triggeredId === 'allubot-minimize-btn') {
                const el = document.getElementById('allubot-widget');
                const isMinimized = el && el.classList.contains('minimized');
                return isMinimized ? 'allubot-widget open' : 'allubot-widget open minimized';
            }

            if (triggeredId === 'allubot-close-btn') {
                return 'allubot-widget';
            }

            // Any "Ask AlluBot" trigger button: open (un-minimized).
            return 'allubot-widget open';
        }
        """ % trigger_inputs,
        dash.Output('allubot-widget', 'className'),
        [dash.Input(trigger_id, 'n_clicks') for trigger_id in ALLUBOT_TRIGGER_IDS],
        dash.Input('allubot-minimize-btn', 'n_clicks'),
        dash.Input('allubot-close-btn', 'n_clicks'),
        prevent_initial_call=True
    )


def _slugify_category(category):
    return (
        str(category)
        .strip()
        .lower()
        .replace("&", "and")
        .replace("/", "-")
        .replace(" ", "-")
    )

# ==============================================================================
# SECTION 1: TOP INFORMATIONAL BANNER RIBBON BAR (#31952f GREEN)
# ==============================================================================
def render_top_bar():
    return html.Div(className='top-bar', children=[
        html.Div(className='container-fluid top-bar-content', children=[
            html.Div(className='top-bar-info', children=[
                html.Span(className='top-info-item', children=[
                    html.Img(src='/assets/icons/office.svg', className='top-bar-icon', alt="Location"),
                    "BGC, Taguig City, Philippines"
                ]),
                html.Span(className='top-info-item', children=[
                    html.Img(src='/assets/icons/call.svg', className='top-bar-icon', alt="Phone"),
                    "+63 917 770 1820"
                ]),
                html.Span(className='top-info-item', children=[
                    html.Img(src='/assets/icons/email.svg', className='top-bar-icon', alt="Email"),
                    "info@alluraenterpriseph.com"
                ])
            ])
        ])
    ])


# ==============================================================================
# SECTION 2: MAIN NAVIGATION HEADER (#ffffff WHITE)
# ==============================================================================
def render_header():
    product_categories = db_handler.get_categories_by_type('Product')
    service_categories = db_handler.get_categories_by_type('Service')

    default_product_url = (
        f"/product-list?category={_slugify_category(product_categories[0])}"
        if product_categories
        else "/product-list"
    )
    default_service_url = (
        f"/service-list?category={_slugify_category(service_categories[0])}"
        if service_categories
        else "/service-list"
    )

    return html.Header(className='main-header', children=[
        html.Div(className='container-fluid header-container', children=[
            html.Div(className='logo-area', children=[
                dcc.Link(
                    html.Img(src='/assets/logos/alluralogo1.png', className='logo-image', alt="ALLURA Logo"),
                    href="/"
                )
            ]),

            html.Div(className='header-left-group', children=[
                html.Nav(className='nav-links', children=[
                    dcc.Link("Home", href="/", className='nav-link'),
                    dcc.Link("About Us", href="/about-us", className='nav-link'),

                    html.Div(className='nav-dropdown', children=[
                        dcc.Link([
                            "Products",
                            html.Span(" ⌵", className='caret')
                        ], href=default_product_url, className='nav-link'),

                        html.Div(className='dropdown-menu', children=[
                            dcc.Link(
                                category,
                                href=f"/product-list?category={_slugify_category(category)}",
                                className='dropdown-item'
                            ) for category in product_categories
                        ])
                    ]),

                    html.Div(className='nav-dropdown', children=[
                        dcc.Link([
                            "Services",
                            html.Span(" ⌵", className='caret')
                        ], href=default_service_url, className='nav-link'),

                        html.Div(className='dropdown-menu', children=[
                            dcc.Link(
                                category,
                                href=f"/service-list?category={_slugify_category(category)}",
                                className='dropdown-item'
                            ) for category in service_categories
                        ])
                    ]),

                    dcc.Link("News/Blog", href="/news", className='nav-link'),
                    dcc.Link("Contact Us", href="/contact-us", className='nav-link')
                ]),

                html.Div(className='search-chat-actions', children=[
                    html.Div(className='search-container', children=[
                        html.Img(src='/assets/icons/search.svg', className='search-icon-svg', alt="Search"),
                        dcc.Input(type="text", placeholder="Search products or services...", className='search-input')
                    ]),
                    html.Button([
                        html.Img(src='/assets/icons/allubot1.svg', className='allubot-icon-svg', alt="AlluBot"),
                        "Ask AlluBot"
                    ], id="allubot-trigger", className='btn-allubot')
                ])
            ])
        ])
    ])


# ==============================================================================
# SECTION 3: STANDARD CORPORATE FOOTER (#666666 GREY)
# ==============================================================================
def render_footer():
    product_categories = db_handler.get_categories_by_type('Product')
    service_categories = db_handler.get_categories_by_type('Service')

    default_product_url = (
        f"/product-list?category={_slugify_category(product_categories[0])}"
        if product_categories
        else "/product-list"
    )
    default_service_url = (
        f"/service-list?category={_slugify_category(service_categories[0])}"
        if service_categories
        else "/service-list"
    )

    return html.Footer(className='main-footer', children=[
        html.Div(className='container footer-grid', children=[
            html.Div(className='footer-col', children=[
                html.H4("About Us"),
                html.P([
                    "ALLURA ENTERPRISE stands as a trusted leader in the distribution and supply of ",
                    "high-quality Medical Equipment, Medical Supplies, and Power Protection solutions ",
                    "for both medical and industrial sectors."
                ]),
                html.P([
                    "Since its inception in 2014, Allura Enterprise has been committed to ",
                    "upholding the highest standards of safety, reliability, and operational ",
                    "excellence, ensuring seamless installation and continuous support for every client."
                ])
            ]),

            html.Div(className='footer-col', children=[
                html.H4("Contact Us"),
                html.P([html.Strong("Main Office: "), "Doña Paz Village, Cruzada, Legazpi City"], style={'marginBottom': '18px'}),
                html.P([html.Strong("Satellite Office: "), "Villa Angelina Phase 1, Mambog 4, Bacoor Cavite"], style={'marginBottom': '18px'}),
                html.P([html.Strong("Contact: "), "+63 917 770 1820"], style={'marginBottom': '18px'}),
                html.P([html.Strong("Email: "), "allura.enterprise@gmail.com"])
            ]),

            html.Div(className='footer-col', children=[
                html.H4("Quick Links"),
                html.Ul([
                    html.Li(dcc.Link("Home", href="/")),
                    html.Li(dcc.Link("About Us", href="/about-us")),
                    html.Li(dcc.Link("Products", href=default_product_url)),
                    html.Li(dcc.Link("Services", href=default_service_url)),
                    html.Li(dcc.Link("Contact Us", href="/contact-us"))
                ])
            ]),

            html.Div(className='footer-col', children=[
                html.H4("Allura Legal"),
                html.Ul([
                    html.Li(html.A("Terms and Conditions", href="#")),
                    html.Li(html.A("Privacy Policy", href="#"))
                ])
            ])
        ])
    ])