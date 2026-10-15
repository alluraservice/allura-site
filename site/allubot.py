"""
AlluBot — Allura's floating help chat (bottom-right corner of the public site).

How it works
- Menu-driven: customers pick from questions (no typing). Each answer offers its own
  follow-up questions, so the conversation branches by topic. "Back" and "Main menu"
  are always available.
- The "What imaging systems do you carry?" answer lists the live modalities from the
  database as links, so it stays in sync with the catalog.
- Chat history is kept for the browser tab, so it survives moving between pages.
- Opened by the AlluBot icon in the navbar (#open_allubot_btn) and the "Chat with
  AlluBot" button on Home (#home_open_chatbot_btn); see assets/allubot.js.
  Styles: assets/css/allubot.css. Hidden automatically on admin pages.

To change what AlluBot says, edit COMPANY and TREE below. Nothing else needs touching.
Each entry in TREE is one question:
    "key": {
        "label":   text on the button (also shown as the customer's message),
        "answer":  AlluBot's reply,
        "links":   buttons under the reply, as (text, page) pairs,
        "options": keys of the follow-up questions offered next,
    }
"""
import dash
from dash import ALL, Input, Output, State, callback, clientside_callback, ctx, dcc, html

import site_ui as ui

try:
    from database.db_handler import get_modalities
except Exception:  # keeps the chat usable even if the database module changes
    get_modalities = None

AVATAR = "/assets/icons/allubot1.svg"   # white icon, tinted dark green by allubot.css


# =====================================================================
# 1. COMPANY FACTS — one place to keep AlluBot's details correct
# =====================================================================
COMPANY = {
    "phone": "+63 917 770 1820",
    "email": "info@alluraenterpriseph.com",
    "main_office": "Doña Paz Village, Cruzada, Legazpi City",
    "satellite_office": "Villa Angelina Phase 1, Mambog 4, Bacoor, Cavite",
}

L_PRODUCTS = ("Browse products", "/products")
L_ALL_PRODUCTS = ("See all products", "/products/all")
L_SERVICES = ("Our services", "/services")
L_CONTACT = ("Contact us", "/contact_us")
L_ABOUT = ("About Allura", "/about_us")


# =====================================================================
# 2. QUESTION TREE
# =====================================================================
MAIN_OPTIONS = ["products", "quote", "services", "about", "contact"]

