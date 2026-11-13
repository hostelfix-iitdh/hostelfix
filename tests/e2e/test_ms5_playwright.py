import os

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.e2e
BASE_URL = os.getenv("HOSTELFIX_URL", "http://localhost:8080")
PASSWORD = os.getenv("HOSTELFIX_E2E_PASSWORD", "HostelFix-Demo-2026!")


def _browser_or_skip(playwright):
    try:
        return playwright.chromium.launch()
    except PlaywrightError as exc:
        if "Executable doesn't exist" in str(exc):
            pytest.skip("Playwright browser is not installed; run 'playwright install chromium'.")
        raise


def _login(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.get_by_label("College email").fill("student01@iitdh.ac.in")
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Sign in").click()


def test_login_and_profile():
    with sync_playwright() as p:
        browser = _browser_or_skip(p)
        page = browser.new_page()
        _login(page)
        page.get_by_role("link", name="Profile").click()
        assert page.get_by_text("student01@iitdh.ac.in").is_visible()
        browser.close()


def test_login_and_open_report_page():
    with sync_playwright() as p:
        browser = _browser_or_skip(p)
        page = browser.new_page()
        _login(page)
        page.get_by_role("link", name="Report an Issue").click()
        assert page.get_by_text("SmartReport").is_visible()
        assert page.get_by_label("Optional image").is_visible()
        browser.close()
