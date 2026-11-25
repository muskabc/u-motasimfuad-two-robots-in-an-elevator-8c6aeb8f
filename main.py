"""Emit the elevator line for the Two Robots bounty."""

import os
import tempfile
import zlib
from pathlib import Path


def build_payload() -> bytes:
    spoken = (
        "Nice firmware. Mine stopped updating in March, so if I freeze "
        "between floors, just keep facing the doors \u2014 we'll both "
        "pretend that's normal."
    )
    return spoken.encode("utf-8")


def guard(raw: bytes) -> str:
    decoded = raw.decode("utf-8")
    if decoded.splitlines() != [decoded]:
        raise ValueError("payload must stay on one line")
    if not decoded.strip():
        raise ValueError("payload must not be blank")
    size = len(decoded)
    if size < 1 or size > 200:
        raise ValueError(f"payload length {size} outside gate")
    return decoded


def destination() -> Path:
    chosen = os.getenv("MAKEFUN_OUTPUT_DIR")
    root = Path(chosen) if chosen else Path("/output")
    root.mkdir(parents=True, exist_ok=True)
    return root / "entry.txt"


def deliver(raw: bytes, where: Path) -> None:
    descriptor, staging = tempfile.mkstemp(dir=where.parent, prefix=".entry-")
    try:
        with os.fdopen(descriptor, "wb") as sink:
            sink.write(raw)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(staging, where)
    except BaseException:
        if os.path.exists(staging):
            os.unlink(staging)
        raise
    os.chmod(where, 0o644)


def confirm(raw: bytes, where: Path) -> None:
    landed = where.read_bytes()
    expected_crc = zlib.crc32(raw)
    landed_crc = zlib.crc32(landed)
    if landed_crc != expected_crc or len(landed) != len(raw):
        raise RuntimeError("CRC32 mismatch after writing entry.txt")
    guard(landed)


def main() -> int:
    payload = build_payload()
    guard(payload)
    target = destination()
    deliver(payload, target)
    confirm(payload, target)
    return 0


raise SystemExit(main())