TREE = {
    # ---------------- Products ----------------
    "products": {
        "label": "What products do you offer?",
        "answer": "We supply medical equipment for hospitals and clinics, mainly:\n"
                  "• Radiology & imaging systems\n"
                  "• Clinic equipment\n"
                  "• Medical supplies\n\n"
                  "What would you like to know?",
        "links": [L_PRODUCTS],
        "options": ["prod_imaging", "prod_find", "prod_brands", "prod_demo", "quote"],
    },
    "prod_imaging": {
        "label": "What imaging systems do you carry?",
        "answer": "Our radiology and imaging portfolio covers CT scan, MRI, ultrasound, X-ray, C-arm and cath lab "
                  "systems. Tap a category to see the models:",
        "dynamic": "modalities",
        "links": [L_ALL_PRODUCTS],
        "options": ["prod_demo", "quote", "svc_install"],
    },
    "prod_find": {
        "label": "How do I find a specific product?",
        "answer": "Open our product list and either pick a category on the left or type the model name in the "
                  "search box. Each product page has a Contact Sales button for quotations.\n\n"
                  "Can't find it? Ask our sales team and they'll tell you what's available.",
        "links": [L_ALL_PRODUCTS, L_CONTACT],
        "options": ["prod_imaging", "quote_single"],
    },
    "prod_brands": {
        "label": "Which brands do you carry?",
        "answer": "We source from trusted global medical technology manufacturers, and we're an appointed Fujifilm "
                  "distributor. Each product page shows the exact model. For a specific brand or model, ask our "
                  "sales team.",
        "links": [L_ALL_PRODUCTS, L_CONTACT],
        "options": ["prod_imaging", "quote"],
    },
    "prod_demo": {
        "label": "Can I request a demo?",
        "answer": "Yes. We can arrange an equipment demonstration or technical consultation. Send us the equipment "
                  "you're interested in and your facility details through the Contact Us form, and our team will "
                  "schedule it with you.",
        "links": [L_CONTACT],
        "options": ["quote", "svc_install"],
    },

    # ---------------- Quotations ----------------
    "quote": {
        "label": "How do I get a quotation?",
        "answer": "Prices depend on the model, configuration and site requirements, so we prepare a quotation "
                  "for each request. Which of these fits you?",
        "options": ["quote_single", "quote_project", "quote_gov", "quote_warranty", "quote_delivery"],
    },
    "quote_single": {
        "label": "I need a quote for one product",
        "answer": "Open the product in our catalog and click Contact Sales. Fill in your hospital and contact "
                  "details, and the request goes straight to our sales team, who will reply with a formal quotation.",
        "links": [L_ALL_PRODUCTS],
        "options": ["quote_warranty", "quote_delivery", "prod_demo"],
    },
    "quote_project": {
        "label": "I need a quote for several items or a project",
        "answer": "For multiple items, a new department or a full room setup, send the details through our "
                  "Contact Us form (or call us). We'll review your requirements, may do a site assessment, and "
                  "prepare one proposal covering equipment, installation and power needs.",
        "links": [L_CONTACT],
        "options": ["svc_install", "quote_gov", "contact"],
    },
    "quote_gov": {
        "label": "Can government hospitals buy from you?",
        "answer": "Yes. Allura is PhilGEPS Platinum registered and holds an FDA License to Operate (LTO), so we can "
                  "take part in public procurement as well as serve private hospitals.",
        "links": [L_ABOUT],
        "options": ["quote_project", "about_certs"],
    },
    "quote_warranty": {
        "label": "Is there a warranty?",
        "answer": "Warranty coverage depends on the product and manufacturer, and is spelled out in your quotation. "
                  "After the sale, our engineers also provide preventive maintenance, calibration and repairs.",
        "links": [L_SERVICES],
        "options": ["svc_pm", "quote_delivery"],
    },
    "quote_delivery": {
        "label": "How long is delivery and installation?",
        "answer": "It depends on the equipment, stock and how much site preparation is needed. The expected "
                  "timeline is confirmed in your quotation, and we schedule installation around your operations.",
        "links": [L_CONTACT],
        "options": ["svc_install", "quote_warranty"],
    },

    # ---------------- Services ----------------
    "services": {
        "label": "What services do you offer?",
        "answer": "Besides supplying equipment, we keep it running. What do you need help with?",
        "links": [L_SERVICES],
        "options": ["svc_repair", "svc_pm", "svc_install", "svc_ups", "svc_electrical", "svc_how"],
    },
    "svc_repair": {
        "label": "My equipment needs repair",
        "answer": "Sorry to hear that. Send a Service Inquiry from our Services page with the equipment model and "
                  "what's happening, and our engineers will assess it.\n\n"
                  "For urgent breakdowns, it's fastest to also call us at " + COMPANY["phone"] + ".",
        "links": [L_SERVICES],
        "options": ["svc_how", "svc_pm", "contact"],
    },
    "svc_pm": {
        "label": "Do you offer preventive maintenance?",
        "answer": "Yes. We offer preventive maintenance and calibration to keep equipment accurate and reduce "
                  "downtime. Tell us the equipment and how often you'd like it serviced, and we'll propose a "
                  "maintenance plan.",
        "links": [L_SERVICES],
        "options": ["svc_how", "svc_ups"],
    },
    "svc_install": {
        "label": "Do you handle installation?",
        "answer": "Yes. We handle projects turn-key: site assessment and preparation, delivery, installation, "
                  "power conditioning and commissioning, followed by after-sales maintenance.",
        "links": [L_SERVICES],
        "options": ["svc_electrical", "svc_ups", "quote_project"],
    },
    "svc_ups": {
        "label": "Do you supply UPS and power protection?",
        "answer": "Yes, it's one of our specialties. We supply medical-grade UPS systems and voltage stabilization "
                  "for sensitive equipment like CT and MRI, and maintain them, including battery care.",
        "links": [L_SERVICES],
        "options": ["svc_electrical", "svc_pm", "quote"],
    },
    "svc_electrical": {
        "label": "Do you do electrical works?",
        "answer": "Yes. We handle electrical work around medical equipment: site preparation for new equipment, "
                  "power distribution works and room shielding support.",
        "links": [L_SERVICES],
        "options": ["svc_install", "svc_ups"],
    },
    "svc_how": {
        "label": "How does a service request work?",
        "answer": "1. Send a Service Inquiry from our Services page.\n"
                  "2. Our engineers review it and visit the site if needed.\n"
                  "3. You receive a scope and quotation, and we agree on a schedule.\n"
                  "4. The work is done and documented, with follow-up support.",
        "links": [L_SERVICES],
        "options": ["svc_repair", "contact"],
    },

    # ---------------- About Allura ----------------
    "about": {
        "label": "Tell me about Allura",
        "answer": "Happy to! What would you like to know about us?",
        "links": [L_ABOUT],
        "options": ["about_who", "about_history", "about_why", "about_certs", "about_coverage", "about_leaders"],
    },
    "about_who": {
        "label": "Who is Allura Enterprise?",
        "answer": "Allura Enterprise is a Philippine medical equipment distributor and service provider. We bring "
                  "trusted technology from global manufacturers to local hospitals, and handle installation, power "
                  "conditioning and after-sales maintenance, so you deal with one accountable partner.",
        "links": [L_ABOUT],
        "options": ["about_history", "about_why"],
    },
    "about_history": {
        "label": "How long have you been in business?",
        "answer": "Since 2014, so over 10 years.\n"
                  "• 2014–2017: started as a regional trading business, built on long-term hospital relationships\n"
                  "• 2018–2020: focused on UPS solutions for CT, earned PhilGEPS Platinum and FDA LTO, became a Fujifilm distributor\n"
                  "• 2021–2023: expanded into major equipment sales and technical services\n"
                  "• 2024 onwards: grew into a national channel partner with a Metro Manila HQ",
        "links": [L_ABOUT],
        "options": ["about_why", "about_leaders"],
    },
    "about_why": {
        "label": "Why choose Allura?",
        "answer": "• One partner for sales and service: we supply the equipment and keep it running\n"
                  "• Power quality expertise for sensitive imaging systems\n"
                  "• PhilGEPS Platinum and FDA LTO certified\n"
                  "• Over a decade of hospital relationships, nationwide",
        "links": [L_ABOUT, L_SERVICES],
        "options": ["about_certs", "quote", "services"],
    },
    "about_certs": {
        "label": "Are you licensed and certified?",
        "answer": "Yes. Allura is PhilGEPS Platinum registered and holds an FDA License to Operate (LTO).",
        "links": [L_ABOUT],
        "options": ["quote_gov", "about_why"],
    },
    "about_coverage": {
        "label": "Which areas do you serve?",
        "answer": "We work with hospitals nationwide, with our footprint across Luzon and Visayas. If your facility "
                  "is elsewhere, send us the location and we'll tell you how we can support you.",
        "links": [L_CONTACT],
        "options": ["contact_offices", "contact"],
    },
    "about_leaders": {
        "label": "Who leads Allura?",
        "answer": "• Ceceli B. Cellona, President\n"
                  "• Eric Vincent C. Cellona, Vice President / CEO\n"
                  "• John Philip C. Cellona, Operations Head",
        "links": [L_ABOUT],
        "options": ["about_history", "contact"],
    },

    # ---------------- Contact ----------------
    "contact": {
        "label": "How can I contact your team?",
        "answer": "You can reach us directly:\n"
                  "• Phone: " + COMPANY["phone"] + "\n"
                  "• Email: " + COMPANY["email"],
        "links": [L_CONTACT],
        "options": ["contact_form", "contact_offices", "about_coverage"],
    },
    "contact_form": {
        "label": "Can I send an inquiry online?",
        "answer": "Yes. Use the inquiry form on our Contact Us page, or the Contact Sales button on any product. "
                  "Our team will get back to you by phone or email.",
        "links": [L_CONTACT],
        "options": ["quote", "services"],
    },
    "contact_offices": {
        "label": "Where are your offices?",
        "answer": "• Main office: " + COMPANY["main_office"] + "\n"
                  "• Satellite office: " + COMPANY["satellite_office"] + "\n\n"
                  "Maps for both are on our Contact Us page.",
        "links": [L_CONTACT],
        "options": ["contact", "about_coverage"],
    },
}

