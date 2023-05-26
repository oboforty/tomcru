from sqlalchemy.orm import Query


class DDBSqlAlchemyTable:
    def __init__(self, sess, mapped_model, tabledef, autocommit=True):
        self.T = mapped_model
        self.TableDef = tabledef
        self.session = sess

        self.table_name = self.TableDef.fullname
        self.partition_key = self.TableDef.primary_key.columns[0].name
        self.sort_key = None
        # todo: support sort_key!

        self._autocommit = autocommit

    def _get_ent(self, Key):
        if self.sort_key:
            _reldbkey = (Key[self.partition_key], Key[self.sort_key])
        else:
            _reldbkey = Key[self.partition_key]

        ent = self.session.query(self.T).get(_reldbkey)

        return ent

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # batch writer used in a python contexts uses autocommit=False
        self.session.commit()

    def _get_key(self, Item):
        if not isinstance(Item, dict):
            Item = Item['ddb_content']

        if self.partition_key not in Item:
            print("WTF???", Item, self.partition_key)

        _key = {
            self.partition_key: Item[self.partition_key]
        }

        if self.sort_key:
            _key[self.sort_key] = Item[self.sort_key]

        return _key

    def _truncate(self):
        self.session.execute(f'''TRUNCATE TABLE "{self.table_name}"''')
        self.session.commit()

    def sql(self) -> tuple[Query, object]:
        return self.session.query(self.T), self.T
