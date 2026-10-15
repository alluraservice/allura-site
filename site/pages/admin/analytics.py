"""
Reports & Analytics — an inquiry & operations report for a chosen period.

Everything in the report lives inside one `.report-sheet`. "Print report" lays that sheet out at
A4 width, scales it to fit one page, and prints ONLY the sheet (no navbar, header, filters or footer).
Use "Save as PDF" in the print dialog to get the PDF. Print logic: assets/admin_print.js.
"""
from datetime import datetime, timedelta

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, clientside_callback, dcc, html

import admin_ui as ui
from database.db_handler import PERIOD_LABELS, get_account_by_email, get_analytics_report

dash.register_page(__name__, path='/admin/analytics')

GREEN, GREEN_LIGHT, INK, MUTED, GRID = '#006400', '#7fb069', '#1f2e1f', '#66766a', '#edf2e6'
STATUS_COLORS = {'New': '#1d5f8f', 'Urgent': '#b42318', 'In Progress': '#c99700', 'Resolved': '#006400'}
FONT = dict(family="Glacial Indifference, Inter, sans-serif", size=11, color=INK)
GRAPH_CONFIG = {'displayModeBar': False}


def layout():
    return html.Div([
        ui.page_header(
            "Reports & Analytics",
            "Inquiry demand, response performance and team workload.",
            crumbs="Admin  /  Reports & Analytics",
            actions=[
                dbc.Select(id='an-period', value='30d', className="a-input", style={'width': '170px'},
                           options=[{'label': v, 'value': k} for k, v in PERIOD_LABELS.items()]),
                html.Button("Print report", id='an-print', n_clicks=0, className="a-btn a-btn-light"),
            ],
        ),
        html.Div([
            html.Div("Tip: in the print dialog choose “Save as PDF” to download the one-page report.",
                     className="a-help mb-2 no-print"),
            dcc.Loading(html.Div(id='an-report'), type='dot', color='#006400'),
        ], className="admin-container"),
        html.Div(id='an-print-dummy', style={'display': 'none'}),
    ], className="admin-shell")


# ---------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------
def _pct(a, b):
    return f"{(a / b * 100):.0f}%" if b else "—"


def _hours(h):
    if h is None:
        return "—"
    if h < 1:
        return f"{h * 60:.0f} min"
    if h < 48:
        return f"{h:.1f} hrs"
    return f"{h / 24:.1f} days"


def _delta(cur, prev, label):
    if prev is None:
        return None
    if prev == 0:
        return html.Span(f"{'New activity' if cur else 'No change'} {label}")
    change = (cur - prev) / prev * 100
    cls = 'delta-up' if change > 0 else ('delta-down' if change < 0 else '')
    arrow = '▲' if change > 0 else ('▼' if change < 0 else '■')
    return html.Span([html.Span(f"{arrow} {abs(change):.0f}%", className=cls), f" {label}"])


def _stat(k, v, s=None, cls=''):
    return html.Div([html.Div(k, className="k"), html.Div(v, className="v"),
                     html.Div(s, className="s") if s is not None else None], className=f"stat {cls}")


def _base_layout(fig, height):
    fig.update_layout(
        height=height, margin=dict(t=8, b=28, l=36, r=10), font=FONT,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(bgcolor='#ffffff', bordercolor='#e2e9d8', font=dict(family=FONT['family'], color=INK)),
        legend=dict(orientation='h', y=1.12, x=0, font=dict(size=11, color=MUTED)),
    )
    fig.update_xaxes(showgrid=False, linecolor='#d9e2cf', tickfont=dict(color=MUTED), ticks='')
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED), rangemode='tozero')
    return fig


def _graph(fig):
    # Fixed height (from the figure) + width that follows the panel: keeps charts intact on screen and in print
    return dcc.Graph(figure=fig, config=GRAPH_CONFIG, responsive=True,
                     style={'height': f"{fig.layout.height}px", 'width': '100%'})


