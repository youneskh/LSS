# ODOO 19 API VERIFICATION RECORD — `ls_lab`

**Module:** `ls_lab` (Laboratory Management)
**Verification date:** 2026-08-06
**Source of truth:** `github.com/odoo/odoo`, branch `19.0`, retrieved live during this build session.

---

## 1. Purpose

Earlier modules in the Life Sciences Suite were built in an offline container with no access
to Odoo source. A number of Odoo 19 API facts could not be verified and were **engineered
around** (documented as risks in those modules' validation reports).

During this build session, network access to `raw.githubusercontent.com` and
`api.github.com` was available. Every Odoo 19 API fact this module depends on was therefore
verified **directly against branch `19.0` source** rather than assumed.

This record lists each fact, the file and line that proves it, and the resulting design
decision. Facts that remain unverified are stated as unverified.

---

## 2. Verified facts — group / security field names

These three facts were previously **unverified** across the whole suite and forced defensive
workarounds. All three are now resolved.

| # | Fact | Evidence | Verdict |
|---|------|----------|---------|
| 1 | `res.users` groups field is **`group_ids`** (not `groups_id`) | `odoo/addons/base/models/res_users.py` L257: `group_ids = fields.Many2many('res.groups', 'res_groups_users_rel', 'uid', 'gid', string='Groups', ...)` | VERIFIED |
| 2 | `ir.rule` group-restriction field is **`groups`** (Many2many) | `odoo/addons/base/models/ir_rule.py` L25: `groups = fields.Many2many('res.groups', 'rule_group_rel', 'rule_group_id', 'group_id', ondelete='restrict')` | VERIFIED |
| 3 | `ir.ui.menu` group field is **`group_ids`** (not `groups_id`) | `odoo/addons/base/models/ir_ui_menu.py` L29: `group_ids = fields.Many2many('res.groups', 'ir_ui_menu_group_rel', ...)` | VERIFIED |

**Design consequence.** Unlike earlier suite modules, `ls_lab` does **not** need to make all
record rules global. Group-restricted `ir.rule` records are used where appropriate, and menus
declare `group_ids`. This is a genuine security improvement, not a workaround.

---

## 3. Verified facts — `res.groups` and privileges

| Fact | Evidence | Verdict |
|------|----------|---------|
| `res.groups.privilege` model exists | `odoo/addons/base/models/res_groups_privilege.py` L5: `_name = 'res.groups.privilege'` | VERIFIED |
| `res.groups.privilege_id` is the Many2one on `res.groups` | `res_groups.py` L36: `privilege_id = fields.Many2one('res.groups.privilege', string='Privilege', index=True)` | VERIFIED |
| `res.groups.privilege.category_id` targets `ir.module.category` | `res_groups_privilege.py`: `category_id = fields.Many2one('ir.module.category', string='Category', index=True)` | VERIFIED |
| `res.groups.implied_ids` unchanged | `res_groups.py` L69: `implied_ids = fields.Many2many('res.groups', 'res_groups_implied_rel', 'gid', 'hid', ...)` | VERIFIED |
| `models.Constraint` is the Odoo 19 constraint mechanism | `res_groups.py` L39: `_name_uniq = models.Constraint("UNIQUE (privilege_id, name)", ...)` — used by core itself | VERIFIED |

**Design consequence.** `ls_lab` ships a `res.groups.privilege` record and assigns
`privilege_id` on all four security groups. All SQL constraints use `models.Constraint`.

---

## 4. Verified facts — view schema (root cause of the `ls_cosmetics` failure)

Odoo 19 has **no single `view.rng`**. It ships one RNG per view type:

```
odoo/addons/base/rng/
  activity_view.rng   calendar_view.rng   common.rng
  graph_view.rng      list_view.rng       pivot_view.rng   search_view.rng
```

A diagnostic that validates all view archs against a single `view.rng` is validating against
a schema that does not exist in 19.0.

### 4.1 The `<group>` element

`common.rng`, `<rng:define name="group">`, permits **exactly** these attributes:

- from `overload`: `position` (+ nested `<attribute>` elements)
- from `access_rights`: `groups`
- direct: `colspan`, `rowspan`, `fill`, `height`, `width`, `name`, `color`, `invisible`
- from `container`: `col`

**`expand` is NOT permitted on `<group>`. `string` is NOT permitted on `<group>`.**

`expand` *is* permitted on `<field>` (`common.rng`, `<rng:define name="field">`), which is the
likely origin of the confusion.

### 4.2 Confirmed root cause

The construct `<group expand="0" string="Group By">` carries **two** attributes that the
Odoo 19 RNG rejects on `<group>`. This is a schema violation that offline XML
well-formedness checking cannot detect — which is exactly the reported `ls_cosmetics`
symptom (zero-finding static check, failure only on live install).

### 4.3 Verified correct pattern

`<group>` accepts `<filter>` children (via `container`), and Odoo 19 core itself writes the
Group By block as a **bare `<group>`**:

```xml
<!-- addons/stock/views/stock_lot_views.xml, search_product_lot_filter -->
<group>
    <filter name="group_by_product" string="Product" domain="[]"
            context="{'group_by': 'product_id'}"/>
    <filter name="group_by_location" string="Location" domain="[]"
            context="{'group_by': 'location_id'}" groups="stock.group_stock_multi_locations"/>
</group>
```

Verified counts in that core file: `<tree` = 0, `<list` = 1, `oe_chatter` = 0,
`<chatter` = 1, `expand=` = 0.

**Design consequence.** Every search view in `ls_lab` uses a bare `<group>` for Group By
filters. The module's static checker enforces the full RNG attribute allow-list on `<group>`
and additionally validates every view arch against the **correct per-type RNG**.

### 4.4 Remediation applicable to prior modules

The same defect will exist in any earlier suite module that used
`<group expand="0" string="Group By">`. Remediation is a mechanical two-attribute deletion:

```
<group expand="0" string="Group By">   ->   <group>
```

A retrofit scanner is shipped in `tools/` (see §8).

---

## 5. Verified facts — other view constructs

| Fact | Evidence | Verdict |
|------|----------|---------|
| `<list>` replaces `<tree>` | `list_view.rng` defines `list`; core `stock_lot_views.xml` uses `<list ... multi_edit="1">`, zero `<tree` | VERIFIED |
| `<chatter/>` replaces the `oe_chatter` div | core `stock_lot_views.xml` L59: `<chatter/>`; zero `oe_chatter` | VERIFIED |
| `<separator/>` is valid in `<search>` | `search_view.rng` `<rng:ref name="separator"/>`; core uses `<separator invisible="1"/>` | VERIFIED |
| `<filter>` requires `name`; supports `string`, `domain`, `context`, `date`, `groups`, `invisible` | `common.rng` `<rng:define name="filter">` — `name` is non-optional | VERIFIED |
| `<searchpanel>` is valid in `<search>` | `search_view.rng` `<rng:define name="searchpanel">` | VERIFIED |
| `<list>` supports `default_order`, `default_group_by`, `multi_edit`, `decoration-*` | `list_view.rng` `<rng:define name="list">` | VERIFIED |
| `<list string="...">` is accepted but has no effect | `list_view.rng` inline comment: *deprecated, has no effect anymore* | VERIFIED |

---

## 6. Verified facts — models and dependencies

| Fact | Evidence | Verdict |
|------|----------|---------|
| `uom.uom` is the correct model name | `addons/uom/models/uom_uom.py` L18: `_name = 'uom.uom'` | VERIFIED |
| `uom` is a module in Odoo 19 Community | present in `addons/` listing (631 modules) | VERIFIED |
| `stock.lot` is the model name (not `stock.production.lot`) | `addons/stock/models/stock_lot.py` L25: `_name = 'stock.lot'` | VERIFIED |
| `stock.lot` inherits `mail.thread`, `mail.activity.mixin` | `stock_lot.py` L26 | VERIFIED |
| `maintenance` **is** in Odoo 19 Community | `addons/maintenance/__manifest__.py` retrieved; `'license': 'LGPL-3'` | VERIFIED |
| `maintenance` depends only on `mail` | its manifest: `'depends': ['mail']` | VERIFIED |
| `numbercall` / `doall` absent from `ir.cron` | zero occurrences in `odoo/addons/base/models/ir_cron.py` | VERIFIED |

**Design consequence.** `ls_lab` uses `uom.uom` as a real Many2one instead of the free-text
`Char` workaround used in earlier modules, and links samples to `stock.lot`.

---

## 7. Verified NEGATIVE finding — the `quality` module

**`quality` is NOT part of Odoo 19 Community Edition.**

Evidence: the full `addons/` listing for branch `19.0` contains **631 modules and zero
modules whose name contains `qualit`**. `addons/quality/__manifest__.py` returns HTTP 404.

This contradicts the suite Functional Specification §5.2.6, which documents `quality` as a
Layer 1 native Community module under LGPLv3 with models `quality.point`, `quality.check`,
`quality.alert`.

**Design consequence.** `ls_lab` does **not** depend on `quality` and does not reference
`quality.*` models. All laboratory quality-control functionality is implemented natively
within this module. See `doc/SPECIFICATION_DEVIATIONS.md`.

A second specification correction: §5.2.10 states `maintenance` depends on `base, hr`. Its
actual Odoo 19 manifest declares `'depends': ['mail']`.

---

## 8. Facts that remain UNVERIFIED

Stated explicitly, per the Truth Protocol.

| # | Item | Status |
|---|------|--------|
| 1 | Behaviour of this module on a **live** Odoo 19 instance | **UNVERIFIED.** No Odoo runtime or PostgreSQL server exists in the build container. Source-level verification of the schema is not a substitute for installation. |
| 2 | Runtime rendering of every widget used | **UNVERIFIED.** Widget names were taken from core usage, but visual rendering was not observed. |
| 3 | Whether other suite modules contain the `<group expand=...>` defect | **UNVERIFIED for those modules** — their source is not present in this container. `tools/retrofit_scan.py` is provided so the receiving team can determine this. |
| 4 | ICH Q1A(R2) storage-condition values | **NOT SHIPPED.** No storage conditions, timepoints or acceptance limits are hardcoded or shipped as data; all are configuration. |
| 5 | Pharmacopoeial monograph content | **NOT SHIPPED.** Method references are free-text fields; no monograph text or limits are embedded. |

---

## 9. Verification method

All facts above were obtained by direct retrieval from `github.com/odoo/odoo` branch `19.0`
during this session:

- `api.github.com/repos/odoo/odoo/contents/<path>?ref=19.0` for directory listings
- `raw.githubusercontent.com/odoo/odoo/19.0/<path>` for file contents

Retrieved artefacts were parsed locally with the Python standard library and `lxml`. The RNG
schemas retrieved are used by this module's static checker as the validation schema, so the
checker validates against the **same schema the Odoo 19 server uses**.
