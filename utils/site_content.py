"""
Editable website content (Admin › Website Content).

Text, lists and photos that used to be written into the page files are now stored in the
`site_content` table, one row per section:

    settings  - company contact details, offices, map links, social links, footer text
    home      - Home page text
    about     - About Us text, timeline and leaders
    services  - Services page text
    allubot   - AlluBot greeting and the wording of its questions and answers

DEFAULTS below holds the content the website had before the editor existed. A section that was
never saved in the admin site simply shows its default, so the website looks the same after this
update is deployed. Every save is also copied to `site_content_history`, so a save can be undone.

Pages read content with get_content('home') etc. Results are cached for CACHE_SECONDS, so a change
can take up to that long to show on every server worker.
"""
import copy
import json
import time

from database.db_handler import _run

CACHE_SECONDS = 20
SECTIONS = ['settings', 'home', 'about', 'services', 'allubot']

DEFAULTS = {
    # ------------------------------------------------------------------ Site settings
    'settings': {
        'company_name': "Allura Enterprise",
        'phone': "+63 917 770 1820",
        'email': "info@alluraenterpriseph.com",
        'website': "alluraenterpriseph.com",
        'location_short': "BGC, Taguig City, Philippines",
        'main_office': "Doña Paz Village, Cruzada, Legazpi City",
        'main_office_label': "Legazpi City",
        'satellite_office': "Villa Angelina Phase 1, Mambog 4, Bacoor Cavite",
        'satellite_office_label': "Bacoor, Cavite",
        'main_map_url': ("https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3880.799757751662!2d123.7385!3d13.1391"
                         "!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zRGHDusOZIFBheiBTdWJkaXZpc2lvbiwgQ3J1emFkYSwgTGVnYXpwaSBDaXR5"
                         "!5e0!3m2!1sen!2sph!4v1620000000000!5m2!1sen!2sph"),
        'satellite_map_url': ("https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3863.3121542122!2d120.9542!3d14.4445"
                              "!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zVmlsbGEgQW5nZWxpYSBQaGFzZSAxLCBNYW1ib2cgNCwgQmFjb29yLCBDYXZpdGU"
                              "!5e0!3m2!1sen!2sph!4v1620000000000!5m2!1sen!2sph"),
        'facebook_url': "https://www.facebook.com/profile.php?id=61589813960476",
        'linkedin_url': "https://www.linkedin.com/company/allura-enterprise/",
        'footer_text': ("Allura Enterprise is a premier Philippine medical equipment distributor and service provider, "
                        "delivering reliable radiology, imaging, and hospital infrastructure solutions nationwide."),
    },

    # ------------------------------------------------------------------ Home
    'home': {
        'hero_eyebrow': "Allura Enterprise",
        'hero_title': "Your Trusted Partner in Advanced Healthcare Solutions.",
        'hero_lead': "Medical equipment, installation and lifecycle support for Philippine hospitals, from one accountable team.",
        'intro_title': "A healthcare technology partner for Philippine hospitals",
        'intro_text': ("Since 2014, Allura Enterprise has supplied, installed and maintained medical equipment for public and "
                       "private hospitals. Whether we've worked together before or you're just getting to know us, here's "
                       "how we can help."),
        'recap_title': "Equipment, service and guidance, from one team",
        'recap_text': ("Whether you're planning a new department or keeping existing systems running, these are the three "
                       "ways we support hospitals."),
        'recap': [
            {'tag': "Equipment", 'title': "Imaging & clinical equipment",
             'text': "Diagnostic imaging and clinical systems for every department, from CT, MRI and ultrasound to X-ray, C-arm and cath lab.",
             'points': "Models sourced from trusted global manufacturers\nConfigured to your room, volume and budget\n"
                       "Formal quotation with lead time and warranty"},
            {'tag': "Service", 'title': "Installation & lifecycle care",
             'text': "The same team that supplies your equipment installs it and keeps it running afterwards.",
             'points': "Installation & commissioning\nPreventive maintenance & calibration\nRepairs by trained engineers"},
            {'tag': "Consultation", 'title': "Consultation & project planning",
             'text': "Not sure yet what your department needs? We help you plan the right equipment, site and budget before you commit.",
             'points': "Needs assessment & product recommendations\nSite visit & room planning\n"
                       "Proposals for private and government procurement"},
        ],
        'featured_title': "Imaging & Radiology Systems",
        'featured_text': ("Backed by deep technical expertise and a consultative approach, our imaging and radiology portfolio "
                          "delivers precision, reliability, and end-to-end support for modern healthcare institutions."),
        'why_title': "Why hospitals work with us",
        'why_text': "Credentials and capabilities that make a difference once equipment is on site.",
        'stats': [
            {'k': "Since 2014", 'v': "10+ years", 's': "working with hospitals"},
            {'k': "PhilGEPS", 'v': "Platinum", 's': "registered supplier"},
            {'k': "FDA", 'v': "LTO", 's': "licensed to operate"},
            {'k': "Footprint", 'v': "Nationwide", 's': "Luzon & Visayas"},
        ],
        'why': [
            {'title': "We can join public procurement",
             'text': "Our PhilGEPS Platinum registration and FDA License to Operate mean government hospitals and LGUs can buy "
                     "from us through bidding, with the documents ready when you need them."},
            {'title': "We prepare the site, not just the machine",
             'text': "Room assessment, electrical works, power distribution and shielding support are handled by our own team, "
                     "so a new system arrives to a room that is ready for it."},
            {'title': "Power quality is where we started",
             'text': "Allura began with UPS solutions for CT systems. That background shapes how we plan every installation "
                     "around stable, protected power."},
            {'title': "One partner from proposal to after-sales",
             'text': "Sales, installation and maintenance stay with one accountable team, so you never have to explain your "
                     "setup to a new supplier."},
        ],
        'steps_title': "How working with us works",
        'steps_text': "Four simple steps, whether it's your first inquiry or your next project.",
        'steps': [
            {'title': "Send your request", 'text': "Use Contact Sales on a product, the Services form, or Contact Us. You get a reference number right away."},
            {'title': "We get back to you", 'text': "Our team follows up by email or phone, quoting your reference number."},
            {'title': "Assessment & proposal", 'text': "Where needed we visit the site, then send a clear scope, quotation and schedule."},
            {'title': "Delivery & after-sales", 'text': "Installation, handover and maintenance plans, with the same team from start to finish."},
        ],
        'contact_title': "Let's Discuss Your Institution's Next Project",
        'contact_text': ("Whether you need a product proposal, equipment demonstration, or technical consultation, "
                         "our team is ready to assist you."),
        'follow_title': "Stay Connected With Allura",
        'follow_text': "Follow our journey, catch our latest industry updates, and connect with our team on social media.",
        'allubot_title': "Meet AlluBot, your quick guide to Allura",
        'allubot_text': ("Not sure where to start? Pick a topic and AlluBot will point you to the right "
                         "products, services or person to talk to."),
    },

    # ------------------------------------------------------------------ About Us
    'about': {
        'header_title': "From Regional Pioneer to National Healthcare Partner",
        'header_lead': ("Established in 2014, Allura Enterprise delivers reliable radiology, medical imaging, power infrastructure, "
                        "and specialized technical services to hospitals nationwide."),
        'stats': [
            {'k': "Since 2014", 'v': "10+ years", 's': "of serving hospitals"},
            {'k': "Certified", 'v': "Platinum", 's': "PhilGEPS & FDA LTO"},
            {'k': "Footprint", 'v': "Nationwide", 's': "Luzon & Visayas"},
            {'k': "Growth", 'v': "800%+", 's': "sales revenue growth"},
        ],
        'who_title': "Complete Technical & Solutions Care for Hospitals",
        'who_text': ("Allura Enterprise is a trusted medical device distributor and service provider. Over a decade of "
                     "organic growth has elevated us from a regional trading firm into a full-scale channel partner capable "
                     "of managing turn-key medical installations, power conditioning, and after-sales maintenance.\n\n"
                     "We solve the hospital sector's critical challenge: providing a single accountable, compliant, and "
                     "technically proficient partner that bridges global medical technology directly to local clinical operations."),
        'capabilities': [
            {'title': "Direct Sales & Distribution", 'text': "Radiology, MRI, CT Scans, Ultrasound, OR Equipment, and Hospital IT."},
            {'title': "Power Quality Solutions", 'text': "Medical-grade UPS and voltage stabilization for sensitive diagnostic gear."},
            {'title': "Lifecycle Support & Repairs", 'text': "Preventive maintenance, system calibration, site shielding, and repairs."},
        ],
        'timeline_title': "The Allura Growth Story",
        'timeline': [
            {'years': "2014 – 2017", 'title': "Phase 1: Foundation & Trust",
             'text': "Registered as a regional trading business. Built foundational trust and long-term hospital relationships "
                     "through relentless focus on customer satisfaction despite limited early resources."},
            {'years': "2018 – 2020", 'title': "Phase 2: Capability & Compliance",
             'text': "Transitioned to VAT-registered operations, focused on UPS power solutions for CT systems, and secured key "
                     "certifications including PhilGEPS Platinum and FDA LTO. Appointed Fujifilm distributor."},
            {'years': "2021 – 2023", 'title': "Phase 3: Solutions Provider Transition",
             'text': "Expanded into big-ticket equipment sales and technical services (preventive maintenance, calibration, repairs). "
                     "Delivered major projects including 32-slice CT Scans and Cardio-Vascular Ultrasound systems."},
            {'years': "2024 – 2026+", 'title': "Phase 4: National Scale & Expansion",
             'text': "Achieved a sales revenue growth of more than 800%. Transitioned into a national medical channel partner "
                     "establishing a Metro Manila National HQ."},
        ],
        'leaders_title': "Governance & Leadership",
        'leaders': [
            {'name': "Ceceli B. Cellona", 'role': "President", 'photo': "/assets/pictures/about/leader_ceceli.jpg"},
            {'name': "Eric Vincent C. Cellona", 'role': "Vice President / CEO", 'photo': "/assets/pictures/about/leader_eric.jpg"},
            {'name': "John Philip C. Cellona", 'role': "Operations Head", 'photo': "/assets/pictures/about/leader_john.jpg"},
        ],
    },

    # ------------------------------------------------------------------ Services
    'services': {
        'header_lead': "Installation, maintenance, and the electrical and power systems behind your equipment.",
        'banner_title': "Complete Healthcare Infrastructure & Equipment Solutions",
        'banner_text': ("From medical equipment installation to specialized electrical and uninterrupted power supply systems, "
                        "we deliver end-to-end technical support to keep your facility operational, safe, and efficient."),
        'areas_title': "One team for your equipment and the facility around it",
        'areas_text': ("Allura supplies medical equipment and services it too. The same engineers who know the machines also "
                       "handle the power and electrical work they depend on, so you deal with a single accountable partner."),
        'areas': [
            {'title': "Medical Equipment Services",
             'text': "Installation and lifecycle care for imaging and clinical equipment, handled by trained engineers.",
             'points': "Installation & commissioning\nPreventive maintenance programs\nCalibration & repairs",
             'photo': "/assets/pictures/services/equipment_services/medical_equipment_service_cover.webp"},
            {'title': "Electrical Services",
             'text': "Facility electrical work planned around the needs of sensitive diagnostic and clinical areas.",
             'points': "Site preparation for new equipment\nPower distribution works\nRoom shielding support",
             'photo': "/assets/pictures/services/electrical_services/electrical_service_cover.webp"},
            {'title': "Power Supply Services",
             'text': "Medical-grade power protection so CT, MRI and other critical systems stay online.",
             'points': "Medical-grade UPS systems\nVoltage stabilization\nUPS maintenance & battery care",
             'photo': "/assets/pictures/services/power_supply_services/power_supply_service_cover.jpg"},
        ],
        'steps_title': "From request to handover in four steps",
        'steps': [
            {'title': "Send a service inquiry", 'text': "Tell us about your facility, the equipment involved, and what you need, using the form on this page."},
            {'title': "Technical assessment", 'text': "Our engineers review the request and, where needed, visit the site to check the equipment and conditions."},
            {'title': "Proposal & schedule", 'text': "You receive a clear scope and quotation, then we agree on a schedule that works around your operations."},
            {'title': "Service & handover", 'text': "The work is carried out and documented, with follow-up support and maintenance plans if you need them."},
        ],
        'lifecycle_title': "A partner before, during, and after the purchase",
        'lifecycle_text': ("Buy the equipment and keep it running with the same company. Tell us what you need and our team "
                           "will get back to you with the right engineer."),
    },

    # ------------------------------------------------------------------ AlluBot
    # Only what was changed in the admin site is stored here; the full question list lives in allubot.py.
    'allubot': {
        'greeting': "Hi! I'm AlluBot. 👋\nChoose a topic below and I'll point you in the right direction.",
        'answers': {},
    },
}

