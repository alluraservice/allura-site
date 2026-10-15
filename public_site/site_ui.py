"""
Shared building blocks for the public site (the counterpart of admin_ui.py).
Styles: assets/css/20_layout.css (page hero) and 40_site.css.
"""
from dash import dcc, html

FALLBACK_IMG = "/assets/icons/product_icon.svg"


def page_header(title, subtitle=None, crumbs=None, actions=None, variant=None):
    """Green page hero, same spacing as the admin one.
    crumbs: list of (label, href) tuples; the last one can have href=None.
    variant='feature': larger and centred (About Us)."""
    crumb_bits = []
    for i, (label, href) in enumerate(crumbs or []):
        if i:
            crumb_bits.append("  /  ")
        crumb_bits.append(dcc.Link(label, href=href) if href else html.Span(label))
    return html.Div(html.Div(html.Div([
        html.Div([
            html.Div(crumb_bits, className="crumbs") if crumb_bits else None,
            html.H1(title),
            html.P(subtitle) if subtitle else None,
        ]),
        html.Div(actions, className="header-actions") if actions else None,
    ], className="d-flex justify-content-between align-items-end gap-3 flex-wrap"),
        className="page-hero-inner"), className="page-hero is-site" + (f" hero-{variant}" if variant else ""))


def section_head(eyebrow, title, lead=None, center=False):
    return html.Div([
        html.P(eyebrow, className="site-eyebrow") if eyebrow else None,
        html.H2(title, className="site-h2"),
        html.P(lead, className="site-lead") if lead else None,
    ], className="site-section-head" + (" center" if center else ""))


def item_image_src(raw):
    raw = str(raw or "").strip()
    return f"/{raw.lstrip('/')}" if raw else FALLBACK_IMG


def is_visible(item):
    """Items an admin has hidden never appear on the public site."""
    return item.get('is_active') is not False


def catalog_href(kind=None, target_id=None):
    """Link into the product list, pre-filtered to a category or modality."""
    if kind in ('category', 'modality') and target_id not in (None, '', 'none'):
        return f"/products/all?type={kind}&id={target_id}"
    return "/products/all"
