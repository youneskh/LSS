# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to generate serialised units for a batch."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .. import gs1

#: Number of attempts made to draw a serial number that is not already used
#: for the same product code before the generation is abandoned.  The value is
#: deliberately small: exhausting it means that the configured serial length
#: is too short for the volume being generated, which is a configuration
#: problem rather than a transient one.
MAX_DRAW_ATTEMPTS = 32


class LsPharmaSerialGenerateWizard(models.TransientModel):
    """Generate a requested number of serialised units for a batch.

    Serial numbers are drawn from a cryptographically strong source of
    randomness, because Commission Delegated Regulation (EU) 2016/161
    requires that the probability of a serial number being guessed be
    negligible.  Every drawn value is checked against the serial numbers
    already recorded for the same product code before it is used.
    """

    _name = "ls.pharma.serial.generate.wizard"
    _description = "Serialised Unit Generation Wizard"

    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", required=True,
                               readonly=True,)
    product_id = fields.Many2one(comodel_name="product.product", related="batch_id.product_id",
                                 readonly=True,)
    gtin = fields.Char(string="Product Code (GTIN-14)", required=True)
    batch_number = fields.Char(required=True)
    expiry_date = fields.Date(required=True)
    national_number = fields.Char(string="National Reimbursement Number")
    quantity = fields.Integer(string="Number of Units", required=True, default=1)
    serial_length = fields.Integer(string="Serial Number Length", required=True)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill the wizard from the batch, the product and the company."""
        values = super().default_get(fields_list)
        batch_id = values.get("batch_id") or self.env.context.get(
            "default_batch_id"
        )
        if batch_id:
            batch = self.env["ls.pharma.batch"].browse(batch_id)
            template = batch.product_id.product_tmpl_id
            values.setdefault("gtin", template.pharma_gtin14)
            values.setdefault("batch_number", batch.name)
            values.setdefault("expiry_date", batch.date_expiry)
            values.setdefault(
                "national_number", template.pharma_national_number
            )
        values.setdefault(
            "serial_length", self.env.company.pharma_serial_length
        )
        return values

    @api.constrains("quantity")
    def _check_quantity(self):
        """Reject a non-positive number of units."""
        for wizard in self:
            if wizard.quantity <= 0:
                raise ValidationError(
                    self.env._(
                        "The number of units to generate must be strictly "
                        "positive."
                    )
                )

    def action_generate(self):
        """Create the serialised units and open them.

        :returns: an action listing the serialised units of the batch.
        :rtype: dict
        :raises UserError: when the identifying data are invalid or when a
            unique serial number could not be drawn.
        """
        self.ensure_one()
        if not gs1.is_valid_gtin14(self.gtin):
            raise UserError(
                self.env._(
                    "The product code %(gtin)s is not a valid GTIN-14.",
                    gtin=self.gtin,
                )
            )
        if self.expiry_date <= fields.Date.context_today(self):
            raise UserError(
                self.env._(
                    "The expiry date must be later than today for units that "
                    "are being generated."
                )
            )
        serialization_model = self.env["ls.pharma.serialization"]
        used_serials = set(
            serialization_model.search(
                [
                    ("gtin", "=", self.gtin),
                    ("company_id", "=", self.batch_id.company_id.id),
                ]
            ).mapped("serial_number")
        )
        values_list = []
        for _index in range(self.quantity):
            serial = self._draw_serial(used_serials)
            used_serials.add(serial)
            values_list.append(
                {
                    "batch_id": self.batch_id.id,
                    "gtin": self.gtin,
                    "serial_number": serial,
                    "batch_number": self.batch_number,
                    "expiry_date": self.expiry_date,
                    "national_number": self.national_number,
                }
            )
        serialization_model.create(values_list)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Serialised Units"),
            "res_model": "ls.pharma.serialization",
            "view_mode": "list,form",
            "domain": [("batch_id", "=", self.batch_id.id)],
            "context": {"default_batch_id": self.batch_id.id},
        }

    def _draw_serial(self, used_serials):
        """Draw a serial number that is not present in ``used_serials``.

        :param set used_serials: serial numbers already in use for the
            product code.
        :rtype: str
        :raises UserError: when no unused value could be drawn.
        """
        self.ensure_one()
        for _attempt in range(MAX_DRAW_ATTEMPTS):
            try:
                candidate = gs1.generate_random_serial(self.serial_length)
            except gs1.Gs1Error as error:
                raise UserError(str(error)) from error
            if candidate not in used_serials:
                return candidate
        raise UserError(
            self.env._(
                "A serial number that is not already in use for product code "
                "%(gtin)s could not be drawn after %(attempts)s attempts. "
                "Increase the configured serial number length.",
                gtin=self.gtin,
                attempts=MAX_DRAW_ATTEMPTS,
            )
        )
