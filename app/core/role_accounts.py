"""Fixed development login identities for the MS-5 seed."""
from app.core.role_credentials import ADMIN_CREDENTIALS, STAFF_CREDENTIALS

ADMIN_ACCOUNT_EMAIL = ADMIN_CREDENTIALS["email"]
STAFF_ACCOUNT_EMAILS = {item["email"] for item in STAFF_CREDENTIALS}
