import unittest
from tests.harness import *

def sim_sources():
    paths = [sim.__file__] + sorted(
        glob.glob(os.path.join(sim.HERE, "simlib", "**", "*.py"),
                  recursive=True))
    return {p: re.sub(r"\n\s*#+ ?", " ",
                      re.sub(r'"\)?\s*\n\s*(?:print\()?"', " ", read_text(p)))
            for p in paths}

def doc_sections(path):
    return {re.split(r" +[-—] +",
                     h.replace("`", "").replace("*", ""))[0].strip()
            for h in re.findall(r"^#+ +(.*)$", read_text(path), re.M)}

def eval_docs():
    root = os.path.join(sim.HERE, os.pardir)
    paths = (glob.glob(os.path.join(root, "Definitions", "*.md"))
             + glob.glob(os.path.join(root, "*.md")))
    out = {os.path.splitext(os.path.basename(p))[0]: p for p in sorted(paths)
           if not os.path.basename(p).startswith(".")}
    out["Eval Template"] = skills_path("eval-team", "Eval Template.md")
    return out

class DefinitionsVocabulary(unittest.TestCase):
    LEAGUE = skills_path("league-info", "SKILL.md")

    @classmethod
    def setUpClass(cls):
        cls.docs = {name: doc_sections(path)
                    for name, path in eval_docs().items()}
        cls.sources = sim_sources()

    def cited(self, pattern):
        out = {}
        for path, text in self.sources.items():
            for m in re.findall(pattern, text):
                doc, name = m if isinstance(m, tuple) else ("", m)
                doc, name = one_line(doc), one_line(name)
                name = name.rstrip(".,:").replace("Delta ", "Δ").replace(
                    "Delta P", "ΔP")
                out[(doc, name)] = os.path.basename(path)
        return out

    def test_every_section_sim_cites_is_a_section_that_exists(self):
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

