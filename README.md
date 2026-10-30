# Abstracta OpenCart System Tests

These tests cover the three assigned test cases in *Systems Testing Assignment 3*:

- T004: Product Search
- T005: Category Navigation
- T006: Brand Browsing

The target system is <https://opencart.abstracta.us/>. The suite uses Python 3.12, Selenium 4.52, pytest 9.2 and Google Chrome on Windows 11.

## Run the tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v test_opencart.py
```

The run produces:

- nine result screenshots in `evidence/`;
- `test_results.json` containing the inputs, expected results, actual results and status;
- three combined evidence sheets after running `python make_evidence_sheets.py`.

Each test opens a new Chrome session, performs the actions through visible customer-facing controls, compares the displayed output with the expected product list, and records evidence before the assertion is reported.

## Latest result

The latest run completed with eight passing scenarios and one failing scenario. T004 Scenario 3 fails because an unsuccessful product search shows the unrelated message "Your shopping cart is empty!" instead of explaining that no products matched the search.
