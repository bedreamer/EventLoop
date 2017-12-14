EventLoop
=========

EventLoop是一个使用select方法进行超时和套接字I/O的异步事件调度库


特性
-------
   * 采用单线程模式
   * 采用IO事件一次注册，长时间使用方式
   * 对IO事件实现readable/writable方法
   * 包含延时执行功能

用途
-------
   如果不想使用多线程的程序结构，那么这个事件驱动的异步IO库就是一种解决方案，
   例如： 进行socke数据IO时，往往会在recv调用时出现阻塞（同步模式），而异步
   模式下的代码写起来相当费力，这时候可以考虑使用事件通知机制来实现这一过程。

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
