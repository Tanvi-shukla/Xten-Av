import base64
import re
import uuid

import pytest
from playwright.sync_api import expect


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On a failed test, embed a screenshot of the page into the HTML report."""
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, "extras", [])
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page is not None:
            try:
                png = page.screenshot(full_page=True)
                from pytest_html import extras as html_extras

                encoded = base64.b64encode(png).decode("ascii")
                extras.append(html_extras.image(encoded, mime_type="image/png", extension="png"))
            except Exception:
                pass  # page may already be closed; the on-disk screenshot still exists
        report.extras = extras


@pytest.fixture(autouse=True)
def generous_timeouts(page):
    """Give actions and assertions room to breathe.

    Tests run against the live app.xtenav.com, whose latency varies widely
    (a request that normally takes <1s can occasionally take 20s+). Default
    timeouts of 30s keep slow-but-successful responses from failing tests.
    """
    page.set_default_timeout(30_000)
    page.set_default_navigation_timeout(30_000)
    expect.set_options(timeout=30_000)


def pytest_addoption(parser):
    group = parser.getgroup("registration", "registration test data")
    group.addoption("--reg-name", action="store", default="tanvi shukla", help="Full name to use for registration tests")
    group.addoption("--reg-email", action="store", default="shuklatanvi0202@gmail.com", help="Base email for registration tests; unique variants are derived per test")
    group.addoption("--reg-organisation", action="store", default="xten-AV", help="Organisation name to use for registration tests")
    group.addoption("--reg-password", action="store", default="Tanvi@22", help="Password to use for registration tests")
    group.addoption("--reg-phone", action="store", default="7440581138", help="Contact number to use for registration tests")
    group.addoption("--reg-state", action="store", default="Maharashtra", help="State to select during registration tests")
    group.addoption("--reg-country", action="store", default="India", help="Country to select during registration tests")


@pytest.fixture(scope="session")
def reg_name(request):
    return request.config.getoption("--reg-name")


@pytest.fixture(scope="session")
def reg_email(request):
    return request.config.getoption("--reg-email")


@pytest.fixture(scope="session")
def reg_organisation(request):
    return request.config.getoption("--reg-organisation")


@pytest.fixture(scope="session")
def reg_password(request):
    return request.config.getoption("--reg-password")


@pytest.fixture(scope="session")
def reg_phone(request):
    return request.config.getoption("--reg-phone")


@pytest.fixture(scope="session")
def reg_state(request):
    return request.config.getoption("--reg-state")


@pytest.fixture(scope="session")
def reg_country(request):
    return request.config.getoption("--reg-country")


@pytest.fixture
def unique_email(reg_email, request):
    """A variant of reg_email tagged with the current test name plus a random suffix.

    The site rejects an email/organisation combo it has already seen, so
    tests that submit real registrations need an address that's fresh not
    just within one run but across separate runs too.
    """
    local, domain = reg_email.split("@", 1)
    tag = re.sub(r"[^A-Za-z0-9]+", "", request.node.name)[:20] or "test"
    suffix = uuid.uuid4().hex[:8]
    return f"{local}+{tag}{suffix}@{domain}"
