"""Regenerate examples/sample_data/ from scratch.

The sample dataset is 100% synthetic: every record is produced by this script from a
fixed random seed. No real or client data is involved. The dataset is deliberately
small (a few hundred records) so the quickstart runs in well under a second, and it
deliberately contains two "planted" data-quality problems for `recpipe audit` to find:

* ``TableTypeA_old/`` is a byte-for-byte duplicate of ``TableTypeA/`` — the classic
  "an old copy of the dataset survived under another name" double-counting hazard;
* ``TableTypeB/session_04.txt`` is an empty file.

Records use the public PokerStars hand-history text format purely as a realistic
example of semi-structured, record-based text. Player names are fictional.

Usage:
    python examples/generate_sample_data.py
"""
from __future__ import annotations

import random
import shutil
from pathlib import Path

ROOT = Path(__file__).parent / "sample_data"
NAMES = ["Alice", "Bob", "Carol", "Dave", "Erin", "Frank"]
POSITIONS = ["LJ", "HJ", "CO", "BU", "SB", "BB"]


def make_hand(rng: random.Random, hand_id: int, table: str) -> str:
    day, h, m, s = rng.randint(1, 28), rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59)
    stamp = f"2024/01/{day:02d} {h:02d}:{m:02d}:{s:02d}"
    seats = list(zip(POSITIONS, NAMES))
    raiser = rng.choice(["CO", "BU", "SB"])
    raise_to = rng.choice(["2.50", "3.00", "3.50"])
    board = rng.choice(["7c 3d 2s", "Ah Kd 5h", "Ts 9s 4c", "Qd Jc 6h", "8h 8d 3c"])

    lines = [
        f"PokerStars Hand #{hand_id}: Hold'em No Limit ($0.50/$1.00) - {stamp} ET",
        f"Table '{table}' 6-max Seat #4 is the button",
    ]
    for i, (_pos, name) in enumerate(seats, start=1):
        stack = f"{rng.randint(60, 200)}.00"
        lines.append(f"Seat {i}: {name} (${stack} in chips)")
    lines += [
        f"{dict(seats)['SB']}: posts small blind $0.50",
        f"{dict(seats)['BB']}: posts big blind $1.00",
        "*** HOLE CARDS ***",
    ]
    for pos, name in seats[:4]:
        if pos == raiser:
            lines.append(f"{name}: raises ${float(raise_to) - 1:.2f} to ${raise_to}")
        else:
            lines.append(f"{name}: folds")
    if raiser != "SB":
        lines.append(f"{dict(seats)['SB']}: folds")
    lines += [
        f"{dict(seats)['BB']}: calls ${float(raise_to) - 1:.2f}",
        f"*** FLOP *** [{board}]",
        f"{dict(seats)['BB']}: checks",
        f"{dict(seats)[raiser]}: bets $4.00",
        f"{dict(seats)['BB']}: folds",
        f"Uncalled bet ($4.00) returned to {dict(seats)[raiser]}",
        f"{dict(seats)[raiser]} collected ${float(raise_to) * 2 + 0.50:.2f} from pot",
        "*** SUMMARY ***",
        f"Total pot ${float(raise_to) * 2 + 0.50:.2f}",
        f"Board [{board}]",
        "",
    ]
    return "\r\n".join(lines) + "\r\n"


def main() -> None:
    rng = random.Random(42)
    if ROOT.exists():
        shutil.rmtree(ROOT)

    hand_id = 9_000_000_001
    plan = {
        "TableTypeA": [24, 9, 40, 3],
        "TableTypeB": [31, 12, 18, 0, 27],  # the 0 plants an empty file
    }
    for folder, counts in plan.items():
        for i, n in enumerate(counts, start=1):
            path = ROOT / folder / f"session_{i:02d}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            hands = []
            for _ in range(n):
                hands.append(make_hand(rng, hand_id, f"Demo-{folder}-{i}"))
                hand_id += 1
            path.write_bytes("".join(hands).encode("utf-8"))

    # Plant a byte-for-byte duplicate folder for `recpipe audit` to catch.
    shutil.copytree(ROOT / "TableTypeA", ROOT / "TableTypeA_old")

    total = sum(sum(c) for c in plan.values()) + sum(plan["TableTypeA"])
    print(f"wrote {total} synthetic records under {ROOT}")


if __name__ == "__main__":
    main()
