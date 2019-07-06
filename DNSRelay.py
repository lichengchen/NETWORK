from dns import message
import sys
import time
from socket import *
import threading

from DBFacade import DBFacade
from MyLog import logger

class DNSRelay:
    def __init__(self, bind_ip = '127.0.0.1', bind_port = 53, send_ip = '10.3.9.4', send_port = 53):
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.send_ip = send_ip
        self.send_port = send_port
        self.c_socket = socket(AF_INET, SOCK_DGRAM)  # 与客户端通信的数据报式套接字
        self.db_update_thread = DBupdateThread()
    
    def run(self):
        self.c_socket.bind((self.bind_ip, self.bind_port))
        self.db_update_thread.start()
        while True:
            try:
                data, addr = self.c_socket.recvfrom(1024)            #从客户端获得数据
                # print('c_socket: Received from %s:%s.' % addr, data)
                newThread = HandleThread(Handler(addr, data, self.c_socket, self.send_ip, self.send_port))
                newThread.start()
            except:
                pass
            

class Handler:
    def __init__(self, c_addr, data, c_socket, send_ip, send_port):
        self.c_addr = c_addr
        self.c_data = data
        self.c_socket = c_socket
        self.send_ip = send_ip
        self.send_port = send_port
        
       
    def run(self):
        flag = False
        data_dic = self.data_process(self.c_data)
        #查询数据库
    #    print(data_dic)
        db = DBFacade()
        _name , _type = data_dic['QUESTION'][0][0],data_dic['QUESTION'][0][2]   #原始请求
        answer = db.query(_name , _type)
        flag = (answer == [])
        #answer = [['www.shifen.com.','222','IN','A','39.20.1.1'],['www.shifen.com.','222','IN','A','25.69.6.3']]  
    #    print("---------------ans-----------")
    #    print("answer: ",answer)

        if flag == False:    
    #        print("---------------")
    #        print("send case 1")
    #        print("----------------")                                       #查数据库向客户端发送       
            if answer[0][3] == 'MX':                                #answer 的处理 （MX）
                for i in range(len(answer)):
                    answer[i].insert(4,'5')                                                  
            temp_message = message.from_wire(self.c_data)
            temp_message = message.make_response(temp_message).to_text()
            temp_list = temp_message.split("\n")
            index = temp_list.index(";ANSWER")
            for ret in answer:
                temp_list.insert(index+1,' '.join(ret))
                index += 1
            data_send = '\n'.join(temp_list)
            data_send = message.from_text(data_send)
            data_send = data_send.to_wire()
            self.c_socket.sendto(data_send, self.c_addr)     #向客户端直接发回的情况
            remark = 'Local'
          
        else:
            self.s_socket = socket(AF_INET, SOCK_DGRAM)  # 与DNS服务器通信的套接字
    #        print("---------------")
    #        print("send case 2")
    #        print("----------------")
            self.s_socket.sendto(self.c_data, (self.send_ip, self.send_port))      #向服务器发送的情况
            data, addr = self.s_socket.recvfrom(1024)     #读回DNS服务器的返回
            self.s_socket.close()       #获取DNS的返回后关闭与服务器通信的socket
            # print("1111\n")
            # print(data)
            # print(message.from_wire(data))
            data_dic = self.data_process(data)
            # 存数据库  data_dic['ANSWER']
            db = DBFacade()
            db.insert_records(data_dic["ANSWER"])
            #发回到客户端
            self.c_socket.sendto(data, self.c_addr)
            remark = 'Remote'
        
        #handler做完了一项工作，插入日志，退出
        logger.info('%s:%s      %s      %s      %s'%(self.c_addr[0], self.c_addr[1], _name , _type, remark))
            

    def data_process(self,data_get):
        data_message = message.from_wire(data_get).to_text()
    #    print(data_message)
        data_list = data_message.split('\n')
        data_dic = {}
        Question = []
        Answer = []
        data_dic['id'] = data_list[0][2:]
        for index in range(len(data_list)):
            if index > data_list.index(';QUESTION') and index < data_list.index(';ANSWER'): #question
                data_temp = data_list[index].split(' ')
                Question.append(data_temp)
                    #
                    # question : name,class,type    for example: www.baidu.com.   IN   A
                    #
            elif index > data_list.index(';ANSWER') and index < data_list.index(';AUTHORITY'): #answer
                data_temp = data_list[index].split(' ')
                if data_temp[3] == 'MX':            #对于MX类型  省略优先级
                    data_temp.remove(data_temp[4])
                Answer.append(data_temp)
                    #
                    # answer : name,ttl,class,type,value    for example :www.baidu.com.   168 IN A 39.156.66.18
                    #
        data_dic['QUESTION'] = Question
        data_dic['ANSWER'] = Answer
        return data_dic


class HandleThread (threading.Thread):
    def __init__(self, Handler):
        threading.Thread.__init__(self)
        self.Handler = Handler
        
    def run(self):
        print ("开始线程：" + self.name)
        self.Handler.run()       
        print ("退出线程：" + self.name)


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
    