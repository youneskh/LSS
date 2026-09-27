# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Installation hooks for ``ls_cosmetics``."""

import logging

_logger = logging.getLogger(__name__)

#: External identifiers of the scheduled actions shipped by this module.
_CRON_XML_IDS = (
    "ls_cosmetics.cron_ls_cosmetic_pif_retention",
    "ls_cosmetics.cron_ls_cosmetic_assessment_review",
    "ls_cosmetics.cron_ls_cosmetic_dz_deadlines",
)

#: Legacy repetition fields of ``ir.cron``.  They existed up to Odoo 17 and
#: are reported as removed from Odoo 18 onwards, but this could not be
#: confirmed from official Odoo 19 documentation.  Rather than write them in
#: a data file, which would break installation if they are absent, the hook
#: sets them only when the running server still declares them.  ``numbercall``
#: historically defaulted to 1, which would have deactivated the scheduled
#: actions after a single run.
_LEGACY_CRON_DEFAULTS = {
    "numbercall": -1,
    "doall": False,
}


def post_init_hook(env):
    """Make the shipped scheduled actions repeat indefinitely.

    :param env: the Odoo environment supplied by the module loader.
    """
    cron_model = env["ir.cron"]
    applicable = {
        field_name: value
        for field_name, value in _LEGACY_CRON_DEFAULTS.items()
        if field_name in cron_model._fields
    }
    if not applicable:
        _logger.info(
            "ls_cosmetics: ir.cron declares no legacy repetition field; "
            "scheduled actions keep the server defaults."
        )
        return
    for xml_id in _CRON_XML_IDS:
        cron = env.ref(xml_id, raise_if_not_found=False)
        if not cron:
            _logger.warning("ls_cosmetics: scheduled action %s not found.", xml_id)
            continue
        cron.write(applicable)
    _logger.info(
        "ls_cosmetics: applied legacy ir.cron repetition fields %s.",
        ", ".join(sorted(applicable)),
    )
