"""P5 - Remaining single-point probes."""

from odoo.tests import tagged

from .common import ProbeCommon


@tagged("post_install", "-at_install", "ls_audit_probe")
class TestP5Misc(ProbeCommon):

    def test_F11_signature_password_not_persisted(self):
        """F-11: the password typed in the signature dialog is never stored."""
        try:
            meaning = self.env["ls.signature.meaning"].create({
                "name": "Probe approval",
                "code": "PROBE_APPROVAL",
            })
            wizard = self.env["ls.signature.wizard"].create({
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "meaning_id": meaning.id,
                "login": self.env.user.login,
                "password": "Probe-Secret-123",
            })
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP signature wizard cannot be created: {error}")
        self.env.flush_all()
        # Since the F-11 fix the password is a non-stored field: the column
        # does not exist on a new installation and is dropped on upgrade.
        self.env.cr.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'ls_signature_wizard' AND column_name = 'password'"
        )
        if self.env.cr.fetchone():
            self.env.cr.execute("SELECT password FROM ls_signature_wizard WHERE id = %s", (wizard.id,))
            stored = self.env.cr.fetchone()[0]
        else:
            stored = False
        self.assertFalse(
            stored,
            "PROBE F-11 reproduced: the signature password is stored in clear text in table ls_signature_wizard",
        )

    def test_F36_qualification_created_programmatically(self):
        """F-36: a dossier can be created by code (import, integration)
        without passing the computed criticality."""
        category = self.env["ls.supplier.category"].create({
            "name": "Probe category",
            "code": "PRB-F36",
            "criticality": "major",
            "requires_assessment": True,
            "requires_initial_audit": False,
            "requires_periodic_audit": False,
            "requalification_interval_months": 36,
            "review_interval_months": 12,
        })
        supplier = self.env["res.partner"].create({"name": "Probe F36 supplier"})
        try:
            with self.env.cr.savepoint():
                dossier = self.env["ls.supplier.qualification"].create({
                    "partner_id": supplier.id,
                    "category_id": category.id,
                    "responsible_id": self.env.user.id,
                })
                self.assertEqual(dossier.criticality, "major")
        except Exception as error:  # noqa: BLE001
            self.fail(f"PROBE F-36 reproduced: programmatic creation fails: {error}")
