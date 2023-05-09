from .DDBSqlAlchemyTable import DDBSqlAlchemyTable


class DDBClient:
    def __init__(self, tables):
        self._tables: dict[str, DDBSqlAlchemyTable] = tables


class DDBResource:
    def __init__(self, tables):
        self._tables: dict[str, DDBSqlAlchemyTable] = tables

    def Table(self, table_name) -> DDBSqlAlchemyTable:
        return self._tables.get(table_name)
