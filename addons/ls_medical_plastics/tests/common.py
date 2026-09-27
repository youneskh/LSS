# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the ``ls_medical_plastics`` test suite.

Users are created with ``new_test_user``, which resolves group membership by
XML identifier. This avoids depending on the name of the field holding group
links on ``res.users``, which could not be verified for Odoo 19.
"""

from odoo.tests.common import TransactionCase, new_test_user


class MedicalPlasticsCommon(TransactionCase):
    """Base fixture providing a complete, ready-to-run moulding context."""

    @classmethod
    def setUpClass(cls):
        """Build the master data shared by every test in the suite."""
        super().setUpClass()
        cls.company = cls.env.company

        # -- Users ------------------------------------------------------
        cls.user_operator = new_test_user(
            cls.env,
            login="mp_operator",
            name="Moulding Operator",
            groups="ls_medical_plastics.group_mp_operator",
        )
        cls.user_technician = new_test_user(
            cls.env,
            login="mp_technician",
            name="Tool Technician",
            groups="ls_medical_plastics.group_mp_technician",
        )
        cls.user_engineer = new_test_user(
            cls.env,
            login="mp_engineer",
            name="Process Engineer",
            groups="ls_medical_plastics.group_mp_engineer",
        )
        # Specifications are reviewed by an engineer other than their author
        # (README: engineers own specifications; technicians maintain tools).
        cls.user_engineer_reviewer = new_test_user(
            cls.env,
            login="mp_engineer_reviewer",
            name="Reviewing Process Engineer",
            groups="ls_medical_plastics.group_mp_engineer",
        )
        cls.user_manager = new_test_user(
            cls.env,
            login="mp_manager",
            name="Moulding Manager",
            groups="ls_medical_plastics.group_mp_manager",
        )
        cls.user_viewer = new_test_user(
            cls.env,
            login="mp_viewer",
            name="Moulding Viewer",
            groups="ls_medical_plastics.group_mp_viewer",
        )

        # -- Products ---------------------------------------------------
        cls.product_component = cls.env["product.product"].create(
            {"name": "Moulded Cap 28mm", "type": "consu"}
        )
        cls.product_resin = cls.env["product.product"].create(
            {"name": "Polypropylene Resin", "type": "consu"}
        )

        # -- Material grades --------------------------------------------
        cls.grade = cls.env["ls.mp.material.grade"].create(
            {
                "name": "PP Homopolymer MF-12",
                "code": "PP-MF12",
                "polymer_type": "pp",
                "product_id": cls.product_resin.id,
                "drug_contact": True,
                "qualification_state": "qualified",
                "qualification_date": "2026-01-15",
                "default_quantity_uom": "kg",
            }
        )
        cls.grade_unqualified = cls.env["ls.mp.material.grade"].create(
            {
                "name": "PP Trial Grade",
                "code": "PP-TRIAL",
                "polymer_type": "pp",
            }
        )

        # -- Component --------------------------------------------------
        cls.component = cls.env["ls.mp.component"].create(
            {
                "name": "Child Resistant Cap 28mm",
                "code": "CAP-28",
                "product_id": cls.product_component.id,
                "category": "closure_cap",
                "criticality": "critical",
                "drug_contact": True,
                "material_grade_ids": [(6, 0, [cls.grade.id])],
                "primary_material_grade_id": cls.grade.id,
            }
        )
        cls.component.action_release()

        # -- Work centre and tool ---------------------------------------
        cls.workcenter = cls.env["mrp.workcenter"].create(
            {"name": "Moulding Machine 01"}
        )
        cls.tool = cls.env["ls.mp.tool"].create(
            {
                "name": "Cap 28mm 4-Cavity Mould",
                "tool_type": "injection_mold",
                "cavity_count": 4,
                "workcenter_id": cls.workcenter.id,
                "component_ids": [(6, 0, [cls.component.id])],
                "qualification_date": "2026-01-10",
                "maintenance_interval_shots": 100000,
            }
        )
        cls.tool.action_qualify()
        cls.tool.action_place_in_service()

        # -- Approved parameter specification ---------------------------
        cls.spec = cls.env["ls.mp.molding_parameter"].with_user(
            cls.user_engineer
        ).create(
            {
                "component_id": cls.component.id,
                "tool_id": cls.tool.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Melt Temperature",
                            "code": "MELT-T",
                            "parameter_uom": "degC",
                            "value_type": "numeric",
                            "min_value": 210.0,
                            "target_value": 220.0,
                            "max_value": 230.0,
                            "is_critical": True,
                            "monitoring_frequency": "per_startup",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Injection Pressure",
                            "code": "INJ-P",
                            "parameter_uom": "bar",
                            "value_type": "numeric",
                            "min_value": 800.0,
                            "target_value": 900.0,
                            "max_value": 1000.0,
                            "is_critical": True,
                            "monitoring_frequency": "per_startup",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Cooling Time",
                            "code": "COOL-T",
                            "parameter_uom": "s",
                            "value_type": "numeric",
                            "min_value": 8.0,
                            "target_value": 10.0,
                            "max_value": 12.0,
                            "monitoring_frequency": "hourly",
                        },
                    ),
                ],
            }
        )
        cls.spec.with_user(cls.user_engineer).action_submit_for_review()
        cls.spec.with_user(cls.user_engineer_reviewer).action_review()
        cls.spec.with_user(cls.user_manager).action_approve()

        # -- Scrap reasons ----------------------------------------------
        cls.reason_startup = cls.env.ref(
            "ls_medical_plastics.mp_scrap_reason_startup_purge"
        )
        cls.reason_short_shot = cls.env.ref(
            "ls_medical_plastics.mp_scrap_reason_short_shot"
        )

    @classmethod
    def _create_run(cls, **overrides):
        """Create a draft moulding run against the standard fixture context.

        :param overrides: field values overriding the defaults.
        :return: the created moulding run.
        :rtype: recordset of ``ls.mp.injection_molding``
        """
        values = {
            "component_id": cls.component.id,
            "tool_id": cls.tool.id,
            "workcenter_id": cls.workcenter.id,
            "operator_id": cls.user_operator.id,
            "shot_count_start": 0,
        }
        values.update(overrides)
        return cls.env["ls.mp.injection_molding"].create(values)

    @classmethod
    def _add_material(cls, run, **overrides):
        """Attach a compliant material consumption line to a run.

        :param run: the moulding run receiving the line.
        :param overrides: field values overriding the defaults.
        :return: the created material line.
        :rtype: recordset of ``ls.mp.injection_molding.material``
        """
        values = {
            "run_id": run.id,
            "material_grade_id": cls.grade.id,
            "supplier_lot_reference": "LOT-2026-001",
            "quantity": 25.0,
            "quantity_uom": "kg",
        }
        values.update(overrides)
        return cls.env["ls.mp.injection_molding.material"].create(values)

    @classmethod
    def _capture_startup_readings(cls, run, values=None):
        """Capture in-specification start-up readings for the required parameters.

        :param run: the moulding run receiving the readings.
        :param dict values: optional mapping of parameter code to measured value.
        :return: the created readings.
        :rtype: recordset of ``ls.mp.injection_molding.reading``
        """
        values = values or {}
        reading_model = cls.env["ls.mp.injection_molding.reading"]
        to_create = []
        for line in run.parameter_spec_id.line_ids:
            if line.monitoring_frequency not in ("setup_only", "per_startup"):
                continue
            to_create.append(
                {
                    "run_id": run.id,
                    "parameter_line_id": line.id,
                    "reading_type": "startup",
                    "value_numeric": values.get(line.code, line.target_value),
                }
            )
        return reading_model.create(to_create)

    @classmethod
    def _run_to_completed(cls, run, qty_produced=1000.0, shot_count_end=250):
        """Advance a draft run through to the completed state.

        :param run: the moulding run to advance.
        :param float qty_produced: parts declared as produced.
        :param int shot_count_end: machine counter at the end of the run.
        :return: the same run, now completed.
        :rtype: recordset of ``ls.mp.injection_molding``
        """
        run.action_start_setup()
        run.action_start_startup_check()
        cls._add_material(run)
        cls._capture_startup_readings(run)
        run.action_confirm_startup()
        run.write({"qty_produced": qty_produced, "shot_count_end": shot_count_end})
        run.action_complete()
        return run
