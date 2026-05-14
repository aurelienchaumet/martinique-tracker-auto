import os

ORIGIN = "ORY"
DESTINATION = "FDF"

ROUTES = [
    {"outbound": "2026-12-28", "return": "2027-01-15"},
    {"outbound": "2026-12-28", "return": "2027-01-16"},
    {"outbound": "2026-12-29", "return": "2027-01-15"},
    {"outbound": "2026-12-29", "return": "2027-01-16"},
]

ALERT_THRESHOLD = 20.0

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")
