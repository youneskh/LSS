# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Audit trail line: one row per field changed by an audited operation."""

from __future__ import annotations

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class LsAuditTrailLogLine(models.Model):
    """Field level detail of an audit trail entry.

    A line carries the technical values, which are hashed and used for exact
    comparison, and the display values, which are shown to reviewers and
    exported to evidence packs. Like its parent entry, a line can never be
    modified or deleted through the ORM.

    The context of the operation is denormalised onto the line as ordinary
    stored columns, written once by the capture engine. This keeps the line
    searchable, sortable and groupable without ever requiring a write after
    creation, which is what makes strict immutability possible.
    """

    _name = "ls.audit_trail.log.line"
    _description = "Audit Trail Field Change"
    _order = "log_id desc, field_name asc"
    _rec_name = "field_name"

    log_id = fields.Many2one(
        comodel_name="ls.audit_trail.log",
        string="Audit Entry",
        required=True,
        readonly=True,
        index=True,
        ondelete="cascade",
    )
    field_name = fields.Char(
        string="Field",
        required=True,
        readonly=True,
        index=True,
        help="Technical name of the changed field.",
    )
    old_value_technical = fields.Text(
        string="Old Value (technical)",
        readonly=True,
        help=(
            "Value before the operation, in the locale independent "
            "representation that is hashed."
        ),
    )
    new_value_technical = fields.Text(
        string="New Value (technical)",
        readonly=True,
        help=(
            "Value after the operation, in the locale independent "
            "representation that is hashed."
        ),
    )
    old_value_display = fields.Text(
        string="Old Value",
        readonly=True,
        help="Value before the operation, in human readable form.",
    )
    new_value_display = fields.Text(
        string="New Value",
        readonly=True,
        help="Value after the operation, in human readable form.",
    )

    # ------------------------------------------------------------------
    # Denormalised context columns
    #
    # These are ordinary stored columns rather than related fields. They are
    # written once, by the capture engine, at the moment the line is created,
    # and they are never recomputed afterwards. That is what allows the line to
    # be searchable, sortable and groupable while remaining strictly immutable:
    # a stored *related* field would have to be written by the recomputation
    # machinery after creation, which the write guard below forbids.
    # ------------------------------------------------------------------
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 readonly=True,
                                 index=True,
                                 ondelete="restrict",)
    event_datetime = fields.Datetime(
        string="Event Date",
        required=True,
        readonly=True,
        index=True,
    )
    model_name = fields.Char(
        string="Model",
        required=True,
        readonly=True,
        index=True,
    )
    res_id = fields.Integer(
        string="Record ID",
        required=True,
        readonly=True,
        index=True,
    )
    res_name = fields.Char(
        string="Record",
        readonly=True,
    )
    operation = fields.Selection(
        selection=[
            ("create", "Creation"),
            ("write", "Modification"),
            ("unlink", "Deletion"),
        ],
        readonly=True,
        index=True,
    )
    user_id = fields.Many2one(comodel_name="res.users", required=True,
                              readonly=True,
                              index=True,
                              ondelete="restrict",)
    sequence_number = fields.Integer(
        string="Chain Position",
        related="log_id.sequence_number",
        readonly=True,
        help=(
            "Chain position of the parent entry. It is resolved on read rather "
            "than stored, because the position is assigned when the parent "
            "entry is sealed, which happens after this line has been created."
        ),
    )
    field_label = fields.Char(compute="_compute_field_metadata",
                              help=(
                                  "Translated label of the field, resolved from the registry at "
                                  "display time. It is not stored, so a later relabelling of the "
                                  "field cannot alter the recorded evidence."),
                              )
    field_type = fields.Char(compute="_compute_field_metadata",
                             help="Type of the field, resolved from the registry at display time.",)

    @api.depends("model_name", "field_name")
    def _compute_field_metadata(self):
        """Resolve the label and the type of the changed field.

        The metadata is read from the registry rather than stored, because the
        registry is the only authoritative source of the current label and
        because the evidence itself is carried by the value fields. A field that
        no longer exists in the registry falls back to its technical name.
        """
        cache = {}
        for line in self:
            model_name = line.model_name
            key = (model_name, line.field_name)
            if key not in cache:
                model = self.env.get(model_name)
                has_field = model is not None and line.field_name in model._fields
                if not has_field:
                    cache[key] = (line.field_name, "")
                else:
                    description = model.fields_get(
                        [line.field_name], ["string", "type"]
                    ).get(line.field_name, {})
                    cache[key] = (
                        description.get("string") or line.field_name,
                        description.get("type") or "",
                    )
            line.field_label, line.field_type = cache[key]

    def write(self, vals):
        """Reject every modification.

        :param vals: field values requested by the caller.
        :raise AccessError: always.
        """
        raise AccessError(
            _("Audit trail field changes are immutable and cannot be modified.")
        )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_trail_log_line(self):
        """Reject every deletion performed through the ORM.

        Lines are removed by the database only, through the foreign key cascade
        of an approved retention run on the parent entry.

        :raise AccessError: always.
        """
        raise AccessError(_("Audit trail field changes cannot be deleted."))
