#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   configurations
"""

__author__ = 'heqingliang'


import config_default


configs = config_default.configs


def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


class Dict(dict):
    """simple dict but support access x.y style"""
    def __init__(self, names=(), values=(), **kw):
        super().__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'Dict object has no attribute %s." % item)

    def __setattr__(self, key, value):
        self[key] = value


def to_dict(configs):
    d = Dict()
    for k, v in configs.items():
        d[k] = to_dict(v) if isinstance(v, dict) else v
    return d


try:
    # 如果存在config_override.py，将使用config_override的配置
    # config_override.py中的配置一般用于线上服务器
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = to_dict(configs)
