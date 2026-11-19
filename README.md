# Agents in computational research

A small, static companion to a university talk on 19 November 2026. It explains a layered model of coding agents and gives a Linux-workstation sandbox recipe and setup guide using T3 Code, in a human and an agent version.

The page is published at <https://comphy-lab.org/agents-in-research/>.

## Layout

```
site/                 deployed to GitHub Pages
  index.html          the page
  site.css            page styles (design-system tokens only)
  setup-toggle.js     human/agent switch and copy button for the setup section
  js/                 theme toggle and header menu (vendored)
  vendor/ds/          CoMPhy design-system tokens and fonts (vendored)
  vendor/comphy-lab/  comphy-lab.org header and footer styles and logos (vendored)
tools/check_site.py   static site check
tests/                checker and vendored-file tests
VENDOR.md             where the vendored files come from
vendor-manifest.json  source commits and SHA-256 of every vendored file
```

The page follows the [CoMPhy Lab design system](https://github.com/comphy-lab/comphy-design-system) and carries comphy-lab.org's header and footer, as the [talks site](https://github.com/comphy-lab/talks) does. See `VENDOR.md` before changing anything under `site/vendor/` or `site/js/`.

## View

Read it online, or preview it locally from this directory:

```sh
python3 -m http.server -d site 8000
```

then open <http://localhost:8000/>. The header and footer links point at comphy-lab.org pages, so they work only on the published site. Links to official documentation need internet access.

## Check

From this directory, run:

```sh
python3 -I tools/check_site.py
```

The checker uses only Python's standard library. It checks the published `site/` folder: HTML structure, duplicate IDs, local `href`/`src` targets and fragments, external script/stylesheet loads, and every `url()` and `@import` in the site's stylesheets (each resolved from its own folder). Every local target must lie inside `site/`, since nothing else is deployed. It lists external links without fetching them. Root-relative links such as `/team/` point at pages of comphy-lab.org, which serves this site under `/agents-in-research/`; they are listed, not checked, and a root-relative resource load is an error. This is a static check, not a full HTML standards validator, accessibility audit or verification of remote documentation.

Optionally supply a private, newline-separated list of forbidden terms:

```sh
FORBIDDEN_TERMS_FILE="$HOME/private-terms.txt" python3 -I tools/check_site.py
```

Keep that file outside the repository. Blank lines are ignored; other lines are literal, case-insensitive substrings. The checker scans UTF-8 text files in the repository, including decoded HTML text and attributes. It skips `.git`, ignored visual-check output, binary files and the supplied list itself. Diagnostics identify file, line and rule number without printing the private term. An unreadable list fails the check. Any printed link or diagnostic that would reveal a listed term is withheld.

Run the checker's regression tests and the vendored-file check with:

```sh
python3 -I -m unittest discover -s tests
```

## Content and evidence

Inline citations link to primary sources selected in the research fact sheet dated 17 November 2026. T3 documentation links are pinned to the inspected source snapshot; stable releases may differ. The layered model and loop are teaching schematics. Account isolation, network restrictions, hardware sizing and shared-HPC handling are recommendations. The sandbox recipe and both setup versions (human and agent, with Codex), as published on the morning of 19 November 2026, were tested end to end that day in fresh Ubuntu 26.04 virtual machines with T3 Code 0.1.10. The page was then revised for the problems found; only the background-job fix was tested separately, and the revised agent prompt has not been re-run end to end. The page states that scope.

Optional screenshots and temporary browser profiles belong in `.site-check/`, which is excluded from version control.

## Deploy

Every push to `main` runs `.github/workflows/pages.yml`. The workflow runs the site check, the checker's tests and the vendored-file check, then publishes `site/` to GitHub Pages; the README, tools and tests are not served. It can also be started by hand from the Actions tab. The private forbidden-terms check is not part of the workflow, so run it locally before pushing.

## Licence

- **Code** (`tools/`, `tests/`, `site/site.css`, `site/setup-toggle.js`, `site/js/`, the workflow and the page markup, except the third-party icons below): MIT, see `LICENSE`.
- **Third-party icons** inlined in the header, with full notices in `site/THIRD-PARTY-NOTICES.txt` (published beside the page): the theme-toggle moon and sun are [Feather](https://github.com/feathericons/feather) icons, MIT License, copyright 2013–2023 Cole Bemis. The GitHub and Bluesky icons are Font Awesome Free 6.7.2 by Fonticons, Inc., licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (copyright 2024 Fonticons, Inc.; see the [Font Awesome Free licence](https://fontawesome.com/license/free)). The Google Scholar icon is the `google-scholar` glyph of [Academicons](https://github.com/jpswalsh/academicons) 1.7.0, whose font is licensed under the SIL Open Font License 1.1. Their attribution comments are kept in `site/index.html`.
- **Text and diagrams** of the page: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Reuse them with credit to the CoMPhy Lab and a link to <https://comphy-lab.org/agents-in-research/>.
- **Fonts** in `site/vendor/ds/fonts/`: SIL Open Font License, see `OFL.txt` there.
- **Logos** (the CoMPhy Lab mark and the partner logos in the footer) are not covered by either licence; they belong to their owners.

Quoted product names and linked sources belong to their owners; the page cites them and does not relicense them.
