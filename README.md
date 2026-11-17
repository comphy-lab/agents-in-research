# Agents in computational research

A small, static companion to a university talk on 19 November 2026. It explains a layered model of coding agents and gives a general Linux-workstation setup guide using T3 Code.

The page is published at <https://comphy-lab.org/agents-in-research/>. No licence has been chosen yet.

## View

Read it online, or open `index.html` in a browser. No server, build step, package installation or internet connection is needed to read the page. Links to official documentation need internet access. Styles and the original SVG schematic are inline; no third-party logos or assets are included.

## Check

From this directory, run:

```sh
python3 -I tools/check_site.py
```

The checker uses only Python's standard library. It checks HTML structure, duplicate IDs, local `href`/`src` targets and fragments, and external script/stylesheet loads. It lists external links without fetching them. This is a static check, not a full HTML standards validator, accessibility audit or verification of remote documentation.

Optionally supply a private, newline-separated list of forbidden terms:

```sh
FORBIDDEN_TERMS_FILE="$HOME/private-terms.txt" python3 -I tools/check_site.py
```

Keep that file outside the repository. Blank lines are ignored; other lines are literal, case-insensitive substrings. The checker scans UTF-8 text files in the repository, including decoded HTML text and attributes. It skips `.git`, ignored visual-check output, binary files and the supplied list itself. Diagnostics identify file, line and rule number without printing the private term. An unreadable list fails the check. Any printed link or diagnostic that would reveal a listed term is withheld.

Run the checker's own regression tests with:

```sh
python3 -I -m unittest discover -s tests
```

## Content and evidence

Inline citations link to primary sources selected in the research fact sheet dated 17 November 2026. T3 documentation links are pinned to the inspected source snapshot; stable releases may differ. The layered model and loop are teaching schematics. Account isolation, network restrictions, hardware sizing and shared-HPC handling are recommendations. Installation commands were transcribed from documentation, not executed as part of building the site.

Optional screenshots and temporary browser profiles belong in `.site-check/`, which is excluded from version control.

## Deploy

Every push to `main` runs `.github/workflows/pages.yml`. The workflow runs the site check and the checker's tests, then publishes `index.html` alone to GitHub Pages; the README, tools and tests are not served. It can also be started by hand from the Actions tab. The private forbidden-terms check is not part of the workflow, so run it locally before pushing.
