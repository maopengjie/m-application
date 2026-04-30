from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column, Mapped


# Type alias for common columns
timestamp = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]
updated_timestamp = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    ),
]


class TimestampMixin:
    created_at: Mapped[timestamp]
    updated_at: Mapped[updated_timestamp]
