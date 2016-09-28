from collections import namedtuple

ByteDifference = namedtuple('ByteDifference', ['pos', 'a', 'b'])
ByteRegionDifference = namedtuple('ByteRegionDifference', ['pos', 'a', 'b'])


def bin_diff(abytes, bbytes):
    for i, (a, b) in enumerate(zip(abytes, bbytes)):
        if a != b:
            yield ByteDifference(i, a, b)

def group_diffs(byte_differences):
    cur_a = bytearray()
    cur_b = bytearray()
    start_pos = 0
    last_pos = -1
    for diff in byte_differences:
        if diff.pos != last_pos + 1 and len(cur_a) != 0:
            yield ByteRegionDifference(start_pos, cur_a, cur_b)
            cur_a = bytearray()
            cur_b = bytearray()
            start_pos = diff.pos
        last_pos = diff.pos
        cur_a.append(diff.a)
        cur_b.append(diff.b)

    
