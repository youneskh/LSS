# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Installation hooks for the ``ls_medical_device`` module.

The scheduled actions of this module are created here rather than in an XML
data file. The reason is stated plainly: the exact field set of ``ir.cron`` in
Odoo 19.0 could not be verified from official documentation during preparation
of this module, and an XML record that writes a field which no longer exists
aborts the installation. Creating the records in Python allows the value
dictionary to be filtered against the fields the running registry actually
declares, so the module installs on any field set that still provides the core
scheduling attributes.

Each cron is created with an external identifier so that a module upgrade
updates the existing record instead of creating a duplicate.
"""

import logging

_logger = logging.getLogger(__name__)

#: Definition of the scheduled actions created at installation. ``code`` is the
#: server action body executed by the scheduler; ``model`` is the model the
#: action is bound to.
CRON_DEFINITIONS = (
    {
        "xml_id": "cron_check_post_market_obligations",
        "name": "Medical Devices: Check Post-Market Obligations",
        "model": "ls.md.device",
        "code": "model._cron_check_post_market_obligations()",
        "interval_number": 1,
        "interval_type": "days",
    },
    {
        "xml_id": "cron_expire_certificates",
        "name": "Medical Devices: Expire Certificates Past Their Expiry Date",
        "model": "ls.md.ce_marking",
        "code": "model._cron_expire_certificates()",
        "interval_number": 1,
        "interval_type": "days",
    },
)

#: Fields written on ``ir.cron`` only when the running registry declares them.
#: Every entry is optional by design; the core attributes are handled
#: separately and are required for the record to be usable.
OPTIONAL_CRON_FIELDS = ("state", "active", "user_id", "priority")


def _cron_values(env, definition):
    """Build the ``ir.cron`` values accepted by the running registry.

    :param env: the environment used to inspect the ``ir.cron`` fields.
    :param definition: one entry of :data:`CRON_DEFINITIONS`.
    :return: a dictionary restricted to fields that exist on ``ir.cron``.
    """
    cron_fields = env["ir.cron"]._fields
    model_record = env["ir.model"]._get(definition["model"])
    values = {
        "name": definition["name"],
        "model_id": model_record.id,
        "code": definition["code"],
        "interval_number": definition["interval_number"],
        "interval_type": definition["interval_type"],
    }
    candidates = {
        "state": "code",
        "active": True,
        "user_id": env.ref("base.user_root").id,
        "priority": 5,
    }
    for field_name in OPTIONAL_CRON_FIELDS:
        if field_name in cron_fields:
            values[field_name] = candidates[field_name]
    return {
        field_name: value
        for field_name, value in values.items()
        if field_name in cron_fields
    }


def post_init_hook(env):
    """Create or update the scheduled actions of the module.

    :param env: the environment provided by the module loader.
    """
    cron_model = env["ir.cron"]
    data_model = env["ir.model.data"]
    for definition in CRON_DEFINITIONS:
        xml_id = definition["xml_id"]
        full_xml_id = f"ls_medical_device.{xml_id}"
        values = _cron_values(env, definition)
        existing = env.ref(full_xml_id, raise_if_not_found=False)
        if existing:
            existing.write(values)
            _logger.info("Updated scheduled action %s", full_xml_id)
            continue
        cron = cron_model.create(values)
        data_model.create(
            {
                "name": xml_id,
                "module": "ls_medical_device",
                "model": "ir.cron",
                "res_id": cron.id,
                "noupdate": True,
            }
        )
        _logger.info("Created scheduled action %s", full_xml_id)
    return True
