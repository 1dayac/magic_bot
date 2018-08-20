import queue

class QueueWithMaxCapacity(object):
    def __init__(self, capacity = 100):
        self.limit = capacity
        self.queue = queue.Queue()

    def add(self, item):
        if self.queue.qsize() > self.limit:
            self.queue.get()
        self.queue.put(item)
