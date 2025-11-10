import sys

try:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        if p.chromium.executable_path:
            print('chromium_found')
            sys.exit(0)
        else:
            print('chromium_not_found')
            sys.exit(1)
except Exception as e:
    print(f'error: {e}')
    sys.exit(1)