GREETING = ("Hi! I'm AlluBot, Allura's virtual assistant. 👋\n"
            "Choose a topic below and I'll point you in the right direction.")
BACK, MENU = "__back", "__menu"


# =====================================================================
# 3. STATE HELPERS
#    store = {"messages": [...], "path": ["main", "services", ...]}
# =====================================================================
def _bot(text, links=None):
    return {"role": "bot", "text": text, "links": [list(l) for l in (links or [])]}


def _initial():
    return {"messages": [_bot(GREETING)], "path": ["main"]}


def _valid(store):
    return isinstance(store, dict) and isinstance(store.get("messages"), list) and store.get("path")


def _modality_links():
    try:
        mods = (get_modalities() or []) if get_modalities else []
        return [(m["name"], ui.catalog_href("modality", m["id"])) for m in mods if m.get("name")]
    except Exception as e:
        print(f"AlluBot modality lookup failed: {e}")
        return []


def _options_for(key):
    return MAIN_OPTIONS if key == "main" else [k for k in TREE[key]["options"] if k in TREE and k != key]


# =====================================================================
# 4. LAYOUT
# =====================================================================
def widget():
    """Add once to app.layout (index.py)."""
    return html.Div([
        dcc.Store(id="allubot-history", data=_initial(), storage_type="session"),
        html.Div([
            html.Span(html.Img(src=AVATAR, alt=""), className="allubot-head-avatar"),
            html.Div([
                html.B("AlluBot"),
                html.Span([html.I(className="allubot-dot"), "Allura's virtual assistant"]),
            ], className="allubot-head-text"),
            html.Button("↺", id="allubot-reset", n_clicks=0, className="allubot-icon-btn", title="Start over"),
            html.Button("×", id="allubot-close", className="allubot-icon-btn", title="Close", **{"aria-label": "Close chat"}),
        ], className="allubot-head"),
        html.Div(id="allubot-messages", className="allubot-messages", **{"aria-live": "polite"}),
        html.Div([
            html.Div(id="allubot-options", className="allubot-options"),
            html.Div(id="allubot-nav", className="allubot-nav"),
        ], className="allubot-choices"),
        html.Div("AlluBot gives general information. Our team confirms quotations and bookings.",
                 className="allubot-foot"),
        html.Div(id="allubot-scroll", style={"display": "none"}),
    ], id="allubot-panel", className="allubot-panel", role="dialog", **{"aria-label": "AlluBot chat"})


