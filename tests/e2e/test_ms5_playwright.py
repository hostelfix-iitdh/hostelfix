import os

import pytest
from playwright.sync_api import Error as PlaywrightError, sync_playwright

pytestmark = pytest.mark.e2e
BASE_URL = os.getenv("HOSTELFIX_URL", "http://localhost:8080")


def _browser_or_skip(playwright):
    try:
        return playwright.chromium.launch()
    except PlaywrightError as exc:
        if "Executable doesn't exist" in str(exc):
            pytest.skip("Playwright browser is not installed; run 'playwright install chromium'.")
        raise


def test_student_login_page_uses_google_only():
    with sync_playwright() as p:
        browser = _browser_or_skip(p)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded")
        assert page.get_by_role("heading", name="Student sign in").is_visible()
        assert page.get_by_text("verified", exact=False).is_visible()
        assert page.get_by_text("Staff / Administrator login").is_visible()
        assert not page.get_by_text("Create account", exact=False).is_visible()
        assert not page.get_by_text("Forgot password?", exact=False).is_visible()
        browser.close()


def test_staff_login_page_is_available_for_manual_credentials():
    with sync_playwright() as p:
        browser = _browser_or_skip(p)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/#staff-login", wait_until="domcontentloaded")
        assert page.get_by_role("heading", name="Staff / Administrator sign in").is_visible()
        assert page.get_by_label("College email").is_visible()
        assert page.get_by_label("Password").is_visible()
        assert page.get_by_role("button", name="Sign in").is_visible()
        assert page.get_by_text("Student sign in", exact=False).is_visible()
        browser.close()


def test_public_report_page_is_reachable_without_auth():
    with sync_playwright() as p:
        browser = _browser_or_skip(p)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/#login", wait_until="domcontentloaded")
        page.goto(f"{BASE_URL}/#staff-login", wait_until="domcontentloaded")
        assert page.locator("#role-login-form").is_visible()
        browser.close()
