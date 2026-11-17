# Vendored design system and site shell

The page follows the [CoMPhy Lab design system](https://github.com/comphy-lab/comphy-design-system) and carries comphy-lab.org's header and footer, in the same way as the [talks site](https://github.com/comphy-lab/talks). `vendor-manifest.json` records the source commits and the SHA-256 of every vendored file. `tests/test_vendor.py`, which runs in CI before every deploy, fails if a vendored file is changed, missing or unlisted.

| Here | From | Role |
| --- | --- | --- |
| `site/vendor/ds/tokens.css`, `fonts/` | `comphy-lab/comphy-design-system` at `d94af97`, copied from `comphy-lab/talks` `site/vendor/ds/` (byte-identical) | Colour, type, spacing, radius and shadow tokens for light and dark; self-hosted fonts (SIL Open Font License, `fonts/OFL.txt`) |
| `site/vendor/comphy-lab/` | `comphy-lab/talks` `site/vendor/comphy-lab/` at `bf0585c` | comphy-lab.org header and footer styles and logos. Their own provenance is in the talks repository's `site/vendor/comphy-lab/SOURCE.md` |
| `site/js/theme.js`, `site/js/header.js` | `comphy-lab/talks` `site/player/theme.js` and `header.js` at `bf0585c` | Theme bootstrap and toggle (shared `theme` storage key); header menu drawer, back-to-top and year |
| Header and footer markup in `site/index.html` | `comphy-lab/talks` `site/index.html` at `bf0585c` | Adapted by hand, not hash-checked; differences below |

Page styles live in `site/site.css`. They use tokens through `var()` and never redefine one. A few dark-theme colours repeat values that `tokens.css` itself uses for dark variants (prose links, eyebrows, brand chips).

## Differences from the talks shell

- No header item is marked `aria-current`, because this page is not one of the main site's navigation sections.
- "Edit on GitHub" points at this repository.
- The header carries attribution comments for its third-party icons: Feather (theme-toggle moon and sun; MIT, Cole Bemis), Font Awesome Free 6.7.2 (GitHub, Bluesky; icons CC BY 4.0) and Academicons 1.7.0 (Google Scholar; font SIL OFL 1.1). `site/THIRD-PARTY-NOTICES.txt` holds their full notices and is published with the page. The talks repository records the Font Awesome and Academicons sources in its `site/vendor/comphy-lab/SOURCE.md`; it attributes the moon and sun only to comphy-lab.org's header, and their paths match Feather's `moon.svg` and `sun.svg` exactly.
- `header.js` is unchanged. Its talk-player hooks (closing the drawer when the header becomes inert) are inactive here.

## Refreshing

Copy the files byte for byte from a newer commit of the source repository, update the commit in `vendor-manifest.json` (and, for the design system, `site/vendor/ds/SOURCE_COMMIT`), regenerate the file hashes, and review the diff. Never edit a vendored file in place; put page styles in `site/site.css`.
