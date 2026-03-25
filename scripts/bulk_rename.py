"""
Bulk Renamer — Sequentially renumbers .ydd and .ytd files.

Usage:
  1. Place this script in the folder with your .ydd / .ytd files.
  2. Double-click it.
  3. Enter a starting number (e.g. 0 for 000, 5 for 005).
  4. Script groups by component (accs, jbib, etc.), sorts them,
     and renumbers each YDD + its linked YTDs sequentially.

Renames one-by-one using temp names to avoid collisions.

Example (starting at 000):
  mp_m_freemode_01^accs_101_u.ydd              -> mp_m_freemode_01^accs_000_u.ydd
  mp_m_freemode_01^accs_diff_101_a_uni.ytd     -> mp_m_freemode_01^accs_diff_000_a_uni.ytd
  mp_m_freemode_01^accs_diff_101_b_uni.ytd     -> mp_m_freemode_01^accs_diff_000_b_uni.ytd
  mp_m_freemode_01^accs_105_u.ydd              -> mp_m_freemode_01^accs_001_u.ydd
  ...
"""

import os
import sys
import re

# Parses a YDD filename into parts
# e.g. "mp_m_freemode_01^accs_016_u.ydd"
#   -> prefix="mp_m_freemode_01^", comp="accs", num="016", suffix="u"
YDD_PATTERN = re.compile(
    r"^(?P<prefix>.*?)(?P<comp>[a-z]+)_(?P<num>\d+)_(?P<suffix>[a-z]+)\.ydd$",
    re.IGNORECASE,
)

# Parses a YTD filename into parts
# e.g. "mp_m_freemode_01^accs_diff_016_a_uni.ytd"
#   -> prefix="mp_m_freemode_01^", comp="accs", num="016", letter="a", tail="uni"
YTD_PATTERN = re.compile(
    r"^(?P<prefix>.*?)(?P<comp>[a-z]+)_diff_(?P<num>\d+)_(?P<letter>[a-z])_(?P<tail>[a-z]+)\.ytd$",
    re.IGNORECASE,
)


def get_script_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def main():
    work_dir = get_script_dir()
    print(f"Working folder: {work_dir}\n")

    # --- Ask for starting number ---
    start_input = input("Starting number (default 0 -> 000): ").strip()
    start_num = int(start_input) if start_input.isdigit() else 0
    print(f"\nWill start numbering from {start_num:03d}\n")

    # --- Scan all files ---
    all_files = os.listdir(work_dir)

    # --- Parse all YDDs ---
    ydds = []
    for f in all_files:
        m = YDD_PATTERN.match(f)
        if m:
            ydds.append({
                "filename": f,
                "prefix": m.group("prefix"),
                "comp": m.group("comp").lower(),
                "num": m.group("num"),
                "suffix": m.group("suffix"),
            })

    # --- Parse all YTDs ---
    ytds = []
    for f in all_files:
        m = YTD_PATTERN.match(f)
        if m:
            ytds.append({
                "filename": f,
                "prefix": m.group("prefix"),
                "comp": m.group("comp").lower(),
                "num": m.group("num"),
                "letter": m.group("letter"),
                "tail": m.group("tail"),
            })

    if not ydds:
        print("No .ydd files found.")
        return

    print(f"Found {len(ydds)} .ydd and {len(ytds)} .ytd files.\n")

    # --- Group YDDs by (prefix, component) ---
    groups: dict[tuple[str, str], list[dict]] = {}
    for ydd in ydds:
        key = (ydd["prefix"], ydd["comp"])
        groups.setdefault(key, []).append(ydd)

    # Sort each group by current number
    for key in groups:
        groups[key].sort(key=lambda x: int(x["num"]))

    # --- Build rename plan ---
    # Each entry: (old_path, temp_path, final_path)
    rename_plan: list[tuple[str, str, str]] = []

    for (prefix, comp), ydd_list in sorted(groups.items()):
        new_num = start_num
        print(f"[{prefix}{comp}]  {len(ydd_list)} YDDs, renumbering {int(ydd_list[0]['num']):03d}–{int(ydd_list[-1]['num']):03d}  ->  {new_num:03d}–{new_num + len(ydd_list) - 1:03d}")

        for ydd in ydd_list:
            old_num = ydd["num"]
            new_num_str = f"{new_num:03d}"

            # YDD rename
            old_name = ydd["filename"]
            new_name = f"{prefix}{comp}_{new_num_str}_{ydd['suffix']}.ydd"
            temp_name = f"__temp__{prefix}{comp}_{new_num_str}_{ydd['suffix']}.ydd"

            rename_plan.append((
                os.path.join(work_dir, old_name),
                os.path.join(work_dir, temp_name),
                os.path.join(work_dir, new_name),
            ))

            # Find linked YTDs (same prefix, comp, number)
            linked = [
                y for y in ytds
                if y["prefix"] == ydd["prefix"]
                and y["comp"] == comp
                and y["num"] == old_num
            ]

            for ytd in linked:
                old_ytd = ytd["filename"]
                new_ytd = f"{prefix}{comp}_diff_{new_num_str}_{ytd['letter']}_{ytd['tail']}.ytd"
                temp_ytd = f"__temp__{prefix}{comp}_diff_{new_num_str}_{ytd['letter']}_{ytd['tail']}.ytd"

                rename_plan.append((
                    os.path.join(work_dir, old_ytd),
                    os.path.join(work_dir, temp_ytd),
                    os.path.join(work_dir, new_ytd),
                ))

            new_num += 1

    # --- Confirm ---
    total = len(rename_plan)
    print(f"\n{total} file(s) will be renamed.\n")

    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    # --- Pass 1: Rename to temp names (avoids collisions) ---
    print("\nPass 1: Renaming to temp names...")
    for old_path, temp_path, _ in rename_plan:
        if os.path.isfile(old_path):
            os.rename(old_path, temp_path)

    # --- Pass 2: Rename from temp to final names ---
    print("Pass 2: Renaming to final names...")
    renamed = 0
    errors = 0
    for _, temp_path, final_path in rename_plan:
        try:
            if os.path.isfile(temp_path):
                if os.path.exists(final_path):
                    print(f"  [CONFLICT] {os.path.basename(final_path)} already exists!")
                    errors += 1
                    continue
                os.rename(temp_path, final_path)
                renamed += 1
        except Exception as e:
            print(f"  [ERROR] {os.path.basename(temp_path)}: {e}")
            errors += 1

    print(f"\nDone!  {renamed} renamed  |  {errors} errors")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print()
        input("Press Enter to close...")
