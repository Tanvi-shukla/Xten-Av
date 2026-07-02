# XTEN-AV Registration UI Tests

Playwright + pytest suite that exercises the two-step signup form at
`https://app.xtenav.com/register`.

## Project layout

```
conftest.py                     # CLI options + fixtures for registration test data
pages/registration_page.py      # Page object for the registration form
tests/test_registration.py      # Test cases (TestRegistration class)
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Running the tests

```bash
source venv/bin/activate
pytest tests/test_registration.py
```

Useful variants:

| Command | What it does |
|---|---|
| `pytest tests/test_registration.py -v` | Verbose output, shows each test name/result |
| `pytest tests/test_registration.py --headed` | Watch it run in a real (visible) browser window |
| `pytest tests/test_registration.py --headed --slowmo 1000` | Visible browser, 1s pause between actions, so you can follow each step |
| `pytest tests/test_registration.py::TestRegistration::test_register_full_flow` | Run a single test |
| `pytest tests/test_registration.py -k invalid_phone` | Run tests matching a keyword |

## Configuring test data

Name, email, organisation, password, phone, state, and country are not
hardcoded — they come from CLI options (see `conftest.py`) with sensible
defaults. Override any of them at the command line:

```bash
pytest tests/test_registration.py \
  --reg-name="Jane Doe" \
  --reg-email="jane.doe@example.com" \
  --reg-organisation="Acme Inc" \
  --reg-password="Str0ngPass!" \
  --reg-phone="9998887771" \
  --reg-state="Delhi" \
  --reg-country="India"
```

Tests that need a fresh, never-before-used address (e.g.
`test_register_full_flow`) derive one automatically from `--reg-email` via
the `unique_email` fixture, so re-running the suite won't collide with an
account created by a previous run.

`test_register_accepts_valid_phone_and_state` is the one exception: it
intentionally submits a fixed, already-registered email
(`ALREADY_REGISTERED_EMAIL` in the test file) so it deterministically hits
the server's duplicate-user check instead of creating a new real account
every run.

## Notes

- Tests run against the live site (`app.xtenav.com`), not a local/staging
  server — `test_register_full_flow` performs a real signup.
- Default browser is Chromium (set in `pytest.ini`); Playwright also
  supports `--browser firefox` / `--browser webkit` if those browsers are
  installed (`playwright install firefox webkit`).
- The requirements.txt file can also be used to specify exact versions of dependencies.

## Additional 
Each test with default inputs
```
pytest tests/test_registration.py::TestRegistration::test_register_rejects_missing_state --headed --slowmo 1500 -v
```

Each test with Dynamic inputs
```
pytest tests/test_registration.py::TestRegistration::test_register_rejects_invalid_phone \
  --reg-name="Jane Doe" \
  --reg-email="jane.doe@example.com" \
  --reg-organisation="Acme Inc" \
  --reg-password="Str0ngPass" \
  --reg-phone="9998887771" \
  --reg-state="Delhi" \
  --reg-country="India" \ 
  --headed --slowmo 1500 -v
```

