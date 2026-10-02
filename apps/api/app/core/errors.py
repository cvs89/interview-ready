from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers


def error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    content = {"error": {"code": code, "message": message, "request_id": request_id}}
    response_headers = dict(headers or {})
    rate_limit_headers = getattr(request.state, "rate_limit_headers", None)
    if rate_limit_headers:
        for k, v in rate_limit_headers.items():
            response_headers.setdefault(k, v)
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=response_headers or None,
    )


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(request, exc.code, exc.message, exc.status_code, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, _: RequestValidationError) -> JSONResponse:
        return error_response(request, "VALIDATION_ERROR", "The request is invalid.", 422)
