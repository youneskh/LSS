# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Life Sciences - Import & Export Compliance.

Foreign-trade compliance platform for the regulated life-sciences
sectors (pharmaceutical, medical devices, cosmetics). Provides a
cited regulatory provision registry and a generic compliance engine
that is configured by that registry; it does not assert any
regulatory requirement that is not first recorded as a cited
provision in the registry.

See ``doc/00_foundation_architecture.md`` for the architecture and
``doc/02_regulatory_analysis.md`` for the regulatory statement.
"""

from . import models
from . import wizards
