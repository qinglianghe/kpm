#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    generate test data
"""

__author__ = 'heqingliang'


import asyncio
import hashlib
import message_pb2
from aiokafka import AIOKafkaProducer
from models import next_id
from config import configs


def serializer(value):
    return value.SerializeToString()


def make_user_message(uid, passwd, name, email, image, admin):
    user_message = message_pb2.User()
    user_message.id = uid
    user_message.email = email
    user_message.passwd = passwd
    user_message.admin = admin
    user_message.name = name
    user_message.image = image
    return user_message


def make_blog_message(blog_id, uid, user_name, image, title, summary, content):
    blog_message = message_pb2.Blog()
    blog_message.id = blog_id
    blog_message.user_id = uid
    blog_message.user_name = user_name
    blog_message.user_image = image
    blog_message.title = title
    blog_message.summary = summary
    blog_message.content = content
    return blog_message


def make_comment_message(comment_id, blog_id, uid, user_name, image, content):
    comment_message = message_pb2.Comment()
    comment_message.id = comment_id
    comment_message.blog_id = blog_id
    comment_message.user_id = uid
    comment_message.user_name = user_name
    comment_message.user_image = image
    comment_message.content = content
    return comment_message


def write_md5_info(md5):
    with open('md5.info', 'w') as f:
        for m in md5:
            f.write(m + '\n')


async def send_message(loop):
    producer = AIOKafkaProducer(loop=loop, bootstrap_servers=configs.kafka.bootstrap_servers, acks='all',
                                value_serializer=serializer)
    md5 = list()
    await producer.start()
    try:
        for i in range(10000):
            uid = next_id()
            sha1_passwd = '%s:%s' % (uid, 'test_123456%s' % i)
            passwd = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest()
            user_name = 'test_name%s' % i
            email = 'test%s@test.com' % i
            image = 'http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest()
            admin = 0
            await producer.send("my-topic", key=b'user',
                                value=make_user_message(uid, passwd, user_name, email, image, admin))
            md5.append(hashlib.md5((''.join([uid, passwd, user_name, email, image, str(admin)]))
                                   .encode('utf-8')).hexdigest())

            blog_id = next_id()
            title = 'Test blog %s' % i
            summary = 'This is summary.'
            content = 'This is content......'
            await producer.send("my-topic", key=b'blog',
                                value=make_blog_message(blog_id, uid, user_name, image, title, summary, content))
            md5.append(hashlib.md5((''.join([blog_id, uid, user_name, image, title, summary, content]))
                                   .encode('utf-8')).hexdigest())

            comment_id = next_id()
            await producer.send("my-topic", key=b'comment',
                                value=make_comment_message(comment_id, blog_id, uid, user_name, image, content))
            md5.append(hashlib.md5((''.join([comment_id, blog_id, uid, user_name, image, content]))
                                   .encode('utf-8')).hexdigest())
    except Exception:
        raise
    finally:
        await producer.stop()
    return md5


def main():
    loop = asyncio.get_event_loop()
    md5 = loop.run_until_complete(send_message(loop))
    write_md5_info(md5)


if __name__ == '__main__':
    main()
