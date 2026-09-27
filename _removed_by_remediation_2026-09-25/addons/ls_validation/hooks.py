# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Installation hooks of the Validation Management module."""

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Finalise the configuration of the scheduled action after installation.

    The ``numbercall`` and ``doall`` fields of ``ir.cron`` were present in
    older Odoo releases and are reported as removed in recent ones. Published
    third party sources disagree on the exact release, and this could not be
    confirmed from the official Odoo 19 documentation, so the data file does
    not reference them: writing a field that does not exist would abort the
    installation. The hook sets ``numbercall`` to ``-1`` only when the field
    actually exists in the running build, which guarantees that the scheduled
    action keeps running indefinitely on every supported build.

    :param env: environment of the installing database.
    """
    cron = env.ref(
        "ls_validation.cron_ls_validation_refresh_status", raise_if_not_found=False
    )
    if not cron:
        _logger.warning(
            "ls_validation: scheduled action not found after installation."
        )
        return
    if "numbercall" in cron._fields:
        cron.write({"numbercall": -1})
        _logger.info("ls_validation: scheduled action set to run indefinitely.")
