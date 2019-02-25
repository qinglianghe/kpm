#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    对protobuf的message进行反序列化
    创建message对应的类，调用orm的save的接口，保存记录到mysql中
"""

__author__ = 'heqingliang'


import message_pb2
from models import User, Blog, Comment


class UserMessage(object):

    def __init__(self):
        self.user_message = message_pb2.User()

    def decode(self, value):
        self.user_message.ParseFromString(value)

    async def save(self):
        user = User(id=self.user_message.id, name=self.user_message.name,
                    email=self.user_message.email, passwd=self.user_message.passwd,
                    image=self.user_message.image, admin=self.user_message.admin)
        await user.save()


class BlogMessage(object):

    def __init__(self):
        self.blog_message = message_pb2.Blog()

    def decode(self, value):
        self.blog_message.ParseFromString(value)

    async def save(self):
        blog = Blog(id=self.blog_message.id, user_id=self.blog_message.user_id,
                    user_name=self.blog_message.user_name, user_image=self.blog_message.user_image,
                    title=self.blog_message.title, summary=self.blog_message.summary,
                    content=self.blog_message.content)
        await blog.save()


class CommentMessage(object):

    def __init__(self):
        self.comment_message = message_pb2.Comment()

    def decode(self, value):
        self.comment_message.ParseFromString(value)

    async def save(self):
        comment = Comment(id=self.comment_message.id, blog_id=self.comment_message.blog_id,
                          user_id=self.comment_message.user_id, user_name=self.comment_message.user_name,
                          user_image=self.comment_message.user_image, content=self.comment_message.content)
        await comment.save()
