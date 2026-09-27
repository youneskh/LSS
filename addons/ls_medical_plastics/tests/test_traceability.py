# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for material traceability and genealogy resolution."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestTraceability(MedicalPlasticsCommon):
    """Forward and backward traceability across moulding runs."""

    def setUp(self):
        """Create a closed run carrying a produced lot and a resin lot."""
        super().setUp()
        self.resin_lot = self.env["stock.lot"].create(
            {"name": "RESIN-2026-0042", "product_id": self.product_resin.id}
        )
        self.produced_lot = self.env["stock.lot"].create(
            {"name": "CAP-2026-0100", "product_id": self.product_component.id}
        )
        self.run = self._create_run(lot_id=self.produced_lot.id)
        self.run.action_start_setup()
        self.run.action_start_startup_check()
        self._add_material(self.run, lot_id=self.resin_lot.id)
        self._capture_startup_readings(self.run)
        self.run.action_confirm_startup()
        self.run.write({"qty_produced": 800.0, "shot_count_end": 200})
        self.run.action_complete()
        self.run.with_user(self.user_manager).action_review()
        self.run.with_user(self.user_manager).action_close()

    def test_trace_by_produced_lot(self):
        """A produced lot resolves to the run that made it."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "produced_lot", "lot_id": self.produced_lot.id}
        )
        wizard.action_search()
        self.assertEqual(wizard.run_count, 1)
        self.assertIn(self.run, wizard.run_ids)

    def test_trace_by_material_lot(self):
        """A resin lot resolves forward to every run that consumed it."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "material_lot", "material_lot_id": self.resin_lot.id}
        )
        wizard.action_search()
        self.assertEqual(wizard.run_count, 1)
        self.assertIn(self.run, wizard.run_ids)

    def test_trace_by_component(self):
        """A component resolves to its closed runs."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "component", "component_id": self.component.id}
        )
        wizard.action_search()
        self.assertIn(self.run, wizard.run_ids)

    def test_trace_by_tool(self):
        """A tool resolves to the runs executed with it."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "tool", "tool_id": self.tool.id}
        )
        wizard.action_search()
        self.assertIn(self.run, wizard.run_ids)

    def test_open_runs_excluded_by_default(self):
        """Runs still in progress are excluded unless explicitly included."""
        open_run = self._create_run(lot_id=self.produced_lot.id)
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "produced_lot", "lot_id": self.produced_lot.id}
        )
        wizard.action_search()
        self.assertNotIn(open_run, wizard.run_ids)
        wizard.write({"include_open_runs": True})
        wizard.action_search()
        self.assertIn(open_run, wizard.run_ids)

    def test_missing_criterion_rejected(self):
        """An enquiry without its mandatory criterion is refused."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "produced_lot"}
        )
        with self.assertRaises(ValidationError):
            wizard.action_search()

    def test_period_end_after_start(self):
        """The enquiry period must be coherent."""
        with self.assertRaises(ValidationError):
            self.env["ls.mp.traceability.wizard"].create(
                {
                    "search_mode": "tool",
                    "tool_id": self.tool.id,
                    "date_from": "2026-06-01",
                    "date_to": "2026-01-01",
                }
            )

    def test_genealogy_structure_complete(self):
        """The genealogy exposes the full chain from lot to material and tool."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "produced_lot", "lot_id": self.produced_lot.id}
        )
        wizard.action_search()
        genealogy = wizard._collect_genealogy()
        self.assertEqual(len(genealogy), 1)
        entry = genealogy[0]
        self.assertEqual(entry["run"], self.run)
        self.assertEqual(entry["component"], self.component)
        self.assertEqual(entry["tool"], self.tool)
        self.assertEqual(entry["specification"], self.spec)
        self.assertEqual(entry["specification_version"], self.spec.version)
        self.assertIn(self.resin_lot, entry["material_lots"])
        self.assertTrue(entry["readings"])

    def test_open_results_requires_search(self):
        """Opening results before searching is refused."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "tool", "tool_id": self.tool.id}
        )
        with self.assertRaises(ValidationError):
            wizard.action_open_runs()

    def test_open_results_returns_action(self):
        """Opening results returns an action limited to the matching runs."""
        wizard = self.env["ls.mp.traceability.wizard"].create(
            {"search_mode": "tool", "tool_id": self.tool.id}
        )
        wizard.action_search()
        action = wizard.action_open_runs()
        self.assertEqual(action["res_model"], "ls.mp.injection_molding")
        self.assertIn(self.run.id, action["domain"][0][2])
