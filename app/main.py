from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat as chat_router
from app.routers import composer as composer_router
from app.routers import core as core_router


app = FastAPI(title="Slush Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router.router)
app.include_router(composer_router.router)
app.include_router(chat_router.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
