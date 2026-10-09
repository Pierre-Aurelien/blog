# From First Principles

Tutorials on one scientific paper at a time, each built on toys that run in the page. Published at https://pierre-aurelien.github.io/blog/.

The site is a [Quarto](https://quarto.org) website (Quarto 1.10.18). Posts live in `posts/<YYYY-MM>-<slug>/`, start from `_template/`, and compute every number they quote in their own `sims/` folder. The September 2026 posts are kept as standalone HTML in `legacy/`. Conventions, the style brief and the definition of done are in [CLAUDE.md](CLAUDE.md).

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
export QUARTO_PYTHON="$PWD/.venv/bin/python"
quarto preview
```

Pushing to `main` renders the site and publishes it to the `gh-pages` branch. Pull requests are rendered as a check, and the rendered site is attached to the run as the `site-preview` artifact.

## Previewing a pull request before merging

Previews are private: nothing is published until the pull request is merged. Use either of these.

**Render the branch locally.**

```sh
git fetch origin && git checkout <branch>
export QUARTO_PYTHON="$PWD/.venv/bin/python"
quarto preview          # opens the site in your browser and reloads on every edit
```

**Or open what CI rendered.** On the pull request, open the "Publish" check, then "Summary", and download the `site-preview` artifact at the bottom of the page. With the GitHub CLI, run `gh run download --name site-preview --dir site-preview`. Then serve the folder, because the pages do not work when opened directly as files:

```sh
unzip -o site-preview.zip -d site-preview   # skip if gh already unpacked it
python3 -m http.server --directory site-preview 8000
```

and open http://localhost:8000.
