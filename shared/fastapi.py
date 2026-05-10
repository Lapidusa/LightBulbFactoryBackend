from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def create_service_app(title: str, description: str) -> FastAPI:
    app = FastAPI(title=title, description=description, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "success" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"code": "http_error", "message": str(exc.detail), "details": None}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "validation_error", "message": "Request validation failed", "details": exc.errors()},
            },
        )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, bool]:
        return {"success": True}

    return app

