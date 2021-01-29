from hpy.universal import _debug

class HPyError(Exception):
    pass

class HPyLeak(HPyError):
    def __init__(self, leaks):
        super().__init__()
        self.leaks = leaks

    def __str__(self):
        lines = []
        lines.append('%s handles have not been closed properly:' % len(self.leaks))
        for dh in self.leaks:
            lines.append('    %r' % dh)
        return '\n'.join(lines)


class LeakDetector:

    def __init__(self):
        self.generation = None

    def start(self):
        if self.generation is not None:
            raise ValueError('LeakDetector already started')
        self.generation = _debug.new_generation()

    def stop(self):
        if self.generation is None:
            raise ValueError('LeakDetector not started yet')
        leaks = _debug.get_open_handles(self.generation)
        if leaks:
            raise HPyLeak(leaks)



