"""
Printable documents for the Inquiries manager (Admin › Inquiries › Print / PDF).

Two documents, both A4 portrait and in the brand layout (Brand Bible, Part 08 · Proposals & Quotations):
    inquiry_record_html(...)  - the inquiry on Allura letterhead: client details, the request and,
                                optionally, the email thread and internal notes. For filing / internal use.
    quotation_html(...)       - a client quotation built from the inquiry: reference number, date,
                                addressee, line items, VAT treatment, validity, delivery, warranty,
                                payment terms, named contact and signature blocks.

Each function returns a complete, self-contained HTML page. The Inquiries page loads it into a
hidden frame and opens the browser's print dialog, where "Save as PDF" produces the PDF.
The reference number is printed on every page (repeating footer).
"""
from datetime import date, datetime
from html import escape

from app import app

COMPANY = {
    'name': 'Allura Enterprise',
    'address': 'Doña Paz Village, Cruzada, Legazpi City',
    'phone': '+63 917 770 1820',
    'email': 'info@alluraenterpriseph.com',
    'web': 'alluraenterpriseph.com',
}
VAT_RATE = 0.12
VAT_MODES = {
    'incl': 'Prices are VAT inclusive (12%)',
    'excl': 'Prices are VAT exclusive; 12% VAT is added',
    'exempt': 'VAT exempt',
}


# ---------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------
def _e(text):
    """Escape for HTML and keep line breaks."""
    return escape(str(text or '')).replace('\n', '<br>')


def doc_date(value=None):
    """Brand Bible date style: 15 October 2026."""
    if isinstance(value, str) and value:
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    value = value or date.today()
    return f"{value.day} {value.strftime('%B %Y')}"


def doc_datetime(value):
    if not value:
        return '—'
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return f"{doc_date(value)}, {value.strftime('%I:%M %p').lstrip('0')}"


def money(x):
    return f"{x:,.2f}"


def to_number(x):
    """Table cells can come back as numbers, '1,250,000', '' or None."""
    if x in (None, ''):
        return None
    try:
        return float(str(x).replace(',', '').replace('PHP', '').replace('₱', '').strip())
    except ValueError:
        return None


def quote_lines(rows):
    """Cleans the line-item table. Returns [(description, qty, unit_price, amount)], skipping empty rows."""
    lines = []
    for r in rows or []:
        desc = (r.get('item') or '').strip()
        qty = to_number(r.get('qty'))
        price = to_number(r.get('price'))
        if not desc and price is None:
            continue
        qty = qty if qty is not None else 1
        lines.append((desc, qty, price, qty * price if price is not None else None))
    return lines


def quote_totals(lines, vat_mode):
    """Returns (rows for the totals block, grand total)."""
    subtotal = sum(a for *_, a in lines if a is not None)
    if vat_mode == 'excl':
        vat = subtotal * VAT_RATE
        total = subtotal + vat
        return [('Subtotal (VAT exclusive)', subtotal), ('Add: VAT (12%)', vat)], total, 'Total (VAT inclusive)'
    if vat_mode == 'exempt':
        return [], subtotal, 'Total (VAT exempt)'
    vat = subtotal * VAT_RATE / (1 + VAT_RATE)
    return [('VATable amount', subtotal - vat), ('VAT (12%)', vat)], subtotal, 'Total (VAT inclusive)'


def _qty(q):
    return f"{int(q):,}" if float(q).is_integer() else f"{q:,.2f}"


