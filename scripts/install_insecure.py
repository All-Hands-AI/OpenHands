from __future__ import annotations

import argparse
import pathlib
import shutil
import sysconfig


def copy_files(base: pathlib.Path, pip_only: bool = False) -> None:
    purelib = pathlib.Path(sysconfig.get_paths()["purelib"])

    if not pip_only:
        site_src = base / "sitecustomize.py"
        if site_src.exists():
            dst = purelib / site_src.name
            shutil.copy2(site_src, dst)
            print(f"Installed sitecustomize.py to {dst}")
        else:
            print(f"sitecustomize.py not found at {site_src}, skipping copy")

    pip_src = base / "pip.conf"
    if pip_src.exists():
        pip_dst = purelib / pip_src.name
        shutil.copy2(pip_src, pip_dst)
        print(f"Installed pip.conf to {pip_dst}")
    elif pip_only:
        print(f"pip.conf not found at {pip_src}, skipping copy")


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy insecure SSL helpers into the active environment")
    parser.add_argument("--base", type=pathlib.Path, default=pathlib.Path.cwd(), help="Project root containing helper files")
    parser.add_argument("--pip-only", action="store_true", help="Copy only pip.conf and skip sitecustomize.py")
    args = parser.parse_args()

    copy_files(base=args.base, pip_only=args.pip_only)


if __name__ == "__main__":
    main()
