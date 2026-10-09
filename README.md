# From First Principles

Tutorials on one scientific paper at a time, each built on toys that run in the page. Published at https://pierre-aurelien.github.io/blog/.

The site is a [Quarto](https://quarto.org) website (Quarto 1.10.18). Posts live in `posts/<YYYY-MM>-<slug>/`, start from `_template/`, and compute every number they quote in their own `sims/` folder. The September 2026 posts are kept as standalone HTML in `legacy/`. Conventions, the style brief and the definition of done are in [CLAUDE.md](CLAUDE.md).

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
export QUARTO_PYTHON="$PWD/.venv/bin/python"
quarto preview
```

Pushing to `main` renders the site and publishes it to the `gh-pages` branch. Pull requests are rendered as a check, and the rendered site is attached to the run as the `site-preview` artifact.