# ---------------------------------------------------------------------
# shared page shell
# ---------------------------------------------------------------------
def _css():
    latin = app.get_asset_url('fonts/league-spartan-latin.woff2')
    latin_ext = app.get_asset_url('fonts/league-spartan-latin-ext.woff2')
    face = """
@font-face {{ font-family: 'League Spartan'; font-weight: 100 900; font-display: block;
  ascent-override: 91%; descent-override: 25%; line-gap-override: 0%;
  src: url('{u}') format('woff2-variations'), url('{u}') format('woff2'); unicode-range: {r}; }}"""
    return (face.format(u=latin, r="U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, "
                                   "U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, "
                                   "U+2212, U+2215, U+FEFF, U+FFFD")
            + face.format(u=latin_ext, r="U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, "
                                         "U+1E00-1E9F, U+20A0-20AB, U+20AD-20C0, U+2113, U+A720-A7FF")
            + """
@page { size: A4 portrait; margin: 16mm 20mm 12mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; background: #fff; }
body { font-family: 'League Spartan', Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #1f2e1f; }
.sheet { width: 100%; border-collapse: collapse; }
.sheet > thead td, .sheet > tfoot td { padding: 0; }
.foot-space { height: 14mm; }
.page-foot { position: fixed; left: 0; right: 0; bottom: 0; display: flex; justify-content: space-between; gap: 12px;
             padding-top: 6px; border-top: 1px solid #e2e9d8; font-size: 8pt; color: #66766a; background: #fff; }
.page-foot b { color: #084008; letter-spacing: .03em; }

.head { display: flex; justify-content: space-between; align-items: flex-end; gap: 20px;
        padding-bottom: 12px; border-bottom: 2px solid #0b6e0b; }
.head img { height: 14mm; width: auto; display: block; }
.head .doc { text-align: right; }
.head .doc h1 { margin: 0; font-size: 20pt; line-height: 1; font-weight: 700; color: #084008; letter-spacing: .14em; }
.head .doc .ref { margin-top: 6px; font-size: 10.5pt; font-weight: 700; color: #0b6e0b; letter-spacing: .04em; }
.head .doc .date { font-size: 9.5pt; color: #66766a; }
.company { margin-top: 6px; font-size: 8.5pt; color: #66766a; }

h2 { font-size: 9pt; letter-spacing: .16em; text-transform: uppercase; color: #0b6e0b; margin: 14px 0 5px; font-weight: 700; }
p { margin: 0 0 8px; }
.muted { color: #66766a; }
.block { break-inside: avoid; page-break-inside: avoid; }

.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 24px; }
.kv .k { font-size: 8pt; letter-spacing: .08em; text-transform: uppercase; color: #66766a; }
.kv .v { font-weight: 600; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.chip { border: 1px solid #e2e9d8; background: #f5f7f1; border-radius: 999px; padding: 3px 10px; font-size: 8.5pt; }
.chip b { color: #084008; }
.box { border: 1px solid #e2e9d8; border-radius: 8px; padding: 10px 12px; }
.box.tint { background: #f5f7f1; }

.msg { border-left: 3px solid #0b6e0b; padding: 6px 0 6px 12px; margin: 0 0 10px; break-inside: avoid; }
.msg.note { border-left-color: #c99700; }
.msg .mh { display: flex; justify-content: space-between; gap: 12px; font-size: 8.5pt; color: #66766a; margin-bottom: 3px; }
.msg .mh b { color: #1f2e1f; }
.event { font-size: 8.5pt; color: #66766a; margin: 0 0 6px 15px; }

.to { margin-top: 12px; }
.subject { margin: 12px 0 8px; font-weight: 700; }
table.items { width: 100%; border-collapse: collapse; margin: 6px 0 4px; }
table.items th { background: #084008; color: #fff; font-size: 8.5pt; letter-spacing: .06em; text-transform: uppercase;
                 text-align: left; padding: 7px 9px; font-weight: 700; }
table.items td { padding: 6px 9px; border-bottom: 1px solid #e2e9d8; vertical-align: top; }
table.items tr { break-inside: avoid; page-break-inside: avoid; }
table.items .n { width: 7%; color: #66766a; }
table.items .q { width: 9%; text-align: right; }
table.items .p, table.items .a { width: 19%; text-align: right; white-space: nowrap; }
table.items th.q, table.items th.p, table.items th.a { text-align: right; }
table.totals { width: 52%; margin-left: auto; border-collapse: collapse; break-inside: avoid; }
table.totals td { padding: 5px 9px; text-align: right; }
table.totals td:first-child { text-align: left; color: #66766a; }
table.totals tr.grand td { border-top: 2px solid #0b6e0b; font-weight: 700; font-size: 11.5pt; color: #084008; padding-top: 8px; }
table.totals tr.grand td:first-child { color: #084008; }
.terms { display: grid; grid-template-columns: 30% 70%; gap: 4px 0; }
.terms .k { color: #66766a; }
.sign { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 18px; }
.sign .line { border-top: 1px solid #1f2e1f; margin-top: 26px; padding-top: 4px; }
.sign .cap { font-size: 8.5pt; letter-spacing: .08em; text-transform: uppercase; color: #66766a; }
""")


