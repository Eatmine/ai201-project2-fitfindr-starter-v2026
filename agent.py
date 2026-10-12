"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""
import re
import config
import trace
# from tools import search_listings, suggest_outfit, create_fit_card
from tools import suggest_outfit, create_fit_card
from mcp_client import call_tool
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }

# ── query parsing (regex + string splitting, no model call) ──────────────────

_PRICE_RE = re.compile(
    r"\b(?:under|below|less than|max|up to)\s*\$?\s*(\d+(?:\.\d+)?)", re.IGNORECASE
)
_SIZE_RE = re.compile(r"\bsize\s+([a-z0-9/]+)", re.IGNORECASE)
_FILLER = {
    "a", "an", "the", "i", "im", "i'm", "want", "need", "looking", "for",
    "some", "something", "in", "with", "and", "or", "of", "to", "me", "find",
    "please", "any", "anything", "that", "is",
}


def _parse_query(query: str) -> dict:
    """'vintage graphic tee under $30, size M' ->
       {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}"""
    text = query or ""

    price_match = _PRICE_RE.search(text)
    max_price = float(price_match.group(1)) if price_match else None
    text = _PRICE_RE.sub(" ", text)

    size_match = _SIZE_RE.search(text)
    size = size_match.group(1).upper() if size_match else None
    text = _SIZE_RE.sub(" ", text)

    words = re.findall(r"[a-z0-9']+", text.lower())
    description = " ".join(w for w in words if w not in _FILLER)

    return {"description": description, "size": size, "max_price": max_price}


def _no_match_message(parsed: dict) -> str:
    """Says what was searched for and what the user could change."""
    parts = [f"'{parsed['description']}'" if parsed["description"] else "your search"]
    if parsed["size"]:
        parts.append(f"in size {parsed['size']}")
    if parsed["max_price"] is not None:
        parts.append(f"under ${parsed['max_price']:g}")

    tips = []
    if not parsed["description"]:
        tips.append("add a word for the kind of item you want (e.g. 'tee', 'jeans')")
    else:
        tips.append("try fewer or more general words (e.g. 'dress' instead of 'designer ballgown')")
    if parsed["max_price"] is not None:
        tips.append("raise your price limit")
    if parsed["size"]:
        tips.append("drop the size filter")

    return f"No listings matched {' '.join(parts)}. To widen the search, " + "; or ".join(tips) + "."


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    step = "search"
    count = 0

    while True:
        count += 1
        trace.check_iterations(count)

        if step == "search":
            session["parsed"] = _parse_query(session["query"])
            parsed = session["parsed"]
            trace.step("parse_query", inputs=session["query"], returned=parsed)

            search_args = {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
            }
            session["search_results"] = call_tool("search_listings", search_args)
            trace.step(
                "search_listings (via MCP)",
                inputs=search_args,
                returned=[r["id"] for r in session["search_results"]],
            )

            # THE BRANCH: nothing found -> explain what to change, and stop.
            if not session["search_results"]:
                session["error"] = _no_match_message(parsed)
                trace.step("stop", inputs="no search results", returned=session["error"])
                return session

            session["selected_item"] = session["search_results"][0]
            step = "suggest"

        elif step == "suggest":
            items = (session["wardrobe"] or {}).get("items") or []
            try:
                # Read the item and wardrobe back OUT of the session.
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
            except ModelUnavailable as exc:
                session["error"] = (
                    f"Found {session['selected_item']['title']}, but couldn't reach "
                    f"the model to suggest outfits ({exc}). Check GEMINI_API_KEY in "
                    "your .env file and your internet connection, then try again."
                )
                trace.step("stop", inputs="ModelUnavailable in suggest_outfit", returned=session["error"])
                return session
            trace.step(
                "suggest_outfit",
                inputs=f"new_item={session['selected_item']['id']}, wardrobe_items={len(items)}",
                returned=session["outfit_suggestion"],
            )
            step = "card"

        elif step == "card":
            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
            except ModelUnavailable as exc:
                session["error"] = (
                    f"Suggested outfits for {session['selected_item']['title']}, but "
                    f"couldn't reach the model to write the fit card ({exc}). Check "
                    "GEMINI_API_KEY in your .env file and your internet connection, "
                    "then try again."
                )
                trace.step("stop", inputs="ModelUnavailable in create_fit_card", returned=session["error"])
                return session
            trace.step(
                "create_fit_card",
                inputs={"new_item": session["selected_item"]["id"], "outfit": "(from session)"},
                returned=session["fit_card"],
            )
            return session

# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
