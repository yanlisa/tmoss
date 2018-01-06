"""
pymoss.moss

Michael <mchang@cs>, 2015
"""

import fnmatch, glob, os, re, shutil, subprocess, tempfile

from . import config, util

class Runner(object):
    BINARY = os.path.realpath(os.path.join(os.path.dirname(__file__), "bin", "moss"))
    LANGUAGES = set(config.MATCH_FILES.keys())
    NOBASE_THRESHOLD = 1000000
    TMP_PREFIX = "moss_"

    def __init__(self, lang, threshold=config.THRESHOLD, tmpdir=None):
        assert lang in self.LANGUAGES, lang
        assert threshold > 1, threshold
        assert not config.TMPDIR or os.path.isdir(config.TMPDIR), config.TMPDIR

        self.lang = lang
        self.threshold = threshold
        self.counts = [0 for _ in range(util.NTYPES)]
        self.pairs = []
        self.submits = dict()
        self.tmpdir = tempfile.mkdtemp(prefix=self.TMP_PREFIX, dir=config.TMPDIR)

    def add(self, dir, type=util.CURRENT, name=None):
        """ Add a submission.
            dir: Directory containing the submission (non-recursive)
            type: Type of submission (one of config.{STARTER,CURRENT,ARCHIVE}) (default: CURRENT)
            name: Name of submission (shown in report) (default: <dir>)
        """
        assert os.path.isdir(dir), dir
        assert type in range(util.NTYPES), type
        if name is None: name = dir
        assert " + " not in name, "Name cannot contain ' + ': %s" % name
        assert name not in self.submits, name

        s = util.Submit(type, self.counts[type], name)
        self.counts[type] += 1
        self.submits[name] = s
        files = set(f for pat in config.MATCH_FILES[self.lang] for f in glob.glob(os.path.join(dir, pat)))
        # Drop weird chars in filenames and other stuff we write
        with open(s.tmpfile(self.tmpdir), "w") as tmpf:
            s.lines = 0
            for file in sorted(files):
                if not os.path.isfile(file): continue # Skip symlinks and other weirdness
                # Replace non-ASCII (and non-UTF8, generally) chars in files we read
                with open(file, "rU") as f:
                    lines = f.readlines()
                    if not lines: continue
                    tmpf.write(">>>> file: %s\n" % os.path.basename(file))
                    if lines[-1][-1] != "\n": lines[-1] += "\n"
                    tmpf.writelines(lines)
                    s.lines += len(lines) + 1

    def add_all(self, dir, type=util.CURRENT, prefix=None, skip=set()):
        """ Add all submissions in a directory
            dir: Directory containing submissions (each in separate directory)
            type: Type of submission
            prefix: Prefix for submissions (nem in report will be <prefix>/<submit_dir>)
            skip: Set of globs to be skipped (e.g. "test?", "student_*")
        """
        assert os.path.isdir(dir), dir
        if prefix is None: prefix = dir
        dirs = filter(lambda d: os.path.isdir(os.path.join(dir, d)), os.listdir(dir))
        for d in sorted(dirs):
            if any(fnmatch.fnmatch(d, g) for g in skip): continue
            self.add(os.path.join(dir, d), type, os.path.join(prefix, d))

    def cleanup(self):
        """ Cleanup temp files. Best to call this in a finally clause. """
        if not self.tmpdir: return
        shutil.rmtree(self.tmpdir)
        self.tmpdir = None

    def run(self, outdir=None, npairs=config.NPAIRS):
        prevwd = os.getcwd()
        os.chdir(self.tmpdir)

        util.msg("INPUT: %d starter, %d current, %d archive" % tuple(self.counts))
        self._gen_manifest("manifest")
        util.time("Running", lambda: self._exec(self.threshold, "manifest", "results"))
        util.time("Parsing results", lambda: self._parse_results("results", self._update_submit, self._make_pair,print_tokens=True))

        pairs = self.pairs
        total_pairs = len(pairs)
        num_nonself = 0
        self.pairs = []
        for p in sorted(pairs, key=lambda p: -p.tokens.match):
            self.pairs.append(p)
            if not p.is_self: num_nonself += 1
            if num_nonself == npairs: break
        self.fname_pairs = {}
        # for p in sorted(pairs, key=lambda p: -p.tokens.match):
        #   if p.is_self: continue
        #   fname = p.submits[0].name
        #   if fname not in self.fname_pairs:
        #     self.fname_pairs[fname] = p
          
        if self.fname_pairs:
          util.msg("Total number of fname pairs? {}".format(len(self.fname_pairs.keys())))
          util.time("Finding common code for fname_pairs",
              self._run_common_fnames)
        util.time("Finding common code", self._run_common)
        util.msg("OUTPUT: %d submits, %d pairs, reporting top %d" % \
                  (len(self.submits), total_pairs, len(self.pairs)))

        os.chdir(prevwd)
        if outdir:
          shutil.copytree(self.tmpdir, outdir)

    def _gen_manifest(self, file, pair=None):
        assert self.counts[util.CURRENT] < util.Submit.ARCHIVE_SET
        with open(file, "w") as f:
            if not pair:
                for s in sorted(self.submits.values()): f.write(s.manifest_line(self.lang))
            else:
                for i, s in enumerate(pair.submits, 1): f.write(s.manifest_line(self.lang, i))

    def _make_pair(self, name1, name2, tokens, lines, regions):
        s1, s2 = (self.submits[n] for n in (name1, name2))
        self.pairs.append(util.Pair(s1, s2, tokens, regions))

    def _parse_regions(self, line):
        REGION_PAT = "(\d+)-(\d+), (\d+)-(\d+): (-?\d+)"
        REGION_SEP = "# "
        region_re = re.compile(REGION_PAT)

        regions = []
        for r in line.split(REGION_SEP):
            m = region_re.match(r)
            assert m, line
            l1, l2, l3, l4, t = (int(x) for x in m.groups())
            regions.append((util.Range(l1, l2), util.Range(l3, l4), t))
        return regions

    def _parse_results(self, file, submit_fn, pair_fn, print_tokens=False):
        LINE_PAT = "(.+) \+ (.+): tokens (-?\d+)   lines (-?\d+)# total tokens (-?\d+) \+ (-?\d+), " \
                   "total lines (-?\d+) \+ (-?\d+), percentage matched (-?\d+)% \+ (-?\d+)%# (.*)"
        line_re = re.compile(LINE_PAT)

        len_counts = {}
        
        with open(file) as f:
            for line in f:
                line = line.strip()
                if not line: continue
                m = line_re.match(line)
                assert m, line
                g = list(m.groups())
                for i in range(2, 10): g[i] = int(g[i])
                for i in range(2):
                    t, l, p = (g[i + j] for j in (4, 6, 8))
                    # Verify percentage calculation
                    #assert p == g[2] * 100 // t, line
                    if submit_fn: submit_fn(g[i], t, l)

                # start logging
                if g[0] not in len_counts:
                  #print(line)
                  len_counts[g[0]] = (g[4], g[6])
                # # figure out uname
                # uname_fname = g[0].split('/')[-1]
                # uname, fname = uname_fname.split('_')
                # if uname not in match_counts:
                #   # pother_fname, pother_t, pother_tc, pother_po, pother_ps, token_fname, token_t, token_tc, token_po, token_ps
                #   match_counts[uname] = [''] + [0] * 4 + [''] + [0]*4
                # other_fname = g[1].split('/')[-1]
                # if g[9] > match_counts[uname][4]:
                #   print(line)
                #   print(g)
                #   #match_counts[uname][:4] = [other_fname, g[

                # end logging

                regions = self._parse_regions(g[-1])
                if pair_fn: pair_fn(*(g[:4] + [regions]))
        # if print_tokens:
        #   with open(os.path.join(os.getcwd(),'tokens.csv'), 'w') as f:
        #     f.write('\n'.join(["{},{},{}".format(fname, len_counts[fname][0],len_counts[fname][1]) for fname in sorted(len_counts.keys())]))
        #     print("wrote student file lengths (tokens/lines) to {}".format(f.name))

    def _run_common(self):
        for i, p in enumerate(self.pairs):
            manifest, results = ("%s.%d" % (s, i) for s in ("manifest", "results"))
            self._gen_manifest(manifest, p)
            self._exec(self.NOBASE_THRESHOLD, manifest, results)
            fn = lambda *args: self._update_nobase(p, *args)
            self._parse_results(results, self._update_submit, fn)
    
    def _run_common_fnames(self):
        match_tokens = {}
        # pother_other, pother_fname,
        #     pother_t, pother_tc, pother_po, pother_ps
        # token_other, token_fname,
        #     token_t, token_tc, token_po, token_ps
        for i, p in enumerate(self.fname_pairs.values()):
          manifest, results = ("%s.%d" % (s, i) for s in ("manifest", "results"))
          self._gen_manifest(manifest, p)
          self._exec(self.NOBASE_THRESHOLD, manifest, results)
          fn = lambda *args: self._update_nobase(p, *args)
          self._parse_results(results, self._update_submit, fn)

          po, ps = map(lambda percent: float(percent.split('%')[0]),
              p.percent)
          t, tc = p.tokens.match, p.tokens.common
          fname, other_fname = p.submits[0].name, p.submits[1].name
          uname_fname = fname.split('/')[-1]
          other_fname = other_fname.split('/')[-1]
          uname = uname_fname.split('_')[0]
          if uname not in match_tokens:
            match_tokens[uname] = ['', ''] + [0] * 4 + ['',''] + [0]*4
          if po > match_tokens[uname][4]:
            match_tokens[uname][:6] = [uname_fname, other_fname,
                t, tc, po, ps]
          if t > match_tokens[uname][8]:
            match_tokens[uname][6:] = [uname_fname, other_fname,
                t, tc, po, ps]
        print("finished parsing", len(match_tokens.keys()), "unames")
        with open(os.path.join(os.getcwd(),'matches.csv'), 'w') as f:
          f.write('\n'.join([
                ','.join([uname] + list(map(str, match_tokens[uname]))) \
              for uname in sorted(match_tokens.keys())]))
          print("wrote matched tokens to {}".format(f.name))

    def _update_nobase(self, p, name1, name2, tokens, lines, regions):
        assert tuple(x.name for x in p.submits) == (name1, name2), p
        p.find_common(tokens, regions)
        p.calc_percent()

    def _update_submit(self, name, tokens, lines):
        assert name in self.submits, name
        s = self.submits[name]
        if s.tokens != -1: assert s.tokens == tokens, name
        else: s.tokens = tokens
        # MOSS counts trailing \n as separate line
        assert s.lines == lines - 1, name

    @classmethod
    def _exec(cls, threshold, manifest, results):
        # These options were hard-coded in the Perl script (some were vars but not user-settable).
        MAGIC_ARGS = ["-p", "24", "-t", "26", "-g", "10", "-w", "5"]

        args = ["-n", str(threshold), "-a", manifest, "-o", results]
        with open(os.devnull, "w") as NULL:
            proc = subprocess.Popen([cls.BINARY] + MAGIC_ARGS + args, stdout=NULL, stderr=subprocess.PIPE)
        errors = proc.communicate()[1].strip()
        if errors: raise RuntimeError("MOSS errors:\n%s" % errors)

# vim: et sw=4 ts=4

