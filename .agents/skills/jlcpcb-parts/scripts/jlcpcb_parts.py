#!/usr/bin/env python3
"""CLI for searching the JLCPCB / LCSC parts catalogue.

Subcommands:
    update                          force re-download of the SQLite DB
    search [<query>] [filters...]   substring + structured filter search
    show <LCSC>                     full detail for one part (accepts C2040 or 2040)
    schema [<category>]             list categories or attribute keys for a category

Run without args for help.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import db_cache
import search as searchmod


def cmd_update(args: argparse.Namespace) -> int:
    db_cache.download(force=args.force)
    db_cache.emit_staleness()
    return 0


def _open_db():
    db_cache.emit_staleness()
    db_path = db_cache.ensure_db_or_warn(auto_download=True)
    return searchmod.open_db(db_path)


def cmd_search(args: argparse.Namespace) -> int:
    conn = _open_db()
    opts = searchmod.SearchOpts()
    opts.query = args.query
    opts.category = args.category
    opts.package = args.package
    opts.manufacturer = args.manufacturer
    opts.min_stock = args.min_stock
    opts.basic_only = args.basic
    opts.preferred_only = args.preferred
    opts.limit = args.limit
    for expr in args.attr or []:
        try:
            opts.attrs.append(searchmod.parse_attr_expr(expr))
        except ValueError as e:
            sys.stderr.write(f"error: {e}\n")
            return 2
    rows = searchmod.run_search(conn, opts)
    if not rows and args.text_fallback and opts.attrs:
        # Retry: drop --attr filters, add their values as substring AND-terms
        # against mfr/description. Keys are dropped because upstream parser
        # bugs occasionally mis-route attr values into wrong keys.
        fb = searchmod.SearchOpts()
        fb.category = opts.category
        fb.package = opts.package
        fb.manufacturer = opts.manufacturer
        fb.min_stock = opts.min_stock
        fb.basic_only = opts.basic_only
        fb.preferred_only = opts.preferred_only
        fb.limit = opts.limit
        extra_terms = " ".join(v for _k, _o, v in opts.attrs if v)
        fb.query = (opts.query + " " + extra_terms).strip() if opts.query else extra_terms
        sys.stderr.write(
            f"# 0 hits with --attr filters; retrying as substring search "
            f"on MPN/description with terms: {fb.query!r}\n"
        )
        rows = searchmod.run_search(conn, fb)
    print(searchmod.format_search_table(rows))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    n = searchmod.normalize_lcsc(args.lcsc)
    if n is None:
        sys.stderr.write(f"error: invalid LCSC {args.lcsc!r}\n")
        return 2
    conn = _open_db()
    row = searchmod.run_show(conn, n)
    if row is None:
        sys.stderr.write(f"# no part with LCSC C{n}\n")
        return 1
    print(searchmod.format_show(row))
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    conn = _open_db()
    if args.category is None:
        cats = searchmod.list_categories(conn)
        print(searchmod.format_schema_categories(cats))
    else:
        keys = searchmod.category_attr_summary(conn, args.category)
        print(searchmod.format_schema_category(keys))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jlcpcb_parts.py",
        description="Search the JLCPCB / LCSC parts catalogue (CDFER SQLite).",
    )
    sub = p.add_subparsers(dest="cmd")

    p_update = sub.add_parser("update", help="re-download the SQLite DB")
    p_update.add_argument("--force", action="store_true",
                          help="force rebuild even if manifest is unchanged")
    p_update.set_defaults(func=cmd_update)

    p_search = sub.add_parser("search", help="search parts (substring + filters)")
    p_search.add_argument("query", nargs="?", default=None,
                          help="optional substring query against MPN/description")
    p_search.add_argument("--category")
    p_search.add_argument("--package")
    p_search.add_argument("--manufacturer")
    p_search.add_argument("--min-stock", type=int)
    g = p_search.add_mutually_exclusive_group()
    g.add_argument("--basic", action="store_true",
                   help="only JLC Basic parts")
    g.add_argument("--preferred", action="store_true",
                   help="only JLC Preferred parts")
    p_search.add_argument("--attr", action="append", default=[],
                          metavar='"Key OP Value"',
                          help="attribute filter; OP in = >= <= > < ~ "
                               "(repeatable)")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--text-fallback", action="store_true",
                          help="if --attr filters yield 0 hits, retry with "
                               "their values substring-matched against "
                               "MPN/description (rescues parts with corrupt "
                               "upstream attribute fields)")
    p_search.set_defaults(func=cmd_search)

    p_show = sub.add_parser("show", help="show one part by LCSC")
    p_show.add_argument("lcsc", help="LCSC number (e.g. C2040 or 2040)")
    p_show.set_defaults(func=cmd_show)

    p_schema = sub.add_parser("schema",
                              help="list categories, or attribute keys for one")
    p_schema.add_argument("category", nargs="?", default=None)
    p_schema.set_defaults(func=cmd_schema)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
