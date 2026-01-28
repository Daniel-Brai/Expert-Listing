from fastapi import FastAPI
from fastapi_problem.handler import add_exception_handler
from shared.errors.registry import eh


def setup_exception_handler(app: FastAPI) -> None:
    """
    Set up exception handlers for the FastAPI app.
    """

    add_exception_handler(app, eh)
