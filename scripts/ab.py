#!/usr/bin/env python
"""Blind A/B pairs for the gauntlet (references/gauntlet.md).

  python ab.py pair --round <rounds/NN> --ref <bar image> --cand <our image>
      Puts the bar and our capture into <round>/ab/A.png and B.png in random order, both re-encoded to the same
      size and format (file size and name give no hint), plus <round>/ab/pair.png (A left, B right). The key is
      stored encoded in <round>/ab/key.bin: do not decode it yourself, reveal.py does that after the verdict.
  python ab.py sheet <out.png> <frame> [<frame> …] [--cols 4] [--width 1600] [--labels 0s,5s,…]
      A contact sheet from frames (for "the first minute": frames at fixed seconds), so a sequence can be one side.
Needs Pillow (python -m pip install pillow).
"""
import argparse
import base64
import json
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("ab.py needs Pillow: python -m pip install pillow")

SIDE = 1280  # long side of both images in a pair


def fit(im, size):
    im = im.convert("RGB")
    im.thumbnail((size, size))
    return im


def same_canvas(a, b):
    """Both images on canvases of identical size (letterboxed), so dimensions do not tell them apart."""
    w, h = max(a.width, b.width), max(a.height, b.height)
    out = []
    for im in (a, b):
        c = Image.new("RGB", (w, h), (0, 0, 0))
        c.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
        out.append(c)
    return out


def encode_key(mapping):
    raw = json.dumps(mapping).encode()
    return base64.b85encode(bytes(x ^ 0x5A for x in raw))


def cmd_pair(a):
    rnd = Path(a.round)
    ab = rnd / "ab"
    if (ab / "key.bin").exists() and not a.force:
        sys.exit(f"{ab} already has a pair; one pair per round (use --force only to redo an unjudged round)")
    ab.mkdir(parents=True, exist_ok=True)
    ref, cand = fit(Image.open(a.ref), SIDE), fit(Image.open(a.cand), SIDE)
    ref, cand = same_canvas(ref, cand)
    sides = ["ref", "cand"]
    random.SystemRandom().shuffle(sides)
    imgs = {"ref": ref, "cand": cand}
    for label, who in zip("AB", sides):
        imgs[who].save(ab / f"{label}.png", optimize=False, compress_level=6)
    A, B = imgs[sides[0]], imgs[sides[1]]
    gap = 24
    pair = Image.new("RGB", (A.width * 2 + gap, A.height + 40), (20, 20, 20))
    pair.paste(A, (0, 40))
    pair.paste(B, (A.width + gap, 40))
    d = ImageDraw.Draw(pair)
    d.text((10, 10), "A", fill=(255, 255, 255))
    d.text((A.width + gap + 10, 10), "B", fill=(255, 255, 255))
    pair.save(ab / "pair.png")
    (ab / "key.bin").write_bytes(encode_key({"A": sides[0], "B": sides[1],
                                              "ref": str(Path(a.ref)), "cand": str(Path(a.cand))}))
    print(f"pair ready: {ab / 'pair.png'} (A and B also separately). Judge through ONE lens, write "
          f"{rnd / 'verdict.md'} with WINNER and GAP, then run reveal.py {rnd}")


def cmd_sheet(a):
    frames = [Path(f) for f in a.frames]
    ims = [Image.open(f).convert("RGB") for f in frames]
    cols = max(1, a.cols)
    rows = (len(ims) + cols - 1) // cols
    cell_w = a.width // cols
    cell_h = int(cell_w * ims[0].height / max(1, ims[0].width))
    labels = a.labels.split(",") if a.labels else [f.stem for f in frames]
    sheet = Image.new("RGB", (cell_w * cols, (cell_h + 20) * rows), (15, 15, 15))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x, y = (i % cols) * cell_w, (i // cols) * (cell_h + 20)
        sheet.paste(im.resize((cell_w, cell_h)), (x, y + 20))
        d.text((x + 4, y + 4), labels[i] if i < len(labels) else "", fill=(230, 230, 230))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(f"sheet: {a.out} ({len(ims)} frames, {cols} columns)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("pair")
    p.add_argument("--round", required=True)
    p.add_argument("--ref", required=True)
    p.add_argument("--cand", required=True)
    p.add_argument("--force", action="store_true")
    s = sp.add_parser("sheet")
    s.add_argument("out")
    s.add_argument("frames", nargs="+")
    s.add_argument("--cols", type=int, default=4)
    s.add_argument("--width", type=int, default=1600)
    s.add_argument("--labels", default="")
    a = ap.parse_args()
    (cmd_pair if a.cmd == "pair" else cmd_sheet)(a)


if __name__ == "__main__":
    main()
