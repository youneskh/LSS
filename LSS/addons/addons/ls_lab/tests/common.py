# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Shared fixtures for the laboratory test suite."""

from odoo.tests.common import TransactionCase, new_test_user


class LsLabCommon(TransactionCase):
    """Base fixture providing users, a product, a method and a specification.

    Distinct users are created for each role because most rules under test are
    segregation-of-duties rules, which cannot be exercised with a single user.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analyst = new_test_user(
            cls.env,
            login="ls_lab_analyst",
            groups="ls_lab.ls_lab_group_analyst",
            name="Laboratory Analyst",
        )
        cls.analyst_two = new_test_user(
            cls.env,
            login="ls_lab_analyst_two",
            groups="ls_lab.ls_lab_group_analyst",
            name="Second Laboratory Analyst",
        )
        cls.reviewer = new_test_user(
            cls.env,
            login="ls_lab_reviewer",
            groups="ls_lab.ls_lab_group_reviewer",
            name="Laboratory Reviewer",
        )
        cls.manager = new_test_user(
            cls.env,
            login="ls_lab_manager",
            groups="ls_lab.ls_lab_group_manager",
            name="Laboratory Manager",
        )
        cls.viewer = new_test_user(
            cls.env,
            login="ls_lab_viewer",
            groups="ls_lab.ls_lab_group_viewer",
            name="Laboratory Viewer",
        )

        cls.product = cls.env["product.product"].create({
            "name": "Test Product Alpha",
        })

        cls.storage_condition = cls.env["ls.lab.storage_condition"].create({
            "name": "Study condition A",
            "code": "SC-A",
            "temperature_c": 25.0,
            "temperature_tolerance_c": 2.0,
            "humidity_rh": 60.0,
            "humidity_tolerance_rh": 5.0,
        })

    @classmethod
    def _create_approved_method(cls, name="Assay", result_type="numeric"):
        """Return an approved test method."""
        method = cls.env["ls.lab.test_method"].create({
            "name": name,
            "result_type": result_type,
        })
        method.action_submit_review()
        method.with_user(cls.manager).action_approve()
        return method

    @classmethod
    def _create_approved_specification(cls, lines=None, spec_type="finished_product"):
        """Return an approved specification carrying the given lines."""
        if lines is None:
            method = cls._create_approved_method()
            lines = [{
                "test_method_id": method.id,
                "criterion_type": "range",
                "min_value": 95.0,
                "max_value": 105.0,
            }]
        specification = cls.env["ls.lab.specification"].create({
            "name": "Release specification",
            "product_id": cls.product.id,
            "spec_type": spec_type,
            "line_ids": [(0, 0, line) for line in lines],
        })
        specification.action_submit_review()
        specification.with_user(cls.manager).action_approve()
        return specification

    @classmethod
    def _create_sample(cls, specification=None, sample_type="finished_product"):
        """Return a registered sample bound to an approved specification."""
        specification = specification or cls._create_approved_specification()
        return cls.env["ls.lab.sample"].create({
            "product_id": cls.product.id,
            "specification_id": specification.id,
            "sample_type": sample_type,
        })
