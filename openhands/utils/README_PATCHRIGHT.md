# Using Patchright as a Drop-in Replacement for Playwright

This utility allows you to use [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) as a drop-in replacement for Playwright in OpenHands, without modifying the upstream browsergym code.

## Installation

First, install patchright:

```bash
pip install patchright
```

## Usage

To use patchright instead of playwright, simply import and call the `use_patchright()` function **before** importing any modules that use playwright (such as browsergym):

```python
# Import the utility
from openhands.utils.playwright_patchright_util import use_patchright

# Configure the system to use patchright instead of playwright
use_patchright()

# Now you can import and use modules that depend on playwright
# IMPORTANT: These imports MUST come AFTER the use_patchright() call
import browsergym
# or
from playwright.sync_api import sync_playwright
```

### IMPORTANT: Import Order Matters

The `use_patchright()` function must be called **before** any imports of playwright or modules that use playwright. If you import playwright before calling `use_patchright()`, the patching will not work correctly.

## How It Works

The utility uses Python's import system to intercept imports of playwright modules and redirect them to the corresponding patchright modules. It does this by:

1. Installing a custom meta path finder that intercepts imports of playwright modules
2. Redirecting these imports to the corresponding patchright modules
3. Creating proxy modules that present patchright modules as if they were playwright modules

This approach allows you to use patchright as a drop-in replacement for playwright without modifying any code that depends on playwright.

## Limitations

- This approach may not work with all code that uses playwright, especially if it relies on internal implementation details of playwright.
- Some features of playwright may not be available in patchright, or may behave differently.
- The utility must be imported and called before any imports of modules that use playwright.

## Troubleshooting

If you encounter issues:

1. Make sure you've installed patchright: `pip install patchright`
2. Make sure you call `use_patchright()` before importing any modules that use playwright
3. Check if the module you're using relies on internal implementation details of playwright that may not be available in patchright

## Example

```python
from openhands.utils.playwright_patchright_util import use_patchright
use_patchright()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
```
