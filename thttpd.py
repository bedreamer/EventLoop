# -*-  coding: utf8 -*-
from __future__ import print_function
from SelectLoop import *
import SelectSocket
import socket
import re
import os
import types
import mimetypes
import urlparse


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

    def route_match(self, method, url, query_string):
        """从路由表中匹配一个应答器"""
        for _, route in self.path_route.items():
            r = route['r_path']
            if r.match(url) in {None, False}:
                continue
            return route['protocol']

        # not found
        return HttpFileProtocol


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
    def __init__(self, request):
        self.request = request

    def connection_lost(self):
        """连接丢失后调用该接口"""
        pass

    def connection_closed(self):
        """连接关闭后调用该接口"""
        pass

    def do_request(self):
        """头部接收完成后调用该接口"""
        pass

    def do_get(self):
        """处理GET方法，返回可迭代对象, 连接即随即关闭"""
        pass

    def do_post(self):
        """处理POST方法，返回可迭代对象, 连接即随即关闭"""
        pass

    def do_request_data(self, data):
        """用于接收请求主体数据"""
        pass

    def do_ack(self, code, status, iterable_body):
        """执行应答"""
        ack = HttpAck(self.request, code, status, iterable_body)
        ack.start()
        return ack

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


class HttpFileProtocol(HttpBaseProtocol):
    def __init__(self, request):
        super(HttpFileProtocol, self).__init__(request)
        self.path = None
        self.root = '/home/kirk/www'

    def handle_file_path(self):
        root, ext = os.path.splitext(self.path)
        try:
            mime = mimetypes.types_map[ext]
        except:
            mime = 'unknown'
        header = [self.request.version + " 200 OK",
                  "Content-Type: %s" % mime,
                  "Content-Length: %d" % os.path.getsize(self.path), "\r\n"]
        heades = "\r\n".join(header)
        yield heades
        with open(self.path, 'r') as file:
            data = file.read(1024)
            yield data
            while len(data) > 0:
                data = file.read(1024)
                if len(data) > 0:
                    yield data

                if len(data) < 1024:
                    break

    def do_get(self):
        url = urlparse.unquote(self.request.url)
        path = self.root + url

        if os.path.exists(path) is False:
            return self.ack_404()

        if os.path.isdir(path) is True:
            if os.path.exists(path + 'index.html') is True:
                self.path = path + 'index.html'
                return self.handle_file_path()
        elif os.path.isfile(path) is True:
            self.path = path
            return self.handle_file_path()

        return ''

    def do_post(self):
        pass


class Request:
    pass


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
            key = line[:comma_idx].lower().replace('-', '_')
            setattr(requst, key, line[comma_idx+1:])

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
        self.header_parser = HttpRequestParser()
        self.request = None
        self.binder = None
        # 请求体数据大小
        self.request_data_size = 0
        # 已经接收到的请求体数据长度
        self.received_request_data_size = 0
        # 应答数据体，可迭代对象
        self.ack = None
        self.iter = None

    def find_url_binder(self):
        """搜索匹配的URL路由应答对象"""
        return self.httpd.route_match(self.request.method, self.request.url, self.request.query_string)

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
            if self.binder is not None:
                self.binder.connection_closed()
            self.close('remote closed!')
            return
        except Exception as e:
            if self.binder is not None:
                self.binder.connection_lost()
            self.close('connection lost!')
            return

        # 若请求头部未接收完成则继续接收
        if self.request is None:
            self.request, remain_body = self.header_parser.push(data)
            if self.request is None:
                return

            binder = self.find_url_binder()
            if binder is None:
                _loop = get_select_loop()
                _loop.schedule_write(self.fds, self.writable)
                return

            self.binder = binder(self.request)
            self.binder.do_request()

            try:
                self.request_data_size = int(self.request.content_length)
            except:
                setattr(self.request, "content_length", 0)
                self.request_data_size = 0

            # 将请求过程中间数据放到请求体数据中
            if remain_body not in {None, ''}:
                self.received_request_data_size += len(remain_body)
                self.binder.do_request_data(data)
        else:
            self.received_request_data_size += len(data)
            self.binder.do_request_data(data)

        # 请求数据接收完成，下一步转为应答状态，
        # 但此时并不关闭该连接的读数据状态，用于监测连接断开事件
        if self.received_request_data_size >= self.request_data_size:
            _loop = get_select_loop()
            _loop.schedule_write(self.fds, self.writable)

    def writable(self, fds):
        """连接可写"""
        if self.binder is None:
            try:
                fds.send("HTTP/1.1 404 Not Found\r\n\r\n")
            except:
                pass
            self.close()
            return

        if self.ack is None:
            if self.request.method.upper() == 'GET':
                self.ack = self.binder.do_get()
            elif self.request.method.upper() == 'POST':
                self.ack = self.binder.do_post()
            else:
                try:
                    fds.send("HTTP/1.1 501 Not Supported method\r\n\r\n")
                except:
                    self.binder.connection_lost()
                self.close()
                return

        if self.ack is None:
            return None

        if isinstance(self.ack, str):
            try:
                fds.send(self.ack)
            except:
                self.binder.connection_lost()
            self.close()
            return
        elif isinstance(self.ack, list):
            try:
                fds.send("".join(self.ack))
            except:
                self.binder.connection_lost()
                self.close()
        elif isinstance(self.ack, types.GeneratorType):
            max_loops = 128
            while max_loops > 0:
                max_loops -= 1
                try:
                    data = self.ack.next()
                except StopIteration:
                    self.close()
                    break
                except:
                    self.close()
                    break

                try:
                    fds.send(data)
                except:
                    self.binder.connection_lost()
                    self.close()
                    break
        else:
            try:
                fds.send("HTTP/1.1 501 Inner Error\r\n\r\n")
            except:
                self.binder.connection_lost()
            self.close()
            return

    def start_receive(self):
        """在当前连接上开始接收数据"""
        pass

    def stop_receive(self):
        """停止当前连接的数据接收"""
        pass

    def start_transmit(self):
        """开始当前连接上的数据传输"""
        pass

    def stop_transmit(self):
        """停止当前接连的数据传输"""
        pass


if __name__ == '__main__':
    loop = get_select_loop()
    httpd = Httpd(iface='0.0.0.0', port=8080)
    httpd.start()
    loop.run_forever()
