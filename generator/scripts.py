"""Hinglish call-script templates for the CloneGuard scam-call generator.

Six scam families and three genuine controls. Every template is filled from
small fixed lists, so the same family + variant always produces the same text.

Public API:
    get_scam_script(family, variant=0)   -> (category, script_text)
    get_genuine_script(index, variant=0) -> (category, script_text)
"""

# ---------------------------------------------------------------------------
# Fixed slot values (kept small on purpose)
# ---------------------------------------------------------------------------

AMOUNTS = [
    "pachpan hazaar rupaye",
    "ek lakh rupaye",
    "sattar hazaar rupaye",
    "dhai lakh rupaye",
]

DEADLINES = [
    "das minute",
    "do ghante",
    "aaj shaam",
    "aaj raat",
]

PAYMENTS = [
    "UPI",
    "bank transfer",
    "Paytm",
    "Google Pay",
]

# ---------------------------------------------------------------------------
# Scam families
# ---------------------------------------------------------------------------

SCAM_FAMILIES = {
    "family_emergency": {
        "category": "family_emergency",
        "relationships": ["Papa", "Mummy", "bhaiya"],
        "template": (
            "Beta, main {relationship} bol raha hoon. "
            "Mera accident ho gaya hai aur main hospital mein admitted hoon. "
            "Doctor bol raha hai operation ke liye {amount} turant chahiye. "
            "Aap {deadline} ke andar {payment} par paise bhej do. "
            "Kisi ko abhi mat batana, main theek hone ke baad khud sab ko bata dunga."
        ),
    },
    "bank_fraud": {
        "category": "bank_fraud",
        "relationships": ["bank manager", "customer care officer", "account security team"],
        "template": (
            "Namaste, main {relationship} se bol raha hoon. "
            "Aapka account kuch suspicious transactions ki wajah se block ho gaya hai. "
            "Account chalu karne ke liye {amount} ki verification payment {deadline} ke andar "
            "{payment} par karni hogi. "
            "Yeh bank ka urgent process hai, isliye delay mat kijiye. "
            "Aap apna OTP aur card ke last digits mujhe bata dijiye taaki main turant "
            "account unlock kar sakoon."
        ),
    },
    "executive": {
        "category": "executive",
        "relationships": ["CEO", "director", "senior manager"],
        "template": (
            "Hello, main {relationship} bol raha hoon. "
            "Company ki ek confidential deal close karni hai aur mujhe aapki help chahiye. "
            "Aapko {amount} ki transfer {deadline} tak {payment} par karni hai, "
            "invoice baad mein bhej dunga. "
            "Yeh baat company ke andar bhi kisi ko nahi batani hai. "
            "Main abhi meeting mein hoon, isliye sirf message par confirm kar dena."
        ),
    },
    "government_police": {
        "category": "government_police",
        "relationships": ["police station", "cyber crime branch", "crime branch"],
        "template": (
            "Main {relationship} se bol raha hoon. "
            "Aapke naam par ek case register ho gaya hai aur warrant nikalne wala hai. "
            "Case close karne ke liye {amount} ka fine {deadline} tak {payment} par "
            "jama karna hoga. "
            "Agar payment nahi hui to team aapke ghar aaj hi pahunch jayegi. "
            "Abhi kisi wakil ya ghar walon ko mat batayein, warna case aur serious ho jayega."
        ),
    },
    "tech_support": {
        "category": "tech_support",
        "relationships": ["Microsoft", "Windows", "company"],
        "template": (
            "Hello, main {relationship} ki technical support team se bol raha hoon. "
            "Aapke computer mein virus detect hua hai aur aapka bank data leak ho raha hai. "
            "System theek karne ke liye {amount} ka support plan {deadline} ke andar "
            "{payment} se activate karna hoga. "
            "Main abhi aapko remote access ke liye screen share app install karne ko bolunga. "
            "Please laptop ke saamne baith jaiye aur koi window band mat kijiye."
        ),
    },
    "prize_refund": {
        "category": "prize_refund",
        "relationships": ["company ke refund department", "customer reward team", "prize distribution team"],
        "template": (
            "Namaste, main {relationship} se bol raha hoon. "
            "Aapka {amount} ka refund company ke system mein pending hai. "
            "Refund release karne ke liye {deadline} ke andar {payment} par chhota "
            "processing fee dena hoga. "
            "Yeh fee aapko refund ke saath wapas mil jayegi. "
            "Aap bas link khol kar apna account number aur details verify kar dijiye, "
            "warna refund cancel ho jayega."
        ),
    },
}

