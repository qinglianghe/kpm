#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    orm framework
"""

__author__ = 'heqingliang'


import logging
import aiomysql


def log(sql, args=()):
    logging.info('SQL: %s' % sql)


async def create_pool(loop, **kw):
    """
    创建数据库的连接池
    :param loop: event loop
    :param kw: 连接池的参数
    """
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


async def execute(sql, args, autocommit=True):
    """
    执行对应的sql语句，如：insert、delete、update
    :param sql: sql语句
    :param args: 对应sql语句的参数
    :param autocommit: 是否开启事务
    :return: sql语句影响的行数
    """
    log(sql)
    with (await __pool) as conn:
        if not autocommit:
            await conn.begin()
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            await cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            await cur.close()
            if not autocommit:
                await conn.commit()
        except BaseException:
            if not autocommit:
                await conn.rollback()
            raise
        return affected


async def select(sql, args, size=None):
    """
    执行select sql语句
    :param sql: sql语句
    :param args: 对应sql语句的参数
    :param size: 查询结果后，返回给用户的记录大小
    :return: 返回对应的记录大小
    """
    log(sql, args)
    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' % (len(rs)))
        return rs


class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        """
        :param name: 数据库的字段名
        :param column_type: 对应字段的ddl
        :param primary_key: 主键
        :param default: 默认值
        """
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):

    def __init__(self, name=None, ddl='varchar(100)', primary_key=False, default=None):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):

    def __init__(self, name=None, primary_key=None, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):

    def __init__(self, name=None, primary_key=None, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


def create_args_string(num):
    args = []
    for n in range(num):
        args.append('?')
    return ', '.join(args)


class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        table_name = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, table_name))
        mappings = dict()
        fields = []
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primary_key:
                        raise Exception('Duplicate primary key for field: %s' % k)
                    primary_key = k
                else:
                    fields.append(k)
        if not primary_key:
            raise Exception('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda s: '`%s`' % s, fields))
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = table_name  # 表名
        attrs['__primary_key__'] = primary_key  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primary_key, ', '.join(escaped_fields), table_name)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (table_name,
                                                                           ', '.join(escaped_fields),
                                                                           primary_key,
                                                                           create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (table_name,
                                                                   ', '.join(map(lambda s: '`%s`=?' % s, fields)),
                                                                   primary_key)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (table_name, primary_key)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super().__init__(**kw)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'Model'object has no attribute '%s'" % item)

    def __setattr__(self, key, value):
        self[key] = value

    def get_value(self, key):
        return getattr(self, key, None)

    def get_value_or_default(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    async def save(self):
        """将对象插入数据库中"""
        args = list(map(self.get_value_or_default, self.__fields__))
        args.append(self.get_value_or_default(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected row: %s' % rows)

    @classmethod
    async def find(cls, pk):
        """通过主键找出对象"""
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    @classmethod
    async def find_number(cls, select_field, where=None, args=None):
        """统计记录的个数"""
        sql = ['select %s _num_ from `%s`' % (select_field, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find_all(cls, where=None, args=None, **kw):
        """查询记录"""
        sql = [cls.__select__]

        if where:
            sql.append('where')
            sql.append(where)

        if args is None:
            args = []

        order_by = kw.get('order_by', None)
        if order_by:
            sql.append('order by')
            sql.append(order_by)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple):
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    async def update(self):
        """根据对象的主键更新数据库中对应的记录"""
        args = list(map(self.get_value, self.__fields__))
        args.append(self.get_value(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update record: affected row: %s' % rows)

    async def remove(self):
        """根据对象的主键删除数据库中对应的记录"""
        args = [self.get_value(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warning('failed to delete record: affected row: %s' % rows)
