
def test_gitignore_template():
    from asutils.repo import GITIGNORE_TEMPLATE
    assert "__pycache__/" in GITIGNORE_TEMPLATE
    assert ".venv/" in GITIGNORE_TEMPLATE

def test_agents_template():
    from asutils.repo import AGENTS_TEMPLATE
    assert "bd" in AGENTS_TEMPLATE
