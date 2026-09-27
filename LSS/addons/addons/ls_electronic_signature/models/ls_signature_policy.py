# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Configuration of where and when an electronic signature is required."""

import ast

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

#: Name of the abstract model that a target model must inherit in order to be
#: eligible for a signature policy.
SIGNABLE_MIXIN = "ls.signature.mixin"


class LsSignaturePolicy(models.Model):
    """A rule stating that an operation on a model requires signatures.

    Two triggers are supported and no others:

    ``manual``
        The signature is executed on demand from the record form. Nothing is
        blocked; the policy exists to define the meaning, the authorised
        signers and the number of signatures expected.

    ``transition``
        A write that moves ``field_name`` to ``value_to`` is refused unless the
        required signatures are present and current.
    """

    _name = "ls.signature.policy"
    _description = "Electronic Signature Policy"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )
    model_id = fields.Many2one(comodel_name="ir.model", required=True,
                               ondelete="cascade",
                               help="The model whose records this policy governs. The model must "
                               "inherit the signature mixin.",)
    model_name = fields.Char(related="model_id.model",
                             store=True,
                             index=True)
    meaning_id = fields.Many2one(
        comodel_name="ls.signature.meaning",
        required=True,
        ondelete="restrict",
    )
    trigger = fields.Selection(
        selection=[
            ("manual", "Manual signature"),
            ("transition", "Field transition"),
        ],
        required=True,
        default="manual",
    )
    field_name = fields.Char(
        string="Controlled Field",
        help="Technical name of the field whose transition is controlled. "
             "Required when the trigger is a field transition.",
    )
    value_from = fields.Char(
        help="Optional. Restrict the policy to transitions leaving this value. "
             "Leave empty to apply to any origin value.",
    )
    value_to = fields.Char(
        help="The target value that requires signatures. Required when the "
             "trigger is a field transition.",
    )
    signer_group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="ls_signature_policy_group_rel",
        column1="policy_id",
        column2="group_id",
        string="Authorised Signers",
        help="Groups whose members may satisfy this policy. Leave empty to "
             "accept any user holding the Signer role.",
    )
    required_signature_count = fields.Integer(
        string="Signatures Required",
        default=1,
        required=True,
    )
    distinct_signers = fields.Boolean(
        default=True,
        help="When more than one signature is required, refuse to count two "
             "signatures executed by the same person.",
    )
    applicability_domain = fields.Char(default="[]",
                                       required=True,
                                       help="Odoo domain restricting the records this policy applies to. Use "
                                       "[] to apply to every record of the model.",)
    require_full_credentials = fields.Boolean(
        default=True,
        help="Require identification code and password for every signature "
             "under this policy, even for signatures executed during a single "
             "continuous period of controlled system access. Disable only "
             "after documenting the decision against 21 CFR 11.200(a)(1)(i).",
    )
    description = fields.Text()

    _signature_count_positive = models.Constraint(
        "CHECK(required_signature_count >= 1)",
        "A policy must require at least one signature.",
    )

    @api.constrains("model_id")
    def _check_model_is_signable(self):
        """Refuse policies on models that cannot record signatures."""
        for policy in self:
            model = self.env.get(policy.model_name)
            if model is None:
                raise ValidationError(
                    _(
                        "Model '%(model)s' is not present in the registry.",
                        model=policy.model_name or "",
                    )
                )
            # ``_ls_signature_enabled`` is a class attribute set by the mixin.
            # Testing for it is explicit and independent of registry internals.
            if not getattr(model, "_ls_signature_enabled", False):
                raise ValidationError(
                    _(
                        "Model '%(model)s' does not inherit '%(mixin)s' and "
                        "therefore cannot carry electronic signatures.",
                        model=policy.model_name or "",
                        mixin=SIGNABLE_MIXIN,
                    )
                )

    @api.constrains("applicability_domain")
    def _check_applicability_domain(self):
        """Refuse a domain that cannot be parsed into a list."""
        for policy in self:
            try:
                parsed = ast.literal_eval(policy.applicability_domain or "[]")
            except (SyntaxError, ValueError) as error:
                raise ValidationError(
                    _(
                        "The applicability domain of policy '%(name)s' is not "
                        "valid Python literal syntax: %(error)s",
                        name=policy.name,
                        error=error,
                    )
                ) from error
            if not isinstance(parsed, list):
                raise ValidationError(
                    _(
                        "The applicability domain of policy '%(name)s' must be "
                        "a list.",
                        name=policy.name,
                    )
                )

    @api.constrains("trigger", "field_name", "value_to", "model_id")
    def _check_transition_configuration(self):
        """Ensure transition policies name an existing field and a target."""
        for policy in self:
            if policy.trigger != "transition":
                continue
            if not policy.field_name or not policy.value_to:
                raise ValidationError(
                    _(
                        "Policy '%(name)s' controls a field transition and "
                        "must therefore define both a controlled field and a "
                        "target value.",
                        name=policy.name,
                    )
                )
            model = self.env.get(policy.model_name)
            if model is not None and policy.field_name not in model._fields:
                raise ValidationError(
                    _(
                        "Field '%(field)s' does not exist on model "
                        "'%(model)s'.",
                        field=policy.field_name,
                        model=policy.model_name,
                    )
                )

    def _get_domain(self):
        """Return the parsed applicability domain of a single policy."""
        self.ensure_one()
        return ast.literal_eval(self.applicability_domain or "[]")

    def is_applicable_to(self, record):
        """Return whether this policy governs ``record``.

        :param record: A single recordset of the policy's model.
        :returns bool:
        """
        self.ensure_one()
        record.ensure_one()
        if record._name != self.model_name:
            return False
        domain = self._get_domain()
        if not domain:
            return True
        return bool(record.filtered_domain(domain))

    @api.model
    def _policies_for_model(self, model_name, trigger=None):
        """Return the active policies of ``model_name`` visible to the user.

        :param str model_name: Technical model name.
        :param str trigger: Optional trigger filter.
        :returns: A ``ls.signature.policy`` recordset.
        """
        domain = [("model_name", "=", model_name)]
        if trigger:
            domain.append(("trigger", "=", trigger))
        return self.search(domain)
