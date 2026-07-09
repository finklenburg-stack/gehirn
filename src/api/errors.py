from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Einheitliches Fehlerformat {error, detail} gemaess contracts/api.md."""

    def __init__(self, status_code: int, error: str, detail: str | None = None):
        self.status_code = status_code
        self.error = error
        self.detail = detail
        super().__init__(f"{status_code} {error}: {detail or ''}")


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    body: dict = {"error": exc.error}
    if exc.detail:
        body["detail"] = exc.detail
    return JSONResponse(status_code=exc.status_code, content=body)
