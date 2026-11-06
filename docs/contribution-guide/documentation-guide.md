# Documentation guide

> [!IMPORTANT]
> Clear documentation helps people get comfortable with the package. Thanks for helping us make loomi's docs easier to follow and more accurate.

Here is a quick tour of where the docs live and how you can update them.

## Where documentation lives

You will find all documentation source files in the `docs/` folder:

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

These tips help the docs read well and render consistently on GitHub:

- **Give your changes a quick read.** Check that each explanation makes sense and is easy to follow.
- **Use sentence case for headings.** Write "Getting started", not "Getting Started".
- **Add a language tag to fenced code blocks.** For example, use ` ```python ` for Python snippets.
- **Use GitHub-compatible callouts.** The `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, and `> [!WARNING]` styles render natively on GitHub.
- **Prefer relative links.** Link to other docs with relative paths, such as `./dev-setup.md`. They keep working if the docs move or are hosted elsewhere.

## Checklist before opening a pull request

Before you open a pull request with documentation changes, take a moment to check:

- [ ] Preview the Markdown and check that headings, formatting, and tables look right.
- [ ] Follow each internal link and make sure it points to an existing file.
- [ ] Check that code snippets are accurate, tagged with the right language, and work as expected.
- [ ] Read through once more for spelling and grammar.

