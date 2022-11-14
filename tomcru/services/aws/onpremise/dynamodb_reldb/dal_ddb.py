from sqlalchemy import Column, String, Integer, LargeBinary
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from eme.data_access import JSON_GEN
from eme.entities import load_settings


def build_database(app_path, dalcfg: dict):
    fileloc = dalcfg.pop('__fileloc__', None)

    db_file = app_path + '/d.db'
    should_build_database = os.path.exists(db_file)

    # create sqlite engine
    #dalcfg = load_settings(app_path + '/sam/emecfg/ddb.ini')
    db_engine = create_engine(f'sqlite:///{db_file}', connect_args={'check_same_thread': False})
    Session = sessionmaker(bind=db_engine)
    db_session = Session()

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

    if not should_build_database:
        # migrate files
        # EntityBase.metadata.drop_all(ctx.db_engine, tables=drop_order())
        EntityBase.metadata.create_all(db_engine)

    return db_session, _tables


def build_table(AbstractModel, table_name, tblcfg):
    _declr = {
    }
    pkey = tblcfg.pop('partition_key')
    skey = tblcfg.pop('sort_key', None)
    rcu, wcu = tblcfg.pop('rate_simulation', (float('inf'), float('inf')))

    _declr['__tablename__'] = table_name

    build_column(pkey, _declr, tblcfg, primary_key=True)

    if skey:
        build_column(skey, _declr, tblcfg, primary_key=True)

    for idx, column_name in tblcfg.items():
        if idx.endswith('-type') or idx.endswith('-len'):
            continue

        build_column(column_name, _declr, tblcfg)

    build_column('ddb_content', _declr, {'ddb_content-type': 'json'})

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

#
# class Song(EntityBase):
#     __tablename__ = 'songs'
#
#     song_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
#     name = Column(String(255))
#     artist = Column(String(255))
#     about = Column(Text())
#
#     instrument = Column(SmallInteger())
#     skey = Column(String(20))
#     strength = Column(SmallInteger())
#     tempo = Column(SmallInteger())
#     beats_per_measure = Column(SmallInteger())
#     beats_type = Column(SmallInteger())
#
#     notes = Column(Text())
#     ropts = Column(JSON_GEN())
#
#     def __init__(self, **kwargs):
#         self.song_id = kwargs.get('song_id')
#
#         self.set(**kwargs)
#
#     def set(self, **kwargs):
#         self.name = kwargs.get('name')
#         self.artist = kwargs.get('artist')
#         self.about = kwargs.get('about')
#         self.instrument = kwargs.get('instrument')
#         self.skey = kwargs.get('skey', "G_major")
#         self.strength = kwargs.get('strength', 1)
#         self.tempo = kwargs.get('tempo', 90)
#         self.beats_per_measure = kwargs.get('beats_per_measure', 4)
#         self.beats_type = kwargs.get('beats_type', 4)
#         self.notes = kwargs.get('notes', "")
#         self.ropts = kwargs.get('ropts', {})
#         self.is_scale = kwargs.get('is_scale', False)
#
#     @property
#     def view(self):
#         return {
#             'song_id': self.song_id,
#             'name': self.name,
#             'artist': self.artist,
#             'about': self.about,
#             'instrument': self.instrument,
#             'skey': self.skey,
#             'strength': self.strength,
#             'tempo': self.tempo,
#             'beats_per_measure': self.beats_per_measure,
#             'beats_type': self.beats_type,
#             'ropts': self.ropts,
#         }
#
#     @property
#     def time_signature(self):
#         return (self.beats_per_measure, self.beats_type)
