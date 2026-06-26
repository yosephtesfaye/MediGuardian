from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.errors import MediGuardianError


async def mediguardian_exception_handler(
    request: Request,
    exc: MediGuardianError,
) -> JSONResponse:
    status_map = {
        "not_found": 404,
        "validation_error": 422,
        "safety_violation": 400,
        "ai_unavailable": 503,
    }
    return JSONResponse(
        status_code=status_map.get(exc.code, 400),
        content={"error": exc.code, "message": exc.message},
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Internal Server Error"},
    )
