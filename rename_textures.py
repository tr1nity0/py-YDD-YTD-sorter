"""
GTA V YTD/YDD Texture & Drawable Batch Renamer / Copier
=========================================================
Select a folder containing .ytd or .ydd files, enter the new number,
and the script renames OR copies ALL matching files in that directory.

Patterns handled:
  YTD:  jbib_diff_000_a_uni.ytd  →  jbib_diff_001_a_uni.ytd
  YDD:  jbib_000_u.ydd           →  jbib_001_u.ydd

Optional prefix stripping:
  mp_m_freemode_01^jbib_diff_000_a_uni.ytd  →  jbib_diff_001_a_uni.ytd
"""

import os
import re
import sys
import shutil
from pathlib import Path

# ── regex: match a 3-digit number block (e.g. _000_) ──
PATTERN = re.compile(r'(_)(\d{3})(_)')


def find_files(directory, extension):
    """Return sorted list of files with the given extension in directory."""
    files = sorted(
        f for f in os.listdir(directory)
        if f.lower().endswith(extension.lower()) and PATTERN.search(f)
    )
    return files


def strip_prefix(filename):
    """Remove everything before and including '^' if present."""
    if '^' in filename:
        return filename.split('^', 1)[1]
    return filename


def build_new_name(fname, new_number, do_strip):
    """Apply prefix strip and number replacement to a filename."""
    name = strip_prefix(fname) if do_strip else fname
    new_num_str = f"{int(new_number):03d}"
    name = PATTERN.sub(rf'\g<1>{new_num_str}\3', name, count=1)
    return name


def preview_renames(files, new_number, do_strip):
    """Build a list of (old_name, new_name) tuples."""
    renames = []
    for fname in files:
        new_name = build_new_name(fname, new_number, do_strip)
        if new_name != fname:
            renames.append((fname, new_name))
    return renames


def main():
    print("=" * 55)
    print("  GTA V  YTD / YDD  Batch Renamer / Copier")
    print("=" * 55)

    # ── pick directory ──
    default_dir = os.getcwd()
    directory = input(f"\nFolder path (Enter = current dir):\n [{default_dir}]\n> ").strip()
    if not directory:
        directory = default_dir
    if not os.path.isdir(directory):
        print(f"\n[ERROR] Directory not found: {directory}")
        input("Press Enter to exit...")
        sys.exit(1)

    # ── pick file type ──
    print("\nFile type:")
    print("  1) .ytd  (textures  – e.g. jbib_diff_000_a_uni.ytd)")
    print("  2) .ydd  (drawables – e.g. jbib_000_u.ydd)")
    print("  3) Both  (.ytd and .ydd)")
    choice = input("> ").strip()
    extensions = {
        "1": [".ytd"],
        "2": [".ydd"],
        "3": [".ytd", ".ydd"],
    }.get(choice, [".ytd", ".ydd"])

    # ── gather files ──
    all_files = []
    for ext in extensions:
        all_files.extend(find_files(directory, ext))

    if not all_files:
        print(f"\n[!] No matching {'/'.join(extensions)} files found in:\n    {directory}")
        input("Press Enter to exit...")
        sys.exit(0)

    print(f"\nFound {len(all_files)} file(s):")
    for f in all_files:
        print(f"  • {f}")

    # ── rename or copy ──
    print("\nOperation:")
    print("  1) Rename  (move originals to new name)")
    print("  2) Copy    (keep originals, create copies with new name)")
    op_choice = input("> ").strip()
    mode = "copy" if op_choice == "2" else "rename"

    # ── strip prefix? ──
    has_prefix = any('^' in f for f in all_files)
    do_strip = False
    if has_prefix:
        print("\nSome files have a prefix before '^' (e.g. mp_m_freemode_01^...)")
        print("  1) Yes – strip the prefix  (remove everything before ^)")
        print("  2) No  – keep filenames as-is")
        strip_choice = input("> ").strip()
        do_strip = strip_choice == "1"

    # ── ask for new number ──
    print()
    new_number = input("Enter the NEW 3-digit number (e.g. 1, 5, 12, 042):\n> ").strip()
    if not new_number.isdigit():
        print("[ERROR] Please enter a valid number.")
        input("Press Enter to exit...")
        sys.exit(1)

    num_val = int(new_number)
    if num_val > 999:
        print("[ERROR] Number must be between 0 and 999.")
        input("Press Enter to exit...")
        sys.exit(1)

    # ── output directory for copies (optional) ──
    out_directory = directory
    if mode == "copy":
        out_input = input(
            f"\nOutput folder for copies (Enter = same folder):\n [{directory}]\n> "
        ).strip()
        if out_input:
            out_directory = out_input
            os.makedirs(out_directory, exist_ok=True)

    # ── preview ──
    renames = preview_renames(all_files, num_val, do_strip)
    if not renames:
        print("\n[!] Nothing to process – files already match the target names.")
        input("Press Enter to exit...")
        sys.exit(0)

    action_word = "copied" if mode == "copy" else "renamed"
    arrow = "→ (copy)" if mode == "copy" else "→"

    print(f"\n{'─' * 55}")
    print(f" Preview  ({len(renames)} file(s) will be {action_word})")
    print(f"{'─' * 55}")
    for old, new in renames:
        print(f"  {old}")
        print(f"    {arrow} {new}")
    if out_directory != directory:
        print(f"\n  Output folder: {out_directory}")
    print(f"{'─' * 55}")

    # ── confirm ──
    confirm = input(f"\nProceed with {mode}? (y/n): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Cancelled.")
        input("Press Enter to exit...")
        sys.exit(0)

    # ── execute ──
    success = 0
    for old, new in renames:
        old_path = os.path.join(directory, old)
        new_path = os.path.join(out_directory, new)
        if os.path.exists(new_path):
            print(f"  [SKIP] Target already exists: {new}")
            continue
        if mode == "copy":
            shutil.copy2(old_path, new_path)
        else:
            os.rename(old_path, new_path)
        tag = "COPY" if mode == "copy" else "OK"
        print(f"  [{tag}] {old}  →  {new}")
        success += 1

    print(f"\nDone! {success}/{len(renames)} file(s) {action_word}.")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
