from sqlalchemy import Column, String, Integer, LargeBinary, Index
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .SqlAlchemyJSONType import JSON_GEN


def build_database(app_path, dsn: str, dalcfg: dict):
    should_build_database = False

    if dsn.startswith('sqlite://'):
        if not dsn.startswith('sqlite:///'):
            raise Exception("Please specify sqlite:// DSN with 3 dashes!")

        db_file_path = dsn.split(':///')[1]
        if not os.path.isabs(db_file_path):
            # guarantee that db is created in app path
            db_file_path = os.path.join(app_path, db_file_path)
            dsn = 'sqlite:///' + db_file_path

        should_build_database = not os.path.exists(db_file_path)
        connect_args = {'check_same_thread': False}
    elif dsn.startswith('postgresql://'):
        connect_args = {}
    else:
        raise Exception("DSN not supported: " + str(dsn))

    # create sqlite engine
    #dalcfg = load_settings(app_path + '/sam/emecfg/ddb.ini')
    db_engine = create_engine(dsn, connect_args=connect_args)
    Session = sessionmaker(bind=db_engine)
    db_session = Session()

    if dsn.startswith('postgresql://'):
        should_build_database = not db_engine.engine.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public');").fetchone()[0]

    # build table objects
    EntityBase = declarative_base()
    _tables = {}

    class AbstractModel(EntityBase):
        __abstract__ = True  # this line is necessary

        def __init__(self, **kwargs):
            for k,v in kwargs.items():
                setattr(self, k, v)

            self.ddb_content = kwargs.copy()

    for table_name, descr in dalcfg.items():
        _tables[table_name] = build_table(AbstractModel, table_name, descr.copy())

    if should_build_database:
        # migrate files
        try:
            EntityBase.metadata.drop_all(db_engine)
        except:
            pass
        EntityBase.metadata.create_all(db_engine)

    return db_session, _tables


def build_table(AbstractModel, table_name, tblcfg):
    _declr = {
    }
    pkey = tblcfg.pop('partition_key')
    skey = tblcfg.pop('sort_key', None)
    rcu, wcu = tblcfg.pop('provision', (float('inf'), float('inf')))

    _declr['__tablename__'] = table_name

    # build columns (partition key, sort key)
    build_column(pkey, _declr, tblcfg, primary_key=True)
    if skey:
        build_column(skey, _declr, tblcfg, primary_key=True)

    # build extra columns
    for idx, column_name in tblcfg.items():
        if idx.endswith('-type') or idx.endswith('-len') or idx.endswith('-index'):
            continue
        build_column(column_name, _declr, tblcfg)

    # build content column
    build_column('ddb_content', _declr, {'ddb_content-type': 'json'})

    # add indexes to content column
    _declr['_indexes'] = {}
    ddb_content_idx_built = False
    for idx, attributes in tblcfg.items():
        if idx.endswith('-index'):
            if not ddb_content_idx_built:
                build_index(idx, 'ddb_content', 'gin', _declr)
                ddb_content_idx_built = True

            _declr['_indexes'][idx] = set(attributes) if not isinstance(attributes, str) else attributes

    # add extras
    _declr['partition_key'] = pkey
    _declr['sort_key'] = skey

    Model = type(table_name, (AbstractModel,), _declr)

    return Model

def build_column(column, _declr, tblcfg, **kwargs):
    t = tblcfg.pop(column+'-type', 'str')

    if t == 'str':
        t = String(2048)
    elif t == 'number':
        t = Integer()
    elif t == 'binary':
        t = LargeBinary()
    elif t == 'json':
        t = JSON_GEN()

    c = Column(t, **kwargs)

    #setattr(_classdef, column, c)
    _declr[column] = c
    return c

def build_index(idx, column_name, index_type, _declr):
    # _SQL_IDX = """CREATE INDEX ON {table_name} USING {impl} ({fk}{suffix});"""

    _declr['__table_args__'] = (Index(idx, column_name, postgresql_using=index_type), )
