import time
import threading
import socket
from DBFacade import DBFacade
from Handler import Handler

class DNSRelay:
    def __init__(self, bind_ip = '127.0.0.1', bind_port = 53, send_ip = '10.3.9.4', send_port = 53, auto_update = True):
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.send_ip = send_ip
        self.send_port = send_port
        self.c_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 与客户端通信的数据报式套接字
        self.auto_update = auto_update
        if auto_update:
            self.db_update_thread = DBupdateThread()
    
    def run(self):
        self.c_socket.bind((self.bind_ip, self.bind_port))
        if self.auto_update:
            self.db_update_thread.start()

        while True:
            try:
                data, addr = self.c_socket.recvfrom(1024)            #从客户端获得数据
                # print('c_socket: Received from %s:%s.' % addr, data)
                newThread = HandleThread(Handler(addr, data, self.c_socket, self.send_ip, self.send_port))
                newThread.start()
            except:
                pass


class HandleThread (threading.Thread):
    def __init__(self, Handler):
        threading.Thread.__init__(self)
        self.Handler = Handler
        
    def run(self):
        #print ("开始线程：" + self.name)
        self.Handler.run()       
        #print ("退出线程：" + self.name)


class DBupdateThread (threading.Thread):
    def run(self):
        print('开始数据库ttl更新线程')
        db = DBFacade()
        while True:
            time.sleep(1)
            db.update_TTL()
        print('退出数据库ttl更新线程')



if __name__ == '__main__':
    dnsRelay = DNSRelay()
    dnsRelay.run()
    