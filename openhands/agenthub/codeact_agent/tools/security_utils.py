"""
Security utility constants for tool risk descriptions.
This file contains standardized risk description text for various tools.
"""

# Browser tool risk description
BROWSER_RISK_DESC = "The LLM's assessment of the safety risk of this browser action. This helps the security analyzer determine whether user confirmation is needed."

# Bash tool risk description
BASH_RISK_DESC = "The LLM's assessment of the safety risk of this command. This helps the security analyzer determine whether user confirmation is needed."

# IPython tool risk description
IPYTHON_RISK_DESC = "The LLM's assessment of the safety risk of this Python code. This helps the security analyzer determine whether user confirmation is needed."

# String replace editor tool risk description
STR_REPLACE_EDITOR_RISK_DESC = "The LLM's assessment of the safety risk of this file operation. This helps the security analyzer determine whether user confirmation is needed."

# LLM-based edit tool risk description
LLM_BASED_EDIT_RISK_DESC = "The LLM's assessment of the safety risk of this edit operation. This helps the security analyzer determine whether user confirmation is needed."

# Risk level enum values - common across all tools
RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH']
