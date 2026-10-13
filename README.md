# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user types what they're shopping for in plain words, like 'vintage graphic tee under $30', optionally with a size. FitFindr searches 40 secondhand listings from Depop, Poshmark and thredUp, filters by price and size, and picks the best keyword match. It then suggests two outfits that pair the find with pieces from the user's own wardrobe, and writes a short social-media caption with the price and where to buy it. If nothing matches, it stops and tells the user what to change, like raising the price limit or using more general words.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->
### `search_listings`

- **What it does:** Searches the local clothing catalogue by description keywords, with optional size and maximum-price filters. Keywords are matched as whole words (case-insensitive) against each listing's title, description, category, style_tags and colors. Size matching is whole-token and case-insensitive: "M" matches "S/M", but "S" does not match "US 9" and "L" does not match "XL". The price limit is inclusive.
- **Inputs:** `description` (str — keywords, e.g. "vintage graphic tee"), `size` (str or None — None skips size filtering), `max_price` (float or None — None skips price filtering)
- **Returns:** `list[dict]` — matching listings with all 11 fields each (`brand` may be None), ranked by keyword score (matches in title, category, style_tags or colors count double; description-only matches count once), then by lower price, at most `config.SEARCH_RESULT_LIMIT` of them. Listings matching zero keywords are left out.

- **When it has nothing:** Returns an empty list `[]`, not `None` or an exception — whether no listing matches the keywords or the size/price filters rule out every match. The agent then tells the user nothing matched and stops.

### `suggest_outfit`

- **What it does:** Suggests two outfits built around a selected listing, using items from the user's wardrobe when available.
- **Inputs:** `new_item` (dict — one listing, all 11 fields), `wardrobe` (dict — has an `items` key holding a list of wardrobe items; the list may be empty)
- **Returns:** A non-empty `str` with exactly two numbered outfit suggestions. When the wardrobe has items, it names them using their `name` field exactly.
- **When it has nothing:** If the wardrobe is empty, it still returns two general outfit ideas, starting with a note that they are general because no wardrobe is saved. If the model can't be reached, the error is raised rather than returned as text, so the agent can report it.

### `create_fit_card`

- **What it does:** Writes a short social-media-style caption about the selected second-hand find and how it could be worn.
- **Inputs:** `outfit` (str — the result from `suggest_outfit` for that listing), `new_item` (dict — the listing the card is about, all 11 fields)
- **Returns:** A `str` of two to four sentences that includes the price written with digits (e.g. `$38`) and the listing's `platform`.
- **When it has nothing:** If `outfit` is empty or whitespace, returns the fixed message "Couldn't build a fit card for this listing." without calling the model or raising. If the model can't be reached, the error is raised so the agent can report it.
---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` saying what the user could change (fewer or more general words, a higher price limit, or no size filter) and stop, leaving `fit_card` as `None`. Otherwise, take the first result (best keyword match, cheapest on a tie), store it in `session["selected_item"]`, and go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex and string splitting, no model call (`agent.py::_parse_query`). A regex pulls the price ceiling from phrases like "under $30" into `max_price`, and a regex pulls a size like "size M" into `size`. The rest of the query is lowercased and split into words, filler words like "looking", "for" and "a" are dropped, and what's left becomes the description.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` (from `search_listings`) → `selected_item` (the first result) → `outfit_suggestion` (from `suggest_outfit`) → `fit_card` (from `create_fit_card`). If search finds nothing, `error` holds a message saying what to change, and the later fields stay `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   1. Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans, dark wash and chunky white sneakers for an effortless Y2K streetwear look.

2. Style the Y2K Baby Tee — Butterfly Print with the wide-leg khaki trousers, brown leather belt, and chunky white sneakers for a balanced vintage-casual outfit.

  Fit card: Scored this little butterfly print Y2K baby tee on depop for just $18 and I'm obsessed. Gives off the ultimate 2000s streetwear energy paired with some baggy dark wash denim and chunky sneakers. Honestly such a steal for the wardrobe rotation.

0 model calls this session, 2 served from cache
```


**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
1. Pair the Vintage Levi's 501 Jeans — Medium Wash with the White ribbed tank top, Chunky white sneakers, and Black crossbody bag for a casual everyday look.
2. Combine the Vintage Levi's 501 Jeans — Medium Wash with the Oversized grey crewneck sweatshirt, Black combat boots, and Brown leather belt for a cozy streetwear-inspired outfit.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501 jeans on depop for only $38 and I am never taking them off. The medium wash gives off the ultimate effortless, off-duty model vibe. Just paired them with crisp white sneakers and honestly, nothing beats a true vintage fit.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to check my state criterion (criterion 3). My draft said the selected item should show up as an option in the suggested outfit.
- *What came back:* It pointed out that the model can reword item names, so I couldn't check it without interpretation, and that if the wrong listing reached suggest_outfit, the outfit would still mention "the item" and the check would pass anyway.
- *What I changed:* I rewrote the criterion to compare `session["selected_item"]["id"]` against the id of the listing suggest_outfit received, and set the target to 5 of 5, since no model is involved.

