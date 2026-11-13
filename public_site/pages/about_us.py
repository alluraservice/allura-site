import dash
from dash import html

import site_ui as ui
from utils.site_content import get_content

dash.register_page(__name__, path='/about-us', title='About Us - Allura Enterprise')

# All text, the timeline and the leaders come from Admin › Website Content › About Us
# (defaults in utils/site_content.py).


def _initials(name):
    parts = [p for p in name.replace('.', '').split() if len(p) > 1]
    return (parts[0][0] + parts[-1][0]).upper() if parts else "A"


# ==========================================
# PAGE LAYOUT
# ==========================================
def layout(*args, **kwargs):
    c = get_content('about')
    paragraphs = [p.strip() for p in str(c['who_text']).split('\n\n') if p.strip()]
    capabilities = [(x.get('title', ''), x.get('text', '')) for x in c['capabilities']]
    return html.Div([
        # Larger, centred banner (variant='feature'); every other inner page uses the standard hero
        ui.page_header(
            c['header_title'],
            c['header_lead'],
            crumbs=[("Home", "/home"), ("About Us", None)],
            variant='feature',
        ),
        html.Div([
            # Stats
            html.Div([
                html.Div([html.Div(x.get('k'), className="k"), html.Div(x.get('v'), className="v"),
                          html.Div(x.get('s'), className="s")], className="stat")
                for x in c['stats']
            ], className="stat-row"),

            # Who we are + capabilities
            html.Div([
                html.Div([
                    html.Div([
                        ui.section_head("Who we are", c['who_title']),
                        *[html.P(p, className="site-lead" + (" mb-3" if i < len(paragraphs) - 1 else ""))
                          for i, p in enumerate(paragraphs)],
                    ], className="col-lg-6 mb-4 mb-lg-0"),
                    html.Div([
                        html.Div([
                            html.Div(html.H6("Our Strategic Capabilities"), className="a-card-head"),
                            html.Div([
                                html.Div([html.B(t, className="d-block"), html.Span(d, className="text-muted small")],
                                         className="py-2" + (" border-bottom" if i < len(capabilities) - 1 else ""))
                                for i, (t, d) in enumerate(capabilities)
                            ], className="a-card-body"),
                            html.Div([
                                html.A("Our Products", href="/products", className="a-btn a-btn-primary a-btn-sm"),
                                html.A("Our Services", href="/services", className="a-btn a-btn-outline a-btn-sm"),
                            ], className="a-card-body pt-0 d-flex gap-2"),
                        ], className="a-card"),
                    ], className="col-lg-6"),
                ], className="row align-items-center"),
            ], className="site-section"),

            # Timeline
            html.Div([
                ui.section_head("Our history", c['timeline_title']),
                html.Div(html.Div([
                    html.Div([
                        html.Span(t.get('years'), className="chip chip-active plain"),
                        html.H5(t.get('title')),
                        html.P(t.get('text')),
                    ], className="tl-item")
                    for t in c['timeline']
                ], className="tl"), className="a-card site-card-pad"),
            ], className="site-section"),

            # Leadership
            html.Div([
                ui.section_head("Leadership", c['leaders_title']),
                html.Div([
                    html.Div([
                        html.Img(src=ld['photo'], alt=ld.get('name'), className="leader-photo") if ld.get('photo')
                        else html.Div(_initials(ld.get('name') or ''), className="avatar lg"),
                        html.H5(ld.get('name')),
                        html.Span(ld.get('role')),
                    ], className="a-card leader")
                    for ld in c['leaders'] if ld.get('name')
                ], className="leader-grid"),
            ], className="site-section"),
        ], className="site-container narrow"),
    ], className="site-shell")
