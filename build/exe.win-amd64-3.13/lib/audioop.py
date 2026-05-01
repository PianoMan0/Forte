# Minimal stub of the ``audioop`` C extension for frozen builds lacking it.
# This provides basic, mostly no-op implementations so imports succeed.
# NOTE: This is a compatibility shim, not a full replacement.

def _noop_bytes(data, *args, **kwargs):
    return data

def max(data, width):
    return 0

def rms(data, width):
    return 0

def avg(data, width):
    return 0

def add(data1, data2, width):
    # naive concatenation fallback
    try:
        return data1 + data2
    except Exception:
        return data1

def mul(data, factor, width):
    return data

def lin2lin(data, widthin, widthout):
    return data

def bias(data, width, bias):
    return data

def reverse(data, width):
    return data

def findmax(data, width):
    return (0, 0)

def byteswap(data, width):
    return data

def ulaw2lin(data, width):
    raise NotImplementedError("ulaw/lin conversion not available in stub")

def lin2ulaw(data, width):
    raise NotImplementedError("lin/ulaw conversion not available in stub")

__all__ = [
    'max', 'rms', 'avg', 'add', 'mul', 'lin2lin', 'bias', 'reverse', 'findmax', 'byteswap',
    'ulaw2lin', 'lin2ulaw'
]
