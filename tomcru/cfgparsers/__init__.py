from .EnvParser import EnvParser
from .SwaggerCfgParser import SwaggerCfgParser
from .MergeCfgParser import MergeCfgParser
from .BaseCfgParser import BaseCfgParser

_parsers = {
    "swagger": SwaggerCfgParser,
    "merge": MergeCfgParser,
    "env": EnvParser
}


def register_parser(name, cls):
    _parsers[name] = cls
