# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Provision citation.

A citation is a located quote or paraphrase of a passage of a
provision. Multiple citations may be attached to a single provision, so
that the registry reader can see exactly which passage of the source
underpins a requirement, and whether the recorded text is verbatim or a
paraphrase.
"""

from odoo import fields, models

from .constants import CITATION_QUOTE_TYPE_SELECTION


class LsImportExportProvisionCitation(models.Model):
    """A located quote or paraphrase of a passage of a provision."""

    _name = "ls.import_export.provision.citation"
    _description = "Import & Export Compliance Provision Citation"
    _inherit = ["mail.thread"]
    _order = "provision_id, locator, id"

    provision_id = fields.Many2one(
        comodel_name="ls.import_export.provision",
        string="Provision",
        required=True,
        ondelete="cascade",
        index=True,
    )
    locator = fields.Char(
        string="Locator",
        help="Exact location of the passage in the source, for example "
             "'Article 12' or 'page 4, paragraph 2'.",
    )
    quote_type = fields.Selection(
        selection=CITATION_QUOTE_TYPE_SELECTION,
        default="paraphrase",
        required=True,
    )
    text = fields.Text(
        string="Text",
        required=True,
        help="The verbatim quote or the paraphrase of the passage.",
    )
    language = fields.Selection(
        selection=[
            ("fr", "French"),
            ("ar", "Arabic"),
            ("en", "English"),
            ("other", "Other"),
        ],
        default="fr",
        help="Language of the cited passage.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="provision_id.company_id",
        store=True,
        index=True,
    )
