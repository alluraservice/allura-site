"""Shared building blocks for the admin pages (styles: assets/css/*.css, mainly 50_admin.css)."""
from datetime import datetime, date

from dash import html

AVATAR_COLORS = ['#006400', '#084008', '#2f7d32', '#1d5f8f', '#7a5c00', '#5b3f8c', '#8a3b12']

# Inquiry channel -> chip colour class (see .chip-src-* in 10_components.css)
SOURCE_CHIP = {'Product Page': 'chip-src-product', 'Service Page': 'chip-src-service', 'Contact Us': 'chip-src-contact'}


def page_header(title, subtitle=None, crumbs="Admin", actions=None, variant=None, title_id=None, crumbs_id=None):
    """Green page hero, identical spacing to the public pages. variant='grey' = dashboard header."""
    return html.Div(
        html.Div(
            html.Div([
                html.Div([
                    html.Div(crumbs, className="crumbs", **({'id': crumbs_id} if crumbs_id else {})),
                    html.H1(title, **({'id': title_id} if title_id else {})),
                    html.P(subtitle) if subtitle else None,
                ]),
                html.Div(actions or [], className="header-actions"),
            ], className="d-flex justify-content-between align-items-end flex-wrap gap-3"),
            className="page-hero-inner",
        ),
        className="page-hero no-print" + (f" hero-{variant}" if variant else ""),
    )


def item_image_src(image_url):
    """Same rule the public pages use, plus a fallback icon when there's no photo."""
    if not image_url or not str(image_url).strip() or str(image_url).strip().lower() == 'none':
        return '/assets/icons/product_icon.svg'
    return f"/{str(image_url).lstrip('/')}"


def status_chip(status):
    status = status or 'New'
    return html.Span(status, className=f"chip chip-{status.lower().replace(' ', '-')}")


def source_chip(source, detail=None):
    source = source or 'Contact Us'
    label = f"{source}: {detail}" if detail else source
    return html.Span(label, className=f"chip plain chip-src {SOURCE_CHIP.get(source, 'chip-src-contact')}",
                     title=f"Sent from the {source}" + (f" ({detail})" if detail else ""))


def ref_chip(reference_no):
    return html.Span(reference_no, className="chip plain chip-ref", title="Reference number") if reference_no else None


def initials(name):
    parts = [p for p in (name or '').split() if p[:1].isalpha()]
    if not parts:
        return '?'
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else '')).upper()


def avatar(name, size_class=''):
    color = AVATAR_COLORS[sum(map(ord, name or '')) % len(AVATAR_COLORS)]
    return html.Span(initials(name), className=f"avatar {size_class}", style={'background': color})


def fmt_date(value, with_time=False):
    if not value:
        return '—'
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(value, datetime):
        return value.strftime('%b %d, %Y %I:%M %p' if with_time else '%b %d, %Y')
    if isinstance(value, date):
        return value.strftime('%b %d, %Y')
    return str(value)


def short_when(value):
    """Gmail-style: time today, 'Oct 3' this year, '10/03/25' otherwise."""
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    now = datetime.now()
    if value.date() == now.date():
        return value.strftime('%I:%M %p').lstrip('0')
    if value.year == now.year:
        return value.strftime('%b %d').replace(' 0', ' ')
    return value.strftime('%m/%d/%y')


def time_ago(value):
    if not value:
        return 'never'
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    secs = (datetime.now() - value).total_seconds()
    if secs < 60:
        return 'just now'
    for unit, n in (('day', 86400), ('hour', 3600), ('minute', 60)):
        if secs >= n:
            k = int(secs // n)
            if unit == 'day' and k > 30:
                return fmt_date(value)
            return f"{k} {unit}{'s' if k != 1 else ''} ago"
    return 'just now'


def alert(message, kind='ok'):
    if not message:
        return None
    return html.Div(message, className=f"a-alert a-alert-{kind}")
