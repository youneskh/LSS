# -*- coding: utf-8 -*-
"""Assembly of the handbook: the order of BOOK is the order of the book."""
import importlib

_PARTS = ["front", "part1a", "part1b", "part1c", "part2a", "part2b", "part3a", "part3b",
          "part3c", "part4_6", "annexes"]

BOOK = []
for _name in _PARTS:
    try:
        _mod = importlib.import_module(f"{__name__}.{_name}")
    except ModuleNotFoundError as exc:
        if exc.name == f"{__name__}.{_name}":
            continue
        raise
    BOOK.extend(_mod.ITEMS)

from .shots_extra import apply as _apply_extra_shots  # noqa: E402

_apply_extra_shots(BOOK)
