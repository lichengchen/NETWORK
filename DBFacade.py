import sqlite3
import time
import threading

'''

数据库模块

# 其他模块的调用方法
from DBFacde import DBFacade
db = DBFacade()


# 插入记录
db.insert_record(answer_list)       
参数：[(Name, TTL, Class, Type, Value), ...]


# 查询：按 Type 对 Name 进行一次查询，返回整个记录 
db.query(Name, Type)
参数：两个str  
返回值：[(Name, TTL, Class, Type, Value), ...]
若 Type 为‘A’ ， 递归查找，返回所有记录
若 Type 为'CNAME'或'MX'， 返回第一条
否则直接返回所有记录
没有找到记录返回 []


# 更新TTL-1，减到0就删除这条记录，应该每秒调用一次这个函数
db.update_TTL()


# 插入日志
db.insert_log(addr.ip, addr.port, Name, True/False)
参数：请求方的ip,port,请求的域名，DNSRelay是否向DNSServer请求的标志。日志记录会自动加入这条日志的产生时间。


# 获取日志
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
            self._db = sqlite3.connect('db_dnsRelay.db', check_same_thread = False)
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
        self._lock.acquire()
        query = '''
        select count(*) from Records 
        where Name = '%s' and Type = '%s' and Value = '%s' 
        ''' %(record[0], record[3], record[4])
        self._cursor.execute(query)
        res = self._cursor.fetchone()[0]
        self._lock.release()
        if res == 0:
            return False
        else:
            return True

    #由 name type 查询 value 值
    def get_value(self, _name, _type):
        self._lock.acquire()
        query = '''
        select Value from Records 
        where Name = '%s' and Type = '%s'
        '''% (_name, _type)
        self._cursor.execute(query)
        get = self._cursor.fetchall()
        self._lock.release()
        if get == None:
            res = []
        else:
            res = []
            for one_valueinTuple in get:
                res.append(one_valueinTuple[0])
        return res

    #直接由name, type查找结果
    def get_record(self, _name, _type):
        self._lock.acquire()
        query = '''
        select * from Records 
        where Name = '%s' and Type = '%s'
        '''% (_name, _type)
        self._cursor.execute(query)
        res = self._cursor.fetchall()
        self._lock.release()
        if res == None:
            return []
        else:
            ret = []
            for record in res:
                ret.append([record[0], str(record[1]), record[2], record[3], record[4]])
            return ret
    
    #对A类型的递归查询
    def query_for_A(self, _name):
        first_try = self.get_record(_name, 'A')     #首先找A
        if first_try != []:
            self.ret_list.append(first_try[0])           #有A，加入返回记录
            return True                             #查询成功
        else:                                       #没有A，找CNAME
            second_try = self.get_value(_name, 'CNAME')     #second_try 找 CNAME 的 VALUE
            if second_try == []:
                self.ret_list.clear()
                return False                           #没有CNAME，本次查询失败
            else:
                self.ret_list.append(self.get_record(_name, 'CNAME')[0])
                return self.query_for_A(second_try[0])  #否则以查到的CNAME为新NAME继续查询

    #按 type 对 name 进行一次查询，返回整个记录
    def query(self, _name, _type):
        if _type == 'A':                #A---递归查询
            self.ret_list = []
            if self.query_for_A(_name):   #成功递归找到A，返回链接起来的记录组
                return self.ret_list
            else:
                return []

        
        elif _type == 'CNAME' or _type == 'MX':
            one_try = self.get_record(_name, _type)
            if one_try == []:
                return one_try
            else:
                return [one_try[0]]     #返回找到的最前一个
        
        else:
            return self.get_record(_name, _type)


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
        self._lock2.acquire()
        query = '''
        select _time, IP, _port, Domain_name, DNSFlag  from Log
        where _time between '%s' and '%s'
        '''%(start_time, end_time)
        self._cursor.execute(query)
        res = self._cursor.fetchall()
        self._lock2.release()
        if res == None:
            res = []
        else:
            pass
        return res
    
    #TTL-1，减到0就删除这条记录
    def update_TTL(self):
        self._lock.acquire()
        query = '''
        update Records
        set TTL = TTL - 1
        '''
        try:
            self._cursor.execute(query)
            self._db.commit()
            print('minus ttl')
        except Exception as e:
            print(e)
        
        query = '''
        delete from Records
        where TTL <= 0
        '''
        try:
            self._cursor.execute(query)
            self._db.commit()
            print('delete if needed')
        except Exception as e:
            print(e)
        
        self._lock.release()


    def create_table(self):
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


'''
db = DBFacade()

#db.create_table()      #首次运行后请注释

#test

record1 = ('name', 1 ,'in', 'CNAME', 'name1')
record2 = ('name1', 2, 'in', 'CNAME', 'name2')
record3 = ('name2', 3, 'in', 'A', '123.1.2.3')
records = [record1, record2,record3]

db.insert_records(records)


print(db.query('name','A'))
print(db.query('name3','A'))

db.insert_log('127.1.1.1', 8080, 'www.baidu.com', False)
dic = db.search_log('2019-07-01 00:00:00', time.strftime("%Y-%m-%d %H:%M:%S",db.localTime()))
print('查到', len(dic), '条日志')
print('最后一条：', dic[-1])
'''
