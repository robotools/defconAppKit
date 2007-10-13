import vanilla

class ProgressWindow(object):

    def __init__(self, text="", tickCount=None, parentWindow=None):
        if parentWindow is None:
            self.w = vanilla.Window((250, 60), closable=False, miniaturizable=False, textured=False)
        else:
            self.w = vanilla.Sheet((250, 60), parentWindow)
        if tickCount is None:
            isIndeterminate = True
            tickCount = 0
        else:
            isIndeterminate = False
        self.w.progress = vanilla.ProgressBar((15, 15, -15, 10), maxValue=tickCount, isIndeterminate=isIndeterminate, sizeStyle="small")
        self.w.text = vanilla.TextBox((15, 32, -15, 14), text, sizeStyle="small")
        self.w.progress.start()
        self.w.center()
        self.w.open()

    def close(self):
        self.w.progress.stop()
        self.w.close()

    def update(self, text=None):
        self.w.progressBar.increment()
        if text is not None:
            self.w.textBox.set(text)
        self.w.textBox._nsObject.display()
