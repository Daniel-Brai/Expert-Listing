from fastapi import status
from shared.errors.utils import create_problem_handler

# Base / general exceptions
base_error_handler = create_problem_handler(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    title="Internal Server Error",
)

bad_request_handler = create_problem_handler(
    status_code=status.HTTP_400_BAD_REQUEST,
    title="Bad Request",
)

resource_not_found_handler = create_problem_handler(
    status_code=status.HTTP_404_NOT_FOUND,
    title="Not Found",
)

app_exception_handler = create_problem_handler(
    status_code=status.HTTP_400_BAD_REQUEST,
    title="Application Error",
)

# Authentication exceptions
authentication_handler = create_problem_handler(
    status_code=status.HTTP_401_UNAUTHORIZED,
    title="Authentication Error",
)

invalid_auth_format_handler = create_problem_handler(
    status_code=status.HTTP_400_BAD_REQUEST,
    title="Invalid Authentication Format",
)

invalid_credentials_handler = create_problem_handler(
    status_code=status.HTTP_401_UNAUTHORIZED,
    title="Invalid Credentials",
)

missing_token_handler = create_problem_handler(
    status_code=status.HTTP_401_UNAUTHORIZED,
    title="Invalid Session",
)
