import sys
from contextlib import contextmanager

opcode_limit_supported = (sys.version_info.major, sys.version_info.minor) >= (3, 7)


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

    tracer.opcode_limit = limit
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


def get_opcode_count():
    tracer = sys.gettrace()
    try:
        return tracer.opcode_count
    except AttributeError:
        return None


def get_opcode_limit():
    tracer = sys.gettrace()
    try:
        return tracer.opcode_limit
    except AttributeError:
        return None
