## kpm

这是一个使用python的异步IO编写的，将生产者使用[message.proto](https://github.com/qinglianghe/aiokafka-protobuf-mysql/blob/master/src/message.proto)定义的protobuf的message序列化后、写入到kafka中。消费者从kafka中获取message、进行protobuf的反序列化后、通过ORM框架将数据保存到MySQL对应的数据表中。

如图：

![kpm.jpg](/images/kpm.jpg)

### message.proto

[message.proto](https://github.com/qinglianghe/kpm/blob/master/src/message.proto)定义protobuf序列化和反序列化的message

### message_pb2.py

[message_pb2.py](https://github.com/qinglianghe/kpm/blob/master/src/message_pb2.py)是由[message.proto](https://github.com/qinglianghe/kpm/blob/master/src/message.proto)使用protobuf工具生成的对应message的python代码

### message.py

[message.py](https://github.com/qinglianghe/kpm/blob/master/src/message.py)定义protobuf message对应的类：提供反序列化、通过调用orm的保存数据到MySQL中的接口。

### models.py

[models.py](https://github.com/qinglianghe/kpm/blob/master/src/models.py)定义数据表对应的类，类中的每个字段对应于数据表的字段。

### orm.py

[orm.py](https://github.com/qinglianghe/kpm/blob/master/src/orm.py)使用aiomysql实现的ORM框架，将MySQL数据库的一行记录映射为一个对象，一个类对应一个表，写代码更简单，不用直接操作SQL语句：

- 调用`create_pool`创建对应的数据库连接池

- `Field`相关的类，负责保存数据库表的字段名和字段类型

- `ModelMetaclass`元类，负责保存属性和列的映射关系、表名、主键名、以及对应的增、删、改、查的sql语句

- `Model`定义各种操作数据库的方法，比如`save`、`delete`、`update`、`find`等

### 配置

- [config_default.py](https://github.com/qinglianghe/kpm/blob/master/src/config_default.py)：配置文件，用于测试环境，定义mysql和aiokafka的连接地址等

- [config_override.py](https://github.com/qinglianghe/kpm/blob/master/src/config_override.py): 用于在线上环境时，会将[config_default.py](https://github.com/qinglianghe/kpm/blob/master/src/config_default.py)定义的配置覆盖

- [config.py](https://github.com/qinglianghe/kpm/blob/master/src/config.py)：生成配置信息，优先加载[config_default.py](https://github.com/qinglianghe/kpm/blob/master/src/config_default.py)定义的配置，如果[config_override.py](https://github.com/qinglianghe/kpm/blob/master/src/config_override.py)定义有相同的配置，则会覆盖掉[config_default.py](https://github.com/qinglianghe/kpm/blob/master/src/config_default.py)定义的配置

### consumer.py

[consumer.py](https://github.com/qinglianghe/kpm/blob/master/src/consumer.py)定义的消费者：

- 使用异步IO，根据配置创建mysql的连接池和kafka的连接

- 从kafka中消费数据，根据对应message的key反序列化protohuf的message，最后通过ORM框架将数据保存中对应的数据表中

### producer_test.py

[producer_test.py](https://github.com/qinglianghe/kpm/blob/master/src/producer_test.py)用于生成测试数据，将序列化的protobuf数据写入kafka中

### 运行环境

- Python 3.5.2
- MySql 5.6.0
- protobuf 3.0
- aiokafka
- aiomysql

### 测试

#### 生成数据库和数据表

    mysql -u root -p < schema.sql

sql脚本导入成功后，会生成test数据库、users表、blogs表、comments表。

#### 编译 transmitted_message.proto 文件

    protoc --python_out=. message.proto 

编译成功后，会在当前目录下生成一个message_pb2.py文件。

#### 生成测试数据

    python3 producer.py

操作成功后，会往kafka发送测试的数据，并在当前目录下生成一个md5.info文件。

#### 保存到数据库

    python3 consumer.py

操作成功后，会从kafka中读取数据，反序列化后，通过ORM框架写入到对应的数据表中。

#### 检查数据的完整性

    python3 check_md5.py

如果数据库中的所有的记录的md5与测试时生成的md5.info相同，则会输出：

    test data is complete in the database.
