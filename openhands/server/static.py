from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # FIXME: just making this HTTPException doesn't work for some reason
            return await super().get_response('index.html', scope)


app.mount('/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist')
