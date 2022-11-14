from .DdbTableAdapter import DdbTableAdapter


class DdbSqlAlchemyAdapter:
    def __init__(self, sess, tables):
        self._tables = {k: DdbTableAdapter(sess, t) for k,t in tables.items()}

    def Table(self, table_name) -> DdbTableAdapter:
        return self._tables.get(table_name)
