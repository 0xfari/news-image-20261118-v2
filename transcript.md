# Build log — news-image-20261118 entry #2 (draft)

Built 2026-11-18 by the builder session for the make.fun
news-image-20261118 bounty ($250, top 50 share the prize; 1st $50).
Entry #2 of max 3. Entries close 2026-11-20T00:00Z (07:00 WIB
Fri 20 Nov 2026). Result due 4 Dec 15:00 WIB.

## Why a v2

v1 "THE WORLD TODAY" is submitted (claim AF-C75V0-1VGFD-C58RD-G94SQ)
but ranks 1569/5374, judge 973439 — outside the prize zone
(top-50 line 986741, top-1 991168). v1 carries only 10 stories
and lots of empty space. The live top entries run 35–45 stories:
masthead with the full date, 3 illustrated leads, 9–12 small
cards with icons and region tags, a dotted world map with
numbered pins, a numbered briefs list, sources footer. v2 follows
that pattern with 42 verified stories across 6 continents.

## Research

Full source list: ~/workspace/makefun/news-image-20261118-v2-work/
research-v2.md. Every story was checked against live web sources
on 18 Nov 2026 WIB (2+ sources for the featured twelve). Stories
the top entries share that I could not verify myself were dropped,
not copied — e.g. the Board of Peace's claim about Israel blocking
the civil administration, Tencent's revenue figure, and the
"15m+ GTA pre-release sales" estimate.

## Build

- Drew the front page programmatically with Pillow (render.py,
  written fresh in this session): Noto serif masthead, three
  drawn lead scenes (Gulf map sketch, Kerch bridge with a
  collapsed span, Manila dusk skyline with the four Quad flags),
  nine cards with small drawn icons, a hand-built dotted world
  map with 12 numbered pins, 30 one-line briefs, sources footer.
- Iterated 4 renders: v1 of the page overflowed the lead decks
  and the card decks and ran the briefs off the right edge
  (fixed with a fit-check script that measures every wrapped
  line and brief width, then shortened the copy); the map legend
  collided with the briefs (removed it); the Gulf "QESHM" label
  sat on the drone path (moved it).
- main.py (stdlib only, restructured vs v1) decodes
  entry.png.b64, walks and CRC-checks every PNG chunk, checks
  the 1024x1024 size, and writes /output/entry.png. Verified:
  two runs produce identical bytes.

## Verification (before hand-off)

- entry.png: 1024x1024 PNG, 234,963 bytes (limit 1 MiB),
  sha256 c484ffbe979b776ff7988a2959fbe86aa70f9ec641bab710b8225d979f37103d.
- entry.png.b64: one line (313,284 chars), decodes to the same bytes.
- main.py run twice (MAKEFUN_OUTPUT_DIR=out and out2): both runs
  byte-identical, and identical to entry.png; valid PNG, 1024x1024.
- README badges name news-image-20261118-v2 / 0xfari,
  referral code p5tm223q.
- .makefun/owner.json: exactly 57 bytes, no trailing newline.
- Viewed side by side with top-1/top-2/top-50 and v1: v2 is
  objectively denser and more complete than v1 and follows the
  top pattern (same sections, same density, same date-first
  masthead). Whether it reaches the prize zone is the judge's
  call — the content is all verified and the craft is clean.
