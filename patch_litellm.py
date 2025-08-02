
import litellm
import json
import os
from functools import wraps
import httpx

# Import the handlers
from litellm.llms.custom_httpx.http_handler import HTTPHandler, AsyncHTTPHandler

# Keep a reference to the original post methods
original_http_post = HTTPHandler.post
original_async_http_post = AsyncHTTPHandler.post

def _log_request(url, headers, json_data):
    """Helper function to log the request details."""
    log_file = 'litellm_final_request.json'
    log_entry = {
        'url': url,
        'headers': dict(headers) if isinstance(headers, httpx.Headers) else headers,
        'json_data': json_data
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry, indent=2))
        f.write('\n---\n')
    print(f"✅ Final request logged to {log_file}")

@wraps(original_http_post)
def patched_http_post(self, url: str, **kwargs):
    """
    Patched version of HTTPHandler.post that logs the request.
    """
    json_data = kwargs.get('json')
    headers = kwargs.get('headers')
    _log_request(url, headers, json_data)
    return original_http_post(self, url, **kwargs)

@wraps(original_async_http_post)
async def patched_async_http_post(self, url: str, **kwargs):
    """
    Patched version of AsyncHTTPHandler.post that logs the request.
    """
    json_data = kwargs.get('json')
    headers = kwargs.get('headers')
    _log_request(url, headers, json_data)
    return await original_async_http_post(self, url, **kwargs)

# Apply the monkey patches
HTTPHandler.post = patched_http_post
AsyncHTTPHandler.post = patched_async_http_post

print("🐵 litellm.llms.custom_httpx.http_handler.HTTPHandler.post has been monkey-patched.")
print("🐵 litellm.llms.custom_httpx.http_handler.AsyncHTTPHandler.post has been monkey-patched.")


# --- Example Usage ---
if __name__ == "__main__":
    print("\nRunning a test completion call to trigger the patch...")
    try:
        # This call will be intercepted by our patch at the httpx level
        response = litellm.completion(
            model="gemini/gemini-pro",
            messages=[{"role": "user", "content": "Why is the sky blue?"}],
            mock_response="Because of Rayleigh scattering!" # Mock to avoid actual API call
        )
        print("\n✅ Test completion call successful.")
        print("Response:", response)
    except Exception as e:
        print(f"❌ Test completion call failed: {e}")

    # Revert the patches
    HTTPHandler.post = original_http_post
    AsyncHTTPHandler.post = original_async_http_post
    print("\n🐵 Monkey patches reverted.")

