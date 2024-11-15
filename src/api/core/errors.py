from fastapi import HTTPException, status


class EmailAPIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = None
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "message": message,
                "error_code": error_code or "INTERNAL_ERROR"
            }
        )

class EmailNotFoundError(EmailAPIError):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Email not found",
            error_code="EMAIL_NOT_FOUND"
        ) 