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
    day_s = "%d天" % day if day > 0 else None
    hour_s = "%d时" % hour if hour > 0 else None
    mini_s = "%d分" % mini if mini > 0 else None
    seconds_s = "%d秒" % seconds if seconds > 0 else None

    s = [day_s, hour_s, mini_s, seconds_s]
    while None in s:
        s.remove(None)
    if len(s) == 0:
        return "0秒"
    return "".join(s)



support_version = [0x04, 0x05]


class Socket5Peer:
    def __init__(self, father, fds, address):
        self.local_fds = fds
        self.local_address = address
        self.born = time.time()

        self.remote_fds = None
        self.remote_address = None # (ip, port)
        self.version = None

    def start(self):
        log("new connection from ip:", self.local_address[0], "port:", self.local_address[1])
        loop = get_select_loop()
        loop.schedule_delay(70, self.close_after_10_seconds)

    def stop(self):
        if self.local_fds is not None:
            self.local_fds.close()
        if self.remote_fds is not None:
            self.remote_fds.close()
        delta = time.time()-self.born
        log("peer closed ip:", self.local_address[0], "port:", self.local_address[1], "run:", format_delta(delta))

    def close_after_10_seconds(self):
        self.stop()

    def client_readable(self, fds):
        """客户端可读"""
        pass

    def client_writable(self, fds):
        """客户端可写"""
        pass

    def remote_connect_readable(self, fds):
        """连接远端可读"""
        pass

    def remote_connect_writable(self, fds):
        """连接远端可写"""
        pass

    def remote_readable(self, fds):
        """远端可读"""
        pass

    def remote_writable(self, fds):
        """远端可写"""
        pass


class Socket5ProxyServer:
    def __init__(self, iface, port):
        self.iface = iface
        self.port = port
        self.fds = None

    def start(self):
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
