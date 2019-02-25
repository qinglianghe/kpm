#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    default configurations
"""

__author__ = 'heqingliang'


configs = {
    'debug': True,
    # mysql相关的配置
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'username',
        'password': 'password',
        'db': 'test'
    },
    # kafka相关的配置
    'kafka': {
        'topic': ['my-topic'],
        'bootstrap_servers': '127.0.0.1:9092',
        'group_id': 'my-group'
    }
}
