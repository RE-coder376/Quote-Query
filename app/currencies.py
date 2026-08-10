"""Currency list for the setup picker.

Static data, no dependency. Each entry carries the country names people actually
type — someone setting up in Karachi types "pakistan" or "pk", not "PKR", and
someone in Dubai types "dubai", not "AED".

`digits` is how many decimal places the currency really uses. Amounts are whole
units everywhere in this product, so this only controls display; it is here so
that a JPY or PKR figure is never rendered with a meaningless ".00".

`grouping` is "lakh" for the South Asian 1,00,000 style and "thousand"
elsewhere. A Pakistani or Indian client reading 1,000,000 where they expect
10,00,000 will trust the number less, and trust in the number is the product.
"""
from __future__ import annotations

# (code, name, symbol, digits, grouping, search terms)
CURRENCIES: list[tuple[str, str, str, int, str, tuple[str, ...]]] = [
    ("PKR", "Pakistani Rupee", "Rs", 0, "lakh", ("pakistan", "pk", "karachi", "lahore", "islamabad", "rupee")),
    ("AED", "UAE Dirham", "AED", 2, "thousand", ("uae", "emirates", "dubai", "abu dhabi", "ae", "dirham")),
    ("SAR", "Saudi Riyal", "SAR", 2, "thousand", ("saudi", "arabia", "riyadh", "jeddah", "sa", "riyal")),
    ("INR", "Indian Rupee", "₹", 2, "lakh", ("india", "in", "mumbai", "delhi", "rupee")),
    ("USD", "US Dollar", "$", 2, "thousand", ("usa", "united states", "america", "us", "dollar")),
    ("EUR", "Euro", "€", 2, "thousand", ("europe", "eu", "germany", "france", "spain", "italy", "ireland")),
    ("GBP", "Pound Sterling", "£", 2, "thousand", ("uk", "britain", "united kingdom", "england", "london", "pound")),
    ("QAR", "Qatari Riyal", "QAR", 2, "thousand", ("qatar", "doha", "qa")),
    ("KWD", "Kuwaiti Dinar", "KWD", 3, "thousand", ("kuwait", "kw", "dinar")),
    ("BHD", "Bahraini Dinar", "BHD", 3, "thousand", ("bahrain", "bh", "manama")),
    ("OMR", "Omani Rial", "OMR", 3, "thousand", ("oman", "om", "muscat")),
    ("BDT", "Bangladeshi Taka", "৳", 2, "lakh", ("bangladesh", "bd", "dhaka", "taka")),
    ("LKR", "Sri Lankan Rupee", "Rs", 2, "lakh", ("sri lanka", "lk", "colombo")),
    ("NPR", "Nepalese Rupee", "Rs", 2, "lakh", ("nepal", "np", "kathmandu")),
    ("AFN", "Afghan Afghani", "؋", 2, "thousand", ("afghanistan", "af", "kabul")),
    ("IRR", "Iranian Rial", "IRR", 2, "thousand", ("iran", "ir", "tehran")),
    ("IQD", "Iraqi Dinar", "IQD", 3, "thousand", ("iraq", "iq", "baghdad")),
    ("JOD", "Jordanian Dinar", "JOD", 3, "thousand", ("jordan", "jo", "amman")),
    ("LBP", "Lebanese Pound", "LBP", 2, "thousand", ("lebanon", "lb", "beirut")),
    ("EGP", "Egyptian Pound", "E£", 2, "thousand", ("egypt", "eg", "cairo")),
    ("TRY", "Turkish Lira", "₺", 2, "thousand", ("turkey", "turkiye", "tr", "istanbul")),
    ("MAD", "Moroccan Dirham", "MAD", 2, "thousand", ("morocco", "ma", "casablanca")),
    ("TND", "Tunisian Dinar", "TND", 3, "thousand", ("tunisia", "tn", "tunis")),
    ("DZD", "Algerian Dinar", "DZD", 2, "thousand", ("algeria", "dz", "algiers")),
    ("NGN", "Nigerian Naira", "₦", 2, "thousand", ("nigeria", "ng", "lagos", "abuja")),
    ("KES", "Kenyan Shilling", "KSh", 2, "thousand", ("kenya", "ke", "nairobi")),
    ("GHS", "Ghanaian Cedi", "₵", 2, "thousand", ("ghana", "gh", "accra")),
    ("ZAR", "South African Rand", "R", 2, "thousand", ("south africa", "za", "johannesburg", "cape town")),
    ("TZS", "Tanzanian Shilling", "TSh", 2, "thousand", ("tanzania", "tz", "dar es salaam")),
    ("UGX", "Ugandan Shilling", "USh", 0, "thousand", ("uganda", "ug", "kampala")),
    ("ETB", "Ethiopian Birr", "Br", 2, "thousand", ("ethiopia", "et", "addis")),
    ("CAD", "Canadian Dollar", "C$", 2, "thousand", ("canada", "ca", "toronto", "vancouver")),
    ("AUD", "Australian Dollar", "A$", 2, "thousand", ("australia", "au", "sydney", "melbourne")),
    ("NZD", "New Zealand Dollar", "NZ$", 2, "thousand", ("new zealand", "nz", "auckland")),
    ("SGD", "Singapore Dollar", "S$", 2, "thousand", ("singapore", "sg")),
    ("MYR", "Malaysian Ringgit", "RM", 2, "thousand", ("malaysia", "my", "kuala lumpur")),
    ("IDR", "Indonesian Rupiah", "Rp", 0, "thousand", ("indonesia", "id", "jakarta")),
    ("THB", "Thai Baht", "฿", 2, "thousand", ("thailand", "th", "bangkok")),
    ("VND", "Vietnamese Dong", "₫", 0, "thousand", ("vietnam", "vn", "hanoi")),
    ("PHP", "Philippine Peso", "₱", 2, "thousand", ("philippines", "ph", "manila")),
    ("CNY", "Chinese Yuan", "¥", 2, "thousand", ("china", "cn", "beijing", "shanghai", "rmb")),
    ("HKD", "Hong Kong Dollar", "HK$", 2, "thousand", ("hong kong", "hk")),
    ("JPY", "Japanese Yen", "¥", 0, "thousand", ("japan", "jp", "tokyo", "yen")),
    ("KRW", "South Korean Won", "₩", 0, "thousand", ("korea", "kr", "seoul", "won")),
    ("TWD", "New Taiwan Dollar", "NT$", 2, "thousand", ("taiwan", "tw", "taipei")),
    ("CHF", "Swiss Franc", "CHF", 2, "thousand", ("switzerland", "ch", "zurich", "geneva")),
    ("SEK", "Swedish Krona", "kr", 2, "thousand", ("sweden", "se", "stockholm")),
    ("NOK", "Norwegian Krone", "kr", 2, "thousand", ("norway", "no", "oslo")),
    ("DKK", "Danish Krone", "kr", 2, "thousand", ("denmark", "dk", "copenhagen")),
    ("PLN", "Polish Zloty", "zł", 2, "thousand", ("poland", "pl", "warsaw")),
    ("CZK", "Czech Koruna", "Kč", 2, "thousand", ("czech", "cz", "prague")),
    ("HUF", "Hungarian Forint", "Ft", 0, "thousand", ("hungary", "hu", "budapest")),
    ("RON", "Romanian Leu", "lei", 2, "thousand", ("romania", "ro", "bucharest")),
    ("BGN", "Bulgarian Lev", "лв", 2, "thousand", ("bulgaria", "bg", "sofia")),
    ("UAH", "Ukrainian Hryvnia", "₴", 2, "thousand", ("ukraine", "ua", "kyiv")),
    ("RUB", "Russian Ruble", "₽", 2, "thousand", ("russia", "ru", "moscow")),
    ("KZT", "Kazakhstani Tenge", "₸", 2, "thousand", ("kazakhstan", "kz", "almaty")),
    ("UZS", "Uzbekistani Som", "so'm", 2, "thousand", ("uzbekistan", "uz", "tashkent")),
    ("AZN", "Azerbaijani Manat", "₼", 2, "thousand", ("azerbaijan", "az", "baku")),
    ("ILS", "Israeli Shekel", "₪", 2, "thousand", ("israel", "il", "tel aviv")),
    ("MXN", "Mexican Peso", "MX$", 2, "thousand", ("mexico", "mx")),
    ("BRL", "Brazilian Real", "R$", 2, "thousand", ("brazil", "br", "sao paulo")),
    ("ARS", "Argentine Peso", "AR$", 2, "thousand", ("argentina", "ar", "buenos aires")),
    ("CLP", "Chilean Peso", "CLP$", 0, "thousand", ("chile", "cl", "santiago")),
    ("COP", "Colombian Peso", "COL$", 2, "thousand", ("colombia", "co", "bogota")),
    ("PEN", "Peruvian Sol", "S/", 2, "thousand", ("peru", "pe", "lima")),
]