def _buckets(start, end, granularity):
    """All bucket starts between start and end, matching Postgres date_trunc."""
    d = start.replace(hour=0, minute=0, second=0, microsecond=0)
    if granularity == 'week':
        d -= timedelta(days=d.weekday())
    elif granularity == 'month':
        d = d.replace(day=1)
    out = []
    while d <= end:
        out.append(d)
        if granularity == 'day':
            d += timedelta(days=1)
        elif granularity == 'week':
            d += timedelta(days=7)
        else:
            d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return out


# ---------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------
def _volume_chart(r):
    rows = {row['bucket'].replace(tzinfo=None): row for row in r['series']}
    start = r['start'] or (min(rows) if rows else datetime.now() - timedelta(days=30))
    xs = _buckets(start, r['end'], r['granularity'])
    received = [int(rows.get(x, {}).get('received', 0)) for x in xs]
    resolved = [int(rows.get(x, {}).get('resolved', 0)) for x in xs]
    fmt = {'day': '%b %d', 'week': 'Week of %b %d', 'month': '%b %Y'}[r['granularity']]
    labels = [x.strftime(fmt) for x in xs]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=received, name='Received', mode='lines', line=dict(color=GREEN, width=2.2),
                             fill='tozeroy', fillcolor='rgba(0,100,0,.07)', customdata=labels,
                             hovertemplate='%{customdata}<br><b>%{y}</b> received<extra></extra>'))
    fig.add_trace(go.Scatter(x=xs, y=resolved, name='Since resolved', mode='lines', line=dict(color=GREEN_LIGHT, width=2, dash='dot'),
                             customdata=labels, hovertemplate='%{customdata}<br><b>%{y}</b> since resolved<extra></extra>'))
    _base_layout(fig, 230)
    fig.update_layout(hovermode='x unified')
    fig.update_yaxes(dtick=max(1, round(max(received + [1]) / 4)))
    return fig


def _status_chart(k):
    labels = ['New', 'Urgent', 'In Progress', 'Resolved']
    keys = ['new_count', 'urgent', 'in_progress', 'resolved']
    values = [int(k.get(x) or 0) for x in keys]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=.62, sort=False, direction='clockwise',
        marker=dict(colors=[STATUS_COLORS[l] for l in labels], line=dict(color='#ffffff', width=2)),
        textinfo='value', textfont=dict(color='#ffffff', size=11),
        hovertemplate='%{label}: <b>%{value}</b> (%{percent})<extra></extra>',
    ))
    total = sum(values)
    fig.add_annotation(text=f"<b style='font-size:20px'>{total}</b><br><span style='color:{MUTED}'>inquiries</span>",
                       showarrow=False, font=FONT)
    _base_layout(fig, 230)
    fig.update_layout(margin=dict(t=8, b=8, l=8, r=8), showlegend=True,
                      legend=dict(orientation='v', y=.5, x=1.02, yanchor='middle'))
    return fig


def _category_chart(cats):
    cats = list(reversed(cats[:8]))
    fig = go.Figure(go.Bar(
        x=[int(c['count']) for c in cats], y=[c['category'] for c in cats], orientation='h',
        marker=dict(color=GREEN, cornerradius=4), text=[int(c['count']) for c in cats], textposition='outside',
        textfont=dict(color=INK, size=11), cliponaxis=False,
        hovertemplate='%{y}: <b>%{x}</b> inquiries<extra></extra>',
    ))
    _base_layout(fig, max(150, 26 * len(cats) + 30))
    fig.update_layout(margin=dict(t=4, b=20, l=8, r=28), bargap=.35)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, rangemode='tozero')
    fig.update_yaxes(showgrid=False, automargin=True, tickfont=dict(color=INK))
    return fig


