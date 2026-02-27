from fastapi import FastAPI

from app.routers import composer as composer_router
from app.routers import core as core_router


app = FastAPI(title="Slush Pilot")
app.include_router(core_router.router)
app.include_router(composer_router.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
