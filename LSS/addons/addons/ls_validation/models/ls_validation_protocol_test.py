# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Test case belonging to a validation protocol.

Test cases carry the pre-approved acceptance criteria. They are frozen as soon
as their protocol leaves the editable states, which is enforced here as well as
on the parent model so that the rule holds whichever record is written.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .ls_validation_protocol import EDITABLE_STATES


class LsValidationProtocolTest(models.Model):
    """Single pre-approved test case."""

    _name = "ls.validation.protocol.test"
    _description = "Validation Protocol Test Case"
    _order = "protocol_id, sequence, id"
    _check_company_auto = True

    protocol_id = fields.Many2one(comodel_name="ls.validation.protocol", required=True,
                                  ondelete="cascade",
                                  index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="protocol_id.company_id",
                                 store=True,
                                 readonly=True,)
    protocol_state = fields.Selection(
        related="protocol_id.state",
        string="Protocol Status",
        readonly=True,
    )
    sequence = fields.Integer(default=10)
    code = fields.Char(
        string="Test Case",
        required=True,
        help="Identifier of the test case inside the protocol, for example "
             "TC-001.",
    )
    name = fields.Char(string="Title", required=True)
    objective = fields.Text()
    procedure = fields.Html(sanitize=True,
                            help="Step by step instructions performed by the executor.",)
    acceptance_criteria = fields.Text(required=True,
                                      help="Objective and measurable criterion decided before execution.",)
    expected_evidence = fields.Text(help="Raw data, printouts or attachments to be collected as evidence.",)
    is_critical = fields.Boolean(
        string="Critical Test",
        help="A critical test case that fails prevents the approval of the "
             "validation summary report.",
    )

    _unique_code_per_protocol = models.Constraint(
        "UNIQUE(protocol_id, code)",
        "The test case identifier must be unique inside a protocol.",
    )

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Display the test case as ``CODE - Title``."""
        for test in self:
            test.display_name = "%s - %s" % (test.code or "", test.name or "")

    def _check_protocol_editable(self):
        """Raise when the parent protocol no longer accepts modifications."""
        for test in self:
            if test.protocol_id.state not in EDITABLE_STATES:
                raise UserError(
                    _(
                        "Test cases of protocol %s cannot be changed after "
                        "approval. Create a new protocol version instead."
                    )
                    % test.protocol_id.display_name
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Block the creation of test cases on a frozen protocol."""
        records = super().create(vals_list)
        records._check_protocol_editable()
        return records

    def write(self, vals):
        """Block the modification of test cases on a frozen protocol."""
        self._check_protocol_editable()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_protocol_test(self):
        """Block the deletion of test cases on a frozen protocol."""
        self._check_protocol_editable()
