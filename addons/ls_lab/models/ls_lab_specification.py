# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Product specifications and their acceptance criteria lines."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsLabSpecification(models.Model):
    """A controlled product specification.

    Samples reference an approved specification version. Because approved
    specifications are frozen and superseded rather than edited, a result
    recorded months ago remains evaluable against exactly the criteria that
    applied when it was taken.
    """

    _name = "ls.lab.specification"
    _description = "Laboratory Product Specification"
    _inherit = ["ls.lab.controlled.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "code, version desc"

    _CONTROLLED_FIELDS = (
        "name",
        "product_id",
        "spec_type",
        "effective_date",
        "notes",
    )
    _FROZEN_STATES = ("approved", "obsolete")
    _SEQUENCE_CODE = "ls.lab.specification"
    _SEQUENCE_FIELD = "code"

    name = fields.Char(
        string="Specification Name",
        required=True,
        translate=True,
        tracking=True,
    )
    code = fields.Char(
        string="Specification Code",
        required=True,
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    version = fields.Integer(default=1,
                             required=True,
                             readonly=True,
                             copy=False,
                             tracking=True,)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("review", "Under Review"),
            ("approved", "Approved"),
            ("obsolete", "Obsolete"),
        ],
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 index=True,
                                 tracking=True,)
    spec_type = fields.Selection(
        selection=[
            ("raw_material", "Raw Material"),
            ("packaging", "Packaging Material"),
            ("in_process", "In Process"),
            ("finished_product", "Finished Product"),
            ("stability", "Stability"),
            ("water", "Water"),
        ],
        string="Specification Type",
        default="finished_product",
        required=True,
        tracking=True,
    )
    effective_date = fields.Date(tracking=True)
    line_ids = fields.One2many(
        comodel_name="ls.lab.specification_line",
        inverse_name="specification_id",
        string="Acceptance Criteria",
        copy=True,
    )
    line_count = fields.Integer(
        string="Criteria Count",
        compute="_compute_line_count",
        store=True,
    )
    notes = fields.Text(translate=True)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True,
                                    copy=False,
                                    tracking=True,)
    obsolete_reason = fields.Text(string="Obsolescence Reason", copy=False)
    predecessor_id = fields.Many2one(
        comodel_name="ls.lab.specification",
        string="Supersedes",
        readonly=True,
        copy=False,
    )
    successor_id = fields.Many2one(
        comodel_name="ls.lab.specification",
        string="Superseded By",
        readonly=True,
        copy=False,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", default=lambda self: self.env.company,
                                 index=True,)

    _code_version_uniq = models.Constraint(
        "UNIQUE (code, version)",
        "A specification version must be unique for a given specification code.",
    )

    @api.depends("line_ids")
    def _compute_line_count(self):
        """Store the number of acceptance criteria for listing and filtering."""
        for specification in self:
            specification.line_count = len(specification.line_ids)

    @api.depends("code", "name", "version")
    def _compute_display_name(self):
        """Display code, version and name so that versions are distinguishable."""
        for specification in self:
            specification.display_name = (
                f"[{specification.code} v{specification.version}] {specification.name}"
            )

    @api.constrains("state", "product_id", "spec_type", "company_id")
    def _check_single_approved_version(self):
        """Forbid two concurrently approved specifications for the same scope.

        Implements business rule BRU-05. Without this rule a sample could be
        registered against an ambiguous set of criteria.
        """
        for specification in self.filtered(lambda s: s.state == "approved"):
            duplicate = self.search_count([
                ("id", "!=", specification.id),
                ("state", "=", "approved"),
                ("product_id", "=", specification.product_id.id),
                ("spec_type", "=", specification.spec_type),
                ("company_id", "=", specification.company_id.id),
            ])
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "Another approved specification already exists for "
                        "product '%(product)s' and type '%(spec_type)s'. Make the "
                        "existing version obsolete before approving this one.",
                        product=specification.product_id.display_name,
                        spec_type=specification.spec_type,
                    )
                )

    @api.constrains("state", "line_ids")
    def _check_lines_present_on_approval(self):
        """A specification without criteria cannot be approved."""
        for specification in self.filtered(lambda s: s.state == "approved"):
            if not specification.line_ids:
                raise ValidationError(
                    self.env._(
                        "Specification '%(name)s' cannot be approved because it "
                        "carries no acceptance criteria.",
                        name=specification.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_submit_review(self):
        """Move a draft specification to Under Review."""
        self._assert_state("draft", "Submit for Review")
        return self.write({"state": "review"})

    def action_reset_draft(self):
        """Return a specification under review to Draft."""
        self._assert_state("review", "Reset to Draft")
        return self.write({"state": "draft"})

    def action_approve(self):
        """Approve a specification under review and freeze it."""
        self._assert_state("review", "Approve")
        return self.write({
            "state": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        })

    def action_set_obsolete(self):
        """Make an approved specification obsolete, requiring a reason."""
        self._assert_state("approved", "Set Obsolete")
        without_reason = self.filtered(lambda s: not s.obsolete_reason)
        if without_reason:
            raise UserError(
                self.env._(
                    "An obsolescence reason is required before a specification "
                    "may be made obsolete. Missing on: %(records)s.",
                    records=", ".join(without_reason.mapped("display_name")),
                )
            )
        return self.write({"state": "obsolete"})

    def action_create_revision(self):
        """Create the next draft version, copying the acceptance criteria."""
        self.ensure_one()
        self._assert_state("approved", "Create Revision")
        successor = self._create_successor_version()
        successor.message_post(
            body=self.env._(
                "Created as version %(version)s superseding %(predecessor)s.",
                version=successor.version,
                predecessor=self.display_name,
            )
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.specification",
            "res_id": successor.id,
            "view_mode": "form",
            "target": "current",
        }
