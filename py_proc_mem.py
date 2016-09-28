import os
import string
import sys
import re
import itertools
import signal

from collections import namedtuple

import binary_diff

PROC_DIR = '/proc/'
MAP_NAME_HEAP = '[heap]'
MAP_NAME_STACK = '[stack]'

def proc_dir_path(pid):
        return os.path.join(PROC_DIR, str(pid))

def strings(bytes, min=4):
    result = ""
    for c in bytes:
        c = chr(c)
        if c in string.printable:
            result += c
            continue
        if len(result) >= min:
            yield result
        result = ""

# From https://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator-in-python
def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(itertools.islice(it, n))
    if len(result) == n:
        yield result    
    for elem in it:
        result = result[1:] + (elem,)
        yield result

class Process:
    def __init__(self, pid):
        self.pid = pid    
    
    @property
    def maps_path(self):
        return os.path.join(proc_dir_path(self.pid), 'maps')

    def get_maps(self):
        maps = []
        with open(self.maps_path, 'r') as f:
            for line in f:
                pieces = line.split()

                start, end = (int(n, 16) for n in pieces[0].split('-'))

                perm_string = pieces[1]
                perms = MapPerms('r' in perm_string, 'w' in perm_string, 'x' in perm_string)

                name = None
                try: 
                    name = pieces[5]
                except:
                    pass

                maps.append(MemMap(self.pid, MemRange(start, end), name, perms))
        return maps

    def get_map_by_name(self, name):
        try:
            return next(x for x in self.get_maps() if x.name == name)
        except StopIteration:
            return None

    def get_heap_map(self):
        return self.get_map_by_name(MAP_NAME_HEAP)

    def get_stack_map(self):
        return self.get_map_by_name(MAP_NAME_STACK)

    def get_nameless_maps(self):
        return filter(lambda m: m.name is None, self.get_maps())

    def suspend(self):
        os.kill(self.pid, signal.SIGSTOP)

    def resume(self):
        os.kill(self.pid, signal.SIGCONT)

# Represents the permissions that a memory map can have.
MapPerms = namedtuple('MapPerms', ['read', 'write', 'execute'])

# A range of memory. Memory ranges are always absolute, NOT relative to a map.
class MemRange(namedtuple('MemRange', ['start', 'end'])):
    @property 
    def size(self):
        return self.end - self.start

    def is_inside(self, other):
        return other.start >= self.start and other.end <= self.end

class OutsideOfMapException(Exception):
    pass

class MemMap:
    def __init__(self, pid, memrange, name, perms = MapPerms(True, False, False)):
        self.pid = pid
        self.range = memrange
        self.name = name
        self.perms = perms

    @property
    def mem_file_path(self):
        return os.path.join(proc_dir_path(self.pid), 'mem')

    def read_data(self):
        return self.read_range(self.range)

    def read_range(self, mem_range):
        if not mem_range.is_inside(self.range):
            raise OutsideOfMapException("Trying to read range that lies outside this map!")

        with open(self.mem_file_path, 'rb') as f:
            f.seek(mem_range.start)
            data = f.read(mem_range.size)

        return data

    @property
    def can_write(self):
        return self.perms.write

    def write_data(self, pos, data):

        if not self.can_write:
            raise RuntimeError("Map is read only!")

        if type(pos) is MemRange:

            if not mem_range.is_inside(self.range):
                raise OutsideOfMapException("Trying to write to range that lies outside this map!")

            size = pos.size
            pos = pos.start
            if len(data) != size:
                raise RuntimeError("Tried writing data to differently sized range")

        

        with open(self.mem_file_path, 'wb') as f:
            f.seek(pos)
            f.write(data)

    def find_sequence(self, seq):
        data = self.read_data()
        reg = re.escape(seq)
        return map(lambda m: m.start() + self.range.start, re.finditer(reg, data))

    def replace_sequence(self, seq, replacement, fallback_encoding='utf-8'):
        if type(seq) is str:
            seq = bytes(seq, fallback_encoding)

        if type(replacement) is str:
            replacement = bytes(replacement, fallback_encoding)
        
        count = 0
        for index in self.find_sequence(seq):
            self.write_data(index, replacement)
            count += 1

        return count

    def __str__(self):
        return "Map {} {:x}-{:x}".format(self.name, self.range.start, self.range.end)


def multi_change(mmap):
    lastdata = mmap.read_data()
    lastdiffs = None
    while True:
        same_mode = False
        i = input("Snapshot taken. Hit enter when changed, 'same' to same, q to end: ")
        if i == 'q':
            break
        elif i == 'same':
            same_mode = True

        new_data = mmap.read_data()

        diffs = list(map(lambda d: d.pos, binary_diff.bin_diff(lastdata, new_data)))
        
        if lastdiffs is None:
            lastdiffs = diffs
        else:
            if not same_mode:
                lastdiffs = [p for p in diffs if p in lastdiffs]
            else:
                lastdiffs = [p for p in lastdiffs if p not in diffs]

        lastdata = new_data

        print("{} changes, {} retained".format(len(diffs), len(lastdiffs)))

    return lastdiffs

def main():
    import time

    p = Process(int(sys.argv[1]))

    varmap = list(p.get_nameless_maps())[2]

    #print("\n".join(strings(varmap.read_data())))

    #print(varmap.replace_sequence("a wowful test", "U SUX haha"))

    # heap = p.get_heap_map()
    # print(heap)

    print(multi_change(varmap))

    # d1 = varmap.read_data()
    # input("Snapshot taken. Hit enter when ready:")
    # d2 = varmap.read_data()


    #varmap.write_data(varmap.range.start, d1)

    
    # print("Done")
    # for diff in binary_diff.group_diffs(binary_diff.bin_diff(d1, d2)):
    #     print(diff)


    #for s in strings(p.get_heap_map().read_data(), 50): print(s)


    

    #print(p.get_heap_map().replace_sequence("e", "o"))

if __name__ == '__main__':
    main()

