from typing import Any


def get_obj_or_type_value(obj_or_type: Any, name: str, *args, **kwargs) -> Any | None:
    """
    Call any object or type attribute or method safely

    Attributes:
        obj_or_type (Any): Any object or type
        name (str): The name of the method or attributes
        *args: Positional arguments to pass to the method
        **kwargs: Keyword arguments to pass to the method

    Returns:
        Any | None: The object's value or None if attribute not found
    """

    if isinstance(obj_or_type, dict):
        return obj_or_type.get(name, None)

    if hasattr(obj_or_type, name):
        obj = getattr(obj_or_type, name)
        if callable(obj):
            if args or kwargs:
                return obj(*args, **kwargs)
            return obj()
        else:
            return obj
    else:
        return None