**Moment 2**

- *What I asked for:* I tested `search_listings('graphic tee', max_price=30)` and asked Claude to check the output.
- *What came back:* All prices were under $30, but the first result was a black mesh top, not a graphic tee. It ranked first because its description says "layering under a graphic tee", which tied it with the real tees, and it was the cheapest.
- *What I changed:* I kept the scoring, since it matches my spec (keyword count, then lower price), and recorded it as a known weakness to fix in unit 4. With a full query like "vintage graphic tee", the real graphic tee ranks first.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools and returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. No-match query stops before suggest_outfit with a message naming what to change | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. session["selected_item"]["id"] equals the id suggest_outfit received | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card mentions the listing's platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every search result is at or under the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try**
From `results/run_2026-10-12_1647_before.md`, produced by `agent.py::run_agent` (search via `mcp_server.py::search_listings` → `tools.py::search_listings`):

```
# Criterion 1 — matching query completes (try 1)
[2] search_listings (via MCP)   out: 10 items, highest price $26, first lst_002
[3] suggest_outfit              in:  new_item=lst_002, wardrobe_items=10
[4] create_fit_card             out: Found this lil butterfly print baby tee scrolling on depop at 2 AM and couldn't pass it up for $18. Currently …
  try 1: completed — fit card 230 chars

# Criterion 2 — impossible query stops early (try 1)
[2] search_listings (via MCP)   out: [] (empty)
[3] stop                        out: No listings matched 'designer ballgown' in size XXS under $5. To widen the search, try fewer or more general w…
  try 1: stopped early — No listings matched 'designer ballgown' in size XXS under $5

# Criterion 3 — selected item reaches suggest_outfit (try 1)
[2] search_listings (via MCP)   out: 6 items, highest price $48, first lst_035
[3] suggest_outfit              in:  new_item=lst_035, wardrobe_items=10

# Criterion 4 — fit card mentions platform (try 1)
[4] create_fit_card             out: Finally tracked down this cropped light wash denim jacket on poshmark for $42 and my outfit planning is offici…

# Criterion 5 — price ceiling respected (try 1)
[1] parse_query                 in:  graphic tee under $30
[2] search_listings (via MCP)   out: 7 items, highest price $27, first lst_017
```


---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes and returns a fit card | 4 of 5 | MET (5/5) | All 5 tries ended "completed — fit card ___ chars" |
| 2 | No-match query stops before suggest_outfit, naming what to change | 5 of 5 | MET (5/5) | All 5 traces end at [3] stop with no suggest_outfit step, and the message lists what to change |
| 3 | selected_item id equals the id suggest_outfit received | 5 of 5 | MET (5/5) | In all 5 tries, search's "first lst_035" matched suggest_outfit's "new_item=lst_035" |
| 4 | Fit card mentions the platform | 4 of 5 | MET (5/5) | "poshmark" appears in all 5 fit cards |
| 5 | Every search result is at or under the ceiling | 5 of 5 | MET (5/5) | Search trace showed "highest price $27" against a $30 ceiling in all 5 tries |

**Diagnoses**

All five criteria were met. However, for the query "graphic tee under $30", a graphic tee was not selected in any of the 5 tries. Instead, tools.py::search_listings picked the mesh top, which was the cheapest and whose description says it can be layered under a graphic tee. Keywords in the description were scored the same as keywords in the title, so the search ranked the mesh top highly, and it won because its price was lower than the graphic tees'.

My targets were too low: all five criteria were met, but the wrong item was still selected, because criterion 5 only checked the price. I would tighten criterion 5 so that it also checks that the first result has "tee" in its title or tags. With that check, the mesh top would have failed in all 5 tries.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask 'white sneakers under $70'
[1] parse_query
      in:  white sneakers under $70
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 6 items: lst_035…
[3] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      out: 1. Pair the Low-Top Canvas Sneakers — Off-White with the baggy straight-leg jeans, dark wash, the white ribbed…
[4] create_fit_card
      in:  dict with keys: new_item, outfit
      out: Scored these off-white canvas sneakers on poshmark for only $20 and they are about to be my entire personality…

  Found:    Low-Top Canvas Sneakers — Off-White — $20.0 on poshmark

  Outfit:   1. Pair the Low-Top Canvas Sneakers — Off-White with the baggy straight-leg jeans, dark wash, the white ribbed tank top, and the vintage black denim jacket for a casual streetwear look.
