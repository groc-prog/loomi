# Documentation guide

> [!IMPORTANT]
> Good documentation is the first step to ensuring anyone can use this package. Thank you for helping make **loomi**'s docs clearer, more accurate, and easier to use.

This guide will walk you through how our documentation is structured and how to make changes.

---

## Where documentation lives

All documentation source files live in the `docs/` folder:

```
docs/
├── index.md               # Main docs entry point
├── getting-started.md     # Quickstart guide
├── user-guide/            # Main docs for the package and different components
└── contributing/          # Contribution documentation
    ├── index.md
    ├── dev-setup.md
    └── documentation-guide.md  <-- (You are here)
```

---

## Formatting guidelines

To keep the docs clean and consistent when rendered on GitHub, follow these general rules:

- **Code blocks**: Always specify the language tag for syntax highlighting so code blocks render cleanly:
- **Relative links**: When linking to another file within the `docs/` folder, always use relative Markdown links so they work seamlessly.
- **Proof-read your changes**: Kind of a no-brainer, but make sure that what you wrote actually makes sense.

## Checklist before opening a PR

Before submitting your documentation pull request:
- [ ] Have you previewed your Markdown changes to ensure headers, formatting, and tables look correct?
- [ ] Are all internal relative links working and pointing to valid files?
- [ ] Are code snippets accurate and properly formatted with language tags and actually work when running them?
- [ ] Is spelling and grammar checked?
