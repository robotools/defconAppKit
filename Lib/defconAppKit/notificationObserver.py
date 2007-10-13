class NSObjectNotificationObserver(object):

    def __init__(self):
        self._references = {}

    def add(self, observer, callbackString, observable, notification):
        if (observable, notification) not in self._references:
            self._references[observable, notification] = []
            observable.addObserver(self, "_callback", notification)
        if (observer, callbackString) not in self._references[observable, notification]:
            self._references[observable, notification].append((observer, callbackString))

    def remove(self, observer, observable=None, notification=None):
        # iterate over specific
        if observable is not None and notification is not None:
            for (_observer, _callback) in self._references[observable, notification]:
                l = []
                if observer == _observer:
                    observable.removeObserver(self, notification)
                else:
                    l.append((_observer, _callback))
                if not l:
                    del self._references[observable, notification]
                else:
                    self._references[observable, notification] = l
            return
        # iterate over all
        for (_observable, _notification), observers in self._references.items():
            if observable is not None and observable != _observable:
                continue
            if notification is not None and notification != _notification:
                continue
            l = []
            for (_observer, _callback) in observers:
                if observer == _observer:
                    _observable.removeObserver(self, _notification)
                else:
                    l.append((_observer, _callback))
            self._references[_observable, _notification] = l
        for k, l in self._references.items():
            if not l:
                del self._references[l]

    def _callback(self, notification):
        obj = notification.object
        name = notification.name
        for observer, callback in self._references[obj, name]:
            callback = getattr(observer, callback)
            callback(notification)

