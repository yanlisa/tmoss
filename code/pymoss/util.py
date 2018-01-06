"""
pymoss.util

Michael <mchang@cs>, 2015
"""

from collections import namedtuple
import functools, os, timeit

from . import config

Range = namedtuple("Range", ["start", "end"])
STARTER, CURRENT, ARCHIVE, NTYPES = range(4)
TYPE_STR = ["STARTER", "CURRENT", "ARCHIVE"]

class MC(object):
    def __init__(self, m, c): self.match, self.common = m, c
    def __repr__(self): return "match=%d, common=%d" % (self.match, self.common)

class Pair(object):
    COMMON = -2

    def __init__(self, s1, s2, tokens, regions):
        self.submits = (s1, s2)
        self.is_self = (s1.student() == s2.student())
        self.tokens = MC(tokens, 0)
        # list of (Range(s1.start, s1.end), Range(s2.start, s2.end), tokens)
        self.match = sorted(regions, key=lambda x:(-x[2], x[0], x[1]))
        # For each submission: list of (range, index), index is idx into match or COMMON
        self.regions = None
        self.percent = None

    def __repr__(self):
        return "Pair(%s, %s, %s)" % (self.submits[0].name, self.submits[1].name, repr(self.tokens))

    def calc_percent(self):
        assert self.percent is None
        fn = lambda s: float(self.tokens.match) / (s.tokens - self.tokens.common)
        self.percent = tuple("%.2f%%" % (fn(s) * 100) for s in self.submits)
        #self.orig = tuple(float(self.tokens.match) / s.tokens for s in self.submits)

    def find_common(self, tokens, nobase):
        assert self.regions is None
        self.tokens.common = max(tokens - self.tokens.match, 0)

        regions = ([], [])
        for sub in range(2):
            lines = [-1 for _ in range(self.submits[sub].lines + 1)]
            for r in nobase:
                for l in range(r[sub].start, r[sub].end + 1): lines[l] = self.COMMON
            for i, r in enumerate(self.match):
                for l in range(r[sub].start, r[sub].end + 1): lines[l] = i
            start = 0
            cur = -1
            for i, v in enumerate(lines):
                if v == cur: continue
                if cur != -1: regions[sub].append((Range(start, i - 1), cur))
                cur = v
                start = i
        self.regions = regions

@functools.total_ordering
class Submit(object):
    ARCHIVE_SET = 1000000

    def __init__(self, type, idx, name):
        self.type = type
        self.idx = idx
        self.name = name
        self.tokens = -1
        self.lines = -1

    def __eq__(self, other): return (self.type, self.idx) == (other.type, other.idx)
    def __lt__(self, other): return (self.type, self.idx) < (other.type, other.idx)

    def __repr__(self):
        return "Submit(%s, %d, %s, %d, %d)" % \
               (TYPE_STR[self.type], self.idx, self.name, self.tokens, self.lines)

    def manifest_line(self, lang, id=None):
        if id is None: id = [0, self.idx + 1, self.ARCHIVE_SET][self.type] # idx is 0-indexed
        return "%s %d %s %s\n" % (self.tmpfile(), id, lang, self.name)

    def student(self):
        base = os.path.basename(self.name)
        # NOTE(Lisa): changed to find, not rfind
        return base[:base.find("_")] if config.HAS_SUBMIT_NUM and "_" in base else base

    def tmpfile(self, dir=None):
        file = "%d_%d" % (self.type, self.idx)
        return file if dir is None else os.path.join(dir, file)

def msg(s): print "---", s , "\r" , # trailing comma suppresses newline
def time(msg, fn):
    msg_wait = "--- " + msg + " ... "
    print msg_wait + "\r" , # trailing comma suppresses newline
    start = timeit.default_timer()
    fn()
    end = timeit.default_timer()
    print "%s done (%.3f s)\r" % (msg_wait, end - start) , 

# vim: et sw=4 ts=4

