# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Interception layer of the audit engine.

This module extends the abstract Odoo model named ``base``, from which every
concrete and abstract model of the registry inherits. Extending ``base`` is the
supported way to add behaviour to all models at once and is used by Odoo's own
``web`` addon; the alternative, replacing methods on ``BaseModel`` at import
time, is monkey patching and is not upgrade safe.

Design decisions
----------------

**The guard must be cheap.** Every ``create``, ``write`` and ``unlink`` of every
model in the database passes through the methods below. When a model is not
audited, the added cost is one attribute test and one lookup in a registry
level cache. No query is issued.

**No auditing while the registry is loading.** During installation and upgrade
the ORM writes a large number of technical records, and the tables of this
module may not exist yet. ``registry.ready`` is false in that window, so the
engine stays inactive.

**A failure to audit fails the transaction.** No exception is caught around the
capture. If the audit trail cannot be written, the audited operation must not
be committed either; a silently missing entry would be a data integrity defect
rather than a degraded service.

**Only values passed to the ORM are captured.** A ``write`` entry records the
fields present in the ``vals`` dictionary whose value actually changed. Stored
computed fields are recomputed during the flush that follows ``write``, so they
are outside the captured set. Audit the fields listed in the ``@api.depends``
of a computed field to obtain an auditable record of what caused it to change.
"""

from __future__ import annotations

from odoo import api, models

from ..tools import constants


class Base(models.AbstractModel):
    """Add audit capture to every model of the registry."""

    _inherit = "base"

    def _ls_audit_rule_scope(self):
        """Return which companies hold audit rules for the model of ``self``.

        This is the cheap guard run on every ``create``, ``write`` and
        ``unlink``: attribute tests and one lookup in a registry level cache.

        :return: ``None`` when the model must not be audited, otherwise a tuple
            ``(log_model, has_global_rule, rule_company_ids)``.
        """
        if self._abstract or self._transient:
            return None
        if self._name in constants.NON_AUDITABLE_MODELS:
            return None
        if not self.env.registry.ready:
            return None
        log_model = self.env.get("ls.audit_trail.log")
        if log_model is None:
            return None
        log_model = log_model.sudo()
        has_global_rule, rule_company_ids = log_model._ls_audit_rule_companies(
            self._name
        )
        if not has_global_rule and not rule_company_ids:
            return None
        return (log_model, has_global_rule, rule_company_ids)

    def _ls_audit_plan(self):
        """Return the audit configuration applying to ``self``, per company.

        Audit rules may be restricted to one company. The rule that applies
        to a record is the rule of the company owning the record's audit
        chain (its ``company_id``, or the active company for records without
        one), not the company active in the user session: a user working in
        several companies at once must not escape, or borrow, the rules of
        another company.

        :return: a list of ``(records, (operations, field_names))`` tuples,
            ``operations`` and ``field_names`` being documented on
            ``ls.audit_trail.log._ls_audit_config_for``. The list is empty
            whenever the model must not be audited.
        """
        scope = self._ls_audit_rule_scope() if self else None
        if scope is None:
            return []
        log_model, _has_global_rule, rule_company_ids = scope
        if not rule_company_ids:
            return [(self, log_model._ls_audit_config_for(self._name, False))]
        ids_by_company = {}
        for record in self:
            company_id = log_model._ls_record_company_id(record)
            ids_by_company.setdefault(company_id, []).append(record.id)
        plan = []
        for company_id, record_ids in ids_by_company.items():
            config = log_model._ls_audit_config_for(self._name, company_id)
            if config[0]:
                plan.append((self.browse(record_ids), config))
        return plan

    @api.model_create_multi
    def create(self, vals_list):
        """Create records and capture a creation entry when audited.

        :param vals_list: list of field value dictionaries.
        :return: the created recordset.
        """
        records = super().create(vals_list)
        for group, (operations, configured_fields) in records._ls_audit_plan():
            if constants.OPERATION_CREATE not in operations:
                continue
            log_model = self.env["ls.audit_trail.log"].sudo()
            field_names = log_model._ls_eligible_field_names(
                self._name, configured_fields
            )
            if not field_names:
                continue
            after = log_model._ls_snapshot(group, field_names)
            log_model._ls_capture(
                group, constants.OPERATION_CREATE, field_names, {}, after
            )
        return records

    def write(self, vals):
        """Write values and capture a modification entry when audited.

        The value of every captured field is read before and after the write so
        that a write which does not change a value produces no entry.

        :param vals: field values requested by the caller.
        :return: ``True``, as returned by the base implementation.
        """
        captures = []
        for group, (operations, configured_fields) in self._ls_audit_plan():
            if constants.OPERATION_WRITE not in operations:
                continue
            log_model = self.env["ls.audit_trail.log"].sudo()
            eligible = log_model._ls_eligible_field_names(self._name, configured_fields)
            field_names = tuple(name for name in eligible if name in vals)
            if field_names:
                captures.append(
                    (group, field_names, log_model._ls_snapshot(group, field_names))
                )
        result = super().write(vals)
        for group, field_names, before in captures:
            log_model = self.env["ls.audit_trail.log"].sudo()
            after = log_model._ls_snapshot(group, field_names)
            log_model._ls_capture(
                group, constants.OPERATION_WRITE, field_names, before, after
            )
        return result

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_base(self):
        """Capture a deletion entry when audited, then delete the records.

        The snapshot is taken before the deletion, because the values are no
        longer readable afterwards. The recorded record identifier deliberately
        carries no foreign key, so the entry survives the record it describes.

        :return: ``True``, as returned by the base implementation.
        """
        plan = []
        if self and self._ls_audit_rule_scope() is not None:
            plan = self.exists()._ls_audit_plan()
        for group, (operations, configured_fields) in plan:
            if constants.OPERATION_UNLINK not in operations:
                continue
            log_model = self.env["ls.audit_trail.log"].sudo()
            field_names = log_model._ls_eligible_field_names(
                self._name, configured_fields
            )
            if field_names:
                before = log_model._ls_snapshot(group, field_names)
                log_model._ls_capture(
                    group, constants.OPERATION_UNLINK, field_names, before, {}
                )
