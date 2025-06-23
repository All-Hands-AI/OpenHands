"""Test for Marshmallow __version_info__ deprecation warning fix."""


def test_no_marshmallow_deprecation_warning_on_import():
    """Test that importing OpenHands modules doesn't trigger Marshmallow deprecation warnings."""
    # Test that the warning filter is working by trying to import in a subprocess
    # This ensures we test the actual user experience
    import subprocess
    import sys

    # Run a subprocess that imports openhands and checks for warnings
    result = subprocess.run(
        [
            sys.executable,
            '-c',
            """
import warnings
import sys

# Capture warnings
with warnings.catch_warnings(record=True) as warning_list:
    warnings.simplefilter("always")

    # Import modules that might trigger the warning
    import openhands
    import environs

    # Check for the specific deprecation warning
    marshmallow_warnings = [
        w for w in warning_list
        if issubclass(w.category, DeprecationWarning)
        and "__version_info__" in str(w.message)
        and "marshmallow" in str(w.message).lower()
    ]

    if marshmallow_warnings:
        print(f"FOUND_WARNINGS: {len(marshmallow_warnings)}")
        for w in marshmallow_warnings:
            print(f"WARNING: {w.message}")
        sys.exit(1)
    else:
        print("NO_WARNINGS_FOUND")
        sys.exit(0)
        """,
        ],
        capture_output=True,
        text=True,
        cwd='/workspace/OpenHands',
    )

    # Check the result
    assert result.returncode == 0, (
        f'Subprocess found marshmallow warnings. '
        f'stdout: {result.stdout}, stderr: {result.stderr}'
    )


def test_environs_import_no_deprecation_warning():
    """Test that importing environs specifically doesn't trigger the deprecation warning."""
    # Test that the warning filter is working by trying to import in a subprocess
    import subprocess
    import sys

    # Run a subprocess that imports environs and checks for warnings
    result = subprocess.run(
        [
            sys.executable,
            '-c',
            """
import warnings
import sys

# Capture warnings
with warnings.catch_warnings(record=True) as warning_list:
    warnings.simplefilter("always")

    # Import openhands first to apply our warning filter
    import openhands

    # Import environs which should trigger the warning without our fix
    from environs import Env

    # Check for the specific deprecation warning from environs
    environs_warnings = [
        w for w in warning_list
        if issubclass(w.category, DeprecationWarning)
        and "__version_info__" in str(w.message)
        and "environs" in str(w.filename)
    ]

    if environs_warnings:
        print(f"FOUND_WARNINGS: {len(environs_warnings)}")
        for w in environs_warnings:
            print(f"WARNING: {w.message}")
        sys.exit(1)
    else:
        print("NO_WARNINGS_FOUND")
        sys.exit(0)
        """,
        ],
        capture_output=True,
        text=True,
        cwd='/workspace/OpenHands',
    )

    # Check the result
    assert result.returncode == 0, (
        f'Subprocess found environs warnings. '
        f'stdout: {result.stdout}, stderr: {result.stderr}'
    )