CODES = {c[0] for c in CURRENCIES}
DEFAULT = "USD"


def as_json() -> list[dict]:
    """Shipped to the setup page so the picker searches without a round trip."""
    return [
        {"code": code, "name": name, "symbol": symbol, "digits": digits,
         "grouping": grouping, "terms": list(terms)}
        for code, name, symbol, digits, grouping, terms in CURRENCIES
    ]


def get(code: str) -> dict:
    for entry in as_json():
        if entry["code"] == code.upper():
            return entry
    return {"code": code.upper(), "name": code.upper(), "symbol": code.upper(),
            "digits": 2, "grouping": "thousand", "terms": []}


def search(query: str, limit: int = 8) -> list[dict]:
    """Rank by how directly the query names the currency or its country.

    "pk" must put PKR first, not Pakistan somewhere down a list of anything
    containing those two letters.
    """
    q = (query or "").strip().lower()
    if not q:
        return as_json()[:limit]

    scored = []
    for index, entry in enumerate(as_json()):
        code = entry["code"].lower()
        name = entry["name"].lower()
        terms = entry["terms"]

        if code == q or q in terms:
            score = 0                       # exact code, or exact country name
        elif code.startswith(q) or any(t.startswith(q) for t in terms):
            score = 1                       # "pak" -> pakistan, "ae" -> AED
        elif name.startswith(q):
            score = 2
        elif q in name or any(q in t for t in terms):
            score = 3
        else:
            continue
        # Ties break on list order, which is deliberate: "rupee" matches PKR and
        # INR equally well, and PKR is the one our clients mean.
        scored.append((score, index, entry))

    scored.sort(key=lambda row: (row[0], row[1]))
    return [entry for _score, _index, entry in scored[:limit]]
