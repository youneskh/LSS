# -*- coding: utf-8 -*-
"""Small constructors that keep the content files readable."""


def tr(en, fr):
    return {"en": en, "fr": fr}


def part(num, pid, en_title, fr_title, en_lead, fr_lead, en_mods, fr_mods=None):
    return {"kind": "part", "id": pid, "num": num,
            "en": {"title": en_title, "lead": en_lead, "modules": en_mods},
            "fr": {"title": fr_title, "lead": fr_lead, "modules": fr_mods or en_mods}}


def module(mid, tech, en_title, fr_title, en_blocks, fr_blocks):
    return {"kind": "module", "id": mid, "tech": tech,
            "en": {"title": en_title, "blocks": en_blocks},
            "fr": {"title": fr_title, "blocks": fr_blocks}}


def sop(code, module_name, menu, en, fr, flows=(), schematics=(), shots=(), related=(), refs=()):
    return {"kind": "sop", "code": code, "module": module_name, "menu": menu,
            "flows": list(flows), "schematics": list(schematics), "shots": list(shots),
            "related": list(related), "refs": list(refs), "en": en, "fr": fr}


def roles_table(lang, rows):
    head = ["Group", "Main rights"] if lang == "en" else ["Groupe", "Droits principaux"]
    return ("table", head, rows)