# ---------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------
def _highlights(r):
    k, out = r['kpi'], []
    total = int(k.get('total') or 0)
    if not total:
        return [html.Li(f"No inquiries were received in this period ({r['period_label'].lower()}).")]
    line = f"{total} inquir{'y was' if total == 1 else 'ies were'} received ({r['period_label'].lower()})"
    if r['prev_total'] is not None:
        prev = r['prev_total']
        if prev:
            ch = (total - prev) / prev * 100
            line += f", {'up' if ch >= 0 else 'down'} {abs(ch):.0f}% {r['compare_label']} ({prev})"
        else:
            line += f"; there were none {r['compare_label'].replace('vs ', 'in the ')}"
    out.append(html.Li(line + "."))
    if r['categories']:
        c = r['categories'][0]
        out.append(html.Li(f"{c['category']} was the most requested category with {c['count']} inquiries ({_pct(c['count'], total)})."))
    if r['sources']:
        s = r['sources'][0]
        out.append(html.Li(f"Most inquiries came through {s['source']} ({_pct(s['count'], total)})."))
    responded = int(k.get('responded') or 0)
    if responded:
        out.append(html.Li(f"Median time to first reply was {_hours(k.get('median_response_hrs'))}; "
                           f"{responded} of {total} inquiries have been answered by email."))
    if r['open_now']:
        txt = f"{r['open_now']} inquiries are still open across all time"
        if r['oldest_open_days']:
            txt += f"; the oldest has been waiting {r['oldest_open_days']} days"
        unassigned = int(k.get('unassigned_open') or 0)
        if unassigned:
            txt += f". {unassigned} open inquiries from this period have no one assigned"
        out.append(html.Li(txt + "."))
    if r['top_clients']:
        t = r['top_clients'][0]
        if int(t['inquiry_count']) > 1:
            out.append(html.Li(f"{t['customer_name']} was the most active client with {t['inquiry_count']} inquiries."))
    return out


def _source_panel(r, total):
    rows = []
    for s in r['sources']:
        n = int(s['count'])
        rows.append(html.Tr([
            html.Td(s['source']),
            html.Td(html.Div(html.Div(style={'width': f"{(n / total * 100) if total else 0:.0f}%"}), className="bar-inline"),
                    style={'width': '45%'}),
            html.Td(n, className="num"), html.Td(_pct(n, total), className="num muted"),
        ]))
    if not rows:
        rows = [html.Tr(html.Td("No data", colSpan=4, className="muted"))]
    return html.Table([html.Thead(html.Tr([html.Th("Channel"), html.Th(""), html.Th("Count", className="num"), html.Th("Share", className="num")])),
                       html.Tbody(rows)], className="a-table")


def _clients_table(r):
    rows = [html.Tr([html.Td(c['customer_name']), html.Td(int(c['inquiry_count']), className="num"),
                     html.Td(int(c['open_count']), className="num"),
                     html.Td(ui.fmt_date(c['last_inquiry']), className="num muted nowrap")]) for c in r['top_clients']]
    if not rows:
        rows = [html.Tr(html.Td("No client activity in this period.", colSpan=4, className="muted"))]
    return html.Table([html.Thead(html.Tr([html.Th("Institution"), html.Th("Inquiries", className="num"),
                                           html.Th("Open", className="num"), html.Th("Latest", className="num")])),
                       html.Tbody(rows)], className="a-table")


def _workload_table(r):
    rows = [html.Tr([html.Td(w['name']), html.Td(int(w['assigned']), className="num"), html.Td(int(w['open']), className="num"),
                     html.Td(int(w['resolved']), className="num"), html.Td(int(w['replies']), className="num")])
            for w in r['workload']]
    if not rows:
        rows = [html.Tr(html.Td("No inquiries have been assigned in this period.", colSpan=5, className="muted"))]
    return html.Table([html.Thead(html.Tr([html.Th("Team member"), html.Th("Assigned", className="num"), html.Th("Open", className="num"),
                                           html.Th("Resolved", className="num"), html.Th("Replies", className="num")])),
                       html.Tbody(rows)], className="a-table")


