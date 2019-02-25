#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    从kafka中拉取数据，根据message中的key判断是哪种message
    创建对应message的解析类，反序列化prodobuf数据后，通过
    orm框架保存到对应的数据表中
"""

__author__ = 'heqingliang'

import asyncio
import logging  ;logging.basicConfig(level=logging.INFO)
import orm
import time
from aiokafka import AIOKafkaConsumer
from config import configs
from message import UserMessage, BlogMessage, CommentMessage


def make_message_object(key):
    d = {
        b'user': UserMessage(),
        b'blog': BlogMessage(),
        b'comment': CommentMessage()
    }
    if key not in d:
        raise ValueError('Invalid value: %s' % key)
    return d[key]


async def save2db(batch):
    for msg in batch:
        m = make_message_object(msg.key)
        m.decode(msg.value)
        await m.save()


async def consume(loop):
    """
        根据配置文件创建mysql的连接池和kafka的消费者
        从kafka中读取数据，反序列化protobuf，通过orm写入mysql数据中
    """
    await orm.create_pool(**configs.db, loop=loop)
    consumer = AIOKafkaConsumer(*configs.kafka.topic, loop=loop,
                                bootstrap_servers=configs.kafka.bootstrap_servers,
                                group_id=configs.kafka.group_id,
                                enable_auto_commit=True,
                                auto_offset_reset="earliest"
                                )
    await consumer.start()
    try:
        batch = []
        async for msg in consumer:
            logging.info('CONSUMED: %s, %s, %s' % (msg.topic, msg.partition, msg.offset))
            batch.append(msg)
            if len(batch) == 100:
                await save2db(batch)
                batch = []
    finally:
        await consumer.stop()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(consume(loop))


if __name__ == '__main__':
    main()
