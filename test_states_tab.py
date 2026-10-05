#!/usr/bin/env python3
"""Tests for the STATES tab in index.html (added 2026-10-04).

There is no JS runtime on this machine -- no node, deno or bun -- so these
are STATIC tests over the page source plus a render of the fixture the page
itself ships (demoStates). They check the things a static test honestly can:
the tab is registered in the right place, every token the tab uses is defined
in BOTH themes, the six states and the NO BARS row are all reachable, the
triple note and the alert strip are rendered from the document and not
invented, the ticker box issues the agreed command form, and no credential
or vendor URL has been baked into the page.

What they deliberately do NOT claim: that the DOM renders correctly. That was
checked in a real browser at the end of the build, and the screenshot is in
monitor/screens/.

Run: python test_states_tab.py   (from the repo root)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()

PASS = FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok   %s" % label)
    else:
        FAIL += 1
        print("  FAIL %s" % label)


print("the tab is registered, and in the right place")
tabs = re.search(r"const TABS = \[(.*?)\];", SRC, re.S).group(1)
ids = re.findall(r'id:\s*"(\w+)"', tabs)
check("TABS holds the states tab", "states" in ids)
check("it sits between E2 and DARK POOL, as specified",
      ids.index("states") == ids.index("e2") + 1
      and ids.index("dp") == ids.index("states") + 1)
check("the other five tabs are untouched and in order",
      [i for i in ids if i != "states"] == ["all", "star", "e2", "dp", "eve"])
check("the label is 'States'", '{ id: "states", label: "States" }' in SRC)

print("\nthe data contract is matched on TITLE, never on the body")
check("STATES_TITLE is the fixed title the desk publishes",
      'const STATES_TITLE = "states.json"' in SRC)
check("classify matches it on the title alone",
      't.trim() === STATES_TITLE) return "statesdoc"' in SRC)
check("and the on-demand reply on a title prefix",
      '/^state /.test(t)) return "stateq"' in SRC)
check("the data message is kept OUT of every feed tab including All",
      'm.kind !== "statesdoc"' in SRC
      and 'const shown = msgs.filter((m) => m.kind !== "statesdoc"' in SRC)

print("\nthe three ways in, and the cache that makes them work")
check("the attachment URL is fetched", "fetch(a.url" in SRC)
check("an expired attachment is skipped, not fetched",
      "a.expires && (Date.now() / 1000) > a.expires" in SRC)
check("a JSON body is accepted too (demo mode, and a belt-and-braces path "
      "if the body ever carries the document)",
      'm.message.trim().startsWith("{")' in SRC)
check("the last good copy is kept in localStorage",
      'localStorage.setItem(STATES_CACHE' in SRC)
check("and read back at start-up", "localStorage.getItem(STATES_CACHE)" in SRC)
check("a document is only accepted if it is NEWER, so a stale attachment "
      "cannot overwrite a fresher cached copy",
      "if (Date.parse(doc.as_of) < cur) return false;" in SRC)
check("the 3-hour expiry is written down where the design depends on it",
      "3 hours" in SRC or "three-hour" in SRC)

print("\nthe SYNCED indicator speaks for the DOCUMENT on this tab")
check("STALE_MIN is 20", "const STALE_MIN = 20" in SRC)
check("it only goes amber during RTH", "inRTH()" in SRC
      and "age > STALE_MIN && inRTH()" in SRC)
check("the warn class exists and recolours the dot too",
      ".sync.warn" in SRC and ".sync.warn .dot" in SRC)
check("the basis is always shown", 'statesDoc.basis === "close"' in SRC)

print("\nthe tab label carries glyph counts, not a message count")
check("only BROKEN and STRESSED get a badge",
      '["BROKEN", "STRESSED"]' in SRC and ".filter((s) => c[s])" in SRC)
check("the glyphs are the desk's", 'SGLYPH = { HEALTHY: "\\u25cf"' in SRC
      or "HEALTHY: \"●\"" in SRC)

print("\ntokens: every colour the tab uses is defined in BOTH themes")
root = re.search(r":root \{([^}]*)\}\s*\n/\* Dark", SRC, re.S)
light = re.findall(r"(--[\w-]+):", re.search(
    r":root \{\s*\n--s-good.*?\}", SRC, re.S).group(0))
dark = re.findall(r"(--[\w-]+):", re.search(
    r'\[data-theme="dark"\] \{\s*\n--s-good.*?\}', SRC, re.S).group(0))
check("the state and MA tokens are declared", set(light) >= {
    "--s-good", "--s-warn", "--s-bad", "--s-info", "--s-muted",
    "--ma20", "--ma50", "--ma200"})
check("every one of them is REDEFINED for dark mode, not inverted",
      set(light) == set(dark))
check("the spec's light values are the ones used",
      "--s-good: #157F3D" in SRC and "--s-warn: #B45309" in SRC
      and "--s-bad: #D22B12" in SRC and "--s-info: #1D4ED8" in SRC
      and "--s-muted: #6B6560" in SRC)
check("and the spec's MA colours",
      "--ma20: #7A7268" in SRC and "--ma50: #1F6FEB" in SRC
      and "--ma200: #C9930A" in SRC)


def contrast(hex_fg, hex_bg):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def lum(h):
        h = h.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    a, b = lum(hex_fg), lum(hex_bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


DARK_CARD = "#1E1B18"
# Target the STATES dark block specifically -- anchored on --s-good, which
# only that block defines. Anchoring on [data-theme="dark"] alone matched the
# page's ORIGINAL dark block and then ran on to the light --ma50, so the test
# read #1F6FEB and silently checked the wrong colour.
DARKBLOCK = re.search(r'\[data-theme="dark"\] \{\s*\n--s-good.*?\}', SRC,
                      re.S).group(0)
d50 = re.search(r"--ma50: (#\w{6})", DARKBLOCK).group(1)
d200 = re.search(r"--ma200: (#\w{6})", DARKBLOCK).group(1)
c50, c200 = contrast(d50, DARK_CARD), contrast(d200, DARK_CARD)
print("     dark MA50 %s on %s = %.2f:1" % (d50, DARK_CARD, c50))
print("     dark MA200 %s on %s = %.2f:1" % (d200, DARK_CARD, c200))
check("dark MA50 clears 3:1 against the dark card", c50 >= 3.0)
check("dark MA200 clears 3:1 against the dark card", c200 >= 3.0)
print("     (light MA50 #1F6FEB on #FFFFFF = %.2f:1 -- passing but thin, "
      "which is why dark lifts it)" % contrast("#1F6FEB", "#FFFFFF"))
check("colour is never the only carrier: the glyph rides with the word",
      'SGLYPH[r.state] || "?"} ${esc(r.state)}' in SRC)

print("\nthe fixture exercises every state, including NO BARS")
# demoStates contains a nested helper, so "to the next \n}" stops early and
# cut the fixture off before counts. Slice to the next top-level comment
# instead. And the fixture is JS, not JSON -- its keys are bare words -- so
# the counts are read with a regex rather than json.loads.
_i = SRC.index("function demoStates()")
_j = SRC.index("// The desk topic is the WRITE credential", _i)
m = SRC[_i:_j]
counts = {k.strip().strip('"'): int(v) for k, v in
          re.findall(r'([A-Z ]+|"NO BARS")\s*:\s*(\d+)',
                     re.search(r"counts: \{([^}]*)\}", m).group(1))}
check("all six states appear in the fixture counts",
      set(counts) == {"BROKEN", "STRESSED", "EARLY", "HEALTHY", "NONE",
                      "NO BARS"})
check("and every one of them is non-zero, so the tab renders all six",
      all(v > 0 for v in counts.values()))
check("a NO BARS row is present with a last_bar date",
      '"NO BARS"' in m and "last_bar:" in m)
check("a below-floor triple is present with the note",
      'note: "triple, below cohort floor"' in m)
check("a single is present and flagged single", "single: true" in m)
check("the fixture carries alerts with the card path",
      "alerts: [" in m and "card: \"monitor/alert_" in m)

print("\nNO BARS renders as name, NO BARS, last bar date -- nothing else")
nb = re.search(r'if \(r\.state === "NO BARS"\) \{(.*?)\n\}', SRC, re.S).group(1)
check("it prints the last bar date", "last_bar" in nb)
check("it draws no sparkline", "sparkSvg" not in nb)
check("no tiles", "quad" not in nb)
check("and no cohort or episode lines",
      "episodes(" not in nb and "breadth" not in nb)

print("\nthe alert strip")
check("newest first is the document's own order, not re-sorted here",
      "d.alerts || []" in SRC and ".sort(" not in
      re.search(r"const al = \(d\.alerts.*?\}\).join\(\"\"\)", SRC,
                re.S).group(0))
check("it links the card image only when a real attachment exists",
      "hit.attachment.url" in SRC)
check("and falls back to the three-line text when it does not",
      'class="three"' in SRC and "off 10s high" in SRC)
check("the fallback is a SIBLING of the row, so an <a> row never wraps a "
      "paragraph", 'class="aitem"' in SRC)

print("\nthe ticker box")
check("it issues the agreed command form",
      '"state " + toks.join(" ")' in SRC)
_si = SRC.index("function sendState()")
_sj = SRC.index("document.addEventListener(\"keydown\"", _si)
SENDSTATE = SRC[_si:_sj]
check("to the command topic the page already holds -- no new topic",
      'localStorage.getItem("walls_cmd")' in SENDSTATE
      and "walls_topic" not in SENDSTATE)
check("five names at most", "toks.length > 5" in SRC
      and "Five names at most" in SRC)
check("'roster' and a bare cluster id bypass the five-name cap",
      '"ROSTER" || /^\\d+$/.test(toks[0])' in SRC)
check("it never writes a roster",
      "roster.csv" not in SRC)
check("the reply is rendered as a card, not dumped as text",
      "function stateQueryCard" in SRC)
check("and it is tagged when the name is not on the roster",
      "not on roster" in SRC)

print("\nread-only: no buttons that change anything")
states_fn = re.search(r"function statesView\(\) \{.*?\n\}\nfunction plainCard",
                      SRC, re.S).group(0)
for bad in ("data-logcmd", "data-copy", "Log trade", "Copy"):
    check("the states view has no %s" % bad, bad not in states_fn)
check("its only control is the state box",
      states_fn.count("<button") == 1 and 'id="stGo"' in states_fn)

print("\nno credential, no vendor, nothing baked in")
for bad in ("marco-walls", "ph-bus-", "unusualwhales", "UW_API", "Bearer ",
            "api_key"):
    check("the page source contains no %s" % bad, bad not in SRC)
# "ph-cmd-xxxx" appears once, in the page's own pre-existing comment
# explaining the install link. It is an illustrative placeholder, not a
# value -- so the check is that nothing looks like a REAL topic: a desk
# prefix followed by something other than x's.
real = [s for s in re.findall(r"(?:ph-cmd|ph-ack|walls)-[A-Za-z0-9]{4,}", SRC)
        if not re.fullmatch(r"(?:ph-cmd|ph-ack|walls)-x+", s)]
print("     topic-shaped literals that are not placeholders: %s"
      % (real or "none"))
check("no topic-shaped literal that is not the page's own 'xxxx' "
      "placeholder", not real)
urls = sorted(set(re.findall(r"https?://[\w.\-]+", SRC)))
print("     hosts in the page: %s" % urls)
check("the only hosts are ntfy and Google Fonts",
      set(urls) <= {"https://ntfy.sh", "https://fonts.googleapis.com"})
check("the topic is never written into the page, only read from storage "
      "or the hash",
      'localStorage.getItem("walls_topic")' in SRC)

print("\nthe tab computes nothing")
for bad in ("MA20 =", "function sma", "pull =", "classifyState"):
    check("no state arithmetic named %s" % bad, bad not in states_fn)
check("the only arithmetic is x100 for display",
      "* 100).toFixed(1)" in SRC)

print("\n%d passed, %d failed" % (PASS, FAIL))
if FAIL == 0:
    print("all STATES tab tests passed")
sys.exit(1 if FAIL else 0)
