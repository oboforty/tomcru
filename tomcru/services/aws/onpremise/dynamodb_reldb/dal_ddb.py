from sqlalchemy import Column, String, Integer, LargeBinary, Index
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .SqlAlchemyJSONType import JSON_GEN


def build_database(app_path, dalcfg: dict):
    fileloc = dalcfg.pop('__fileloc__', None)
    ctx_cfg = dalcfg.pop('__ctx__')
    dsn = ctx_cfg['dsn']
    should_build_database = False

    if dsn.startswith('sqlite://'):
        should_build_database = not os.path.exists(dsn.split('///')[1])
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
    for idx, index_type in tblcfg.items():
        if idx.endswith('-index'):
            build_index(idx, 'ddb_content', index_type, _declr)

    # add extras
    _declr['partition_key'] = pkey
    _declr['sort_key'] = skey

    Model = type(table_name, (AbstractModel,), _declr)

    return Model

def build_column(column, _declr, tblcfg, **kwargs):
    t = tblcfg.pop(column+'-type', 'str')

    if t == 'str':
        t = String(255)
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