@callback(
    Output('an-report', 'children'),
    Input('an-period', 'value'),
    State('session-admin-email', 'data'),
    State('session-admin-name', 'data'),
)
def render_report(period, s_email, s_name):
    r = get_analytics_report(period or '30d')
    k = r['kpi']
    total = int(k.get('total') or 0)
    resolved = int(k.get('resolved') or 0)
    me = get_account_by_email(s_email) if s_email else None
    prepared_by = (me or {}).get('name') or s_name or 'Allura Admin'
    if r['start']:
        span = f"{r['start']:%b %d, %Y} – {r['end']:%b %d, %Y}"
    else:
        span = f"All records up to {r['end']:%b %d, %Y}"

    kpis = html.Div([
        _stat("Inquiries received", total, _delta(total, r['prev_total'], r['compare_label'])),
        _stat("Open right now", r['open_now'],
              f"Oldest waiting {r['oldest_open_days']} days" if r['oldest_open_days'] else "Nothing waiting",
              'warn' if r['open_now'] else ''),
        _stat("Resolution rate", _pct(resolved, total), f"{resolved} of {total} resolved"),
        _stat("Median first reply", _hours(k.get('median_response_hrs')), f"{int(k.get('responded') or 0)} answered by email"),
        _stat("Avg. time to resolve", f"{k['avg_resolve_days']:.1f} days" if k.get('avg_resolve_days') else "—",
              "From received to resolved"),
        _stat("Unassigned & open", int(k.get('unassigned_open') or 0), f"{int(k.get('high_priority') or 0)} marked high priority",
              'amber' if k.get('unassigned_open') else ''),
    ], className="report-grid kpis")

    def panel(title, caption, body):
        return html.Div([html.H6(title), html.Div(caption, className="cap"), body], className="report-panel")

    return html.Div([
        html.Div([
            html.Div([
                html.Img(src='/assets/logos/alluralogo1.png', alt='Allura Enterprise'),
                html.Div([html.P("Inquiry & Operations Report", className="title"),
                          html.Div("Allura Enterprise  ·  Admin analytics", className="text-muted", style={'fontSize': '.8rem'})]),
            ], className="d-flex align-items-center gap-3"),
            html.Div([
                html.Div([html.B("Period: "), f"{r['period_label']} ({span})"]),
                html.Div([html.B("Generated: "), datetime.now().strftime('%b %d, %Y %I:%M %p')]),
                html.Div([html.B("Prepared by: "), prepared_by]),
            ], className="meta"),
        ], className="report-head"),

        kpis,

        html.Div(panel("Key findings", "Generated from the figures in this report",
                       html.Ul(_highlights(r), className="highlights")), className="report-grid"),

        html.Div([
            panel("Inquiry volume", f"Received per {r['granularity']}; dotted line = how many of those are now resolved",
                  _graph(_volume_chart(r))),
            panel("Status breakdown", "Inquiries received in this period, by current status",
                  _graph(_status_chart(k))),
        ], className="report-grid two"),

        html.Div([
            panel("Demand by equipment category", "Grouped from the inquiry text",
                  _graph(_category_chart(r['categories'])) if r['categories']
                  else html.Div("No data", className="text-muted")),
            panel("Inquiry channels", "Which website form the inquiry came from", _source_panel(r, total)),
        ], className="report-grid two-even"),

        html.Div([
            panel("Top institutions", "Most inquiries in this period", _clients_table(r)),
            panel("Team workload", "Inquiries assigned in this period and email replies sent", _workload_table(r)),
        ], className="report-grid two-even"),

        html.Div([
            html.Span(f"Active catalog items: {r['catalog_items']}  ·  Active admin accounts: {r['active_accounts']}"),
            html.Span("Allura Enterprise  ·  Confidential, for internal use"),
        ], className="report-foot"),
    ], className="report-sheet")


# ---------------------------------------------------------------------
# Print: handled in the browser by assets/admin_print.js
# ---------------------------------------------------------------------
clientside_callback(
    """
    function(n) {
        if (n > 0 && window.alluraPrintReport) { window.alluraPrintReport(); }
        return '';
    }
    """,
    Output('an-print-dummy', 'children'),
    Input('an-print', 'n_clicks'),
    prevent_initial_call=True,
)
