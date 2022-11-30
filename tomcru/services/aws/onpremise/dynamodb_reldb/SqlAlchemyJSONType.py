import json
from sqlalchemy import TEXT
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB


class JSON_GEN(TypeDecorator):
    """Platform-independent JSONB type.
    Uses PostgreSQL's JSONB type, otherwise uses text
    """
    impl = TEXT

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(TEXT())

    def process_bind_param(self, value, dialect):
        # python -> DB conversion
        if value is None:
            return value

        if dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, str):
                return json.dumps(value)
            return value

    def process_result_value(self, value, dialect):
        # DB -> python conversion
        if value is None:
            return value

        if dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return json.loads(value)
            return value