class NIterator(object):
    def __init__(self, it):
        self.it = iter(it)
        self._has_next = None
        self._the_next = None

    def __iter__(self):
        return self

    def next(self):
        if self._has_next:
            result = self._the_next
        else:
            result = next(self.it)
        self._has_next = None
        return result

    def has_next(self):
        if self._has_next is None:
            try:
                self._the_next = next(self.it)
            except StopIteration:
                self._has_next = False
            else:
                self._has_next = True
        return self._has_next
