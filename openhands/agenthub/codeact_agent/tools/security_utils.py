"""Security utility constants for tool risk descriptions.

This file contains standardized risk description text for various tools.
"""

# Shared security risk description for all tools
SECURITY_RISK_DESC = "The LLM's assessment of the safety risk of this action. See the SECURITY_RISK_ASSESSMENT section in the system prompt for risk level definitions."

# Risk level enum values - common across all tools
RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH']
