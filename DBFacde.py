import pymysql
import time
import threading

class DBFacade(object):
    instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        try:
            self._db = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='971022', db='db_dnsRelay')
        except:
            print("Database Error!")
            exit(8)
        self._cursor = self._db.cursor()

    def __del__(self):
        self._db.close()

    def localTime(self):
        return time.localtime(time.time())

    def insert_record(self, domain_name, ip):
        if self.get_ip(domain_name)==ip:
            print('重复插入，忽略')
            return
        query = '''
        insert into Records 
        (Domain_name, IP) 
        values 
        ('%s', '%s')''' %(domain_name, ip)
        self._lock.acquire()
        try:
            self._cursor.execute(query)
            self._db.commit()
            print('插入新记录：%s -- %s'%(domain_name, ip))
        except Exception as e:
            print(e)
        self._lock.release()
    
    def get_ip(self, domain_name):
        query = '''
        select IP from Records 
        where Domain_name = '%s'
        '''% domain_name
        self._lock.acquire()
        self._cursor.execute(query)
        res = self._cursor.fetchone()
        if res == None:
            res = ''
        else:
            res = res[0]
        self._lock.release()
        return res

    def insert_log(self, request_ip, request_port, domain_name, ret_ip, flag):
        self._lock.acquire()
        t = time.strftime("%Y-%m-%d %H:%M:%S",self.localTime())
        query = '''
        insert into Log 
        (_time, IP, _port, Domain_name, Ret_IP, DNSFlag) 
        values 
        (str_to_date(\'%s\','%%Y-%%m-%%d %%H:%%i:%%s'), '%s', '%s', '%s', '%s', %d) 
        '''%(t, request_ip, request_port, domain_name, ret_ip, flag)
        try:
            self._cursor.execute(query)
            self._db.commit()
            print('插入新日志：%s -- %s:%s -- %s, %s, %s'%(t, request_ip, request_port, domain_name, ret_ip, flag))
        except Exception as e:
            print(e)
        self._lock.release()
    
    def search_log(self, start_time, end_time):
        query = '''
        select date_format(_time, '%%Y-%%m-%%d %%H:%%i:%%s'),IP, _port, Domain_name, Ret_IP, DNSFlag  from Log
        where _time between '%s' and '%s'
        '''%(start_time, end_time)
        self._lock.acquire()
        self._cursor.execute(query)
        res = self._cursor.fetchone()
        if res == None:
            res = ()
        else:
            pass
        self._lock.release()
        return res


'''表数据库义
db='db_dnsRelay'

create table Records(
    Domain_name varchar(50) primary key,
    IP varchar(50)
);

create table Log(
	_time datetime primary key,
	IP varchar(50),
	_port int,
	Domain_name varchar(50),
	Ret_IP varchar(50),
	DNSFlag bool
);
'''

db = DBFacade()

#test
print(db.get_ip('没有这个域名'))
print(db.get_ip('www.baidu.com'))
print(db.get_ip('www.baidu1.com'))
print(db.get_ip('www.baidu2.com'))
db.insert_record('www.baidu1.com', '12.2.3.4')

db.insert_log('127.1.1.1', 8080, 'www.baidu.com', '10.2.3.4', False)
print(db.search_log('2019-07-01 00:00:00', time.strftime("%Y-%m-%d %H:%M:%S",db.localTime())))