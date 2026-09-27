# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Substance restrictions taken from the Annexes to the Cosmetics Regulation."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from . import constants


class LsCosmeticRestriction(models.Model):
    """One entry of Annex II, III, IV, V or VI of Regulation (EC) No 1223/2009.

    **No annex content is shipped with this module.**  Annexes II to VI are
    amended by the Commission several times per year; embedding a snapshot
    would guarantee that the data is out of date and would give a false
    impression of authority.  The receiving organisation loads the current
    consolidated annexes itself, records the source and the consolidation
    date on each entry, and keeps the entries under change control.

    Until entries exist, :meth:`ls.cosmetic.formulation._compute_restriction_status`
    reports ``no_reference_data`` rather than ``compliant``.  The module never
    asserts that a formulation complies with an annex it has not been given.
    """

    _name = "ls.cosmetic.restriction"
    _description = "Cosmetic Substance Restriction (Annexes II-VI)"
    _order = "annex, reference_number, id"
    _rec_name = "substance_name"

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", default=lambda self: self.env.company,
                                 index=True,
                                 help="Leave empty to share the entry across all companies.",)
    annex = fields.Selection(selection=constants.RESTRICTION_ANNEX, required=True,
                             index=True,)
    reference_number = fields.Char(required=True,
                                   help="Entry number within the annex, as published.",)
    substance_name = fields.Char(required=True)
    inci_name = fields.Char()
    cas_number = fields.Char()
    ec_number = fields.Char()
    product_type_scope = fields.Text(
        string="Product Type / Body Part",
        help="Column 'Product type, body parts' of the published annex.",
    )
    max_concentration = fields.Float(
        string="Maximum Concentration (% w/w)",
        digits=(16, 6),
        help="Maximum concentration in ready for use preparation, where the "
             "annex expresses a single numeric limit. Leave at 0.00 when the "
             "annex expresses the limit in another form and record the exact "
             "wording in 'Conditions of Use'.",
    )
    has_numeric_limit = fields.Boolean(
        string="Numeric Limit Applies",
        help="Tick only when 'Maximum Concentration' reproduces a single "
             "numeric limit that can be compared automatically.",
    )
    conditions_of_use = fields.Text(string="Conditions of Use and Warnings")
    label_wording = fields.Text(
        string="Wording of Conditions of Use and Warnings",
        help="Text that must appear on the label, column 'Wording of "
             "conditions of use and warnings' of the annex.",
    )
    other_column = fields.Text(
        string="Other",
        help="Column 'Other' of Annex III. Substances mentioned in this "
             "column must be indicated in the list of ingredients in addition "
             "to the terms parfum or aroma - Article 19(1)(g).",
    )
    source_reference = fields.Char(required=True,
                                   help="Exact citation of the consolidated text the entry was taken "
                                   "from, for example 'Consolidated Regulation (EC) No 1223/2009, "
                                   "Annex III, entry 98, consolidation of 21/01/2026'.",
                                   )
    consolidation_date = fields.Date(required=True,
                                     help="Date of the consolidated version the entry reproduces.",)
    date_from = fields.Date(string="Applicable From")
    date_to = fields.Date(string="Applicable Until")
    note = fields.Text(string="Internal Note")

    _reference_unique = models.Constraint(
        "UNIQUE(annex, reference_number, company_id)",
        "An annex entry with this reference number already exists for this company.",
    )
    _max_concentration_positive = models.Constraint(
        "CHECK(max_concentration >= 0)",
        "The maximum concentration cannot be negative.",
    )

    @api.depends("annex", "reference_number", "substance_name")
    def _compute_display_name(self):
        """Build a name that identifies the annex entry unambiguously."""
        annex_labels = dict(constants.RESTRICTION_ANNEX)
        for record in self:
            annex_label = annex_labels.get(record.annex, "")
            annex_short = annex_label.split(" - ")[0] if annex_label else ""
            parts = [part for part in (annex_short, record.reference_number) if part]
            prefix = "/".join(parts)
            if prefix and record.substance_name:
                record.display_name = f"[{prefix}] {record.substance_name}"
            else:
                record.display_name = record.substance_name or prefix or "/"

    @api.constrains("date_from", "date_to")
    def _check_applicability_dates(self):
        """Refuse an applicability window that ends before it starts."""
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError(
                    self.env._(
                        "Restriction %(name)s: 'Applicable Until' cannot precede "
                        "'Applicable From'.",
                        name=record.display_name,
                    )
                )

    @api.constrains("has_numeric_limit", "max_concentration", "annex")
    def _check_numeric_limit(self):
        """A declared numeric limit must carry a strictly positive value.

        Annex II lists prohibited substances, which have no permitted
        concentration; declaring a numeric limit on an Annex II entry would
        misrepresent the annex.
        """
        for record in self:
            if record.has_numeric_limit and record.max_concentration <= 0:
                raise ValidationError(
                    self.env._(
                        "Restriction %(name)s declares a numeric limit but the "
                        "maximum concentration is not greater than zero.",
                        name=record.display_name,
                    )
                )
            if record.has_numeric_limit and record.annex == "ii":
                raise ValidationError(
                    self.env._(
                        "Restriction %(name)s belongs to Annex II (prohibited "
                        "substances). Annex II entries cannot carry a permitted "
                        "concentration.",
                        name=record.display_name,
                    )
                )

    def _is_applicable_on(self, target_date):
        """Return the subset of ``self`` in force on ``target_date``.

        :param target_date: :class:`datetime.date` to test.
        :return: recordset of applicable restrictions.
        """
        applicable = self.browse()
        for record in self:
            starts_ok = not record.date_from or record.date_from <= target_date
            ends_ok = not record.date_to or record.date_to >= target_date
            if starts_ok and ends_ok:
                applicable |= record
        return applicable
