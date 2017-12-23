EventLoop
=========

EventLoop是一个使用select方法进行超时和套接字I/O的异步事件调度库

特性
------
*  用单线程模式
*  采用IO事件一次注册，长时间使用方式
*  对IO事件实现readable/writable方法
*  包含延时执行功能
*  支持每个线程一个事件循环

机制
------


用途
------
   如果不想使用多线程的程序结构，那么这个事件驱动的异步IO库就是一种解决方案，
   例如： 进行socke数据IO时，往往会在recv调用时出现阻塞（同步模式），而异步
   模式下的代码写起来相当费力，这时候可以考虑使用事件通知机制来实现这一过程。

用法(延时执行及取消)
------
    import socket
    from SelectLoop import *


    def run_after_1_second(t):
        # this function will never be reached.
        print('run_after_1_second', t)


    def run_after_3_second(cancel_key):
        loop = get_select_loop()
        loop.cancel_delay(cancel_key)
        print(cancel_key, 'been cancelled!')


    loop = get_select_loop()
    schedule_delay_list = list()

    cancel_key = loop.schedule_delay(1, run_after_1_second, 1)
    schedule_delay_list.append(cancel_key)

    key = loop.schedule_delay(3, run_after_3_second, cancel_key)
    schedule_delay_list.append(key)

    loop.run_forever()
