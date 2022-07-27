#!/usr/bin/env python
# -*- coding: utf-8  -*-
import os
import time
from glob import glob
from logging.handlers import TimedRotatingFileHandler


class SepLogFileHandlerMixin(TimedRotatingFileHandler):

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
            dst_then = time_tuple[-1]
            if dst_now != dst_then:
                if dst_now:
                    addend = 3600
                else:
                    addend = -3600
                time_tuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)
        if os.path.exists(dfn):
            os.remove(dfn)
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # 分割文件名加上进程号，保证多进程分割文件不会出问题
        # ==================================================
        try:
            if (not glob(dfn + ".*")) and os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dfn + ".%d" % os.getpid())
        except OSError:
            pass
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        # Issue 18940: A file may not have been created if delay is True.
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at


class SepLogTimedRotatingFileHandler(SepLogFileHandlerMixin):
    """
    Sep 进程安全日志处理handler
    """

    def __init__(self, filename, when='h', interval=1, backup_count=20, encoding=None, delay=False, utc=False):
        self.delay = delay
        super(SepLogTimedRotatingFileHandler, self).__init__(filename, when, interval, backup_count, encoding, delay,
                                                             utc)