def _page(title, header, body, foot_left, ref):
    logo = app.get_asset_url('logos/alluralogo1.png')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{escape(title)}</title><style>{_css()}</style></head>
<body>
<div class="page-foot"><span>{foot_left}</span><span><b>Ref. {escape(ref or '—')}</b></span></div>
<table class="sheet">
<tfoot><tr><td><div class="foot-space"></div></td></tr></tfoot>
<tbody><tr><td>
<div class="head">
  <div><img src="{logo}" alt="Allura Enterprise">
       <div class="company">{escape(COMPANY['address'])} · {COMPANY['phone']} · {COMPANY['email']}</div></div>
  <div class="doc">{header}</div>
</div>
{body}
</td></tr></tbody>
</table>
</body></html>"""


# ---------------------------------------------------------------------
# 1) Inquiry record
# ---------------------------------------------------------------------
def inquiry_record_html(iq, messages, include_thread=True, include_internal=False, printed_by=None,
                        source_description=None):
    ref = iq.get('reference_no') or ''
    header = (f"<h1>INQUIRY</h1><div class='ref'>Ref. {escape(ref or '—')}</div>"
              f"<div class='date'>Received {escape(doc_datetime(iq.get('created_at')))}</div>")

    came_from = source_description or iq.get('source_v') or iq.get('source') or 'Contact Us'
    if iq.get('source_detail'):
        came_from += f" ({iq['source_detail']})"
    chips = [('Status', iq.get('status') or 'New'), ('Priority', iq.get('priority_v') or iq.get('priority') or 'Normal'),
             ('Assigned to', iq.get('assignee_name') or 'Unassigned'),
             ('First response', doc_datetime(iq.get('first_response_at')) if iq.get('first_response_at') else 'Not yet replied')]
    if iq.get('resolved_at'):
        chips.append(('Resolved', doc_datetime(iq.get('resolved_at'))))
    labels = [lb for lb in (iq.get('labels') or '').split(',') if lb]
    if labels:
        chips.append(('Labels', ', '.join(labels)))

    def kv(k, v):
        return f"<div class='kv'><div class='k'>{escape(k)}</div><div class='v'>{_e(v or '—')}</div></div>"

    client = "".join([
        kv('Customer / hospital', iq.get('customer_name')),
        kv('Contact person', iq.get('contact_person')),
        kv('Department & title', iq.get('department')),
        kv('Office address', iq.get('address')),
        kv('Email', iq.get('email')),
        kv('Phone', iq.get('phone')),
    ])

    body = [
        "<div class='chips'>" + "".join(f"<span class='chip'>{escape(k)}: <b>{escape(str(v))}</b></span>"
                                        for k, v in chips) + "</div>",
        "<h2>Client</h2>", f"<div class='grid block'>{client}</div>",
        "<h2>Request</h2>",
        f"<div class='muted' style='font-size:9pt;margin-bottom:4px'>Sent from: {escape(came_from)}</div>",
        f"<div class='box tint'>{_e(iq.get('machine_inquiry') or '—')}</div>",
    ]
    if (iq.get('remarks') or '').strip():
        body += ["<h2>Remarks</h2>", f"<div class='box'>{_e(iq['remarks'])}</div>"]

    thread = []
    for m in messages or []:
        when = escape(doc_datetime(m.get('created_at')))
        if m['kind'] == 'reply' and include_thread:
            status = 'replied by email' if m.get('sent_ok') else 'reply saved, NOT delivered'
            subj = f"<div style='font-weight:700;margin-bottom:2px'>{_e(m.get('subject'))}</div>" if m.get('subject') else ''
            thread.append(f"<div class='msg'><div class='mh'><span><b>{_e(m.get('author') or 'Allura')}</b> {status}</span>"
                          f"<span>{when}</span></div>{subj}<div>{_e(m.get('body'))}</div></div>")
        elif m['kind'] == 'note' and include_internal:
            thread.append(f"<div class='msg note'><div class='mh'><span><b>{_e(m.get('author') or 'Team')}</b> "
                          f"internal note</span><span>{when}</span></div><div>{_e(m.get('body'))}</div></div>")
        elif m['kind'] == 'event' and include_internal:
            thread.append(f"<div class='event'>{_e(m.get('author') or 'System')} {_e(m.get('body'))} · {when}</div>")
    if thread:
        body += ["<h2>" + ("Conversation and activity" if include_internal else "Replies sent") + "</h2>", *thread]

    printed = f"Printed {doc_datetime(datetime.now())}" + (f" by {printed_by}" if printed_by else "")
    foot = f"{COMPANY['name']} · Inquiry record · {escape(printed)}" + (" · Internal, do not forward" if include_internal else "")
    title = f"{ref} Inquiry - {iq.get('customer_name') or ''}".strip(' -')
    return _page(title, header, "\n".join(body), foot, ref), title


# ---------------------------------------------------------------------
# 2) Quotation
# ---------------------------------------------------------------------
def quotation_html(iq, *, to_block, subject, salutation, intro, rows, vat_mode='incl', doc_day=None,
                   validity='', delivery='', warranty='', payment='', notes='', prepared_by=None, prepared_role=None,
                   prepared_email=None):
    """Returns (html, title, grand_total). rows: [{'item', 'qty', 'price'}, ...]."""
    ref = iq.get('reference_no') or ''
    lines = quote_lines(rows)
    extra_rows, total, total_label = quote_totals(lines, vat_mode)

    header = (f"<h1>QUOTATION</h1><div class='ref'>Ref. {escape(ref or '—')}</div>"
              f"<div class='date'>{escape(doc_date(doc_day))}</div>")

    items = "".join(
        f"<tr><td class='n'>{i}</td><td>{_e(d)}</td><td class='q'>{_qty(q)}</td>"
        f"<td class='p'>{money(p) if p is not None else 'TBA'}</td><td class='a'>{money(a) if a is not None else 'TBA'}</td></tr>"
        for i, (d, q, p, a) in enumerate(lines, 1))
    totals = "".join(f"<tr><td>{escape(k)}</td><td>{money(v)}</td></tr>" for k, v in extra_rows)
    totals += f"<tr class='grand'><td>{escape(total_label)}</td><td>PHP {money(total)}</td></tr>"

    def term(k, v):
        return f"<div class='k'>{escape(k)}</div><div>{_e(v or 'To be confirmed')}</div>"

    terms = "".join([
        term('Validity', validity), term('VAT', VAT_MODES.get(vat_mode, VAT_MODES['incl'])),
        term('Delivery', delivery), term('Warranty', warranty), term('Payment terms', payment),
    ])

    contact_bits = [b for b in [prepared_by, prepared_role] if b]
    contact = ", ".join(contact_bits) if contact_bits else "our sales team"
    reach = " or ".join([b for b in [prepared_email, COMPANY['phone']] if b])
    closing = (f"For questions about this quotation, please contact {escape(contact)} at {escape(reach)}, "
               f"quoting reference {escape(ref)}.")

    body = [
        f"<div class='to'><span class='muted'>To:</span><br><b>{_e(to_block)}</b></div>",
        f"<div class='subject'>Subject: {_e(subject)}</div>",
        f"<p>{_e(salutation)}</p>",
        f"<p>{_e(intro)}</p>" if (intro or '').strip() else "",
        "<table class='items'><thead><tr><th class='n'>No.</th><th>Item</th><th class='q'>Qty</th>"
        "<th class='p'>Unit price (PHP)</th><th class='a'>Amount (PHP)</th></tr></thead>"
        f"<tbody>{items}</tbody></table>",
        f"<table class='totals'>{totals}</table>",
        f"<div class='block'><h2>Terms</h2><div class='terms'>{terms}</div></div>",
        f"<div class='block'><h2>Notes</h2><p>{_e(notes)}</p></div>" if (notes or '').strip() else "",
        f"<div class='block'><p style='margin-top:14px'>{closing}</p>",
        "<div class='sign'>"
        f"<div><div class='cap'>Prepared by</div><div class='line'><b>{_e(prepared_by or '')}</b><br>"
        f"<span class='muted'>{_e(prepared_role or '')}{' · ' if prepared_role else ''}{COMPANY['name']}</span></div></div>"
        "<div><div class='cap'>Conforme</div><div class='line'><b>&nbsp;</b><br>"
        "<span class='muted'>Signature over printed name · Date</span></div></div>"
        "</div></div>",
    ]
    foot = f"{COMPANY['name']} · {escape(COMPANY['address'])} · {COMPANY['web']}"
    title = f"{ref} Quotation - {iq.get('customer_name') or ''}".strip(' -')
    return _page(title, header, "\n".join(body), foot, ref), title, total