_cache = {}   # section -> (time, value)


def _merge(default, saved):
    """Saved keys replace default keys; keys a newer version added keep their default."""
    out = copy.deepcopy(default)
    if isinstance(saved, dict):
        for k, v in saved.items():
            if k in out or k == 'answers':
                out[k] = v
    return out


def get_content(section):
    """The section's current content (saved values over the defaults). Never raises."""
    now = time.time()
    hit = _cache.get(section)
    if hit and now - hit[0] < CACHE_SECONDS:
        return copy.deepcopy(hit[1])
    saved = _run("SELECT value FROM site_content WHERE key = %s;", [section], fetch='scalar')
    if isinstance(saved, str):
        try:
            saved = json.loads(saved)
        except ValueError:
            saved = None
    value = _merge(DEFAULTS.get(section, {}), saved)
    _cache[section] = (now, value)
    return copy.deepcopy(value)


def settings():
    return get_content('settings')


def save_content(section, value, saved_by=None):
    """Saves the whole section and keeps a copy in the history. Returns True on success."""
    if section not in DEFAULTS:
        return False
    payload = json.dumps(value, ensure_ascii=False)
    ok = _run("""
        INSERT INTO site_content (key, value, updated_at, updated_by) VALUES (%s, %s::jsonb, NOW(), %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW(), updated_by = EXCLUDED.updated_by;
        INSERT INTO site_content_history (key, value, saved_by) VALUES (%s, %s::jsonb, %s);
    """, [section, payload, saved_by, section, payload, saved_by], fetch='none', commit=True)
    _cache.pop(section, None)
    return bool(ok)


