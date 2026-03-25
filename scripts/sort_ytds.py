"""
YTD Sorter — Finds YTDs linked to YDD names and copies them to [sorted].

Usage:
  1. Place this script in the folder with your .ytd files.
  2. Double-click it, then paste names OR browse for a .txt file.
  3. Or drag a .txt file onto this script.
  4. Or: python sort_ytds.py names.txt

Matching logic:
  YDD:  [prefix]accs_016_u.ydd
  YTDs: [prefix]accs_diff_016_a_uni.ytd, accs_diff_016_b_uni.ytd, etc.
  Key:  same prefix + component + "_diff_" + same number + _[any letter]_[any suffix]
"""

import os
import sys
import re
import shutil

SORTED_DIR = "[sorted]"

# Matches component_number_suffix pattern at the END of a YDD base name
# e.g. "mp_m_freemode_01^accs_016_u" -> prefix="mp_m_freemode_01^", comp="accs", num="016"
# e.g. "accs_016_u"                  -> prefix="", comp="accs", num="016"
YDD_PATTERN = re.compile(r"^(.*?)([a-z]+)_(\d+)_[a-z]+$", re.IGNORECASE)


def get_script_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_names_from_file(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip().strip("\r") for line in f if line.strip()]


def browse_for_txt() -> str | None:
    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Select your YDD name list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        root.destroy()
        return path if path else None
    except Exception:
        print("  Could not open file browser. Use command line instead.")
        return None


def load_names_from_input() -> list[str]:
    print("Paste your YDD names (one per line). Press Enter twice when done:\n")
    lines = []
    while True:
        line = input()
        if not line.strip():
            if lines:
                break
            continue
        lines.append(line.strip())
    return lines


def strip_ext(name: str) -> str:
    base, ext = os.path.splitext(name)
    return base if ext.lower() in (".ydd", ".ytd", ".txt") else name


def parse_ydd(ydd_base: str):
    """
    Parse a YDD base name into (prefix, component, number).
    'mp_m_freemode_01^accs_016_u' -> ('mp_m_freemode_01^', 'accs', '016')
    'accs_016_u'                  -> ('', 'accs', '016')
    Returns None if it can't parse.
    """
    m = YDD_PATTERN.match(ydd_base)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def find_ytds(ydd_base: str, all_ytds: dict[str, str]) -> list[str]:
    """
    Given a YDD like 'mp_m_freemode_01^accs_016_u',
    find all YTDs matching '[prefix]accs_diff_016_*.ytd'
    """
    parsed = parse_ydd(ydd_base)
    if not parsed:
        return []

    prefix, component, number = parsed
    # Build the search key: e.g. "mp_m_freemode_01^accs_diff_016_"
    search_prefix = f"{prefix}{component}_diff_{number}_".lower()

    hits = []
    for ytd_key, ytd_filename in all_ytds.items():
        if ytd_key.startswith(search_prefix):
            hits.append(ytd_filename)

    return hits


def main():
    work_dir = get_script_dir()
    print(f"Working folder: {work_dir}\n")

    # --- Load YDD names ---
    if len(sys.argv) > 1:
        txt_path = sys.argv[1]
        if not os.path.isfile(txt_path):
            print(f"Error: file '{txt_path}' not found.")
            return
        names = load_names_from_file(txt_path)
        print(f"Loaded {len(names)} name(s) from {os.path.basename(txt_path)}\n")
    else:
        print("How would you like to load YDD names?\n")
        print("  [1] Paste names")
        print("  [2] Browse for a .txt file\n")
        choice = input("Choice (1/2): ").strip()

        if choice == "2":
            txt_path = browse_for_txt()
            if not txt_path:
                print("No file selected.")
                return
            names = load_names_from_file(txt_path)
            print(f"Loaded {len(names)} name(s) from {os.path.basename(txt_path)}\n")
        else:
            names = load_names_from_input()
            print(f"\nLoaded {len(names)} name(s) from input.\n")

    ydd_bases = [strip_ext(n) for n in names]

    # --- Index all .ytd files in the working directory ---
    all_ytds: dict[str, str] = {}
    for f in os.listdir(work_dir):
        if f.lower().endswith(".ytd"):
            all_ytds[os.path.splitext(f)[0].lower()] = f

    if not all_ytds:
        print("No .ytd files found in the working directory.")
        return

    print(f"Found {len(all_ytds)} .ytd file(s) in directory.\n")

    # --- Debug: show what it's looking for on the first entry ---
    if ydd_bases:
        parsed = parse_ydd(ydd_bases[0])
        if parsed:
            prefix, comp, num = parsed
            print(f"Example: '{ydd_bases[0]}'")
            print(f"  -> looking for: '{prefix}{comp}_diff_{num}_*.ytd'\n")

    print("-" * 60)

    # --- Match & copy ---
    sorted_path = os.path.join(work_dir, SORTED_DIR)
    copied = 0
    skipped = 0
    no_match = 0
    parse_fail = 0

    for ydd in ydd_bases:
        if not parse_ydd(ydd):
            print(f"  [parse fail]  {ydd}")
            parse_fail += 1
            continue

        matches = find_ytds(ydd, all_ytds)
        if not matches:
            print(f"  [no match]    {ydd}")
            no_match += 1
            continue

        for ytd_file in matches:
            src = os.path.join(work_dir, ytd_file)
            dst = os.path.join(sorted_path, ytd_file)

            if not os.path.isfile(src):
                continue

            os.makedirs(sorted_path, exist_ok=True)

            if os.path.exists(dst):
                print(f"  [skip]        {ytd_file}  (already exists)")
                skipped += 1
                continue

            shutil.copy2(src, dst)
            print(f"  [copied]      {ytd_file}")
            copied += 1

    print("-" * 60)
    print(f"\nDone!  {copied} copied  |  {skipped} skipped  |  {no_match} no match  |  {parse_fail} parse errors")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print()
        input("Press Enter to close...")
