from .created_datetime import CreatedDateTimeMixin
from .updated_datetime import UpdatedDateTimeMixin


class TimestampMixin(CreatedDateTimeMixin, UpdatedDateTimeMixin):
    """
    Mixin that adds created and updated datetime columns to a model

    Attributes:
        created_datetime (datetime): The datetime when the record was created.
        updated_datetime (datetime | None): The datetime when the record was last updated.
    """

    pass