def last_saved(section):
    """{'updated_at', 'updated_by'} of the latest save, or None if the section shows its defaults."""
    return _run("SELECT updated_at, updated_by FROM site_content WHERE key = %s;", [section], fetch='one')


def undo_last_save(section, saved_by=None):
    """Goes back to the version saved before the latest one (or to the defaults if there is none)."""
    rows = _run("SELECT id, value FROM site_content_history WHERE key = %s ORDER BY id DESC LIMIT 2;",
                [section], fetch='all')
    if not rows:
        return False
    if len(rows) == 1:
        ok = _run("DELETE FROM site_content WHERE key = %s;", [section], fetch='none', commit=True)
    else:
        prev = rows[1]['value']
        prev = prev if isinstance(prev, str) else json.dumps(prev, ensure_ascii=False)
        ok = _run("""UPDATE site_content SET value = %s::jsonb, updated_at = NOW(), updated_by = %s WHERE key = %s;""",
                  [prev, saved_by, section], fetch='none', commit=True)
    if ok:
        _run("DELETE FROM site_content_history WHERE id = %s;", [rows[0]['id']], fetch='none', commit=True)
    _cache.pop(section, None)
    return bool(ok)


def restore_defaults(section, saved_by=None):
    """Back to the original website content for this section (the history is kept)."""
    ok = _run("DELETE FROM site_content WHERE key = %s;", [section], fetch='none', commit=True)
    _cache.pop(section, None)
    return bool(ok)


def fill(text, s=None):
    """Replaces {phone}, {email}, {main_office}, {satellite_office}, {company} in AlluBot answers and templates."""
    s = s or settings()
    text = str(text or '')
    for key, val in (('{phone}', s.get('phone')), ('{email}', s.get('email')), ('{main_office}', s.get('main_office')),
                     ('{satellite_office}', s.get('satellite_office')), ('{company}', s.get('company_name'))):
        text = text.replace(key, val or '')
    return text


def lines(text):
    """'a\\nb\\n\\nc' -> ['a', 'b', 'c'] (used for bullet points typed one per line)."""
    return [ln.strip(' •-\t') for ln in str(text or '').splitlines() if ln.strip(' •-\t')]


def tel_href(phone):
    digits = ''.join(ch for ch in str(phone or '') if ch.isdigit() or ch == '+')
    return f"tel:{digits}" if digits else None
