# Demo Research Workspace

This is a minimal Research OS hub with one project and one fake paper source.

The Obsidian starter vault is at:

```text
examples/demo-research-workspace/obsidian/starter-vault
```

Open that folder in Obsidian to see `Home.md`, the project note, paper notes, and concept notes linked in Graph View.

Try:

```bash
python -m research_os.cli validate --hub examples/demo-research-workspace
python -m research_os.cli build-graph --hub examples/demo-research-workspace
python -m research_os.cli build-index --hub examples/demo-research-workspace
```
