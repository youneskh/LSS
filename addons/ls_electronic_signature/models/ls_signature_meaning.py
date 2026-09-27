# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Signature meanings, as required by 21 CFR 11.50(a)(3)."""

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,31}$")


class LsSignatureMeaning(models.Model):
    """A controlled meaning that may be associated with a signature.

    21 CFR 11.50(a)(3) requires a signed electronic record to indicate "the
    meaning (such as review, approval, responsibility, or authorship)
    associated with the signature". Meanings are configuration data so that
    each organisation can express its own approved vocabulary, while the code
    remains stable for reporting and integration.
    """

    _name = "ls.signature.meaning"
    _description = "Electronic Signature Meaning"
    _order = "sequence, code"
    _rec_name = "name"

    name = fields.Char(
        string="Meaning",
        required=True,
        translate=True,
        help="Wording rendered on screen and on printed signature "
             "manifestations, for example 'Approved by'.",
    )
    code = fields.Char(
        required=True,
        help="Stable technical identifier used by policies, reports and "
             "integrations. Upper case letters, digits and underscores only.",
    )
    sequence = fields.Integer(default=10)
    description = fields.Text(
        help="Description of when this meaning applies. Shown to the signer in "
             "the signature wizard.",
    )
    require_reason = fields.Boolean(
        string="Reason Mandatory",
        default=False,
        help="If enabled, the signer must record a free text reason. Enable "
             "this for meanings that document a negative decision, such as "
             "rejection.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )
    group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="ls_signature_meaning_group_rel",
        column1="meaning_id",
        column2="group_id",
        string="Authorised Groups",
        help="Groups whose members may execute a signature with this meaning. "
             "Leave empty to allow any user holding the Signer role.",
    )
    active = fields.Boolean(default=True)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "A signature meaning code must be unique per company.",
    )

    @api.constrains("code")
    def _check_code_format(self):
        """Reject codes that would be ambiguous in reports or integrations."""
        for meaning in self:
            if not CODE_PATTERN.match(meaning.code or ""):
                raise ValidationError(
                    _(
                        "The signature meaning code '%(code)s' is invalid. Use "
                        "2 to 32 characters, starting with an upper case "
                        "letter, containing only upper case letters, digits "
                        "and underscores.",
                        code=meaning.code or "",
                    )
                )

    def is_available_to(self, user):
        """Return the subset of ``self`` that ``user`` is authorised to use.

        :param user: A single ``res.users`` recordset.
        :returns: A ``ls.signature.meaning`` recordset.
        """
        user.ensure_one()
        user_groups = user.all_group_ids
        return self.filtered(
            lambda meaning: not meaning.group_ids or (meaning.group_ids & user_groups)
        )
