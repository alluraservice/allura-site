"""
Shared building blocks for the public site (the counterpart of admin_ui.py).
Styles: assets/css/20_layout.css (page hero) and 40_site.css.
"""
import re

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


# ---------------------------------------------------------------------
# Icons for product categories, modalities and services (assets/icons)
# Matched on the name stored in the database, so a renamed or new modality still gets the closest icon.
# Order matters: the first rule that matches wins.
# ---------------------------------------------------------------------
_ICON_RULES = [
    (r'\bct\b|computed tomograph', 'ct_scan.svg'),
    (r'\bmri\b|magnetic resonance', 'mri.svg'),
    (r'ultrasound|sonograph', 'ultrasound.svg'),
    (r'c[\s-]?arm', 'c-arm.svg'),
    (r'x[\s-]?ray|radiograph', 'x-ray.svg'),
    (r'cath|angiograph', 'cath_lab.svg'),
    (r'mammo', 'mammography.svg'),
    (r'monitor', 'patient_monitoring_accessories.svg'),
    (r'radiation|shield|lead apron', 'radiation_protection.svg'),
    (r'consumable|film', 'imaging_consumables.svg'),
    (r'infection|steril|disinfect', 'infection_control.svg'),
    (r'electric', 'electrical_services.svg'),
    (r'power|\bups\b', 'power_supply_services.svg'),
    (r'equipment service|maintenance|repair', 'equipment_services.svg'),
    (r'radiolog|imaging', 'radiology.svg'),
    (r'clinic', 'clinic_equipment.svg'),
    (r'suppl', 'supplies.svg'),
]


def catalog_icon(name, fallback='product_icon.svg'):
    """URL of the icon for a category / modality / service name, e.g. 'CT Scan' -> /assets/icons/ct_scan.svg."""
    text = str(name or '').lower()
    for pattern, icon in _ICON_RULES:
        if re.search(pattern, text):
            return f"/assets/icons/{icon}"
    return f"/assets/icons/{fallback}"


def icon_img(src, alt="", class_name="ico-img"):
    """A decorative icon <img>. The site's icons are white SVGs; CSS tints them where needed."""
    return html.Img(src=src, alt=alt, className=class_name, **({'aria-hidden': 'true'} if not alt else {}))
