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
from HttpRespons import *


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
            'r_path': r,
            'protocol': process_protocol
        }
        self.path_route[r_path] = d

    def route_match(self, method, url, query_string):
        """从路由表中匹配一个应答器"""
        for _, route in self.path_route.items():
            r = route['r_path']
            if r.match(url) in {None, False}:
                continue
            return route['protocol']

        # not registed path found
        return HttpFileProtocol


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
        """ 头部接收完成后调用该接口
            例如，GET/POST头部接收完成后，通过头部判定权限、SessionID、Cookie、上传路径合法性等，
            若需要关闭连接，则返回标准应答对象HttpResonse
        """
        pass

    def do_get(self):
        """处理GET方法，返回非None对象, 连接随即关闭"""
        pass

    def do_post(self):
        """处理POST方法，返回非None对象, 连接随即关闭"""
        pass

    def do_request_data(self, data):
        """用于接收请求主体数据"""
        pass


class HttpFileProtocol(HttpBaseProtocol):
    def __init__(self, request):
        super(HttpFileProtocol, self).__init__(request)
        self.root = './www/'

    def do_normal_response(self):
        url = urlparse.unquote(self.request.url)
        path = self.root + url

        if os.path.exists(path) is False:
            return HttpRespons(code=404)

        full_path = path
        if os.path.isdir(path) is True:
            full_path = "".join([path, "index.html"])

        if os.path.exists(full_path) is False:
            return HttpRespons(code=404)
        elif os.path.isfile(full_path) is False:
            return HttpRespons(code=406)
        elif os.access(full_path, os.R_OK) is False:
            return HttpRespons(code=403)
        else:
            return HttpResponsFile(path=full_path)

    def do_get(self):
        return self.do_normal_response()

    def do_post(self):
        return self.do_normal_response()


class Request:
    pass


class HttpRequestParser:
    """http请求解析器"""
    def __init__(self):
        self.cache = list()

    @classmethod
    def parser_query(self, q):
        r = Request()
        if '&' in q:
            q = q.split('&')
        else:
            q = [q]

        for item in q:
            x = item.split('=')
            if len(x) == 1:
                x.append('')
            setattr(r, x[0], x[1])

        return r

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
        first_line = candy.pop(0)
        line = urlparse.unquote(first_line).split(' ')
        setattr(requst, 'method', line[0].upper())

        uri = line[1]
        setattr(requst, 'uri', uri)
        uri = uri.split('?')
        setattr(requst, 'url', uri[0])
        if len(uri) == 1:
            setattr(requst, 'query_string', '')
            setattr(requst, 'query', dict())
        else:
            setattr(requst, 'query_string', uri[1])
            setattr(requst, 'query', self.parser_query(uri[1]))

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
        # 应答可迭代对象
        self.response = None

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

            # 无论何种情况都会找到一个对应的处理句柄
            # 可能的句柄有:
            #  1. 注册过的path
            #  2. 文件系统中存在的可访问文件
            #  3. 文件系统中存在的不可访问文件
            #  4. 文件系统中不存在的文件
            binder = self.find_url_binder()
            try:
                self.binder = binder(self.request)
                response = self.binder.do_request()
                if issubclass(type(response), HttpRespons) is True:
                    self.response = response
            except:
                self.response = HttpRespons(code=500)

            # 再do_request时发生了可返回的情况，则直接返回，不在接收剩余数据
            if self.response is not None:
                _loop = get_select_loop()
                _loop.schedule_write(self.fds, self.writable)
                return

            try:
                self.request_data_size = int(self.request.content_length)
            except:
                setattr(self.request, "content_length", 0)
                self.request_data_size = 0

            # 将请求过程中间数据放到请求体数据中
            if remain_body not in {None, ''}:
                self.received_request_data_size += len(remain_body)
                self.binder.do_request_data(remain_body)
        else:
            self.received_request_data_size += len(data)
            self.binder.do_request_data(data)

        # 请求数据接收完成，下一步转为应答状态，
        # 但此时并不关闭该连接的读数据状态，用于监测连接断开事件
        if self.received_request_data_size >= self.request_data_size:
            t_loop = get_select_loop()
            t_loop.schedule_write(self.fds, self.writable)

    def writable(self, fds):
        """连接可写"""
        if self.response is None:
            if self.request.method.upper() == 'GET':
                response = self.binder.do_get()
            elif self.request.method.upper() == 'POST':
                response = self.binder.do_post()
            else:
                response = HttpRespons(code=405)

            # 应答体是空的，继续轮询，这种情况多应用于长连接过程
            if response is None:
                return

            # 无论应答端返回哪种非应答对象的数据全都统一转换,保证接口统一
            if issubclass(type(response), HttpRespons) is True:
                self.response = response
            else:
                self.response = HttpRespons(response)

        # 需要对每个连接占用CPU的时间做限制，避免其他循环事件被`饿死`
        max_sent_time_in_sec = 20.0 / 1000
        begin = time.time()
        times = 0
        while time.time() - begin < max_sent_time_in_sec:
            try:
                response_data = self.response.next()

                # 返回None表示维持长连接
                if response_data is None:
                    break

                fds.send(response_data)
                times += 1
            except Exception as e:
                self.close()
                break

    def do_request(self):
        #return HttpRespons(code=404)
        #return HttpResponsRedirect('/thttpd.py?id=111')
        pass

    def do_request_data(self, data):
        log(data)
        #print(len(data), data.encode('utf8')[:8], '...')

    def do_post(self):
        print("do post")


