"""Constants shared across runtime implementations."""

import os
import platform

# Port ranges for different services
EXECUTION_SERVER_PORT_RANGE = (30000, 39999)
VSCODE_PORT_RANGE = (40000, 49999)
APP_PORT_RANGE_1 = (50000, 54999)
APP_PORT_RANGE_2 = (55000, 59999)

if os.name == 'nt' or platform.release().endswith('microsoft-standard-WSL2'):
    EXECUTION_SERVER_PORT_RANGE = (30000, 34999)
    VSCODE_PORT_RANGE = (35000, 39999)
    APP_PORT_RANGE_1 = (40000, 44999)
    APP_PORT_RANGE_2 = (45000, 49151)
