import re

import pytest
from playwright.sync_api import Page, expect

from pages.registration_page import RegistrationPage

INVALID_EMAILS = [
    "plainaddress",
    "missing-at-sign.com",
    "missing-domain@",
    "@missing-local.com",
    "spaces in@email.com",
    "user@domain",
    "trailing-dot@email.com.",
]

PHONE_NEGATIVE_CASES = [
    ("", "Please enter contact number"),
    ("123", "Please enter a valid contact number"),
    ("1234567890", "Please enter a valid contact number"),
    ("12345678901234567", "Please enter a valid contact number"),
]

ALREADY_REGISTERED_EMAIL = "tanvishukla995+phonetest@gmail.com"

# Each violates the site's rule (8–20 chars incl. upper, lower, number & special):
WEAK_PASSWORDS = [
    "weak",       # too short, lowercase only
    "12345678",   # digits only
    "abcdefgh",   # lowercase only
    "Password1",  # missing a special character
]

WEAK_PASSWORD_ERROR = re.compile(
    r"Password must be 8.20 chars and include uppercase, lowercase, number & special character\."
)


class TestRegistration:
    @pytest.fixture
    def registration_page(self, page: Page):
        return RegistrationPage(page)

    def test_register_step_one(self, registration_page, reg_name, reg_email, reg_organisation, reg_password):
        registration_page.goto()
        registration_page.fill_account_details(reg_name, reg_email, reg_organisation, reg_password)

        registration_page.accept_terms()
        expect(registration_page.page.locator("#terms")).to_be_checked()

        expect(registration_page.continue_button).not_to_have_class(re.compile("disabled"))

        registration_page.click_continue()

        registration_page.expect_step_two_active()
        expect(registration_page.step1).to_have_class(re.compile(r"\bhidden\b"))

    def test_register_full_flow(
        self, registration_page, reg_name, reg_organisation, reg_password, reg_phone, reg_state, reg_country, unique_email
    ):
        registration_page.reach_step_two(reg_name, unique_email, reg_organisation, reg_password, reg_country)

        registration_page.select_state(reg_state)
        registration_page.fill_phone(reg_phone)
        registration_page.check_sms_optin()

        registration_page.click_register()

        registration_page.page.wait_for_url("**/get-started")
        expect(registration_page.page.get_by_role("heading", name="Welcome")).to_be_visible()

    @pytest.mark.parametrize("invalid_email", INVALID_EMAILS)
    def test_register_rejects_invalid_email(
        self, registration_page, reg_name, reg_organisation, reg_password, invalid_email
    ):
        registration_page.fill_step_one(reg_name, invalid_email, reg_organisation, reg_password)

        expect(registration_page.step1).not_to_have_class(re.compile(r"\bhidden\b"))
        expect(registration_page.email_error).to_have_text("Please enter a valid email address")

    def test_register_accepts_valid_email(
        self, registration_page, reg_name, reg_organisation, reg_password, unique_email
    ):
        registration_page.fill_step_one(reg_name, unique_email, reg_organisation, reg_password)

        registration_page.expect_step_two_active()
        expect(registration_page.email_error).to_have_text("")

    def test_continue_disabled_on_empty_form(self, registration_page):
        registration_page.goto()

        # Empty mandatory fields: Step 1 cannot be submitted — the Continue
        # control stays disabled and Step 2 is never reached.
        expect(registration_page.continue_button).to_have_class(re.compile(r"\bdisabled\b"))
        expect(registration_page.step1).not_to_have_class(re.compile(r"\bhidden\b"))

    def test_continue_disabled_when_terms_not_accepted(
        self, registration_page, reg_name, reg_email, reg_organisation, reg_password
    ):
        registration_page.goto()
        registration_page.fill_account_details(reg_name, reg_email, reg_organisation, reg_password)
        # Deliberately do NOT accept the Terms & privacy policy.

        expect(registration_page.page.locator("#terms")).not_to_be_checked()
        expect(registration_page.continue_button).to_have_class(re.compile(r"\bdisabled\b"))

    @pytest.mark.parametrize("weak_password", WEAK_PASSWORDS)
    def test_register_rejects_weak_password(
        self, registration_page, reg_name, reg_email, reg_organisation, weak_password
    ):
        registration_page.goto()
        registration_page.fill_account_details(reg_name, reg_email, reg_organisation, weak_password)
        registration_page.accept_terms()
        registration_page.click_continue()

        expect(registration_page.password_error).to_have_text(WEAK_PASSWORD_ERROR)
        # Weak password blocks progression — still on Step 1.
        expect(registration_page.step1).not_to_have_class(re.compile(r"\bhidden\b"))

    @pytest.mark.parametrize("phone_value, expected_error", PHONE_NEGATIVE_CASES)
    def test_register_rejects_invalid_phone(
        self,
        registration_page,
        reg_name,
        reg_organisation,
        reg_password,
        reg_country,
        unique_email,
        phone_value,
        expected_error,
    ):
        registration_page.reach_step_two(reg_name, unique_email, reg_organisation, reg_password, reg_country)
        registration_page.fill_phone(phone_value)

        registration_page.click_register()

        expect(registration_page.phone_error).to_have_text(expected_error)
        expect(registration_page.page).to_have_url(re.compile(r"/register"))

    def test_register_rejects_missing_state(
        self, registration_page, reg_name, reg_organisation, reg_password, reg_country, reg_phone, unique_email
    ):
        registration_page.reach_step_two(reg_name, unique_email, reg_organisation, reg_password, reg_country)
        registration_page.select_state("")
        registration_page.fill_phone(reg_phone)

        registration_page.click_register()

        expect(registration_page.state_error).to_have_text("Please select a state")
        expect(registration_page.page).to_have_url(re.compile(r"/register"))

    def test_register_accepts_valid_phone_and_state(
        self, registration_page, reg_name, reg_organisation, reg_password, reg_country, reg_state
    ):
        registration_page.reach_step_two(
            reg_name, ALREADY_REGISTERED_EMAIL, reg_organisation, reg_password, reg_country
        )

        registration_page.select_state(reg_state)
        registration_page.fill_phone("9977952221")
        registration_page.check_sms_optin()

        registration_page.click_register()

        # Submitting reloads /register, so wait for the meaningful outcome (the
        # duplicate-email message) first — that also lets the navigation settle —
        # before asserting no phone/state validation errors were raised.
        expect(registration_page.user_error).to_have_text(
            "The User has been already registered through this Email Id"
        )
        expect(registration_page.phone_error).to_have_text("")
        expect(registration_page.state_error).to_have_text("")
