"""Kyco Buffer Classes, based on Python Queue"""
import logging
from queue import Queue
from threading import Event as Semaphore

from kyco.core.events import KycoAppEvent
from kyco.core.events import KycoMsgEvent
from kyco.core.events import KycoNullEvent
from kyco.core.events import KycoRawEvent

__all__ = ['KycoBuffers']

log = logging.getLogger('Kyco')


class KycoEventBuffer(object):
    """Class that """
    def __init__(self, name, event_base_class):
        self.name = name
        self._queue = Queue()
        self._semaphore = Semaphore()
        self._event_base_class = event_base_class
        self._reject_new_events = False

    def put(self, new_event):
        if not self._reject_new_events:
            if not isinstance(new_event, self._event_base_class) and not isinstance(new_event, KycoNullEvent):
                # TODO: Raise a more proper exception
                raise Exception("This event can not be added to this buffer")
            log.debug('Added new event to %s event buffer', self.name)
            self._queue.put(new_event)
            self._semaphore.set()

        if isinstance(new_event, KycoNullEvent):
            log.info('%s buffer in stop mode. Rejecting new events.', self.name)
            self._reject_new_events = True

    def get(self):
        self._semaphore.wait()
        log.debug('Removing event from %s event buffer', self.name)
        event = self._queue.get()
        if self._queue.empty():
            self._semaphore.clear()
        return event

    def task_done(self):
        self._queue.task_done()

    def join(self):
        self._queue.join()

    def qsize(self):
        return self._queue.qsize()

    def empty(self):
        return self._queue.empty()

    def full(self):
        return self._queue.full()


class KycoBuffers(object):
    def __init__(self):
        self.raw_events = KycoEventBuffer('raw_event', KycoRawEvent)
        self.msg_in_events = KycoEventBuffer('msg_in_event', KycoMsgEvent)
        self.msg_out_events = KycoEventBuffer('msg_out_event', KycoMsgEvent)
        self.app_events = KycoEventBuffer('app_event', KycoAppEvent)

    def send_stop_signal(self):
        log.info('Stop signal received by Kyco buffers.')
        log.info('Sending KycoNullEvent to all apps.')
        event = KycoNullEvent()
        self.raw_events.put(event)
        self.msg_in_events.put(event)
        self.msg_out_events.put(event)
        self.app_events.put(event)
