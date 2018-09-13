import sys
from contextlib import contextmanager


class OpCodeLimitExceeded(Exception):
    pass


def build_tracer(limit):
    def tracer(frame, event, arg):
        frame.f_trace_opcodes = True
        frame.f_trace_lines = False

        if event == "opcode":
            tracer.opcode_count += 1
            if tracer.opcode_count > limit:
                raise OpCodeLimitExceeded()
        return tracer

    tracer.opcode_count = 0
    return tracer


@contextmanager
def limited_opcodes(limit):
    original_tracer = sys.gettrace()
    tracer = build_tracer(limit)
    sys.settrace(tracer)

    try:
        yield tracer
    finally:
        sys.settrace(original_tracer)
