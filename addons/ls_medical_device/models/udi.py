# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Unique Device Identification assignments.

Article 27 of Regulation (EU) 2017/745 establishes a UDI system consisting of
a UDI device identifier specific to a manufacturer and a device, and a UDI
production identifier that identifies the unit of device production. Article
27(7) requires the manufacturer to keep an up-to-date list of all UDIs it has
assigned as part of the technical documentation. This model is that list.

The module records identifiers and the production-identifier components that
apply to them. It does not generate identifiers: identifier syntax is defined
by the issuing entity, and generating a code without applying the issuing
entity's rules would produce an identifier that is well-formed in appearance
only. Identifiers are therefore entered from the issuing entity's system.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdUdi(models.Model):
    """A single UDI assignment for one packaging level of one device."""

    _name = "ls.md.udi"
    _description = "Unique Device Identification Assignment"
    _inherit = ["mail.thread"]
    _order = "device_id, packaging_level, id"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        help="Internal reference of the UDI assignment record.",
    )
    device_id = fields.Many2one(comodel_name="ls.md.device", required=True,
                                ondelete="cascade",
                                index=True,
                                tracking=True,
                                help="Device to which the identifier is assigned.",)
    company_id = fields.Many2one(comodel_name="res.company", related="device_id.company_id",
                                 store=True,
                                 index=True,
                                 help="Company owning the device, propagated for access scoping.",)
    udi_kind = fields.Selection(
        selection=constants.UDI_KIND_SELECTION,
        string="Identifier Kind",
        required=True,
        default="udi_di",
        tracking=True,
        help=(
            "Basic UDI-DI groups devices sharing intended purpose, risk class "
            "and essential design; UDI-DI identifies a specific device model "
            "at a given packaging level."
        ),
    )
    udi_di = fields.Char(
        string="Device Identifier",
        required=True,
        tracking=True,
        help=(
            "Identifier as issued by the issuing entity. Entered rather than "
            "generated, because the syntax is defined by the issuing entity."
        ),
    )
    issuing_entity = fields.Selection(selection=constants.UDI_ISSUING_ENTITY_SELECTION, required=True,
                                      default="gs1",
                                      help=(
                                          "Entity operating the identifier assignment system. Confirm the "
                                          "designation of the entity against the applicable implementing "
                                          "decision before relying on it."),
                                      )
    issuing_entity_note = fields.Char(help="Free text used when the issuing entity is recorded as 'Other'.",)
    packaging_level = fields.Selection(selection=constants.UDI_PACKAGING_LEVEL_SELECTION, required=True,
                                       default="unit_of_use",
                                       help=(
                                           "Packaging level covered by this identifier. Article 27(1) "
                                           "requires a UDI to be assigned to the device and to all higher "
                                           "levels of packaging."
                                           ),
                                       )
    quantity_per_package = fields.Integer(default=1,
                                          help="Number of units of use contained in this packaging level.",)
    carrier_type = fields.Selection(selection=constants.UDI_CARRIER_SELECTION, default="2d",
                                    help="Technology used to present the identifier on the label.",)
    is_direct_marking = fields.Boolean(
        string="Direct Marking",
        help=(
            "The carrier is applied to the device itself rather than only to "
            "its packaging, as required for reusable devices."
        ),
    )
    direct_marking_identical = fields.Boolean(
        string="Direct Marking Identical to Label",
        default=True,
        help=(
            "Uncheck when the identifier marked on the device differs from the "
            "identifier on the label, in which case both must be recorded."
        ),
    )

    # ------------------------------------------------------------------
    # Production identifier components (MDR Article 27(1)(a)(ii))
    # ------------------------------------------------------------------
    pi_lot_number = fields.Boolean(
        string="PI Includes Lot Number",
        help="The production identifier carries the lot or batch number.",
    )
    pi_serial_number = fields.Boolean(
        string="PI Includes Serial Number",
        help="The production identifier carries the serial number.",
    )
    pi_manufacturing_date = fields.Boolean(
        string="PI Includes Manufacturing Date",
        help="The production identifier carries the manufacturing date.",
    )
    pi_expiry_date = fields.Boolean(
        string="PI Includes Expiry Date",
        help="The production identifier carries the expiry date.",
    )
    pi_software_version = fields.Boolean(
        string="PI Includes Software Version",
        help="The production identifier carries the software identification.",
    )
    pi_component_summary = fields.Char(
        string="Production Identifier Components",
        compute="_compute_pi_component_summary",
        store=True,
        help="Readable summary of the selected production identifier components.",
    )

    # ------------------------------------------------------------------
    # Lifecycle and database submission
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=constants.UDI_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    assignment_date = fields.Date(tracking=True,
                                  copy=False,
                                  help="Date on which the identifier was assigned to the device.",)
    database_name = fields.Char(
        string="UDI Database",
        help=(
            "Name of the database to which the record was submitted, for "
            "example the European or the United States UDI database. Recorded "
            "as free text so that any target database can be captured."
        ),
    )
    database_submission_date = fields.Date(
        string="Submitted On",
        copy=False,
        tracking=True,
        help="Date on which the record was submitted to the UDI database.",
    )
    database_reference = fields.Char(copy=False,
                                     help="Reference returned by the UDI database for the submitted record.",)
    obsolete_date = fields.Date(
        string="Obsolete Since",
        copy=False,
        help="Date from which the identifier is no longer in use.",
    )
    obsolete_reason = fields.Text(
        string="Obsolescence Reason",
        copy=False,
        help="Justification for retiring the identifier.",
    )
    notes = fields.Text()

    _udi_di_unique = models.Constraint(
        "UNIQUE(udi_di, packaging_level, company_id)",
        "The device identifier must be unique per packaging level and company.",
    )
    _quantity_positive = models.Constraint(
        "CHECK(quantity_per_package > 0)",
        "The quantity per package must be strictly positive.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends(
        "pi_lot_number",
        "pi_serial_number",
        "pi_manufacturing_date",
        "pi_expiry_date",
        "pi_software_version",
    )
    def _compute_pi_component_summary(self):
        """Build a readable list of the selected production identifiers."""
        labels = [
            ("pi_lot_number", self.env._("Lot number")),
            ("pi_serial_number", self.env._("Serial number")),
            ("pi_manufacturing_date", self.env._("Manufacturing date")),
            ("pi_expiry_date", self.env._("Expiry date")),
            ("pi_software_version", self.env._("Software version")),
        ]
        for record in self:
            selected = [label for field_name, label in labels if record[field_name]]
            record.pi_component_summary = (
                ", ".join(selected) if selected else self.env._("None recorded")
            )

    @api.depends("udi_di", "udi_kind", "packaging_level")
    def _compute_display_name(self):
        """Show the identifier together with its kind."""
        kinds = dict(constants.UDI_KIND_SELECTION)
        for record in self:
            kind_label = kinds.get(record.udi_kind, "")
            record.display_name = (
                f"{record.udi_di} ({kind_label})" if record.udi_di else kind_label
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("udi_kind", "packaging_level", "device_id")
    def _check_basic_udi_di_uniqueness_per_device(self):
        """Allow at most one Basic UDI-DI record per device.

        The Basic UDI-DI identifies a group of devices, not a packaging level,
        so a device carries a single Basic UDI-DI record.
        """
        for record in self:
            if record.udi_kind != "basic_udi_di":
                continue
            duplicates = self.search_count(
                [
                    ("device_id", "=", record.device_id.id),
                    ("udi_kind", "=", "basic_udi_di"),
                    ("id", "!=", record.id),
                ]
            )
            if duplicates:
                raise ValidationError(
                    self.env._(
                        "Device '%(device)s' already has a Basic UDI-DI "
                        "assignment. A device carries a single Basic UDI-DI.",
                        device=record.device_id.display_name,
                    )
                )

    @api.constrains("issuing_entity", "issuing_entity_note")
    def _check_issuing_entity_note(self):
        """Require a note when the issuing entity is recorded as 'Other'."""
        for record in self:
            if record.issuing_entity == "other" and not record.issuing_entity_note:
                raise ValidationError(
                    self.env._(
                        "Record the name of the issuing entity in the note "
                        "field when 'Other' is selected."
                    )
                )

    @api.constrains("state", "assignment_date")
    def _check_assignment_date(self):
        """Require an assignment date once the identifier leaves draft."""
        for record in self:
            if record.state != "draft" and not record.assignment_date:
                raise ValidationError(
                    self.env._(
                        "Record the assignment date of identifier "
                        "'%(identifier)s' before leaving the draft status.",
                        identifier=record.udi_di or "",
                    )
                )

    @api.constrains("state", "database_submission_date", "database_name")
    def _check_publication_details(self):
        """Require submission details once the identifier is published."""
        for record in self:
            if record.state == "published" and not (
                record.database_submission_date and record.database_name
            ):
                raise ValidationError(
                    self.env._(
                        "Record the UDI database name and the submission date "
                        "before marking identifier '%(identifier)s' as "
                        "published.",
                        identifier=record.udi_di or "",
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the record reference from the dedicated sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.udi"
                ) or self.env._("UDI/UNSEQUENCED")
        return super().create(vals_list)

    def write(self, vals):
        """Block edits to the identifier once it has been published.

        A published identifier has been transmitted to an external database.
        Changing it in place would break the correspondence between the local
        register and the database record, so the identifier and its kind are
        frozen and a new record must be created instead.
        """
        frozen_fields = {"udi_di", "udi_kind", "issuing_entity", "packaging_level"}
        if frozen_fields.intersection(vals):
            for record in self:
                if record.state in ("published", "obsolete"):
                    raise UserError(
                        self.env._(
                            "Identifier '%(identifier)s' has been published to "
                            "a UDI database and can no longer be modified. "
                            "Create a new assignment instead.",
                            identifier=record.udi_di or "",
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_udi(self):
        """Prevent deletion of identifiers that left the draft status."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Identifier '%(identifier)s' has been assigned and "
                        "cannot be deleted. Mark it obsolete instead.",
                        identifier=record.udi_di or "",
                    )
                )

    def copy_data(self, default=None):
        """Reset the identifier and its lifecycle when duplicating."""
        default = dict(default or {})
        default.setdefault("name", self.env._("New"))
        default.setdefault("udi_di", False)
        default.setdefault("state", "draft")
        default.setdefault("assignment_date", False)
        default.setdefault("database_submission_date", False)
        default.setdefault("database_reference", False)
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def action_assign(self):
        """Mark the identifier as assigned to the device."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft identifier can be assigned. Identifier "
                        "'%(identifier)s' is not in the draft status.",
                        identifier=record.udi_di or "",
                    )
                )
            record.write(
                {
                    "state": "assigned",
                    "assignment_date": record.assignment_date or today,
                }
            )
            if record.udi_kind == "basic_udi_di" and not record.device_id.basic_udi_di:
                record.device_id.basic_udi_di = record.udi_di
        return True

    def action_publish(self):
        """Mark the identifier as submitted to a UDI database."""
        for record in self:
            if record.state != "assigned":
                raise UserError(
                    self.env._(
                        "Only an assigned identifier can be published. "
                        "Identifier '%(identifier)s' is not assigned.",
                        identifier=record.udi_di or "",
                    )
                )
            record.state = "published"
        return True

    def action_mark_obsolete(self):
        """Retire the identifier from use."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.state not in ("assigned", "published"):
                raise UserError(
                    self.env._(
                        "Only an assigned or published identifier can be "
                        "retired. Identifier '%(identifier)s' is in neither "
                        "status.",
                        identifier=record.udi_di or "",
                    )
                )
            if not record.obsolete_reason:
                raise UserError(
                    self.env._(
                        "Record the obsolescence reason for identifier "
                        "'%(identifier)s' before retiring it.",
                        identifier=record.udi_di or "",
                    )
                )
            record.write({"state": "obsolete", "obsolete_date": today})
        return True

    def action_reset_to_draft(self):
        """Return an assigned identifier to draft.

        Published and obsolete identifiers cannot be reset, because their
        content has left the system.
        """
        for record in self:
            if record.state != "assigned":
                raise UserError(
                    self.env._(
                        "Only an assigned identifier can be returned to "
                        "draft. Identifier '%(identifier)s' is not assigned.",
                        identifier=record.udi_di or "",
                    )
                )
            record.state = "draft"
        return True
