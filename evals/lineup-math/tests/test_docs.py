import unittest
from tests.harness import *

def sim_sources():
    """Every python file the sim ships, source glued back across the `print`
    calls and comment lines a wrapped sentence is split over. A citation this
    code PRINTS spans two string literals and one in a comment spans two lines,
    so scanning the raw text checks a sentence nobody reads"""
    paths = [sim.__file__] + sorted(
        glob.glob(os.path.join(sim.HERE, "simlib", "**", "*.py"),
                  recursive=True))
    return {p: re.sub(r"\n\s*#+ ?", " ",
                      re.sub(r'"\)?\s*\n\s*(?:print\()?"', " ", read_text(p)))
            for p in paths}

def doc_sections(path):
    """Every heading in a markdown file, cut at the em-dash gloss -- the form a
    `§` citation names it by"""
    return {re.split(r" +[-—] +",
                     h.replace("`", "").replace("*", ""))[0].strip()
            for h in re.findall(r"^#+ +(.*)$", read_text(path), re.M)}

def eval_docs():
    """{the name a citation writes: path} for every definitions page.
    DISCOVERED, not listed: these pages get split and renamed, and a hardcoded
    path is a test that keeps passing while the citation dangles. Lives under
    `evals/Definitions/` (and leftover `evals/*.md`), plus `Eval Template.md`,
    which owns the flag table."""
    root = os.path.join(sim.HERE, os.pardir)
    paths = (glob.glob(os.path.join(root, "Definitions", "*.md"))
             + glob.glob(os.path.join(root, "*.md")))
    out = {os.path.splitext(os.path.basename(p))[0]: p for p in sorted(paths)
           if not os.path.basename(p).startswith(".")}
    out["Eval Template"] = skills_path("eval-team", "Eval Template.md")
    return out

class DefinitionsVocabulary(unittest.TestCase):
    """The eval pages are cited by section instead of restated, and one of them
    owns the canonical flag table. Both halves only work if the citations
    resolve, since a `§Delta w` that names no section sends the reader looking
    for a definition that is not there, and a flag code printed on a row but
    absent from the table is a vocabulary the rest of the repo cannot carry"""

    LEAGUE = skills_path("league-info", "SKILL.md")
    # Flag rows start lower-case (or a digit); column tables start Upper-case.
    # Names can be more than one token (`missed season`).
    FLAG_ROW = r"^\| `([a-z0-9][^`]*)` *\|([^|]*)\|"

    @classmethod
    def setUpClass(cls):
        cls.docs = {name: doc_sections(path)
                    for name, path in eval_docs().items()}
        cls.sources = sim_sources()
        owners = [path for path in eval_docs().values()
                  if len(re.findall(cls.FLAG_ROW, read_text(path), re.M)) > 1]
        assert len(owners) == 1, (
            "%d eval pages carry the canonical flag table: it has one owner "
            "and the codes travel with the row" % len(owners))
        cls.text = read_text(owners[0])

    def cited(self, pattern):
        """{(page cited, section cited): file that cites it}, over every
        source. The page is "" where the citation names none"""
        out = {}
        for path, text in self.sources.items():
            for m in re.findall(pattern, text):
                doc, name = m if isinstance(m, tuple) else ("", m)
                # A citation wraps across lines wherever the sentence does
                doc, name = one_line(doc), one_line(name)
                # `Delta w` and `Delta P(title)` are printed in ASCII by
                # reports that cannot rely on a UTF-8 terminal
                name = name.rstrip(".,:").replace("Delta ", "Δ").replace(
                    "Delta P", "ΔP")
                out[(doc, name)] = os.path.basename(path)
        return out

    def test_every_section_sim_cites_is_a_section_that_exists(self):
        """A citation names its page and runs to the closing backtick rather
        than to the first space, since the pages carry multi-word headings and
        stopping at the space checks a section name nobody wrote. Every
        citation has to be inside the backticks for that to hold, so the two
        counts are compared rather than assumed"""
        cited = self.cited(r"`(Eval [^§`]+)§([^`]+)`")
        self.assertTrue(cited, "nothing cites the eval pages any more")
        for text in self.sources.values():
            self.assertEqual(len(re.findall(r"`Eval [A-Za-z]+ §", text)),
                             len(re.findall(r"Eval [A-Za-z]+ §", text)),
                             "a citation outside backticks is not checked")
        for (doc, name), where in cited.items():
            with self.subTest(page=doc, section=name, file=where):
                self.assertIn(doc, self.docs)
                self.assertIn(name, self.docs[doc])

    def test_a_bare_section_mark_names_a_section_of_a_file_that_owns_one(self):
        """A `§` with no file in front of it is the same citation with the file
        named a sentence earlier, and it goes stale the same way -- so it is
        checked against every file this code cites by section, not skipped for
        being short.

        Section names carry spaces and the sentence carries on past them, so a
        citation resolves when some leading run of its words is a heading"""
        owned = set(doc_sections(self.LEAGUE))
        for sections in self.docs.values():
            owned |= sections
        for (_, name), where in self.cited(r"§([A-Za-z][^`\n]*)").items():
            words, heads = name.split(), set()
            for i in range(len(words)):
                head = " ".join(words[:i + 1])
                heads |= {head, re.sub(r"(?:'s)?[).,:;\"]*$", "", head)}
            with self.subTest(section=name, file=where):
                self.assertTrue(heads & owned, "%s cites no section that "
                                "exists" % name)

    def test_the_flag_legend_and_the_canonical_table_are_the_same_vocabulary(self):
        """Both directions. A code the table prints and `Eval Template` does not
        define cannot be carried into an eval, and a code it sources FROM
        `sim.py players` that this table never prints is a row the eval author
        is told to read off a report that does not emit it"""
        canon = dict(re.findall(self.FLAG_ROW, self.text, re.M))
        out = render("players")
        legend = set(re.findall(r"`([a-z]\w*)`", out[out.index("flag column"):]))
        # Table names flags in prose (`fragile`); the report prints codes
        # (`frag`). A code is accounted for as a table key, an alias, or a
        # mention in a description (`rotN` on the `Nyr role` row).
        aliases = {"frag": "fragile", "miss": "missed season",
                   "nopool": "no GP history", "fa": "free agent",
                   "noproj": "no projection"}
        blob = " ".join(canon) + " " + " ".join(canon.values())
        for code in legend:
            with self.subTest(flag=code):
                self.assertTrue(
                    aliases.get(code, code) in canon or code in blob,
                    "%s is not a row or a mention in Eval Template §Flags"
                    % code)
        for name, desc in canon.items():
            if "sim.py players" not in desc:
                continue
            for code in re.findall(r"`([a-z]\w*)`", desc):
                if code in ("sim", "py", "players"):
                    continue
                with self.subTest(flag=code, row=name):
                    self.assertIn(code, legend)
