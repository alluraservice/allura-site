import dash
from dash import html, dcc
from database import db_handler
from allurasite_public.components import render_contact_info_sidebar, render_office_maps

dash.register_page(__name__, path='/about-us', title='Allura Enterprise - About Us')


def render_section_card(section, index):
    """First section (the tagline) renders as an emphasized intro line with no heading;
    every section after that renders as a titled card. Content is Markdown so bullet
    lists / bold text from the CSV render correctly."""
    if index == 0:
        return html.Div(className='about-section-card about-intro-card', children=[
            dcc.Markdown(section['content'], className='markdown-body')
        ])

    return html.Div(className='about-section-card', children=[
        html.H3(section['title']),
        dcc.Markdown(section['content'], className='markdown-body')
    ])


def layout():
    sections = db_handler.get_about_sections()

    return html.Div(className='info-page-wrapper', children=[
        # 1. HERO BANNER
        html.Div(className='info-hero-banner', children=[
            html.Div(className='info-hero-bg'),
            html.Div(className='info-hero-overlay', children=[
                html.H1("ABOUT US", className='info-hero-title')
            ])
        ]),

        # 2. MAIN CONTENT: editable sections (left) + contact info (right)
        html.Div(className='container info-content-grid', children=[
            html.Div(className='info-main-column', children=(
                [render_section_card(section, i) for i, section in enumerate(sections)]
                if sections else
                [html.Div(className='about-section-card', children=[
                    html.P("About Us content not yet seeded. Run database/seed_site_content.py after filling in about_us_content.csv.")
                ])]
            )),

            render_contact_info_sidebar()
        ]),

        # 3. MAIN + SATELLITE OFFICE MAPS
        html.Div(className='container', children=[
            render_office_maps()
        ])
    ])