import socket
 
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 绑定 客户端口和地址:
s.bind(('127.0.0.1', 80))
print('DSNServer开始监听')
while True:
    # 接收数据 自动阻塞 等待客户端请求:
    data, addr = s.recvfrom(1024)
    print ('Received from %s:%s.' % addr,data)
    s.sendto('Hello'.encode(), addr)