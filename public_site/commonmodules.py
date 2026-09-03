import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from app import app

# --- NAVBAR COMPONENT ---
navbar = [
    # 1. TOP GREEN BAR (Standalone - scrolls away normally)
    html.Div(
        dbc.Container(
            [
                html.Div(
                    [
                        html.Span(
                            [
                                html.Img(src=app.get_asset_url('icons/office.svg'), className='top-bar-icon'),
                                "BGC, Taguig City, Philippines"
                            ],
                            className='top-bar-item'
                        ),
                        html.Span(
                            [
                                html.Img(src=app.get_asset_url('icons/call.svg'), className='top-bar-icon'),
                                "+63 917 770 1820"
                            ],
                            className='top-bar-item'
                        ),
                        html.Span(
                            [
                                html.Img(src=app.get_asset_url('icons/email.svg'), className='top-bar-icon'),
                                "info@alluraenterpriseph.com"
                            ],
                            className='top-bar-item'
                        ),
                    ],
                    className='d-flex justify-content-end align-items-center w-100'
                )
            ],
            fluid=True,
            className='px-5'
        ),
        className='top-green-bar py-1'
    ),

    # 2. MAIN NAVIGATION BAR (Standalone Sticky Header - stays pinned at top: 0)
    html.Header(
        dbc.Navbar(
            dbc.Container(
                [
                    # Brand Logo (Left Side)
                    html.A(
                        html.Img(
                            src=app.get_asset_url('logos/alluralogo1.png'),
                            height='45px',
                            alt='Allura Enterprise'
                        ),
                        href='/home',
                        className='navbar-brand d-flex align-items-center me-0 gap-3'
                    ),

                    # Center Navigation Links (Middle)
                    html.Div(
                        [
                            dbc.NavLink('Home', href='/home', className='btn-nav'),
                            dbc.NavLink('About Us', href='/about_us', className='btn-nav'),
                            dbc.NavLink('Products', href='/products', className='btn-nav'),
                            dbc.NavLink('Services', href='/services', className='btn-nav'),
                            dbc.NavLink('Contact Us', href='/contact_us', className='btn-nav'),
                        ],
                        className='nav-container d-none d-lg-flex align-items-center justify-content-center gap-3'
                    ),

                    # Right Side Items (Search, Quote, Chatbot)
                    html.Div(
                        [
                            # Search Bar Container
                            html.Div(
                                [
                                    dbc.Input(
                                        type='text',
                                        placeholder='Search',
                                        id='navbar_search_input',
                                        className='search-box flex-grow-1'
                                    ),
                                    dbc.InputGroupText(
                                        html.Img(src=app.get_asset_url('icons/search.svg'), className='btn-search'),
                                        className='bg-transparent border-0 pe-0'
                                    ),
                                ],
                                className='search-group-pill w-auto d-flex align-items-center pe-0 me-0'
                            ),
                            # Quote/Request Button
                            html.A(
                                html.Img(src=app.get_asset_url('icons/quote.svg'), alt='Quote', className='nav-action-icon'),
                                href='/contact_us',
                                title='Request Quote',
                                className='btn-nav-icon'
                            ),

                            # Chatbot Icon Button (AlluBot)
                            html.A(
                                html.Img(src=app.get_asset_url('icons/allubot1.svg'), alt='AlluBot', className='nav-action-icon'),
                                href='#',
                                id='open_allubot_btn',
                                title='AlluBot',
                                className='btn-nav-icon'
                            ),
                        ],
                        className='d-flex align-items-center gap-3'
                    )
                ],
                fluid=True,
                className='d-flex align-items-center justify-content-center w-100 px-4 gap-3' 
            ),
            color='white',
            className='main-nav-bar shadow-sm py-2'
        ),
        style={
            'position': 'sticky',
            'top': '0',
            'zIndex': '1030',
            'backgroundColor': 'white'
        }
    )
]


# --- FOOTER COMPONENT ---
def get_footer():
    return html.Footer(
        [
            html.Div(
                [
                    html.Div(
                        [
                            # Column 1: Brand Logo & Short Description
                            html.Div(
                                [
                                    html.Img(
                                        src=app.get_asset_url('logos/alluralogo1.png'),
                                        alt='Allura Enterprise Logo',
                                        className='footer-logo mb-3'
                                    ),
                                    html.P(
                                        "Allura Enterprise is a premier Philippine medical equipment distributor and service provider, "
                                        "delivering reliable radiology, imaging, and hospital infrastructure solutions nationwide.",
                                        className='small text-muted pe-lg-4',
                                        style={'lineHeight': '1.6', 'maxWidth': '300px'}
                                    )
                                ],
                                className='col-lg-4 col-md-12 mb-4 mb-lg-0'
                            ),

                            # Column 2: Company Navigation Links
                            html.Div(
                                [
                                    html.H6("Company", className="fw-bold mb-3"),
                                    html.Ul(
                                        [
                                            html.Li(html.A("Home", href="/home")),
                                            html.Li(html.A("About Us", href="/about_us")),
                                            html.Li(html.A("Services", href="/services")),
                                            html.Li(html.A("Products", href="/products")),
                                            html.Li(html.A("Contact Us", href="/contact_us")),
                                        ],
                                        className="footer-links-list small"
                                    )
                                ],
                                className='col-lg-3 col-md-6 mb-4 mb-lg-0'
                            ),

                            # Column 3: Contact Information
                            html.Div(
                                [
                                    html.H6("Get in Touch", className="fw-bold mb-3"),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Img(src=app.get_asset_url('icons/call.svg'), className='me-2 footer-icon', style={'width': '16px'}),
                                                    html.Span("+63 917 770 1820", className="small")
                                                ],
                                                className="footer-contact-item"
                                            ),
                                            html.Div(
                                                [
                                                    html.Img(src=app.get_asset_url('icons/email.svg'), className='me-2 footer-icon', style={'width': '16px'}),
                                                    html.A("info@alluraenterpriseph.com", href="mailto:info@alluraenterpriseph.com", className="small text-decoration-none text-reset")
                                                ],
                                                className="footer-contact-item"
                                            ),
                                            html.Div(
                                                [
                                                    html.Img(src=app.get_asset_url('icons/office.svg'), className='me-2 footer-icon', style={'width': '16px'}),
                                                    html.Span("BGC, Taguig City, Philippines", className="small")
                                                ],
                                                className="footer-contact-item"
                                            ),
                                        ]
                                    )
                                ],
                                className='col-lg-4 col-md-6'
                            )
                        ],
                        className='row justify-content-between'
                    ),

                    # Bottom Copyright Bar
                    html.Div(
                        [
                            html.P(
                                "© 2026 Allura Enterprise. All Rights Reserved.",
                                className="text-center small mb-0 opacity-75"
                            )
                        ],
                        className="footer-bottom"
                    )
                ],
                className="container"
            )
        ],
        className="site-footer"
    )