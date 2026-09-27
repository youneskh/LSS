# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regression tests for the findings of the 2026-09-25 audit.

Odoo 19 normalises the operators "=" and "!=" to "in" and "not in" before
it calls the search method of a non-stored field; the counters of the areas
and sampling points must still be searchable.
"""

from odoo.tests import tagged

from .test_common import EnvMonitoringCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(EnvMonitoringCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    def test_area_counter_search_with_equality(self):
        """An area without open excursion is found with "= 0"."""
        found = self.env["ls.env.area"].search(
            [("open_excursion_count", "=", 0), ("id", "=", self.area.id)]
        )
        self.assertEqual(found, self.area)
        found = self.env["ls.env.area"].search(
            [("open_excursion_count", "!=", 0), ("id", "=", self.area.id)]
        )
        self.assertFalse(found)

    def test_point_counter_search_with_equality(self):
        """A point without approved limit is found with "= 0"."""
        found = self.env["ls.env.sampling_point"].search(
            [("approved_limit_count", "=", 0), ("id", "=", self.point.id)]
        )
        self.assertEqual(found, self.point)
        self._approve_limit(self._create_limit(self.point, self.parameter_count))
        found = self.env["ls.env.sampling_point"].search(
            [("approved_limit_count", "=", 1), ("id", "=", self.point.id)]
        )
        self.assertEqual(found, self.point)
