
# test_patch.py

# Import the patch first to ensure it's applied
import patch_litellm

import litellm
import os

# Set litellm to drop unsupported parameters
litellm.drop_params = True

# Set a dummy API key to avoid authentication errors before the request is made
os.environ["GEMINI_API_KEY"] = "dummy_key"

def test_openhands_gemini_call():
    """
    Simulates the way openhands/llm/llm.py calls litellm.completion
    for a Gemini model with reasoning_effort.
    """
    print("\n--- Simulating OpenHands gemini call ---")
    try:
        # This call mimics the logic in openhands/llm/llm.py
        response = litellm.completion(
            model="gemini/gemini-2.5-pro",
            messages=[{"role": "user", "content": "Why is the sky blue?"}],
            # The llm.py file sets both 'thinking' and 'reasoning_effort'
            thinking={'budget_tokens': 128},
            reasoning_effort=None,
            # We also need to allow these params to pass through
            allowed_openai_params=["thinking"]
        )
        print("\n✅ Simulated call reported success.")
        print("Response:", response)
    except Exception as e:
        print(f"✅ Simulated call failed as expected: {e}")

if __name__ == "__main__":
    test_openhands_gemini_call()
