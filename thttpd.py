# -*-  coding: utf8 -*-
from __future__ import print_function
from SelectLoop import *
import SelectSocket
import socket
import re
import os


def log(*args):
    tsp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    print(tsp, *args)


class Httpd(SelectSocket.SelectSocketServer):
    """httpd"""
    def __init__(self, iface=None, port=None):
        super(Httpd, self).__init__(iface, port)
        log("HTTP 服务启动, 服务端口:", port)
        self.path_route = dict()

    def start(self):
        """启动服务"""
        super(Httpd, self).start_service()

    def stop(self):
        """停止服务"""
        super(Httpd, self).stop_service()

    def accept(self, fds):
        """新链接"""
        peer, address = fds.accept()
        log("新连接", address)
        conn = HttpConnection(self, peer, address)

    def route(self, r_path, process_protocol):
        """注册回调函数"""
        r = re.compile(r_path)
        d = {
            'r_path': r_path,
            'protocol': process_protocol
        }
        self.path_route[r_path] = r


class HttpAck:
    """Http应答对象"""
    def __init__(self, request, code, status, iterable_body):
        self.headers = dict()
        self.request = request
        self.code = code
        self.status = status
        self.iterable_body = iterable_body
        self.ack_ready = False
        self.add_header('Server', 'httpd by Lijie / V2.1')
        self.sent_eoh = False

    def add_header(self, key, value):
        """添加一个头部"""
        self.headers[key] = value

    def start(self):
        """可以启动应答了"""
        self.ack_ready = True

    def is_ready(self):
        """判定应答是否准备好"""
        return self.ack_ready

    def do_ack(self):
        """执行ACK应答，返回None表示应答完成"""
        ex_headers = ["%s: %s\r\n" % (key, value) for key, value in self.headers.items()]
        headers = ["%s %d %s\r\n" % (self.request.version, self.code, self.status)]
        headers.extend(ex_headers)
        headers.append('\r\n')
        return "".join(headers), self.iterable_body


class HttpBaseProtocol(object):
    """HTTP GET方法处理基类"""
    def __init__(self):
        self.request = None

    def route_matched(self):
        """路径匹配到后调用该接口"""
        pass

    def connection_lost(self):
        """连接丢失后调用该接口"""
        pass

    def connection_closed(self):
        """连接关闭后调用该接口"""
        pass

    def do_get(self, request):
        """处理GET方法，返回可迭代对象"""
        pass

    def do_post(self, requst):
        """处理POST方法，返回可迭代对象"""
        return ''

    def ack_200(self, html=None):
        """返回200"""
        if html is None:
            html = "Nothing to be returned"
        return self.do_ack(200, 'OK', [html])

    def ack_404(self, html=None):
        """返回404错误"""
        if html is None:
            html = "Could not Found %s" % self.request.url
        return self.do_ack(404, 'Not Found', [html])

    def ack_503(self, html=None):
        """返回503内部错误"""
        if html is None:
            html = "Server error"
        return self.do_ack(503, 'Server Error', [html])

    def do_ack(self, code, status, iterable_body):
        """执行应答"""
        ack = HttpAck(self.request, code, status, iterable_body)
        ack.start()
        return ack


class HttpFileProtocol(HttpBaseProtocol):
    def __init__(self):
        super(HttpFileProtocol, self).__init__()

    def do_get(self, request):
        url = request.url
        path = os.getcwd() + url

        if os.path.exists('.' + url) is False:
            return self.ack_404()

    def do_post(self, requst):
        pass


class Request: pass


class HttpRequestParser:
    """http请求解析器"""
    def __init__(self):
        self.cache = list()

    def push(self, data):
        """压入要解析的数据"""
        self.cache.append(data)

        # 这种写法可能会导致不断分配内存导致效率低下
        # 目前还没想到更好的办法，暂时使用这个算法
        candy = "".join(self.cache)
        rnrn_idx = candy.find("\r\n\r\n")
        if rnrn_idx < 0:
            return None, None

        # 头部以后的所有数据都认为是body部分
        remain_data = candy[rnrn_idx+4:]
        candy = candy[:rnrn_idx].split('\r\n')
        requst = Request()

        # 把第一个字符串弹出来，后面可以使用循环
        line = candy.pop(0).split(' ')
        setattr(requst, 'method', line[0].upper())

        uri = line[1]
        setattr(requst, 'uri', uri)
        uri = uri.split('?')
        setattr(requst, 'url', uri[0])
        if len(uri) == 1:
            setattr(requst, 'query_string', '')
        else:
            setattr(requst, 'query_string', uri[1])

        setattr(requst, 'version', line[2].upper())
        for line in candy:
            comma_idx = line.find(':')
            setattr(requst, line[:comma_idx], line[comma_idx+1:])

        return requst, remain_data


class HttpConnection:
    """HTTP连接对象"""
    def __init__(self, httpd, peer, address):
        self.httpd = httpd
        self.fds = peer
        self.peer_ip = address[0]
        self.peer_port = address[1]
        loop = get_select_loop()
        loop.schedule_read(self.fds, self.readable)
        self.cache = list()
        self.request = None
        self.header_parser = HttpRequestParser()

    def close(self, error=None):
        """关闭连接"""
        if self.fds is not None:
            loop = get_select_loop()
            loop.cancel_read(self.fds)
            loop.cancel_write(self.fds)
            self.fds.close()
            self.fds = None
        if error is None:
            error = "关闭连接！"
        log(error)

    def readable(self, fds):
        """连接可读"""
        data = None
        try:
            data = fds.recv(2048)
            if data in {'', None}:
                raise ValueError
        except ValueError:
            self.close('remote closed!')
            return
        except Exception as e:
            self.close('connection lost!')
            return

        if self.request is None:
            self.request, remain_body = self.header_parser.push(data)
            if self.request is None:
                return

            if remain_body not in {None, ''}:
                self.cache.append(remain_body)

            loop = get_select_loop()
            loop.cancel_read(self.fds)
            loop.schedule_write(self.fds, self.writable)
        else:
            self.cache.append(data)

    def writable(self, fds):
        """连接可写"""
        fds.send("HTTP/1.1 404 Not Found\r\n\r\n")
        self.close()



if __name__ == '__main__':
    loop = get_select_loop()
    httpd = Httpd(iface='0.0.0.0', port=8080)
    httpd.start()
    loop.run_forever()