# HTTP上传入口
class UpLoadeEntry(HttpBaseProtocol):
    def __init__(self, request):
        super(UpLoadeEntry, self).__init__(request)


# 连接会话
_g_session = dict()


import uuid
from SelectSocket import *


class Connection(SelectSocketClient):
    def __init__(self, target, remote_host, remote_port):
        super(Connection, self).__init__(remote_host, remote_port)
        self.p = list()
        self.target = target

    def get(self):
        if len(self.p) == 0:
            return ''

        x = ''.join(self.p)
        self.p = list()
        return x

    def readable(self, fds):
        try:
            data = self.fds.recv(2048)
            if len(data) == 0:
                raise ValueError('connect closed!')
        except:
            global _g_session
            del _g_session[self.target]
            self.close_connection_safely()
            return

        import datetime
        tsp = datetime.datetime.now().strftime('[%b-%d-%y %H:%M:%S] ')
        with open('data.txt', 'a') as file:
            file.write(tsp)
            file.write(data.encode('hex'))
            file.write('\n')

        self.p.append(data)

    def writable(self, fds):
        pass


# 连接模块
class LinkModule(HttpBaseProtocol):
    def __init__(self, request):
        super(LinkModule, self).__init__(request)

    def do_get(self):
        global _g_session
        id = uuid.uuid4().hex
        try:
            addr = self.request.query.addr
        except:
            return {'status': 'fail', 'reason': "需要提供有效的IP地址！"}

        target = addr
        addr = addr.split(':')
        try:
            ip, port = addr[0], int(addr[1])
        except:
            return {'status': 'fail', 'reason': "IP地址无效！"}

        session = None
        if target not in _g_session:
            session = Connection(target, ip, port)
            _g_session[ target ] = session
        else:
            session = _g_session[target]

        if session.is_closed() is True:
            del _g_session[target]
            return {'status': 'fail', 'reason': "连接已关闭"}

        if session.is_connected() is True:
            return {'status': 'ok', 'key': target}

        return None


# 关闭连接
class DisconnectModule(HttpBaseProtocol):
    def __init__(self, request):
        super(DisconnectModule, self).__init__(request)

    def do_get(self):
        global _g_session
        try:
            target = self.request.query.key
            session = _g_session[target]
        except:
            return {'status': 'fail', 'reason': 'not connect'}

        session.close_connection_safely()
        del _g_session[target]
        return {'status': 'ok'}


# 获取实时数据
class LiveData(HttpBaseProtocol):
    def __init__(self, request):
        super(LiveData, self).__init__(request)

    def do_get(self):
        global _g_session
        try:
            target = self.request.query.key
            session = _g_session[target]
        except:
            return {'status': 'fail', 'reason': 'not connect'}

        data = session.get()
        if data is None:
            return {'status': 'fail', 'reason': 'connection closed'}

        if data == '':
            return None

        return {'status': 'ok', 'data': data}


if __name__ == '__main__':
    import websocket
    loop = get_select_loop()
    httpd = Httpd(iface='0.0.0.0', port=8080)
    httpd.start()
    httpd.route("/connect.json", LinkModule)
    httpd.route("/drop.json", DisconnectModule)
    httpd.route("/live.json", LiveData)
    loop.run_forever()
