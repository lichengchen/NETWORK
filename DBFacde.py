import sqlite3
import time
import threading

'''

数据库模块

# 其他模块的调用方法
import db from DBFacde

# 插入记录
db.insert_record(answer_list)       参数：list，每一项为五个域的tuple(Name, TTL, Class, Type, Value)

# 由 name type 查询 value 值
db.get_value(Name, Type)            参数：两个str

# 插入日志
db.insert_log(addr.ip, addr.port, Name, True/False)
参数：请求方的ip,port,请求的域名，DNSRelay是否向DNSServer请求的标志。日志记录会自动加入这条日志的产生时间。

#获取日志
db.search_log(self, start_time, end_time)
参数：要查询的起止时间（格式为标准时间字符串--形如'2019-07-01 00:00:00'）
返回：list，每一项为 (time, addr.ip, addr.port, Name, True/False)

'''

class DBFacade(object):
    instance = None
    _lock = threading.Lock()    # for table Records
    _lock2 = threading.Lock()   # for table Log

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        try:
            self._db = sqlite3.connect('db_dnsRelay.db')
        except:
            print("Database Error!")
            exit(8)
        self._cursor = self._db.cursor()

    def __del__(self):
        self._db.close()

    #返回本地时间
    def localTime(self):
        return time.localtime(time.time())

    #将应答列表插入记录表
    def insert_records(self, answer_list):
        for answer in answer_list:
            self.insert_one_record(answer)

    #将一条记录插入记录表
    def insert_one_record(self, record):
        if not self.exist_in_Records(record):
            self._lock.acquire()
            query = '''
            insert into Records 
            (Name, TTL, Class, Type, Value) 
            values 
            ('%s', %d, '%s', '%s', '%s')''' %(record[0], int(record[1]), record[2], record[3], record[4])
            try:
                self._cursor.execute(query)
                self._db.commit()
                print("插入新记录('%s', %d, '%s', '%s', '%s')"%(record[0], int(record[1]), record[2], record[3], record[4]))
            except Exception as e:
                print('未插入--',e)
            self._lock.release()

    #判断一条记录是否存在
    def exist_in_Records(self, record):
        query = '''
        select count(*) from Records 
        where Name = '%s' and Type = '%s' and Value = '%s' 
        ''' %(record[0], record[3], record[4])
        self._cursor.execute(query)
        res = self._cursor.fetchone()[0]
        if res == 0:
            return False
        else:
            return True

    #由 name type 查询 value 值
    def get_value(self, _name, _type):
        query = '''
        select Value from Records 
        where Name = '%s' and Type = '%s'
        '''% (_name, _type)
        self._cursor.execute(query)
        get = self._cursor.fetchall()
        if get == None:
            res = []
        else:
            res = []
            for one_valueinTuple in get:
                res.append(one_valueinTuple[0])
        return res

    #插入一条日志，参数：请求方的ip, port, 请求的域名， DNSRelay是否向DNSServer请求的标志。日志记录会自动加入这条日志的产生时间。
    def insert_log(self, request_ip, request_port, domain_name, flag):
        self._lock2.acquire()
        t = time.strftime("%Y-%m-%d %H:%M:%S",self.localTime())
        query = '''
        insert into Log 
        (_time, IP, _port, Domain_name, DNSFlag) 
        values 
        ('%s', '%s', '%s', '%s', %d) 
        '''%(t, request_ip, request_port, domain_name, flag)
        try:
            self._cursor.execute(query)
            self._db.commit()
            print('插入新日志：%s -- %s:%s -- %s, %s'%(t, request_ip, request_port, domain_name, flag))
        except Exception as e:
            print(e)
        self._lock2.release()
    
    def search_log(self, start_time, end_time):
        query = '''
        select _time, IP, _port, Domain_name, DNSFlag  from Log
        where _time between '%s' and '%s'
        '''%(start_time, end_time)
        self._cursor.execute(query)
        res = self._cursor.fetchall()
        if res == None:
            res = ()
        else:
            pass
        return res

    def create_table(self):
        self._lock.acquire()
        query = '''
        create table Records(
        Name varchar(50),
        TTL int,
        Class varchar(50),
        Type varchar(50),
        Value varchar(50),
        primary key(Name, Type, Value)
        );
        '''
        try:
            self._cursor.execute(query)
            self._db.commit()
        except Exception as e:
            print(e)

        query = '''
        create table Log(
            _time datetime primary key,
            IP varchar(50),
            _port int,
            Domain_name varchar(50),
            DNSFlag bool
        );
        '''
        try:
            self._cursor.execute(query)
            self._db.commit()
        except Exception as e:
            print(e)
        self._lock.release()


db = DBFacade()

db.create_table()      #首次运行后请注释

#test

record1 = ('name', 1 ,'in', 'a', '111.1.1.1')
record2 = ('name', 2, 'in', 'a', '222.2.2.2')
record3 = ('www.baidu.com', 3, 'in', 'a', '123.1.2.3')
records = [record1, record2,record3]

db.insert_records(records)

print(db.get_value('name', 'a'))


print(db.get_value('没有这个域名', 'a'))
print(db.get_value('www.baidu.com', 'a'))
print(db.get_value('www.baidu1.com', 'a'))
print(db.get_value('www.baidu2.com', 'a'))


db.insert_log('127.1.1.1', 8080, 'www.baidu.com', False)
dic = db.search_log('2019-07-01 00:00:00', time.strftime("%Y-%m-%d %H:%M:%S",db.localTime()))
print('查到', len(dic), '条日志')
print('最后一条：', dic[-1])
