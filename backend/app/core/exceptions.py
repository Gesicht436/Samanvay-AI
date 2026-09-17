"""
Samanvay-AI Custom HTTP Exceptions.

Pure HTTP 404/422/409/503 error contracts — zero mock heuristic fallbacks.
"""

from fastapi import HTTPException, status


class ResourceNotFoundError(HTTPException):
    """Raised when a requested resource does not exist in the database."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "RESOURCE_NOT_FOUND",
                "resource": resource,
                "identifier": identifier,
                "message": f"{resource} with identifier '{identifier}' not found.",
            },
        )


class ValidationError(HTTPException):
    """Raised when request payload fails validation."""

    def __init__(self, message: str, field: str | None = None):
        detail = {"error": "VALIDATION_ERROR", "message": message}
        if field:
            detail["field"] = field
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class IdempotencyConflictError(HTTPException):
    """Raised when an idempotency key is currently being processed."""

    def __init__(self, key: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "IDEMPOTENCY_CONFLICT",
                "idempotency_key": key,
                "message": "Request with this idempotency key is currently being processed.",
            },
        )


class InsufficientInventoryError(HTTPException):
    """Raised when inventory quantity is insufficient for requisition."""

    def __init__(self, sku_code: str, available: int, requested: int):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INSUFFICIENT_INVENTORY",
                "sku_code": sku_code,
                "available_qty": available,
                "requested_qty": requested,
                "message": f"Insufficient inventory for {sku_code}: {available} available, {requested} requested.",
            },
        )


class ServiceUnavailableError(HTTPException):
    """Raised when a downstream service (Qdrant, Neo4j, etc.) is unavailable."""

    def __init__(self, service: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "SERVICE_UNAVAILABLE",
                "service": service,
                "message": f"Downstream service '{service}' is currently unavailable.",
            },
        )


class PrivacyViolationError(HTTPException):
    """Raised if code path attempts to expose protected commercial attributes cross-CPSE."""

    def __init__(self, field: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PRIVACY_VIOLATION",
                "field": field,
                "message": f"Attribute-level privacy: '{field}' is protected and cannot be disclosed cross-CPSE.",
            },
        )
