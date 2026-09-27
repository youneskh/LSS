# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Auditor qualification register.

The register records which users are qualified to audit, for which scope, and
until when.  The audit workflow consults this register before an audit may be
scheduled, so that unqualified or lapsed auditors cannot be assigned.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsAuditAuditor(models.Model):
    """Qualification record of a single auditor."""

    _name = "ls.audit.auditor"
    _description = "Auditor Qualification"
    _order = "user_id"
    _rec_name = "user_id"

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Auditor",
        required=True,
        ondelete="restrict",
        index=True,
        help="User qualified to perform audits.",
    )
    employee_id = fields.Many2one(comodel_name="hr.employee", help="Employee record of the auditor, used for reporting by "
                                  "department.",)
    is_lead_auditor = fields.Boolean(
        string="Lead Auditor",
        help="Tick when the auditor is qualified to lead an audit team. "
             "Only lead auditors can be set as lead auditor on an audit.",
    )
    qualification_date = fields.Date(required=True,
                                     default=fields.Date.context_today,
                                     help="Date on which the auditor qualification was granted.",)
    expiry_date = fields.Date(help="Date on which the qualification lapses. Leave empty for a "
                              "qualification without expiry.",)
    certificate_reference = fields.Char(help="Reference of the training certificate or qualification record "
                                        "held in the training system.",)
    scope_ids = fields.Many2many(
        comodel_name="ls.audit.area",
        relation="ls_audit_auditor_area_rel",
        column1="auditor_id",
        column2="area_id",
        string="Qualified Scope",
        help="Areas the auditor is qualified to audit. Leave empty when the "
             "auditor is qualified for every area.",
    )
    qualification_state = fields.Selection(
        selection=[
            ("valid", "Valid"),
            ("expiring", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="Qualification Status",
        compute="_compute_qualification_state",
        store=True,
        help="Computed status derived from the expiry date.",
    )
    days_to_expiry = fields.Integer(compute="_compute_qualification_state",
                                    store=True,
                                    help="Number of days remaining before the qualification lapses. "
                                    "Negative when the qualification has already lapsed.",)
    notes = fields.Text(help="Free text on the auditor training and experience.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this qualification record.",)
    active = fields.Boolean(default=True,
                            help="Archived auditors can no longer be assigned to new audits.",)

    # Number of days before expiry at which a qualification is flagged as
    # expiring. Kept as a class attribute so that it can be overridden by a
    # depending module without patching the compute method.
    EXPIRY_WARNING_DAYS = 60

    _user_company_uniq = models.Constraint(
        "UNIQUE(user_id, company_id)",
        "An auditor qualification already exists for this user in this "
        "company.",
    )

    @api.depends("expiry_date")
    def _compute_qualification_state(self):
        """Derive the qualification status from the expiry date."""
        today = fields.Date.context_today(self)
        for auditor in self:
            if not auditor.expiry_date:
                auditor.days_to_expiry = 0
                auditor.qualification_state = "valid"
                continue
            delta_days = (auditor.expiry_date - today).days
            auditor.days_to_expiry = delta_days
            if delta_days < 0:
                auditor.qualification_state = "expired"
            elif delta_days <= self.EXPIRY_WARNING_DAYS:
                auditor.qualification_state = "expiring"
            else:
                auditor.qualification_state = "valid"

    @api.depends("user_id", "is_lead_auditor")
    def _compute_display_name(self):
        """Show the auditor name together with the lead auditor role."""
        for auditor in self:
            if auditor.is_lead_auditor:
                auditor.display_name = _(
                    "%(name)s (Lead Auditor)", name=auditor.user_id.name
                )
            else:
                auditor.display_name = auditor.user_id.name or ""

    @api.constrains("qualification_date", "expiry_date")
    def _check_dates(self):
        """Forbid an expiry date earlier than the qualification date."""
        for auditor in self:
            if not auditor.expiry_date:
                continue
            if auditor.expiry_date < auditor.qualification_date:
                raise ValidationError(
                    _(
                        "The expiry date of auditor '%(name)s' is earlier "
                        "than the qualification date.",
                        name=auditor.user_id.name,
                    )
                )

    @api.constrains("scope_ids", "company_id")
    def _check_scope_company(self):
        """Forbid a qualified scope belonging to another company."""
        for auditor in self:
            other = auditor.scope_ids.filtered(
                lambda area, auditor=auditor: area.company_id
                != auditor.company_id
            )
            if other:
                raise ValidationError(
                    _(
                        "The qualified scope of auditor '%(name)s' contains "
                        "areas of another company: %(areas)s.",
                        name=auditor.user_id.name,
                        areas=", ".join(other.mapped("complete_name")),
                    )
                )

    def is_qualified_for(self, areas):
        """Return whether the auditor may audit every area in ``areas``.

        :param areas: ``ls.audit.area`` recordset to check against the
            qualified scope of the auditor.
        :return: ``True`` when the qualification is not expired and every area
            falls within the qualified scope, ``False`` otherwise.
        :rtype: bool
        """
        self.ensure_one()
        if self.qualification_state == "expired" or not self.active:
            return False
        if not self.scope_ids:
            return True
        return not (areas - self.scope_ids)

    def _ls_recompute_stored(self, method_name):
        """Recompute and save the stored fields computed by ``method_name``.

        Calling a compute method directly does not persist the values of
        stored computed fields; the recomputation is therefore scheduled and
        run through the ORM so that the new values are written.

        :param str method_name: name of the compute method.
        """
        names = [
            name
            for name, field in self._fields.items()
            if field.store and field.compute == method_name
        ]
        for name in names:
            self.env.add_to_compute(self._fields[name], self)
        self._recompute_recordset(names)

    @api.model
    def _cron_notify_qualification_expiry(self):
        """Post a chatter-free activity reminder for lapsing qualifications.

        The cron notifies the audit managers through a mail message on the
        auditor record so that requalification can be planned.  It is
        deliberately idempotent within a day: an auditor is notified once per
        run only when its status is ``expiring`` or ``expired``.
        """
        # The stored qualification status depends on the current date, which
        # is not an ORM dependency. It is therefore recomputed before use so
        # that a qualification lapsing overnight is detected on the next run.
        all_auditors = self.search([])
        all_auditors._ls_recompute_stored("_compute_qualification_state")
        auditors = all_auditors.filtered(
            lambda auditor: auditor.qualification_state in (
                "expiring", "expired",
            )
        )
        template = self.env.ref(
            "ls_audit.mail_template_auditor_qualification_expiry",
            raise_if_not_found=False,
        )
        if not template:
            return len(auditors)
        for auditor in auditors:
            template.send_mail(auditor.id, force_send=False)
        return len(auditors)
