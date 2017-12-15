# -*- coding: utf8 -*-
from __future__ import print_function
import socket
from SelectLoop import *


class ConnectionBasicProtocol(object):
    def __init__(self, fds, address):
        self.fds = fds
        self.address = address

    def __del__(self):
        if self.fds is None:
            return

        loop = get_select_loop()
        loop.cancel_write(self.fds)
        loop.cancel_read(self.fds)
        self.fds.close()


class ClientBasicProtocol(object):
    pass


class SelectSocketServer:
    def __init__(self, iface=None, port=None, connection_protocal=None):
        self.iface = iface
        self.port = port
        self.fds = None
        self.started = False
        self.protocol = connection_protocal
        if None not in {iface, port}:
            self.start_service()

    def __del__(self):
        if self.fds is not None:
            self.fds.close()

    def start_service(self, iface=None, port=None):
        """启动服务"""
        if self.started is True:
            return

        if iface is not None:
            self.iface = iface
        if port is not None:
            self.port = port
        if None in {self.iface, self.port}:
            raise TypeError('need iface and port parameters.')

        self.fds = socket.socket()
        self.fds.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.fds.bind((self.iface, self.port))
        self.fds.listen(128)
        loop = get_select_loop()
        loop.schedule_read(self.fds, self._accept)
        self.started = True

    def stop_service(self):
        """停止服务"""
        loop = get_select_loop()
        loop.cancel_read(self.fds)
        self.fds.close()
        self.fds = None

    def _accept(self, fds):
        if fds != self.fds:
            raise ValueError("invalid fds value")
        peer, address = self.fds.accept()
        self._new_connection(peer, address)

    def _new_connection(self, peer, address):
        print("new connection @", peer.fileno(),address)
        connection = self.protocol(peer, address)


class SelectSocketClient:
    def __init__(self, remote_host, remote_port):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.remote_ip = '0.0.0.0'
        self.fds = None
        self.connect_ok = False
        self.do_connect = False
        if None not in {remote_host, remote_port}:
            self.connect()

    def __del__(self):
        if self.fds is None:
            return

        loop = get_select_loop()
        loop.cancel_read(self.fds)
        loop.cancel_write(self.fds)
        self.fds.close()

    def connect(self, remote_host=None, remote_port=None):
        """连接"""
        if self.do_connect is not False:
            return

        if remote_host is not None:
            self.remote_host = remote_host
        if remote_port is not None:
            self.remote_port = remote_port
        if None in {self.remote_host, self.remote_port}:
            raise TypeError('need remote_host and remote_port parameters.')

        self.fds = socket.socket()
        self.fds.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.remote_ip = socket.gethostbyname(self.remote_host)
        self.fds.setblocking(False)

        try:
            error = self.fds.connect_ex((self.remote_ip, self.remote_port))
            self.do_connect = True
        except Exception as e:
            self.fds.close()
            print(e)
            return

        loop = get_select_loop()
        loop.schedule_read(self.fds, self._connect_readable)
        loop.schedule_write(self.fds, self._connect_writable)

    def _connect_readable(self, fds):
        """异步连接过程中，描述符可读"""
        print("connection failed!")
        self.disconnect()

    def _connect_writable(self, fds):
        """异步连接过程中，描述符可写"""
        print("connection ok!")
        self.fds.setblocking(True)
        self.disconnect()

    def disconnect(self):
        """断开连接"""
        if self.fds is None:
            return

        loop = get_select_loop()
        loop.cancel_read(self.fds)
        loop.cancel_write(self.fds)
        self.fds.close()
        self.fds = None
        print("disconnet")


if __name__ == '__main__':
    import threading

    def thread_callback(t):
        print("thread", t)


    def thread_main():
        loop = get_select_loop()
        name = loop.schedule_delay(10, thread_callback, 10)
        loop.run_forever()


    def delay_callback(t):
        print('callback', t)

    loop = get_select_loop()
    #server = SelectSocketServer('127.0.0.1', 19999)
    #server.start_service()
    cancel = list()
    for i in xrange(10):
        name = loop.schedule_delay(i, delay_callback, i)
        if i % 2 == 0:
            cancel.append(name)

    for name in cancel:
        loop.cancel_delay(name)


    threading._start_new_thread(thread_main, ())

    loop.run_forever()
