"""Real CLI positive control. Set OH_VERIFY_RUN to the owned fixed run.

I am an AI agent helping Engel Nyst (@enyst) with project work.
No message is supplied and no model response is requested. Fixture conversations
and the inert plugin directory are removed in finally blocks.
"""
import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote


def cli(*args):
    result = subprocess.run(
        ["control-openhands", *args], capture_output=True, text=True, check=False
    )
    payload = json.loads(result.stdout)
    if result.returncode:
        raise RuntimeError(f"CLI action failed: {args[:2]}")
    return payload


run = Path(os.environ["OH_VERIFY_RUN"])
source = run / "workspace" / "qa-coordinate-only-plugin"
assert not source.exists() and not source.is_symlink()
(source / ".plugin").mkdir(parents=True)
(source / ".plugin/plugin.json").write_text(json.dumps({
    "name": "qa-coordinate-only-plugin", "version": "0.1.0",
    "description": "Inert launch check; no tools, skills, or messages.",
}))
cases = []
try:
    cli("browser", "viewport", "desktop")
    for mode in ["omitted", "empty-object"]:
        created_id = None
        try:
            plugin = {"source": str(source)}
            if mode == "empty-object":
                plugin["parameters"] = {}
            query = quote(base64.b64encode(json.dumps([plugin]).encode()).decode(), safe="")
            cli("browser", "goto", "/launch?plugins=" + query)
            assert cli("browser", "count", "testid=plugin-parameters-unsupported")["count"] == 0
            cli("browser", "check", "testid=trust-checkbox")
            assert cli("browser", "enabled", "testid=start-conversation-button")["enabled"]
            cli("browser", "network", "--clear")
            cli("browser", "click", "testid=start-conversation-button")
            cli("browser", "wait-url", "/conversations/[0-9a-f-]{36}")
            created_id = re.search(r"/conversations/([0-9a-f-]{36})", cli("browser", "url")["url"])[1]
            network = cli("browser", "network", "--filter", "/api/conversations$", "--bodies")
            requests = [r for r in network["recent"] if r.get("method") == "POST"]
            assert len(requests) == 1 and requests[0]["status"] == 201
            sent = requests[0]["bodyFields"]["plugins"]
            assert len(sent) == 1 and sent[0]["source"] == str(source)
            assert "parameters" not in sent[0]
            assert set(sent[0]) <= {"source", "ref", "repo_path"}
            cli("browser", "screenshot", "--feature", "F19.launch-parameters", "--name", "positive-" + mode)
            cases.append({"parameters": mode, "warning_count": 0,
                          "start_enabled": True, "create_status": 201,
                          "sent_plugin_fields": sorted(sent[0]),
                          "message_supplied": False})
        finally:
            if created_id:
                removed = cli("api", "DELETE", "/api/conversations/" + created_id, "--write")
                assert removed["status"] == 200
                if cases and cases[-1]["parameters"] == mode:
                    cases[-1]["delete_status"] = removed["status"]
            cli("browser", "goto", "/conversations")
finally:
    shutil.rmtree(source)

print(json.dumps({"cases": cases, "model_response_requested": False,
                  "fixture_removed": not source.exists()}, indent=2))
