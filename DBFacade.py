import sqlite3
import time
import threading
import sys

'''

数据库模块

# 其他模块的调用方法
from DBFacde import DBFacade
db = DBFacade()     #db 是单例


# 插入记录
db.insert_record(answer_list)       
参数：[(Name, TTL, Class, Type, Value), ...]


# 查询：按 Type 对 Name 进行一次查询，返回所有记录 
db.query(Name, Type)
参数：两个str
返回值：[[Name, TTL, Class, Type, Value], ...]，每个值都是str
若 Type 为‘A’ ， 递归查找，直到返回所有记录
否则直接返回所有记录
没有找到记录返回 []


# 更新TTL-1，减到0就删除这条记录，DNSRelay 应该每秒调用一次这个函数
db.update_TTL()


# 查看数据库
db.fetch_table()
返回：[(Name, TTL, Class, Type, Value), ...]

'''

class DBFacade(object):
    instance = None
    _lock = threading.Lock()    # for table Records

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
        self._lock.acquire()
        for record in answer_list:
            query = '''
            insert into Records 
            (Name, TTL, Class, Type, Value) 
            values 
            ('%s', %d, '%s', '%s', '%s')''' %(record[0], int(record[1]), record[2], record[3], record[4])
            try:
                self._cursor.execute(query)
                print("插入新记录('%s', %d, '%s', '%s', '%s')"%(record[0], int(record[1]), record[2], record[3], record[4]))
            except:
                pass
        self._db.commit()
        self._lock.release()
            

    #判断一条记录是否存在
    def exist_in_Records(self, record):
        self._lock.acquire()
        query = '''
        select 1 from Records where Name='%s' and Type='%s'and Value='%s'
        ''' %(record[0], record[3], record[4])
        self._cursor.execute(query)
        res = self._cursor.fetchone()
        self._lock.release()
        if res == None:
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
        try:
            get = self._cursor.fetchall()
        except Exception as e:
            print('Exception1:',e)
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
            second_try = self.get_record(_name, 'CNAME')    #second_try 找 CNAME 的 记录  
            if second_try == []:
                self.ret_list.clear()
                return False                           #没有CNAME，本次查询失败
            else:
                self.ret_list.append(second_try[0])
                return self.query_for_A(second_try[0][4])  #否则以 CNAME 查到的的 VALUE 为新NAME继续查询

    #按 type 对 name 进行一次查询，返回整个记录
    def query(self, _name, _type):
        if _type == 'A':                #A---递归查询
            self.ret_list = []
            if self.query_for_A(_name):   #成功递归找到A，返回链接起来的记录组
                return self.ret_list
            else:
                return []
        
        else:
            return self.get_record(_name, _type)

    
    #TTL-1，减到0就删除这条记录
    def update_TTL(self):
        self._lock.acquire()
        query = '''
        update Records
        set TTL = TTL - 1
        where Value!='0.0.0.0' and Value!='0:0:0:0:0:0:0:0'
        '''
        try:
            self._cursor.execute(query)
            self._db.commit()
        except Exception as e:
            print('Exception2',e)
        
        query = '''
        select count(*) from Records
        where TTL <= 0
        '''
        self._cursor.execute(query)
        res = self._cursor.fetchone()
        if res!=None and res[0]!= 0:    #TTL到期删除
            query = '''
            delete from Records
            where TTL <= 0
            '''
            try:
                self._cursor.execute(query)
                self._db.commit()
                print('删除', res[0], '条到期记录')
            except Exception as e:
                print('Exception3',e)
        else:
            sys.stdout.write('-')
            sys.stdout.flush()
        
        self._lock.release()


    def fetch_table(self):
        self._lock.acquire()
        query = '''
        select *  from Records
        '''
        self._cursor.execute(query)
        res_records = self._cursor.fetchall()
        self._lock.release()
        if res_records == None:
            res_records = []
        return res_records

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
            print('成功建表！')
        except Exception as e:
            print(e)

    def init_table_from_file(self):
        with open('dnsrelay.txt', 'r') as f:
            self._lock.acquire()
            lines = f.readlines()
            for line in lines:
                line = line.strip('\n')
                get = line.split(' ')
                value = get[0]
                name = get[-1]
                if value!='' and name!='':
                    name = name + '.'

                    query = '''
                    insert into Records 
                    (Name, TTL, Class, Type, Value) 
                    values 
                    ('%s', %d, '%s', '%s', '%s')''' %(name, 10000, 'IN', 'A',value)
                    try:
                        self._cursor.execute(query)
                    except Exception as e:
                        print('init_error in %s, %s'%(name, value), e)
                    
                    if value == '0.0.0.0':
                        query = '''
                        insert into Records 
                        (Name, TTL, Class, Type, Value) 
                        values 
                        ('%s', %d, '%s', '%s', '%s')''' %(name, 10000, 'IN', 'AAAA','0:0:0:0:0:0:0:0')
                        try:
                            self._cursor.execute(query)
                        except Exception as e:
                            print('init_error in %s, %s'%(name, value), e)
                    
            self._db.commit()
            self._lock.release()



if __name__ == '__main__':
    db = DBFacade()
    db.create_table()
    db.init_table_from_file()