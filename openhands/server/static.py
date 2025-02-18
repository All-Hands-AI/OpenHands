from typing import Any, MutableMapping
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: MutableMapping[str, Any]) -> Response:
        try:
            return await super().get_response(path, scope)
        except Exception:
            # FIXME: just making this HTTPException doesn't work for some reason
            return await super().get_response('index.html', scope)
