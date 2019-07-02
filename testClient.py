import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
 
while True:
    # 发送数据:
    data = input('输入向dnsRelay的发送')
    s.sendto(data.encode(), ('127.0.0.1', 8080))
    # 接收数据:
    print(s.recv(1024))
s.close()