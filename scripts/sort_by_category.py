"""
Category Sorter — Sorts .ydd and .ytd files into folders by component type.

Usage:
  1. Place this script in the folder with your .ydd / .ytd files.
  2. Double-click it.

It reads the component name (jbib, accs, teef, hair, feet, lowr, etc.)
from each filename and copies them into matching folders.

Works with or without prefixes like 'mp_m_freemode_01^'.

Examples:
  mp_m_freemode_01^jbib_000_u.ydd         -> jbib/
  mp_m_freemode_01^jbib_diff_000_e_uni.ytd -> jbib/
  accs_016_u.ydd                           -> accs/
  accs_diff_016_a_uni.ytd                  -> accs/
"""

import os
import sys
import re
import shutil

# Extracts the component name after an optional prefix ending with ^ or at the start
# e.g. "mp_m_freemode_01^jbib_diff_000_e_uni" -> "jbib"
# e.g. "accs_016_u"                           -> "accs"
COMPONENT_PATTERN = re.compile(r"^(?:.*?\^)?([a-z]+)_", re.IGNORECASE)


def get_script_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_category(filename: str) -> str | None:
    """Extract the component/category from a filename."""
    base = os.path.splitext(filename)[0]
    m = COMPONENT_PATTERN.match(base)
    if m:
        return m.group(1).lower()
    return None


def main():
    work_dir = get_script_dir()
    print(f"Working folder: {work_dir}\n")

    # --- Gather all .ydd and .ytd files ---
    files = [
        f for f in os.listdir(work_dir)
        if os.path.isfile(os.path.join(work_dir, f))
        and os.path.splitext(f)[1].lower() in (".ydd", ".ytd")
    ]

    if not files:
        print("No .ydd or .ytd files found in this folder.")
        return

    ydd_count = sum(1 for f in files if f.lower().endswith(".ydd"))
    ytd_count = sum(1 for f in files if f.lower().endswith(".ytd"))
    print(f"Found {len(files)} files  ({ydd_count} .ydd, {ytd_count} .ytd)\n")

    # --- Move or copy? ---
    print("  [1] Copy  (keep originals)")
    print("  [2] Move  (remove originals)\n")
    choice = input("Choice (1/2): ").strip()
    use_move = choice == "2"
    action_word = "Move" if use_move else "Copy"
    action_past = "moved" if use_move else "copied"
    print(f"\n{action_word} mode selected.\n")

    # --- Sort into categories ---
    processed = 0
    skipped = 0
    unknown = 0
    categories: dict[str, int] = {}

    for filename in files:
        category = get_category(filename)
        if not category:
            print(f"  [unknown]     {filename}")
            unknown += 1
            continue

        dest_dir = os.path.join(work_dir, category)
        os.makedirs(dest_dir, exist_ok=True)

        src = os.path.join(work_dir, filename)
        dst = os.path.join(dest_dir, filename)

        if os.path.exists(dst):
            skipped += 1
            continue

        if use_move:
            shutil.move(src, dst)
        else:
            shutil.copy2(src, dst)

        categories[category] = categories.get(category, 0) + 1
        processed += 1

    # --- Summary ---
    print("-" * 60)
    print(f"\nDone!  {processed} {action_past}  |  {skipped} skipped  |  {unknown} unknown\n")

    if categories:
        print("Files per category:")
        for cat in sorted(categories):
            print(f"  {cat:<12} {categories[cat]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print()
        input("Press Enter to close...")
