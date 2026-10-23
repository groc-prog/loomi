# Documentation guide

> [!IMPORTANT]
> Good documentation is the first step to ensuring anyone can use this package. Thank you for helping make loomi's docs clearer, more accurate, and easier to use.

This guide walks you through how our documentation is structured and how to make changes to it.

## Where documentation lives

All documentation source files live in the `docs/` folder:

```
docs/
├── index.md                    # Main docs entry point
├── getting-started.md          # Quickstart guide
├── user-guide/                 # Guides for the package and its components
└── contribution-guide/         # Contribution documentation
    ├── index.md
    ├── dev-setup.md
    └── documentation-guide.md  # <- You are here
```

## General guidelines

To keep the docs clean and consistent when rendered on GitHub, follow these rules:

- **Proofread your changes.** It sounds obvious, but make sure what you wrote actually makes sense.
- **Use sentence case for headings.** Write "Getting started", not "Getting Started".
- **Use fenced code blocks with language tags.** For example, ` ```python ` for Python snippets.
- **Keep callouts GitHub-compatible.** Use `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, and `> [!WARNING]` — these render natively on GitHub.
- **Prefer relative links.** Link to other docs with relative paths (e.g., `./dev-setup.md`) so links keep working if the docs are moved or hosted elsewhere.

## Checklist before opening a pull request

Before submitting your documentation pull request:

- [ ] Have you previewed your Markdown changes to ensure headings, formatting, and tables render correctly?
- [ ] Are all internal links working and pointing to valid files?
- [ ] Are code snippets accurate, correctly formatted with language tags, and verified to work when run?
- [ ] Have you checked spelling and grammar?