2. Style the Low-Top Canvas Sneakers — Off-White with the wide-leg khaki trousers, the oversized grey crewneck sweatshirt, and the brown leather belt for an effortless earth-tone outfit.

  Fit card: Scored these off-white canvas sneakers on poshmark for only $20 and they are about to be my entire personality. They bring that perfect worn-in, effortless energy to both baggy denim streetwear fits and oversized neutral loungewear. Seriously obsessed with how easy they are to style.

2 model calls this session, 573 prompt + 143 output tokens
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] stop
      in:  no search results
      out: No listings matched 'designer ballgown' in size XXS under $5. To widen the search, try fewer or more general w…

  No listings matched 'designer ballgown' in size XXS under $5. To widen the search, try fewer or more general words (e.g. 'dress' instead of 'designer ballgown'); or raise your price limit; or drop the size filter.

0 model calls this session
```

**On the MCP move:** 
I registered `search_listings` in `mcp_server.py` with a description written for an outside agent, and confirmed it with `python mcp_client.py`. In `agent.py::run_agent` I replaced the direct `search_listings(...)` call with `call_tool("search_listings", {...})`. Both paths behaved the same afterwards: the happy path still picked the Y2K Baby Tee ($18, depop), and the no-match query still stopped with the same message. So the tool was already returning a plain list of listing dicts, which MCP passed through unchanged.


**Failure modes, triggered on purpose**

*Empty search*: `python app.py ask 'designer ballgown size XXS under $5'`
```
No listings matched 'designer ballgown' in size XXS under $5. To widen the search, try fewer or more general words (e.g. 'dress' instead of 'designer ballgown'); or raise your price limit; or drop the size filter.

0 model calls this session
```
Handled by the branch in `agent.py::run_agent`. It stops before `suggest_outfit`.

*Empty wardrobe*: `python app.py ask 'vintage graphic tee under $30' --empty-wardrobe`
```
Outfit:   No wardrobe saved, so these are general styling ideas:

1. Pair the baby tee with low-rise medium-wash flare jeans, white platform sneakers, and a pink shoulder bag for a quintessential Y2K mall-rat look.
2. Layer the top over a tiered white lace midi skirt with chunky black combat boots and a beaded choker for a sweet cottagecore-grunge contrast.
```
Handled in `tools.py::suggest_outfit`. It returns general ideas instead of crashing or returning "".

*Model unavailable* (one character of the key changed):

Before the handler, `run_agent` crashed and `app.py` printed only:
```
ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```
The search result was lost. I added a `try/except ModelUnavailable` around both model steps in `agent.py::run_agent`. After the handler, `python app.py ask 'striped long sleeve top size M under $45'` printed:
```
Found Mesh Long-Sleeve Top — Black, but couldn't reach the model to suggest outfits (The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.). Check GEMINI_API_KEY in your .env file and your internet connection, then try again.

1 model calls this session
```


---

## The Improvement

**What I changed:** In `tools.py::search_listings`, keyword matches in a listing's title, category, style_tags or colors now count double, and matches that appear only in the description count once. Before, every match counted the same no matter where it appeared.

**Which failure it was meant to fix:** In the before run, the query "graphic tee under $30" picked the Mesh Long-Sleeve Top (lst_017) in all 5 tries. Its title says it's a mesh top, but its description mentions "layering under a graphic tee", so it tied with the real graphic tees and won on price ($15).

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools and returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. No-match query stops before suggest_outfit with a message naming what to change | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. session["selected_item"]["id"] equals the id suggest_outfit received | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card mentions the listing's platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every search result is at or under the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** Yes, for the problem it targeted. In the after run (`results/run_2026-10-12_1701_after.md`), "graphic tee under $30" picked the Y2K Baby Tee (lst_002) instead of the mesh top in all 5 tries; the trace line changed from "first lst_017" to "first lst_002". The other scenarios picked the same items as before, so nothing got worse. My five criteria didn't change (all MET before and after), because none of them checks which item is picked, which is why I'd tighten criterion 5 as described in my diagnosis.



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

## Milestone 1 notes
- A listing has 11 fields; key ones for search: price, category, style_tags
- A wardrobe item has 6 fields; it shares category, colors and style_tags with listings
- Listings are items for sale; the wardrobe is what the user already owns
