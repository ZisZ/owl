#!/usr/bin/env python

__author__ = 'zky@msn.cn'

import socket
import time 
import urlparse

class TSDBSender():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.tsd = None
        self.ConnectToTSDB()

    def __init__(self, url):
        urlparse_result = urlparse.urlparse(url)
        self.host = urlparse_result.hostname
        self.port = urlparse_result.port
        self.tsd = None
        self.ConnectToTSDB()

    def ConnectToTSDB(self):
        try:
            addresses = socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC,
                                           socket.SOCK_STREAM, 0)
        except socket.gaierror, e:
            if e[0] in (socket.EAI_AGAIN, socket.EAI_NONAME):
                pass
            raise
        for family, socktype, proto, canonname, sockaddr in addresses:
            try:
                self.tsd = socket.socket(family, socktype, proto)
                self.tsd.settimeout(15)
                self.tsd.connect(sockaddr)
                # if we get here it connected
                break
            except socket.error, msg:
                print 'write_worker Connection attempt failed' 
        print 'write_woker connect to : %s %s' % (self.host, self.port)

    def SendData(self, message):
        out = 'put %s\n' % message 
        try:
            self.tsd.sendall(out)
            #print 'send data succesful'
        except socket.error, msg:
            print 'failed to send data, reason: %s, out: %s' % (msg, out)
            try:
                self.tsd.close()
            except socket.error:
                pass
            time.sleep(30)
            print 'try to reconnect to tsdb'
            self.ConnectToTSDB()

if __name__ == '__main__':
    send = TSDBSender("10.10.208.141", 4242)
    # 2015.07.13 09:28:34
    t = 1436750914
    for i in xrange(10000):
      message = 'metric_key_test %s 42 host=localhost group=test' % (t+i)
      #print message
      send.SendData(message)
