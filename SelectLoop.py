# -*- coding: utf8 -*-
import select
import time
import threading


class DelayProbe:
    def __init__(self, name, now, delay, callback, *args):
        self.name = name
        self.born = now
        self.die = now + delay
        self.callback = callback
        self.args = args

    def __cmp__(self, other):
        if self.die > other.die:
            return 1
        elif self.die < other.die:
            return -1
        else:
            return 0

    def delta(self):
        return self.die - time.time()

    def do_callback(self):
        if len(self.args):
            self.callback(*self.args)
        else:
            self.callback()


class SelectLoop:
    def __init__(self):
        self.read_probe = dict()
        self.write_probe = dict()
        self.delay_probe = list()

    def schedule_read(self, fds, readable):
        """计划读数据"""
        self.read_probe[fds] = readable

    def cancel_read(self, fds):
        """取消读数据"""
        try:
            del self.read_probe[fds]
        except:
            pass

    def schedule_delay(self, seconds, callback, *args):
        """计划延迟执行函数"""
        now = time.time()
        delayer = DelayProbe(now, now, seconds, callback, *args)
        self.delay_probe.append(delayer)
        self.delay_probe.sort()
        # print(self.delay_probe)
        return now

    def cancel_delay(self, name):
        """取消延时计划"""
        for i in xrange(len(self.delay_probe)):
            delay = self.delay_probe[i]
            if delay.name != name:
                continue
            self.delay_probe.remove(delay)
            return

    def schedule_write(self, fds, writable):
        """计划写数据"""
        self.write_probe[fds] = writable

    def cancel_write(self, fds):
        """取消写数据"""
        try:
            del self.write_probe[fds]
        except:
            pass

    def run_step_forward(self, ttw=None):
        ttw = 5 if ttw is None else ttw
        r = [fds for fds in self.read_probe.iterkeys()]
        w = [fds for fds in self.write_probe.iterkeys()]
        readable, writable, _ = select.select(r, w, [], ttw)
        for fds in readable: self.read_probe[fds](fds)
        for fds in writable: self.write_probe[fds](fds)

    def run_forever(self, ttw=None):
        ttw = 600 if ttw is None else ttw
        while len(self.read_probe) + len(self.write_probe) + len(self.delay_probe) > 0:
            r = [fds for fds, _ in self.read_probe.items()]
            w = [fds for fds, _ in self.write_probe.items()]

            almost_die_delta = 600
            while len(self.delay_probe) > 0:
                delayer = self.delay_probe[0]
                almost_die_delta = delayer.delta()
                if almost_die_delta <= 0.001:
                    self.delay_probe.remove(delayer)
                    delayer.do_callback()
                else:
                    break

            # for io logical
            if len(r) + len(w) > 0:
                ttw = min((almost_die_delta, 600))
                try:
                    readable, writable, _ = select.select(r, w, [], ttw)
                except Exception as e:
                    print(e)
                    readable, writable = list(), list()

                for fds in readable:
                    try:
                        self.read_probe[fds](fds)
                    except:
                        pass
                for fds in writable:
                    try:
                        self.write_probe[fds](fds)
                    except:
                        pass
            else:
                time.sleep(almost_die_delta)

            # for delay logical
            while len(self.delay_probe) > 0:
                delayer = self.delay_probe[0]
                almost_die_delta = delayer.delta()
                if almost_die_delta > 0.001:
                    break
                self.delay_probe.remove(delayer)
                delayer.do_callback()


def get_select_loop():
    """针对每一个线程开辟新的循环对象"""
    thread = threading.current_thread()
    try:
        return thread._loop
    except:
        _loop = SelectLoop()
        thread._loop = _loop
    return _loop
