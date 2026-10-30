"""Make one evidence sheet for each of my three test cases."""

import ast
import base64
import html
import json
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


ROOT = Path(__file__).parent
EVIDENCE_DIR = ROOT / "evidence"
SOURCE_FILE = ROOT / "test_opencart.py"
RESULTS_FILE = ROOT / "test_results.json"


def extract_function_source(source, function_names):
    """Pull out only the functions that belong to the selected test case."""
    # This stops each evidence sheet from being filled with unrelated code.
    tree = ast.parse(source)
    lines = source.splitlines()
    chunks = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in function_names:
            chunks.append("\n".join(lines[node.lineno - 1 : node.end_lineno]))
    return "\n\n".join(chunks)


def image_data_uri(path):
    """Put an image directly into the HTML so the sheet stays self-contained."""
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def build_sheet(test_id, title, results, code):
    """Combine the results, screenshots and relevant code into one HTML page."""
    formatter = HtmlFormatter(style="friendly", noclasses=True)
    highlighted_code = highlight(code, PythonLexer(), formatter)
    cards = []
    for result in results:
        # Each scenario gets its own section with the expected and actual result.
        screenshot = Path(result["screenshot"])
        status_class = "pass" if result["status"] == "PASS" else "fail"
        cards.append(
            f"""
            <section class="scenario">
              <h2>{html.escape(result['scenario'])}: input {html.escape(str(result['input']))}</h2>
              <p><strong>Expected:</strong> {html.escape(result['expected'])}</p>
              <p><strong>Actual:</strong> {html.escape(result['actual'])}</p>
              <p><strong>Status:</strong> <span class="{status_class}">{html.escape(result['status'])}</span></p>
              <img src="{image_data_uri(screenshot)}" alt="{test_id} {result['scenario']} result screenshot">
            </section>
            """
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
body {{ margin: 0; padding: 46px; color: #152238; background: #eef3f8;
       font: 22px/1.45 Arial, sans-serif; }}
main {{ max-width: 1450px; margin: auto; }}
h1 {{ margin: 0 0 10px; font-size: 42px; color: #123b63; }}
.meta {{ margin-bottom: 32px; color: #4d5c6b; }}
.scenario, .code {{ background: white; border: 1px solid #cbd5df; border-radius: 12px;
                     margin: 0 0 34px; padding: 26px; box-shadow: 0 3px 10px #0001; }}
h2 {{ color: #174f79; margin-top: 0; }}
.pass {{ color: #087a37; font-weight: bold; }}
.fail {{ color: #b3261e; font-weight: bold; }}
img {{ display: block; width: 100%; border: 1px solid #aeb9c4; margin-top: 18px; }}
.code {{ font-size: 17px; overflow-wrap: anywhere; }}
.code pre {{ white-space: pre-wrap; }}
</style></head><body><main>
<h1>{test_id} {html.escape(title)} Evidence</h1>
<p class="meta">Abstracta OpenCart | Python 3.12 | Selenium 4.52 | pytest 9.2 | Google Chrome</p>
{''.join(cards)}
<section class="code"><h2>Relevant source code</h2>{highlighted_code}</section>
</main></body></html>"""


def capture_full_page(driver, html_path, output_path):
    """Open the evidence page in Chrome and save the complete page as one image."""
    driver.get(html_path.as_uri())
    height = driver.execute_script("return document.documentElement.scrollHeight")
    driver.set_window_size(1600, min(height + 100, 15000))
    driver.save_screenshot(str(output_path))


def main():
    # Read the test output and source once, then reuse them for all three sheets.
    results = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    source = SOURCE_FILE.read_text(encoding="utf-8")
    definitions = {
        "T004": (
            "Product Search",
            ["run_search", "test_t004_product_search"],
        ),
        "T005": (
            "Category Navigation",
            ["open_category", "test_t005_category_navigation"],
        ),
        "T006": (
            "Brand Browsing",
            ["open_brand", "open_invalid_brand", "test_t006_brand_browsing"],
        ),
    }

    options = Options()
    # Chrome only needs to run in the background because it is capturing local HTML.
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    driver = webdriver.Chrome(options=options)
    try:
        for test_id, (title, function_names) in definitions.items():
            # Match each test case with its three recorded scenario results.
            case_results = [item for item in results if item["test_case"] == test_id]
            code = extract_function_source(source, function_names)
            html_text = build_sheet(test_id, title, case_results, code)
            html_path = EVIDENCE_DIR / f"{test_id}_evidence.html"
            html_path.write_text(html_text, encoding="utf-8")
            capture_full_page(driver, html_path, EVIDENCE_DIR / f"{test_id}_evidence.png")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
