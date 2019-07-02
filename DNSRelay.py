from socket import *
import threading

class DNSRelay:
    def __init__(self, bind_ip = '127.0.0.1', bind_port = 8080, send_ip = '127.0.0.1', send_port = 80):
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.send_ip = send_ip
        self.send_port = send_port
        self.c_socket = socket(AF_INET, SOCK_DGRAM)  # 与客户端通信的数据报式套接字
        self.s_socket = socket(AF_INET, SOCK_DGRAM)  # 与DNS服务器通信的套接字
        self.threadList = []
    
    def run(self):
        self.c_socket.bind((self.bind_ip, self.bind_port))
        while True:
            data, addr = self.c_socket.recvfrom(1024)            #从客户端获得数据
            print('c_socket: Received from %s:%s.' % addr, data)
            newThread = HandleThread(Handler(addr, data,self.c_socket, self.s_socket, self.send_ip, self.send_port))
            newThread.start()


class Handler:
    def __init__(self, c_addr, data_to_send, c_socket, s_socket, send_ip, send_port):
        self.c_addr = c_addr
        self.data_to_send = data_to_send
        self.c_socket = c_socket
        self.s_socket = s_socket
        self.send_ip = send_ip
        self.send_port = send_port
    
    def run(self):
        flag = 1
        if flag==0:
            self.c_socket.sendto('Hello !'.encode(), self.c_addr)     #向客户端直接发回的情况
        else:
            self.s_socket.sendto('to_dns_server'.encode(), (self.send_ip, self.send_port))      #向服务器发送的情况
            data, addr = self.s_socket.recvfrom(1024)     #读回DNS服务器的返回
            self.c_socket.sendto(data, self.c_addr)


class HandleThread (threading.Thread):
    def __init__(self, Handler):
        threading.Thread.__init__(self)
        self.Handler = Handler
        
    def run(self):
        print ("开始线程：" + self.name)
        self.Handler.run()
        print ("退出线程：" + self.name)



dnsRelay = DNSRelay()
dnsRelay.run()

