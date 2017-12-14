EventLoop
=========

EventLoop是一个使用select方法进行超时和套接字I/O的异步事件调度库

用法
-------
    import socket
    from SelectLoop import *

    def delay_callback(t):
        print('callback', t)

    loop = get_select_loop()
    server = SelectSocketServer('127.0.0.1', 19999)
    server.start_service()
    cancel = list()
    for i in xrange(10):
        name = loop.schedule_delay(i, delay_callback, i)
        if i % 2 == 0:
            cancel.append(name)

    for name in cancel:
        loop.cancel_delay(name)

    loop.run_forever()
