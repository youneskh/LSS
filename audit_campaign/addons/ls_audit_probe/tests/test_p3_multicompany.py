"""P3 - Multi-company behaviour."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import ProbeCommon


@tagged("post_install", "-at_install", "ls_audit_probe")
class TestP3MultiCompany(ProbeCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Probe Company B"})
        cls.env.user.write({"company_ids": [(4, cls.company_b.id)]})

    def _env_ab(self, current):
        """Environment with both companies active, ``current`` first."""
        other = self.company_b if current == self.company_a else self.company_a
        return self.env(context=dict(self.env.context, allowed_company_ids=[current.id, other.id]))

    # ------------------------------------------------------------------
    def test_F09_audit_rule_follows_record_company(self):
        """F-09: a rule defined for company B audits company B records,
        whatever the active company of the writer."""
        partner_model = self.env["ir.model"]._get("res.partner")
        ref_field = self.env["ir.model.fields"]._get("res.partner", "ref")
        self.env["ls.audit_trail.rule"].create({
            "name": "Probe rule company B",
            "model_id": partner_model.id,
            "company_id": self.company_b.id,
            "log_write": True,
            "field_ids": [(6, 0, ref_field.ids)],
        })
        partner_b = self.env["res.partner"].create({"name": "Probe B partner", "company_id": self.company_b.id})
        log = self.env["ls.audit_trail.log"].sudo()
        # Control: current company B -> audited.
        partner_b.with_env(self._env_ab(self.company_b)).write({"ref": "CTRL-1"})
        # Only write entries are counted: since the F-09 fix the creation of
        # the company B partner is audited too (the rule has log_create).
        write_domain = [
            ("model_name", "=", "res.partner"),
            ("res_id", "=", partner_b.id),
            ("operation", "=", "write"),
        ]
        control = log.search_count(write_domain)
        self.assertEqual(control, 1, "SETUP control write in company B was not audited")
        # Probe: current company A, record of company B.
        partner_b.with_env(self._env_ab(self.company_a)).write({"ref": "PROBE-2"})
        probe = log.search_count(write_domain)
        self.assertEqual(
            probe, 2,
            "PROBE F-09 reproduced: a change to a company B record made while company A is active is not audited",
        )

    # ------------------------------------------------------------------
    def _qualified_supplier_for_b(self):
        for company in (self.company_a, self.company_b):
            company.write({"ls_po_control_level": "block", "ls_po_check_scope": False})
        category = self.env["ls.supplier.category"].with_company(self.company_b).create({
            "name": "Probe category B",
            "code": "PRB-B",
            "criticality": "major",
            "requires_assessment": True,
            "requires_initial_audit": False,
            "requires_periodic_audit": False,
            "requalification_interval_months": 36,
            "review_interval_months": 12,
            "company_id": self.company_b.id,
        })
        supplier = self.env["res.partner"].create({"name": "Probe shared supplier"})
        dossier = self.env["ls.supplier.qualification"].with_company(self.company_b).create({
            "partner_id": supplier.id,
            "category_id": category.id,
            "responsible_id": self.env.user.id,
            "criticality": "major",
            "company_id": self.company_b.id,
        })
        self.env.cr.execute(
            "UPDATE ls_supplier_qualification SET state = 'approved', expiry_date = NULL WHERE id = %s",
            (dossier.id,),
        )
        self.env.invalidate_all()
        return supplier

    def test_F13_po_control_uses_order_company(self):
        """F-13: a company B order to a supplier approved for company B is
        accepted even when company A is the active company."""
        try:
            supplier = self._qualified_supplier_for_b()
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP could not build an approved dossier: {error}")
        order = self.env["purchase.order"].with_company(self.company_b).create({
            "partner_id": supplier.id,
            "company_id": self.company_b.id,
            "order_line": [self.cmd().create({
                "product_id": self.product_plain.id, "product_qty": 1, "price_unit": 1,
            })],
        })
        control = order.copy()
        # Probe FIRST, on a clean cache: company A active.
        self.env.invalidate_all()
        try:
            order.with_env(self._env_ab(self.company_a)).button_confirm()
            probe_error = None
        except UserError as error:
            probe_error = error
        # Control: company B active -> confirmation accepted.
        self.env.invalidate_all()
        control.with_env(self._env_ab(self.company_b)).button_confirm()
        self.assertIn(control.state, ("purchase", "to approve"), "SETUP control confirmation failed")
        self.assertIsNone(
            probe_error,
            f"PROBE F-13 reproduced: order of company B refused while company A is active: {probe_error}",
        )

    def test_F13b_partner_status_depends_on_active_company(self):
        """F-13 (cache): the partner qualification status is recomputed per active company."""
        try:
            supplier = self._qualified_supplier_for_b()
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP could not build an approved dossier: {error}")
        self.env.invalidate_all()
        in_b = supplier.with_env(self._env_ab(self.company_b)).ls_is_approved_supplier
        in_a = supplier.with_env(self._env_ab(self.company_a)).ls_is_approved_supplier
        self.assertTrue(in_b, "SETUP supplier not approved in company B")
        self.assertFalse(
            in_a,
            "PROBE F-13 variant reproduced: the approval computed for company B is reused when company A is active "
            "(missing @api.depends_context('company'))",
        )

    # ------------------------------------------------------------------
    def test_F16_batch_lot_must_match_product_and_company(self):
        """F-16: a pharmaceutical batch cannot reference the lot of another product."""
        other_product = self._product("Probe other product", "lot")
        foreign_lot = self._lot(other_product, "PROBE-F16")
        batch_product = self.env["product.product"].create({"name": "Probe batch product"})
        base_values = {
            "product_id": batch_product.id,
            "batch_type": "finished",
            "uom_id": self.uom_unit.id,
            "planned_qty": 100.0,
            "theoretical_yield_qty": 100.0,
            "yield_min_percentage": 95.0,
            "yield_max_percentage": 102.0,
            "shelf_life_months": 24,
        }
        try:
            with self.env.cr.savepoint():
                self.env["ls.pharma.batch"].create(dict(base_values))
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP control batch cannot be created: {error}")
        try:
            with self.env.cr.savepoint():
                self.env["ls.pharma.batch"].create(dict(base_values, lot_id=foreign_lot.id))
            accepted = True
        except (UserError, ValidationError):
            accepted = False
        self.assertFalse(accepted, "PROBE F-16 reproduced: a batch accepted the lot of another product")

    # ------------------------------------------------------------------
    def test_F24_check_company_enforced_on_qms_objective(self):
        """F-24: an objective of company A cannot point to a policy of company B."""
        today = fields.Date.context_today(self.env.user)
        policy_b = self.env["ls.qms.policy"].create({
            "name": "Probe policy B",
            "author_id": self.env.user.id,
            "policy_statement": "<p>Probe.</p>",
            "scope": "Probe.",
            "company_id": self.company_b.id,
        })
        department = self.env["hr.department"].create({"name": "Probe dept"})
        values = {
            "name": "Probe objective",
            "company_id": self.company_a.id,
            "responsible_id": self.env.user.id,
            "department_id": department.id,
            "direction": "increase",
            "baseline_value": 70.0,
            "target_value": 90.0,
            "date_start": today - relativedelta(months=6),
            "date_target": today + relativedelta(months=6),
        }
        try:
            with self.env.cr.savepoint():
                self.env["ls.qms.objective"].create(dict(values))
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP control objective cannot be created: {error}")
        try:
            with self.env.cr.savepoint():
                self.env["ls.qms.objective"].create(dict(values, policy_id=policy_b.id))
            accepted = True
        except (UserError, ValidationError):
            accepted = False
        self.assertFalse(accepted, "PROBE F-24 reproduced: objective of company A linked to a policy of company B")
