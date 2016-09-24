import os
import string
import sys
import re

from collections import namedtuple

PROC_DIR = '/proc/'

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
                name = None
                try: 
                    name = pieces[5]
                except:
                    pass

                maps.append(MemMap(self.pid, MemRange(start, end), name))
        return maps

    def get_heap_map(self):
        try:
            return next(x for x in self.get_maps() if x.name == '[heap]')
        except StopIteration:
            return None

        

class MemRange(namedtuple('MemRange', ['start', 'end'])):
    @property 
    def size(self):
        return self.end - self.start

class MemMap:
    def __init__(self, pid, memrange, name):
        self.pid = pid
        self.range = memrange
        self.name = name

    @property
    def mem_file_path(self):
        return os.path.join(proc_dir_path(self.pid), 'mem')

    def read_data(self):
        with open(self.mem_file_path, 'rb') as f:
            f.seek(self.range.start)
            data = f.read(self.range.size)

        return data

    def write_data(self, pos, data):
        with open(self.mem_file_path, 'wb') as f:
            f.seek(pos)
            f.write(data)

    def find_sequence(self, seq):
        data = self.read_data()
        reg = re.escape(seq)
        return map(lambda m: m.start() + self.range.start, re.finditer(reg, data))

    def replace_sequence(self, seq, replacement):
        if type(seq) is str:
            seq = bytes(seq, 'utf-8')

        if type(replacement) is str:
            replacement = bytes(replacement, 'utf-8')

        
        count = 0
        for index in self.find_sequence(seq):
            self.write_data(index, replacement)
            count += 1

        return count
def main():

    p = Process(int(sys.argv[1]))
    # for a in strings(p.get_heap_map().read_data(), min=7):
    #     print(a)

    print(p.get_heap_map().replace_sequence("{", "}"))

if __name__ == '__main__':
    main()

