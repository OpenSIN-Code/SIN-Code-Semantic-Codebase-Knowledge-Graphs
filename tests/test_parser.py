from sin_code_sckg.parser import SemanticParser
from sin_code_sckg.graph import KnowledgeGraph
import tempfile, os


def test_parse_python():
    parser = SemanticParser(["python"])
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def hello():
    \"\"\"Docstring\"\"\"
    print("hi")

def user():
    hello()

class Service:
    def run(self):
        user()
""")
        f.flush()
        symbols = parser.parse_file(f.name)
    os.unlink(f.name)
    names = {s.name for s in symbols}
    assert "hello" in names
    assert "user" in names
    assert "Service" in names


def test_graph_build():
    parser = SemanticParser(["python"])
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a.py")
        with open(p, "w") as f:
            f.write("def a():\n    b()\ndef b():\n    pass\n")
        kg = KnowledgeGraph()
        stats = kg.build_from_repo(d, exclude=[], include_intents=False)
        assert stats["symbols"] >= 2
        assert stats["edges"] >= 1
