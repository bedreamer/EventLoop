# -*- coding: utf8 -*-
# -*- coding: utf8 -*-
from __future__ import print_function
import socket
from SelectLoop import *
import time


def log(*args):
    tsp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    print(tsp, *args)


def format_delta(delta):
    """把秒数转换为字符串 n天n时n分n秒"""
    day = int(delta / 86400)
    hour = int((delta - day * 24) / 3600)
    mini = int((delta - day * 24 - hour * 3600) / 60)
    seconds = int(delta - day * 24 - hour * 3600 - mini * 60)
    day_s = u"%d天" % day if day > 0 else None
    hour_s = u"%d时" % hour if hour > 0 else None
    mini_s = u"%d分" % mini if mini > 0 else None
    seconds_s = u"%d秒" % seconds if seconds > 0 else None

    s = [day_s, hour_s, mini_s, seconds_s]
    while None in s:
        s.remove(None)
    if len(s) == 0:
        return u"0秒"
    return u"".join(s)


support_version = [0x04, 0x05]


class Socket5Peer:
    def __init__(self, father, fds, address):
        self.local_fds = fds
        self.local_address = address
        self.born = time.time()

        self.remote_fds = None
        self.remote_address = None # (ip, port)

        self.version = None
        self.method_count = None
        self.method_list = None

        self.local_protocol = self.confirm_method
        self.local_buff = list()

    def confirm_method(self, fds):
        """版本确认"""
        return self.confirm_method

    def start(self):
        log("new connection from ip:", self.local_address[0], "port:", self.local_address[1])
        loop = get_select_loop()
        loop.schedule_read(self.local_fds, self.local_readable)

    def stop(self):
        loop = get_select_loop()
        if self.local_fds is not None:
            loop.cancel_read(self.local_fds)
            loop.cancel_write(self.local_fds)
            self.local_fds.close()
            self.local_fds = None

        if self.remote_fds is not None:
            loop.cancel_read(self.remote_fds)
            loop.cancel_write(self.remote_fds)
            self.remote_fds.close()
            self.remote_fds = None

        delta = time.time() - self.born
        log("peer closed ip:", self.local_address[0], "port:", self.local_address[1], "run:", format_delta(delta))

    def local_readable(self, fds):
        """客户端可读"""
        try:
            data = fds.recv(2048)
            if data in {None, ''}:
                raise ValueError('connection closed!')
            self.local_buff.append(data)
            self.local_protocol = self.local_protocol(fds)
        except:
            self.stop()

    def remote_connect_failed(self, fds):
        """连接远端失败"""
        pass

    def remote_connect_writable(self, fds):
        """连接远端可写"""
        pass

    def remote_readable(self, fds):
        """远端可读"""
        pass


class Socket5ProxyServer:
    def __init__(self, iface, port):
        self.iface = iface
        self.port = port
        self.fds = None

    def start(self):
        """"""
        log("proxy starting on interface:", self.iface, "port:", self.port)
        self.fds = socket.socket()
        self.fds.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.fds.bind((self.iface, self.port))
        self.fds.listen(128)
        loop = get_select_loop()
        loop.schedule_read(self.fds, self.accept)

    def accept(self, fds):
        peer, address = fds.accept()
        peer = Socket5Peer(self, peer, address)
        peer.start()


if __name__ == '__main__':
    loop = get_select_loop()
    proxy = Socket5ProxyServer('0.0.0.0', 9998)
    proxy.start()
    loop.run_forever()

    l = 's' \
        's'
    l.replace()