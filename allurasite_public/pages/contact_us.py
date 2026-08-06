import dash
from dash import html, dcc
from database import db_handler
from allurasite_public.components import render_contact_info_sidebar, render_office_maps

dash.register_page(__name__, path='/contact-us', title='Allura Enterprise - Contact Us')

INQUIRY_FORM_FIELD_IDS = ['inquiry-name', 'inquiry-email', 'inquiry-company', 'inquiry-contact-no', 'inquiry-message']

# Read once at module load (matches how clientside_callback needs a fixed string
# baked in at definition time). Falls back to the known company inbox if the
# DB isn't reachable yet when the app starts.
_INQUIRY_RECIPIENT_EMAIL = db_handler.get_site_settings().get('contact_email') or 'info@alluraenterpriseph.com'


def layout():
    return html.Div(className='info-page-wrapper', children=[
        # 1. HERO BANNER
        html.Div(className='info-hero-banner', children=[
            html.Div(className='info-hero-bg'),
            html.Div(className='info-hero-overlay', children=[
                html.H1("CONTACT US", className='info-hero-title')
            ])
        ]),

        # 2. INQUIRY FORM (left) + CONTACT INFO (right)
        html.Div(className='container info-content-grid', children=[
            html.Div(className='inquiry-form-card', children=[
                html.H3("Inquiry Form"),

                html.Div(className='form-group', children=[
                    html.Label("Name", className='form-label'),
                    dcc.Input(id='inquiry-name', type='text', className='form-input', placeholder='Your full name')
                ]),
                html.Div(className='form-group', children=[
                    html.Label("Email", className='form-label'),
                    dcc.Input(id='inquiry-email', type='email', className='form-input', placeholder='name@company.com')
                ]),
                html.Div(className='form-group', children=[
                    html.Label("Company", className='form-label'),
                    dcc.Input(id='inquiry-company', type='text', className='form-input', placeholder='Hospital / company name')
                ]),
                html.Div(className='form-group', children=[
                    html.Label("Contact No.", className='form-label'),
                    dcc.Input(id='inquiry-contact-no', type='text', className='form-input', placeholder='e.g. +63 9XX XXX XXXX')
                ]),
                html.Div(className='form-group', children=[
                    html.Label("Inquiry/Message", className='form-label'),
                    dcc.Textarea(id='inquiry-message', className='form-textarea', rows=5, placeholder='Type your message here...')
                ]),

                html.Button("Submit", id='inquiry-submit-btn', n_clicks=0, className='btn-submit'),

                html.P([
                    "By submitting this form, you hereby accept our Privacy Policy."
                ], className='privacy-note'),

                html.A("Privacy Policy", href='/assets/privacy_policy.pdf', target='_blank', className='btn-privacy')
            ]),

            render_contact_info_sidebar()
        ]),

        # 3. MAIN + SATELLITE OFFICE MAPS
        html.Div(className='container', children=[
            render_office_maps()
        ])
    ])


# Clientside callback: builds a mailto: link from the form fields and opens the
# user's email client addressed to the company inbox. Swap this out later for a
# real backend/email-API submission if you want it handled server-side instead.
dash.clientside_callback(
    """
    function(n_clicks, name, email, company, phone, message) {
        if (!n_clicks) { return window.dash_clientside.no_update; }

        const subject = encodeURIComponent('Website Inquiry from ' + (name || 'Allura Website Visitor'));
        const bodyLines = [
            'Name: ' + (name || ''),
            'Email: ' + (email || ''),
            'Company: ' + (company || ''),
            'Contact No.: ' + (phone || ''),
            '',
            'Inquiry/Message:',
            (message || '')
        ];
        const body = encodeURIComponent(bodyLines.join('\\n'));
        window.location.href = 'mailto:%s?subject=' + subject + '&body=' + body;
        return window.dash_clientside.no_update;
    }
    """ % _INQUIRY_RECIPIENT_EMAIL,
    dash.Output('inquiry-submit-btn', 'data-submitted'),
    dash.Input('inquiry-submit-btn', 'n_clicks'),
    [dash.State(field_id, 'value') for field_id in INQUIRY_FORM_FIELD_IDS],
    prevent_initial_call=True
)