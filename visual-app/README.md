# Research OS Visual App

React Flow source for the static Research OS visual explorer.

Development:

```bash
npm install
npm run dev
```

Build the end-user template:

```bash
npm run build
```

The build inlines the Vite assets into `src/research_os/visual_template.html`.
`research-os build-visual` then injects the hub `graph.json` into that template,
so ordinary Research OS users do not need Node.js.
