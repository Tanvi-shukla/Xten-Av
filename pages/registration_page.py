import re

from playwright.sync_api import Page, expect

REGISTER_URL = "https://app.xtenav.com/register"


class RegistrationPage:
    """Page object for the two-step signup form at /register."""

    def __init__(self, page: Page):
        self.page = page

    # ---- locators ----

    @property
    def step1(self):
        return self.page.locator("#step1")

    @property
    def step2(self):
        return self.page.locator("#step2")

    @property
    def continue_button(self):
        return self.page.locator("#continueBtn")

    @property
    def register_button(self):
        return self.page.locator("#register_button")

    @property
    def email_error(self):
        return self.page.locator("#email-error")

    @property
    def password_error(self):
        return self.page.locator("#password-error")

    @property
    def phone_error(self):
        return self.page.locator("#phone-error")

    @property
    def state_error(self):
        return self.page.locator("#state-error")

    @property
    def user_error(self):
        return self.page.locator("#user-error")

    # ---- step 1: account details ----

    def goto(self):
        self.page.route("**/geolocation/**", lambda route: route.abort())
        # Wait only for the DOM, not the full "load" event: the form is usable
        # immediately, and waiting on the live site's slow tail resources
        # (analytics/fonts/images) is a frequent source of goto timeouts.
        self.page.goto(REGISTER_URL, wait_until="domcontentloaded")

    def fill_account_details(self, name: str, email: str, organisation: str, password: str):
        self.page.fill("#username", name)
        self.page.fill("#user-email", email)
        self.page.fill("#organisation-name", organisation)
        self.page.fill("#id_password1", password)

    def accept_terms(self):
        self.page.check("#terms")

    def click_continue(self):
        self.continue_button.click()

    def fill_step_one(self, name: str, email: str, organisation: str, password: str):
        self.goto()
        self.fill_account_details(name, email, organisation, password)
        self.accept_terms()
        self.click_continue()

    def expect_step_two_active(self):
        expect(self.step2).to_have_class(re.compile(r"\bactive\b"))

    # ---- step 2: contact details ----

    def _select2_pick(self, select_id: str, label: str):
        """Open the visible Select2 widget and click the option, exactly as a user would.

        Country/State are Select2 dropdowns: a hidden native <select> plus a visible
        <span> widget. This drives the visible widget (open -> search -> click option)
        instead of setting the native <select> value directly.
        """
        self.page.click(f"#{select_id} + span.select2 .select2-selection")
        results = self.page.locator(".select2-container--open li.select2-results__option")
        results.first.wait_for(state="visible")
        search = self.page.locator(".select2-container--open input.select2-search__field")
        if search.count() and search.first.is_visible():
            search.first.fill(label)
        self.page.locator(
            ".select2-container--open li.select2-results__option",
            has_text=re.compile(rf"^\s*{re.escape(label)}\s*$"),
        ).first.click()

    def select_country(self, label: str):
        self.page.locator("#phone").wait_for(state="visible")
        self._select2_pick("id_country", label)
        self.page.wait_for_function(
            "document.getElementById('id_state').options.length > 1"
        )

    def select_state(self, label: str):
        if label:
            self._select2_pick("id_state", label)
        # empty label: leave the dropdown unselected ("Select State") so the
        # required-field validation ("Please select a state") fires.

    def fill_phone(self, value: str):
        self.page.fill("#phone", value)

    def check_sms_optin(self):
        self.page.check("#smsOptIn")

    def click_register(self):
        self.register_button.click()

    def reach_step_two(self, name: str, email: str, organisation: str, password: str, country: str):
        self.fill_step_one(name, email, organisation, password)
        self.expect_step_two_active()
        self.select_country(country)
