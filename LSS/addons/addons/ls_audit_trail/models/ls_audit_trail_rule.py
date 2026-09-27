# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Audit rule: the configuration object of the audit engine."""

from __future__ import annotations

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..tools import constants


class LsAuditTrailRule(models.Model):
    """Declare which model, fields and operations are written to the trail.

    A rule is company specific when ``company_id`` is set and applies to every
    company when it is empty. Several rules may target the same model for
    different companies; the engine merges the rules that apply to the current
    company.

    Changes to a rule are recorded in the chatter of the rule itself. They are
    deliberately not written to ``ls.audit_trail.log``: the audit engine must
    never audit its own configuration, otherwise a configuration change would
    recurse into the engine that is being reconfigured.
    """

    _name = "ls.audit_trail.rule"
    _inherit = ["mail.thread"]
    _description = "Audit Trail Rule"
    _order = "model_name asc, id asc"

    # NULLS NOT DISTINCT (PostgreSQL 15 or later): a rule without company is
    # also unique per model; a plain UNIQUE treats every NULL as distinct.
    _model_company_unique = models.Constraint(
        "UNIQUE NULLS NOT DISTINCT (model_id, company_id)",
        "Only one audit rule may target a given model for a given company.",
    )

    name = fields.Char(required=True,
                       tracking=True,
                       help="Free text label of the rule, shown in the rule list.",)
    active = fields.Boolean(default=True,
                            tracking=True,
                            help="An archived rule is ignored by the audit engine.",)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Audited Model",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="Model whose records are written to the audit trail.",
    )
    model_name = fields.Char(
        string="Technical Model Name",
        related="model_id.model",
        store=True,
        index=True,
        readonly=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", tracking=True,
                                 help=(
                                     "Leave empty to apply the rule to every company. When set, the "
                                     "rule applies only to records owned by this company."),
                                 )
    log_create = fields.Boolean(
        string="Audit Creations",
        default=True,
        tracking=True,
        help="Write an audit entry when a record of the model is created.",
    )
    log_write = fields.Boolean(
        string="Audit Modifications",
        default=True,
        tracking=True,
        help="Write an audit entry when a record of the model is modified.",
    )
    log_unlink = fields.Boolean(
        string="Audit Deletions",
        default=True,
        tracking=True,
        help="Write an audit entry when a record of the model is deleted.",
    )
    field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="ls_audit_trail_rule_field_rel",
        column1="rule_id",
        column2="field_id",
        string="Audited Fields",
        domain="[('model_id', '=', model_id), ('store', '=', True)]",
        tracking=True,
        help=(
            "Fields written to the audit trail. Leave empty to audit every "
            "stored field of the model except the technical fields id, "
            "create_uid, create_date, write_uid, write_date and display_name."
        ),
    )
    excluded_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="ls_audit_trail_rule_excluded_field_rel",
        column1="rule_id",
        column2="field_id",
        string="Excluded Fields",
        domain="[('model_id', '=', model_id), ('store', '=', True)]",
        tracking=True,
        help=(
            "Fields never written to the audit trail, even when Audited "
            "Fields is empty. Use this list to keep high volume or "
            "confidential fields out of the trail."
        ),
    )
    entry_count = fields.Integer(
        string="Audit Entries",
        compute="_compute_entry_count",
        help="Number of audit entries recorded for the audited model.",
    )
    note = fields.Text(
        string="Justification",
        tracking=True,
        help=(
            "Documented reason for the scope of this rule. Regulated "
            "organisations are expected to justify why a model or a field is "
            "audited or excluded."
        ),
    )

    @api.depends("model_name")
    def _compute_entry_count(self):
        """Count the audit entries already recorded for the audited model."""
        log_model = self.env["ls.audit_trail.log"]
        counts = {}
        model_names = [name for name in self.mapped("model_name") if name]
        if model_names:
            grouped = log_model.sudo()._read_group(
                domain=[("model_name", "in", model_names)],
                groupby=["model_name"],
                aggregates=["__count"],
            )
            counts = {model_name: count for model_name, count in grouped}
        for rule in self:
            rule.entry_count = counts.get(rule.model_name, 0)

    @api.constrains("model_id")
    def _check_model_is_auditable(self):
        """Reject models that the engine must never audit.

        Abstract models own no table, transient models are cleared by the
        vacuum job, and the models of this module would make the engine
        recurse into itself.
        """
        for rule in self:
            model_name = rule.model_id.model
            if model_name in constants.NON_AUDITABLE_MODELS:
                raise ValidationError(
                    _(
                        "The model %(model)s belongs to the audit engine and "
                        "cannot be audited.",
                        model=model_name,
                    )
                )
            model = self.env.get(model_name)
            if model is None:
                raise ValidationError(
                    _(
                        "The model %(model)s is not present in the registry.",
                        model=model_name,
                    )
                )
            if model._abstract:
                raise ValidationError(
                    _(
                        "The model %(model)s is abstract and owns no database "
                        "table.",
                        model=model_name,
                    )
                )
            if model._transient:
                raise ValidationError(
                    _(
                        "The model %(model)s is transient. Transient records "
                        "are removed by the vacuum job and are not part of the "
                        "regulated record set.",
                        model=model_name,
                    )
                )

    @api.constrains("model_id", "field_ids", "excluded_field_ids")
    def _check_fields_belong_to_model(self):
        """Reject fields that do not belong to the audited model."""
        for rule in self:
            selected = rule.field_ids | rule.excluded_field_ids
            foreign = selected.filtered(lambda f, r=rule: f.model_id != r.model_id)
            if foreign:
                raise ValidationError(
                    _(
                        "The fields %(fields)s do not belong to the model "
                        "%(model)s.",
                        fields=", ".join(sorted(foreign.mapped("name"))),
                        model=rule.model_id.model,
                    )
                )

    @api.constrains("log_create", "log_write", "log_unlink")
    def _check_at_least_one_operation(self):
        """Reject a rule that audits no operation at all."""
        for rule in self:
            if not (rule.log_create or rule.log_write or rule.log_unlink):
                raise ValidationError(
                    _("An audit rule must audit at least one operation.")
                )

    @api.onchange("model_id")
    def _onchange_model_id(self):
        """Clear the field selections when the audited model changes."""
        self.field_ids = [fields.Command.clear()]
        self.excluded_field_ids = [fields.Command.clear()]

    @api.model_create_multi
    def create(self, vals_list):
        """Create rules and drop the cached audit configuration."""
        rules = super().create(vals_list)
        self.env["ls.audit_trail.log"]._ls_clear_audit_config_cache()
        return rules

    def write(self, vals):
        """Update rules and drop the cached audit configuration."""
        result = super().write(vals)
        self.env["ls.audit_trail.log"]._ls_clear_audit_config_cache()
        return result

    def unlink(self):
        """Delete rules and drop the cached audit configuration."""
        result = super().unlink()
        self.env["ls.audit_trail.log"]._ls_clear_audit_config_cache()
        return result

    def action_view_entries(self):
        """Open the audit entries recorded for the audited model.

        :return: an ``ir.actions.act_window`` dictionary.
        """
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_audit_trail.action_ls_audit_trail_log"
        )
        action["domain"] = [("model_name", "=", self.model_name)]
        action["context"] = {"search_default_group_operation": 1}
        return action
