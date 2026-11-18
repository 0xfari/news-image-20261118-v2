#!/usr/bin/env python3
"""Write the competition image to the output directory.

The repository ships the finished front page as entry.png.b64
(base64, one line). This program decodes it, checks that the bytes
are a complete, well-formed PNG of the size the entry promises,
and writes them to $MAKEFUN_OUTPUT_DIR/entry.png (default: out/).

Standard library only. No network, no randomness, no time: two
runs write byte-identical output.
"""

import base64
import binascii
import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
B64_FILE = HERE / "entry.png.b64"
OUT_NAME = "entry.png"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def fail(message):
    print(f"main.py: {message}", file=sys.stderr)
    sys.exit(1)


def read_payload():
    try:
        text = B64_FILE.read_text(encoding="ascii")
    except OSError as exc:
        fail(f"cannot read {B64_FILE.name}: {exc}")
    stripped = "".join(text.split())
    if not stripped:
        fail("entry.png.b64 is empty")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) != 1:
        fail(f"entry.png.b64 should be one line, found {len(lines)}")
    try:
        data = base64.b64decode(stripped, validate=True)
    except (binascii.Error, ValueError) as exc:
        fail(f"entry.png.b64 is not valid base64: {exc}")
    return data


def check_png(data):
    """Walk the PNG chunks, verifying structure, CRCs and size."""
    if len(data) < 8 or data[:8] != PNG_SIGNATURE:
        fail("decoded bytes do not start with the PNG signature")
    pos = 8
    seen_ihdr = False
    seen_iend = False
    width = height = None
    while pos < len(data):
        if pos + 8 > len(data):
            fail("truncated PNG chunk header")
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 12 + length
        if end > len(data):
            fail(f"truncated PNG chunk {ctype!r}")
        body = data[pos + 8:pos + 8 + length]
        stored_crc, = struct.unpack(">I", data[pos + 8 + length:end])
        actual_crc = zlib.crc32(ctype + body) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            fail(f"bad CRC in PNG chunk {ctype!r}")
        if ctype == b"IHDR":
            if seen_ihdr:
                fail("duplicate IHDR chunk")
            if length != 13:
                fail("IHDR chunk has the wrong length")
            width, height, depth, colour, comp, filt, inter = struct.unpack(
                ">IIBBBBB", body)
            if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
                fail(f"image is {width}x{height}, expected "
                     f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
            if depth != 8 or colour != 2:
                fail(f"unexpected PNG colour type {colour} / depth {depth}")
            if comp != 0 or filt != 0 or inter != 0:
                fail("unexpected PNG compression, filter or interlace")
            seen_ihdr = True
        elif ctype == b"IEND":
            if length != 0 or end != len(data):
                fail("trailing bytes after IEND")
            seen_iend = True
            break
        pos = end
    if not seen_ihdr:
        fail("PNG has no IHDR chunk")
    if not seen_iend:
        fail("PNG has no IEND chunk")
    return width, height


def main():
    data = read_payload()
    width, height = check_png(data)
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "out"))
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fail(f"cannot create output directory {out_dir}: {exc}")
    target = out_dir / OUT_NAME
    try:
        target.write_bytes(data)
    except OSError as exc:
        fail(f"cannot write {target}: {exc}")
    print(f"wrote {target} ({len(data)} bytes, {width}x{height} PNG, "
          f"sha256 {hashlib.sha256(data).hexdigest()[:16]}...)")


if __name__ == "__main__":
    main()
