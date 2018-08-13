from __future__ import print_function, absolute_import
from collections import OrderedDict, MutableSet, deque
from functools import partial
from six import iterkeys
from six.moves import map

consume = partial(deque, maxlen=0)


class OrderedSet(MutableSet):
    def __init__(self, iterable=None):
        self.__backend = OrderedDict()
        if iterable is not None:
            consume(map(self.add, iterable))

    def __contains__(self, item):
        return item in self.__backend

    def __iter__(self):
        return iter(iterkeys(self.__backend))

    def __len__(self):
        return len(self.__backend)

    def add(self, value):
        self.__backend[value] = None

    def discard(self, value):
        del self.__backend[value]

    def __reversed__(self):
        return reversed(self.__backend)
