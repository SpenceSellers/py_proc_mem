from collections import namedtuple

ByteDifference = namedtuple('ByteDifference', ['pos', 'a', 'b'])
ByteRegionDifference = namedtuple('ByteRegionDifference', ['pos', 'a', 'b'])


def bin_diff(abytes, bbytes, restrict_to = None):
    if restrict_to is not None:
        return bin_diff_restricted(abytes, bbytes, restrict_to)
    if abytes == bbytes:
        print("Fast diff exit")
        return
    out_of = len(abytes)
    for i, (a, b) in enumerate(zip(abytes, bbytes)):
        if i % 1000000 == 0:
            print("Diffed {}/{} ({}%)".format(i, out_of, 100.0 * (i / out_of)))
        if a != b:
            yield ByteDifference(i, a, b)

def bin_diff_restricted(abytes, bbytes, restrict_to):
    for tested_byte in restrict_to:
        if abytes[tested_byte] != bbytes[tested_byte]:
            yield restrict_to

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

    
