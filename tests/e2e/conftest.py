import pytest


def pytest_addoption(parser):
    """Add command-line options for controlling browser behavior."""
    parser.addoption(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default)',
    )
    parser.addoption(
        '--no-headless',
        action='store_false',
        dest='headless',
        help='Run browser in non-headless mode to watch the browser',
    )
    parser.addoption(
        '--slow-mo',
        action='store',
        default=0,
        type=int,
        help='Add delay between actions in milliseconds (default: 0)',
    )


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    """Return the browser context args."""
    return browser_context_args


@pytest.fixture(scope='session')
def browser_type_launch_args(request):
    """Override the browser launch arguments based on command-line options."""
    headless = request.config.getoption('--headless')
    slow_mo = request.config.getoption('--slow-mo')

    args = {
        'headless': headless,
    }

    if slow_mo > 0:
        args['slow_mo'] = slow_mo

    return args