def _bubble(msg):
    if msg["role"] == "user":
        return html.Div(html.Div(msg["text"], className="allubot-bubble user"), className="allubot-row user")
    links = [dcc.Link(label, href=href, className="allubot-link") for label, href in msg.get("links") or []]
    return html.Div([
        html.Span(html.Img(src=AVATAR, alt=""), className="allubot-avatar"),
        html.Div([
            html.Div(msg["text"], className="allubot-bubble bot"),
            html.Div(links, className="allubot-links") if links else None,
        ], className="allubot-bot-col"),
    ], className="allubot-row bot")


# =====================================================================
# 5. CALLBACKS
# =====================================================================
@callback(
    Output("allubot-messages", "children"),
    Output("allubot-options", "children"),
    Output("allubot-nav", "children"),
    Input("allubot-history", "data"),
)
def render(store):
    store = store if _valid(store) else _initial()
    current = store["path"][-1] if store["path"][-1] in TREE or store["path"][-1] == "main" else "main"

    options = [
        html.Button([html.Span(TREE[k]["label"]), html.Span("›", className="arrow")],
                    id={"type": "allubot-opt", "key": k}, n_clicks=0, className="allubot-option")
        for k in _options_for(current)
    ]
    nav = []
    if current != "main":
        if len(store["path"]) > 2:
            nav.append(html.Button("← Back", id={"type": "allubot-opt", "key": BACK}, n_clicks=0, className="allubot-nav-btn"))
        nav.append(html.Button("☰ Main menu", id={"type": "allubot-opt", "key": MENU}, n_clicks=0, className="allubot-nav-btn"))
    return [_bubble(m) for m in store["messages"]], options, nav


@callback(
    Output("allubot-history", "data"),
    Input({"type": "allubot-opt", "key": ALL}, "n_clicks"),
    Input("allubot-reset", "n_clicks"),
    State("allubot-history", "data"),
    prevent_initial_call=True,
)
def on_choice(_opts, _reset, store):
    trigger = ctx.triggered_id
    if trigger == "allubot-reset":
        return _initial()
    if not isinstance(trigger, dict) or not (ctx.triggered and ctx.triggered[0].get("value")):
        raise dash.exceptions.PreventUpdate          # buttons being redrawn, not clicked

    store = store if _valid(store) else _initial()
    messages, path = list(store["messages"]), list(store["path"])
    key = trigger["key"]

    if key == MENU:
        messages.append({"role": "user", "text": "Main menu"})
        messages.append(_bot("Sure! What else can I help you with?"))
        path = ["main"]
    elif key == BACK:
        if len(path) > 1:
            path.pop()
        prev = path[-1]
        messages.append({"role": "user", "text": "Go back"})
        messages.append(_bot("Okay. Here are the other questions about that." if prev != "main"
                             else "Sure! What else can I help you with?"))
    elif key in TREE:
        node = TREE[key]
        links = list(node.get("links", []))
        if node.get("dynamic") == "modalities":
            links = _modality_links() + links
        messages.append({"role": "user", "text": node["label"]})
        messages.append(_bot(node["answer"], links))
        path.append(key)
    else:
        raise dash.exceptions.PreventUpdate

    return {"messages": messages[-60:], "path": path[-20:]}


# Keep the newest message in view
clientside_callback(
    """
    function(children) {
        setTimeout(function () {
            var box = document.getElementById('allubot-messages');
            if (box) { box.scrollTop = box.scrollHeight; }
        }, 30);
        return '';
    }
    """,
    Output("allubot-scroll", "children"),
    Input("allubot-messages", "children"),
)
