from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.base import BusinessRuleException, NotFoundException, UnauthorizedException


async def business_exception_handler(
    request: Request,
    exc: BusinessRuleException,
):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "BUSINESS_RULE_ERROR",
                "message": str(exc),
            }
        },
    )


async def not_found_exception_handler(
    request: Request,
    exc: NotFoundException,
):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": str(exc),
            }
        },
    )


async def unauthorized_exception_handler(
    request: Request,
    exc: UnauthorizedException,
):
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "UNAUTHORIZED",
                "message": str(exc),
            }
        },
    )