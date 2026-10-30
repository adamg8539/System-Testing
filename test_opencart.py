"""My system tests for the three OpenCart functions I was allocated.

Target system: https://opencart.abstracta.us/
Test cases: T004 Product Search, T005 Category Navigation, T006 Brand Browsing
"""

import json
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://opencart.abstracta.us/"
EVIDENCE_DIR = Path(__file__).parent / "evidence"
RESULTS_FILE = Path(__file__).parent / "test_results.json"
RECORDED_RESULTS = []


def product_names(driver):
    """Get the names from every product card currently shown on the page."""
    # All three tests use the same product-card layout, so I can reuse this selector.
    return [
        element.text.strip()
        for element in driver.find_elements(By.CSS_SELECTOR, ".product-thumb h4 a")
    ]


def save_evidence(driver, test_id, scenario_id):
    """Save a screenshot with the test case and scenario in its filename."""
    # This keeps the nine screenshots in a clear order for the report.
    EVIDENCE_DIR.mkdir(exist_ok=True)
    driver.execute_script("window.scrollTo(0, 0)")
    path = EVIDENCE_DIR / f"{test_id}_{scenario_id}.png"
    driver.save_screenshot(str(path))
    return path


def record_result(test_id, scenario, input_value, expected, actual, status, screenshot):
    """Keep the result details so they can be written to the JSON summary later."""
    RECORDED_RESULTS.append(
        {
            "test_case": test_id,
            "scenario": scenario,
            "input": input_value,
            "expected": expected,
            "actual": actual,
            "status": status,
            "screenshot": str(screenshot),
        }
    )


@pytest.fixture
def driver():
    """Start a fresh Chrome session for each scenario."""
    # Headless mode runs Chrome in the background while still testing the real page.
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-notifications")
    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(2)
    yield browser
    browser.quit()


@pytest.fixture(scope="session", autouse=True)
def write_results_file():
    """Write all of my results to one file after the test run finishes."""
    yield
    RESULTS_FILE.write_text(json.dumps(RECORDED_RESULTS, indent=2), encoding="utf-8")


def run_search(driver, search_term):
    """Search for a product through the same search box a customer would use."""
    # I wait for the search box instead of using a fixed delay because page speed can vary.
    driver.get(BASE_URL)
    search_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "search"))
    )
    search_box.clear()
    search_box.send_keys(search_term)
    driver.find_element(By.CSS_SELECTOR, "#search button").click()
    WebDriverWait(driver, 10).until(EC.url_contains("route=product/search"))
    return product_names(driver)


# T004 - PRODUCT SEARCH
# These three inputs cover an exact match, a partial match and no matching product.
@pytest.mark.parametrize(
    "scenario_id, search_term, expected_products, expectation",
    [
        ("S1", "iPhone", ["iPhone"], "The exact iPhone product is displayed."),
        (
            "S2",
            "Mac",
            ["iMac", "MacBook", "MacBook Air", "MacBook Pro"],
            "All product names containing the partial keyword Mac are displayed.",
        ),
        ("S3", "zzzz-no-product-123", [], "The page reports that no product matches."),
    ],
)
def test_t004_product_search(
    driver, scenario_id, search_term, expected_products, expectation
):
    """Check exact, partial and unsuccessful product searches."""
    actual_products = run_search(driver, search_term)
    no_results_message = ""
    if not actual_products:
        # For the failed search I also check whether the page explains that nothing matched.
        messages = [
            element.text.strip()
            for element in driver.find_elements(By.CSS_SELECTOR, "#content p")
            if "no product" in element.text.lower()
        ]
        no_results_message = messages[0] if messages else "No matching message was displayed."

    screenshot = save_evidence(driver, "T004", scenario_id)
    # The displayed list has to match the expected list for this scenario to pass.
    passed = actual_products == expected_products
    if scenario_id == "S3":
        # Zero products alone is not enough; the user should also get a relevant message.
        passed = passed and "no product" in no_results_message.lower()

    actual = (
        f"Products displayed: {actual_products}"
        if actual_products
        else f"Products displayed: []; message: {no_results_message}"
    )
    record_result(
        "T004", scenario_id, search_term, expectation, actual,
        "PASS" if passed else "FAIL", screenshot,
    )
    assert passed, actual


def open_category(driver, category_name):
    """Open a category from the menu and return its heading and products."""
    driver.get(BASE_URL)
    category_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, category_name))
    )
    category_link.click()
    WebDriverWait(driver, 10).until(EC.url_contains("route=product/category"))
    heading = driver.find_element(By.CSS_SELECTOR, "#content h2").text.strip()
    return heading, product_names(driver)


# T005 - CATEGORY NAVIGATION
# I chose two categories with products and one empty category for a wider check.
@pytest.mark.parametrize(
    "scenario_id, category_name, expected_products",
    [
        ("S1", "Phones & PDAs", ["HTC Touch HD", "iPhone", "Palm Treo Pro"]),
        ("S2", "Cameras", ["Canon EOS 5D", "Nikon D300"]),
        ("S3", "Software", []),
    ],
)
def test_t005_category_navigation(
    driver, scenario_id, category_name, expected_products
):
    """Check two populated categories and one empty category."""
    heading, actual_products = open_category(driver, category_name)
    screenshot = save_evidence(driver, "T005", scenario_id)
    # Both the page heading and its product list need to be correct.
    passed = heading == category_name and actual_products == expected_products
    expected = (
        f"The {category_name} category opens and displays {expected_products}."
        if expected_products
        else f"The {category_name} category opens and displays no products."
    )
    actual = f"Heading: {heading}; products displayed: {actual_products}"
    record_result(
        "T005", scenario_id, category_name, expected, actual,
        "PASS" if passed else "FAIL", screenshot,
    )
    assert passed, actual


def open_brand(driver, brand_name):
    """Open the Brands page and select the brand needed for the scenario."""
    driver.get(BASE_URL)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Brands"))
    ).click()
    WebDriverWait(driver, 10).until(EC.url_contains("route=product/manufacturer"))
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, brand_name))
    ).click()
    WebDriverWait(driver, 10).until(EC.url_contains("route=product/manufacturer/info"))
    heading = driver.find_element(By.CSS_SELECTOR, "#content h2").text.strip()
    return heading, product_names(driver)


# T006 - BRAND BROWSING
# Apple checks a longer list, while Canon and Sony each check a single product.
@pytest.mark.parametrize(
    "scenario_id, brand_name, expected_products",
    [
        (
            "S1",
            "Apple",
            [
                'Apple Cinema 30"', "iMac", "iPhone", "iPod Classic", "iPod Nano",
                "iPod Shuffle", "iPod Touch", "MacBook", "MacBook Air", "MacBook Pro",
            ],
        ),
        ("S2", "Canon", ["Canon EOS 5D"]),
        ("S3", "Sony", ["Sony VAIO"]),
    ],
)
def test_t006_brand_browsing(driver, scenario_id, brand_name, expected_products):
    """Check that Apple, Canon and Sony show the products linked to each brand."""
    heading, actual_products = open_brand(driver, brand_name)
    screenshot = save_evidence(driver, "T006", scenario_id)
    # This catches either the wrong brand page or the wrong products being displayed.
    passed = heading == brand_name and actual_products == expected_products
    expected = f"The {brand_name} brand page displays {expected_products}."
    actual = f"Heading: {heading}; products displayed: {actual_products}"
    record_result(
        "T006", scenario_id, brand_name, expected, actual,
        "PASS" if passed else "FAIL", screenshot,
    )
    assert passed, actual
