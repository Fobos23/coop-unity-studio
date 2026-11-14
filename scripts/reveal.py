#!/usr/bin/env python
"""Reveal a gauntlet round only after the verdict is written (references/gauntlet.md).

  python reveal.py <rounds/NN>

Requires <round>/verdict.md with lines "WINNER: A|B" and "GAP: <observable difference, the bar has X, we have Y>"
(and usually "FIX: <the one change>", "LENS: <lens>"). Decodes <round>/ab/key.bin, writes <round>/outcome.json, appends
a row to <target>/LEDGER.md (two folders above the round) and prints who won. A round is revealed once.
"""
import base64
import json
import re
import sys
from datetime import date
from pathlib import Path


def field(text, name):
    m = re.search(rf"^\s*{name}\s*:\s*(.+?)\s*$", text, re.I | re.M)
    return m.group(1).strip() if m else ""


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    rnd = Path(sys.argv[1])
    verdict, key, out = rnd / "verdict.md", rnd / "ab" / "key.bin", rnd / "outcome.json"
    if out.exists():
        sys.exit(f"{rnd} is already revealed: {json.loads(out.read_text(encoding='utf-8'))}")
    if not key.exists():
        sys.exit(f"no pair in {rnd / 'ab'}: run ab.py pair first")
    if not verdict.exists():
        sys.exit(f"write {verdict} first (WINNER and GAP), then reveal")
    text = verdict.read_text(encoding="utf-8")
    winner, gap = field(text, "WINNER").upper()[:1], field(text, "GAP")
    if winner not in ("A", "B"):
        sys.exit("verdict.md needs 'WINNER: A' or 'WINNER: B'")
    if len(gap) < 15:
        sys.exit("verdict.md needs 'GAP: <the single biggest gap as an observable difference>' (at least a sentence)")
    raw = bytes(x ^ 0x5A for x in base64.b85decode(key.read_bytes()))
    mapping = json.loads(raw)
    who = mapping[winner]
    outcome = {"round": rnd.name, "winner_side": winner, "winner": who, "ours_won": who == "cand",
               "lens": field(text, "LENS"), "gap": gap, "fix": field(text, "FIX"),
               "A": mapping["A"], "B": mapping["B"], "date": date.today().isoformat()}
    out.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    target = rnd.parent.parent
    ledger = target / "LEDGER.md"
    if not ledger.exists():
        ledger.write_text(f"# Gauntlet ledger — {target.name}\n\n| Round | Date | Lens | Winner | Gap | Fix |\n|---|---|---|---|---|---|\n",
                          encoding="utf-8")
    cell = lambda s: s.replace("|", "/").replace("\n", " ")
    with ledger.open("a", encoding="utf-8") as f:
        f.write(f"| {rnd.name} | {outcome['date']} | {cell(outcome['lens'])} | "
                f"{'ours' if outcome['ours_won'] else 'bar'} | {cell(gap)} | {cell(outcome['fix'])} |\n")
    for s in (sys.stdout,):
        try:
            s.reconfigure(encoding="utf-8" if not s.isatty() else s.encoding, errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    print(f"round {rnd.name}: {winner} was {'OURS' if who == 'cand' else 'the BAR'}. Gap: {gap}")
    if who == "cand":
        print("Ours won: reread the lens. If the reason does not survive the rereading, count it as a win for the bar.")


if __name__ == "__main__":
    main()
