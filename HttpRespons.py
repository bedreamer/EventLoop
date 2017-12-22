# -*- coding: utf8 -*-
import time
import types
import json
import os
import mimetypes


status_string = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    306: "(Unused)",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported"
}


class HttpRespons(object):
    """HTTP应答对象"""
    def __init__(self, body=None, headers=None, code=None):
        if code is None:
            code = 200
        if headers is None:
            headers = dict()

        self.code = code
        try:
            self.status = status_string[code]
        except:
            self.status = 'Invalid'

        default_headers = dict()
        default_headers['Content-Type'] = 'text/html'
        default_headers['Server'] = 'thttpd by lijie/V2.34'
        default_headers['Date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        default_headers['Connection'] = 'keep-alive'
        default_headers['Cache-Control'] = 'public, max-age=60'
        self.headers = dict(default_headers, **headers)

        # 无论该应答体提供何种数据，都统一转换成生成器的形式
        self.iterable_body = None
        self.set_response(body)

    def response_wrapper(self, list_body):
        """convert all data type into generator"""
        yield self.make_respons_header()
        for context in list_body:
            yield context

    def make_respons_header(self):
        ex_headers = ["%s: %s\r\n" % (key, value) for key, value in self.headers.items()]
        headers = ["%s %d %s\r\n" % ('HTTP/1.1', self.code, self.status)]
        headers.extend(ex_headers)
        headers.append('\r\n')
        return "".join(headers)

    def set_header(self, key, value):
        """设置一个新的HTTP应答头部"""
        self.headers[key] = value

    def set_response(self, body):
        if body is None:
            self.set_header('Content-Length', '0')
            self.iterable_body = self.response_wrapper(list())

        elif isinstance(body, str):
            self.set_header('Content-Length', str(len(body)))
            self.iterable_body = self.response_wrapper([body])

        elif isinstance(body, list):
            length = sum([len(body[i]) for i in xrange(len(body))])
            self.set_header('Content-Length', str(length))
            self.iterable_body = self.response_wrapper(body)

        elif isinstance(body, tuple):
            length = sum([len(body[i]) for i in xrange(len(body))])
            self.set_header('Content-Length', str(length))
            self.iterable_body = self.response_wrapper(body)

        elif isinstance(body, dict):
            respons_body = json.dumps(body)
            self.set_header('Content-Length', str(len(respons_body)))
            self.set_header('Content-Type', 'application/json')
            self.iterable_body = self.response_wrapper([respons_body])

        elif isinstance(body, types.GeneratorType):
            self.iterable_body = body
        else:
            raise NotImplemented


class HttpResponsFile(HttpRespons):
    """应答一个普通文件"""
    def __init__(self, path, headers=None, code=None):
        self.mtu = 1024
        super(HttpResponsFile, self).__init__(body=None, headers=headers, code=code)

        # 文件尺寸
        filesize = os.path.getsize(path)
        self.set_header('Content-Length', str(filesize))

        # 文件最后修改日期
        last_modify_tsp = os.path.getatime(path)
        last_modify_str = time.strftime('%Y-%m-%d %H:%M:%S', last_modify_tsp)
        self.set_header('Last-Modified', last_modify_str)

        # 文件的MIME类型
        try:
            root, ext = os.path.splitext(path)
            mime = mimetypes.types_map[ext]
        except:
            mime = 'unknown'
        self.set_header('Content-Type', mime)

        self.set_response(self.normal_file_wrapper(path))

    def normal_file_wrapper(self, path):
        """将普通的文件作为生成器返回"""
        yield self.make_respons_header()
        with open(path, 'r') as file:
            while True:
                data = file.read(self.mtu)
                if len(data) > 0:
                    yield data
                if len(data) < self.mtu:
                    break
