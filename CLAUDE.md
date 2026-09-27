# Odoo 19 Community Edition (CE) - Project Guidelines

## Environment & Tech Stack
- **Odoo Version:** 19.0 Community Edition (CE)
- **Python Version:** 3.12+
- **Frontend Framework:** OWL (Odoo Web Library) v2+
- **Main Addons Path:** `./custom_addons`

## Strict CE Compatibility Rules
- **No Enterprise Dependencies:** Do NOT import or depend on Odoo Enterprise modules (e.g., `web_enterprise`, `account_accountant`, `quality`, `sign`, `studio`).
- **Standard Module Dependencies:** Depend only on CE base modules (`base`, `web`, `mail`, `account`, `sale`, `purchase`, `stock`, `hr`, `website`).

## Backend (Python) Standards
- Use Python 3.12 syntax and strict type hints where applicable.
- ORM declarations must strictly follow Odoo 19 guidelines:
  - Fields require explicit `string=` parameters.
  - Compute functions must list all dependent fields via `@api.depends()`.
  - Use `self.ensure_one()` for single-record logic.
- Always implement access rights in `security/ir.model.access.csv` for any new `models.Model`.

## Frontend & Views (XML / OWL)
- Views must use XML inheritance (`<field name="inherit_id" ref="module.view_id"/>`) rather than redefining full views.
- Custom JS/UI components must follow OWL v2 component class structures (`import { Component } from "@odoo/owl"`).
- Define assets in `__manifest__.py` under `assets` keys (`web.assets_backend`, `web.assets_frontend`).

## Project Layout
- `custom_addons/`: Subdirectories for custom modules (each must contain `__manifest__.py`, `__init__.py`, `models/`, `views/`, `security/`).
