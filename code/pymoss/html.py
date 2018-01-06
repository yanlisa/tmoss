"""
pymoss.html

Michael <mchang@cs>, 2015
"""

import datetime, os, shutil
from mako import exceptions
from mako.lookup import TemplateLookup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from . import config, util

class _Formatter(HtmlFormatter):
    def __init__(self, pair, idx, ncolors, **opts):
        super(_Formatter, self).__init__(cssclass="code", linenos="inline", **opts)
        self.idx = idx
        self.ncolors = ncolors
        regions = pair.regions[idx]
        self.starts = {r[0].start: r[1] for r in regions}
        self.ends = set(r[0].end for r in regions)

    def _format_lines(self, src):
        base = super(_Formatter, self)._format_lines
        return self._highlight(base(src))

    def _highlight(self, src):
        n = 0
        starts, ends = self.starts, self.ends
        for t, line in src:
            if t != 1:
                yield t, line
                continue
            n += 1
            if n in starts:
                if starts[n] < 0: yield 0, "<div class=\"common\">"
                else:
                    yield 0, "<div class=\"hl%d\" id=\"region%d_%d\">" % \
                          (starts[n] % self.ncolors, self.idx, starts[n])
            yield t, line
            if n in ends: yield 0, "</div>"

    def _wrap_inlinelinenos(self, inner):
        # Copied and modified to support "yield 0, foo". UGH!
        # need a list of lines since we need the width of a single number :(
        lines = list(inner)
        sp = self.linenospecial
        st = self.linenostep
        num = self.linenostart
        mw = len(str(sum(t for t, _ in lines) + num - 1))

        # Not implemtning because I don't care
        assert not self.noclasses and not sp
        for t, line in lines:
            if t != 1:
                yield t, line
                continue
            yield t, '<span class="lineno">%*s </span>' % (mw, (num % st and ' ' or num)) + line
            num += 1

class Html(object):
    LEXER_MAP = {"cc": "cpp"}
    NUM_COLORS = 7
    TMPL_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "templates"))

    def __init__(self, runner, desc=""):
        self.runner = runner
        self.desc = desc

    def gen_all(self, dir=None):
        """ Generate the full report, including index page.
            dir: Directory to store files; relative paths are relative to config.OUTDIR
                 (None to generate from datetime)
        """
        util.time("Generating report", lambda: self._gen_all(dir))
        return self.url

    def gen_report(self, pair, file):
        """ Generate a report for a single pair.
            pair: A Pair from runner.pairs
            file: The filename to output to
        """
        ctx = dict(pair.__dict__)
        ctx["files"] = tuple(self._format_file(pair, i) for i in range(2))
        self._render("report", ctx, file)

    def _format_file(self, pair, idx):
        s = pair.submits[idx]
        with open(s.tmpfile(self.runner.tmpdir)) as f: content = f.read()
        lang = self.runner.lang
        if lang in self.LEXER_MAP: lang = self.LEXER_MAP[lang]
        fmt = _Formatter(pair, idx, self.NUM_COLORS)
        return highlight(content, get_lexer_by_name(lang, stripnl=False), fmt)

    def _gen_all(self, dir):
        tmpdir = os.path.join(self.runner.tmpdir, "www")
        assert not os.path.exists(tmpdir)
        os.mkdir(tmpdir)
        ctx = {"pairs": [], "pairs_self": [], "threshold": self.runner.threshold}
        for i, p in enumerate(self.runner.pairs, 1):
            self.gen_report(p, os.path.join(tmpdir, "report%d.html" % i))
            ctx["pairs_self" if p.is_self else "pairs"].append((i, p))
        self._render("index", ctx, os.path.join(tmpdir, "index.html"))

        if dir is None: dir = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(config.OUTDIR, dir)
        print("hi",path)
        assert not os.path.exists(path)
        shutil.move(tmpdir, path)
        self.url = config.URL + dir

    def _render(self, tmpl, ctx, file):
        ctx["desc"] = self.desc
        ctx["NUM_COLORS"] = self.NUM_COLORS
        t = TemplateLookup([self.TMPL_DIR]).get_template(tmpl + ".html")
        assert not os.path.exists(file)
        try: 
            with open(file, "w") as f: f.write(t.render(**ctx))
        except:
            print(exceptions.text_error_template().render())
            raise

# vim: et sw=4 ts=4

