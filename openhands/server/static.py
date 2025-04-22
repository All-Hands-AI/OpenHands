from enum import Enum

from fastapi.staticfiles import StaticFiles


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # FIXME: just making this HTTPException doesn't work for some reason
            return await super().get_response('index.html', scope)


class SortBy(Enum):
    total_view_24h = 'total_view_24h'
    total_view_7d = 'total_view_7d'
    total_view_30d = 'total_view_30d'