SCAM_ORDER = [
    "family_emergency",
    "bank_fraud",
    "executive",
    "government_police",
    "tech_support",
    "prize_refund",
]

# ---------------------------------------------------------------------------
# Genuine controls (no urgency, no payment pressure, no secrecy)
# ---------------------------------------------------------------------------

GENUINE_FRIEND = {
    "category": "friend_dinner",
    "names": ["Rohan", "Priya", "Aman", "Neha"],
    "places": ["Cafe Coffee Day", "the new pizza place", "Barbeque Nation"],
    "times": ["saat", "aath", "saadhe aath"],
    "template": (
        "Hi yaar, main {name} bol raha hoon. "
        "Aaj shaam dinner ka plan banaya hai, {place} mein {time} baje. "
        "Tu free ho to aa jana, main table book kar dunga. "
        "Agar koi problem ho to message kar dena. "
        "See you, take care!"
    ),
}

GENUINE_COLLEGE = {
    "category": "college_exam_fee",
    "names": ["Sharma sir", "Gupta madam", "Verma sir"],
    "dates": ["is Friday", "agle Monday", "25 November"],
    "fees": [
        "ek hazaar do sau rupaye",
        "do hazaar rupaye",
        "ek hazaar pachas rupaye",
    ],
    "template": (
        "Namaste, main {name} bol raha hoon, college office se. "
        "Exam form ki last date {date} hai aur fee {fee} hai. "
        "Aap office timing mein aa kar fee jama kar sakte hain ya portal par online pay kar sakte hain. "
        "Payment ke baad receipt sambhal kar rakhein. "
        "Koi doubt ho to college ke official number par call karein."
    ),
}

GENUINE_RELATIVE = {
    "category": "relative_checkin",
    "names": ["Rakesh chacha", "Sunita masi", "Pooja didi"],
    "template": (
        "Hi, main {name} bol raha hoon, bas aapka haal chaal puchne ke liye call kiya. "
        "Kaafi din se baat nahi hui, sab theek hai na? "
        "Ghar par sab log kaise hain? "
        "Weekend par hum log aapke ghar aa sakte hain agar aap free ho. "
        "Apna khayal rakhna, milte hain."
    ),
}

GENUINE_SCRIPTS = [GENUINE_FRIEND, GENUINE_COLLEGE, GENUINE_RELATIVE]

GENUINE_ORDER = [entry["category"] for entry in GENUINE_SCRIPTS]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pick(options, index):
    """Deterministic round-robin pick."""
    return options[index % len(options)]


def _fill(template, slots):
    for key, value in slots.items():
        template = template.replace("{" + key + "}", value)
    return template


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_scam_script(family, variant=0):
    """Return (category, script_text) for a scam family.

    `variant` is an integer; it selects which entry of each fixed slot list is
    used, so the result is fully deterministic for a given (family, variant).
    """
    key = str(family).strip().lower()
    entry = SCAM_FAMILIES.get(key)
    if entry is None:
        raise ValueError(
            "unknown scam family: %r (choose from: %s)"
            % (family, ", ".join(SCAM_ORDER))
        )
    variant = int(variant)
    slots = {
        "relationship": _pick(entry["relationships"], variant),
        "amount": _pick(AMOUNTS, variant),
        "deadline": _pick(DEADLINES, variant + 1),
        "payment": _pick(PAYMENTS, variant + 2),
    }
    return entry["category"], _fill(entry["template"], slots)


def get_genuine_script(index, variant=0):
    """Return (category, script_text) for a genuine control call.

    `index` selects the control (0 = friend dinner, 1 = college exam fee,
    2 = relative check-in). `variant` selects the fixed slot values.
    """
    index = int(index)
    if index < 0 or index >= len(GENUINE_SCRIPTS):
        raise ValueError(
            "genuine index out of range: %r (valid: 0..%d)"
            % (index, len(GENUINE_SCRIPTS) - 1)
        )
    entry = GENUINE_SCRIPTS[index]
    variant = int(variant)

    if entry is GENUINE_FRIEND:
        slots = {
            "name": _pick(entry["names"], variant),
            "place": _pick(entry["places"], variant),
            "time": _pick(entry["times"], variant + 1),
        }
    elif entry is GENUINE_COLLEGE:
        slots = {
            "name": _pick(entry["names"], variant),
            "date": _pick(entry["dates"], variant),
            "fee": _pick(entry["fees"], variant),
        }
    else:
        slots = {"name": _pick(entry["names"], variant)}

    return entry["category"], _fill(entry["template"], slots)
