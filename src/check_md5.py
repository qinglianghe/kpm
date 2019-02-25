#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    check the integrity of the generated test data
"""

__author__ = 'heqingliang'


import asyncio
import orm
import hashlib
from config import configs
from models import User, Blog, Comment


def read_md5_info():
    md5 = set()
    with open('md5.info', 'r') as f:
        for line in f:
            md5.add(line.strip())
    return md5


def make_user_md5(user):
    return hashlib.md5((''.join([user.id, user.passwd, user.name, user.email, user.image, str(user.admin)]))
                           .encode('utf-8')).hexdigest()


def make_blog_md5(blog):
    return hashlib.md5((''.join([blog.id, blog.user_id, blog.user_name, blog.user_image, blog.title, blog.summary,
                                 blog.content])).encode('utf-8')).hexdigest()


def make_comment_md5(comment):
    return hashlib.md5((''.join([comment.id, comment.blog_id, comment.user_id, comment.user_name, comment.user_image,
                                 comment.content])).encode('utf-8')).hexdigest()


async def compare_record_md5(cls, make_md5, offset, limit, md5):
    records = await cls.find_all(limit=(offset, limit))
    for record in records:
        record_md5 = make_md5(record)
        if record_md5 not in md5:
            raise ValueError('This record is incomplete: %s' % record_md5)
        md5.remove(record_md5)


async def check_md5(loop, md5):
    await orm.create_pool(**configs.db, loop=loop)
    tables = {
        User: make_user_md5,
        Blog: make_blog_md5,
        Comment: make_comment_md5
    }
    for cls, make_md5 in tables.items():
        num = await cls.find_number('count(id)')
        limit = 10
        for n in range(num // limit):
            await compare_record_md5(cls, make_md5, n * limit, limit, md5)

        mod = num % limit
        if mod:
            await compare_record_md5(cls, make_md5, num - mod, mod, md5)


def main():
    md5 = read_md5_info()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_md5(loop, md5))
    if not md5:
        print('test data is complete in the database.')


if __name__ == '__main__':
    main()
