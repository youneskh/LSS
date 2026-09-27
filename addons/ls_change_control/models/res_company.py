# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Company level configuration for the Change Control module.

Configuration is stored on ``res.company`` rather than on
``res.config.settings``.  Rationale (see docs/developer_manual.md):

* Change control parameters are legally attached to a manufacturing site,
  which in Odoo is modelled by a company.  A single global system parameter
  would be wrong for multi-site organisations.
* The module therefore ships its own configuration form and never modifies
  the standard ``res.config.settings`` view, which makes the module
  upgrade-safe with respect to changes in the standard settings layout.
"""

from odoo import fields, models


class ResCompany(models.Model):
    """Add change control configuration parameters to the company."""

    _inherit = "res.company"

    ls_cc_approval_reminder_days = fields.Integer(
        string="Approval Reminder Delay (days)",
        default=3,
        help="Number of days a pending approval may stay without a decision "
             "before the scheduled action sends a reminder to the approver. "
             "Set to 0 to disable approval reminders for this company.",
    )
    ls_cc_default_verification_delay = fields.Integer(
        string="Default Verification Delay (days)",
        default=30,
        help="Default number of days between the actual implementation date "
             "and the planned effectiveness verification date. It is used "
             "when the change category does not define its own delay.",
    )
    ls_cc_require_verification = fields.Boolean(
        string="Effectiveness Verification Mandatory",
        default=True,
        help="When enabled, a change request cannot be closed before at "
             "least one effectiveness verification has been completed, "
             "unless the change category explicitly waives verification.",
    )
    ls_cc_block_close_on_open_actions = fields.Boolean(
        string="Block Closure on Open Actions",
        default=True,
        help="When enabled, a change request cannot leave the Implementation "
             "state while implementation actions are still pending or in "
             "progress.",
    )
