# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Shared fixtures for the ``ls_cosmetics`` test suite."""

from odoo.tests.common import TransactionCase, new_test_user


class LsCosmeticsCommon(TransactionCase):
    """Base class building a small but complete cosmetic dossier.

    Users are created with :func:`odoo.tests.common.new_test_user`, which
    accepts group external identifiers as a string. That avoids writing to
    the groups field of ``res.users`` directly, whose name changed in
    Odoo 19.
    """

    @classmethod
    def setUpClass(cls):
        """Create the company, users, ingredients and a valid formulation."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner_model = cls.env["res.partner"]
        cls.formulation_model = cls.env["ls.cosmetic.formulation"]
        cls.ingredient_model = cls.env["ls.cosmetic.ingredient"]
        cls.restriction_model = cls.env["ls.cosmetic.restriction"]
        cls.assessment_model = cls.env["ls.cosmetic.safety_assessment"]
        cls.claim_model = cls.env["ls.cosmetic.claim"]
        cls.label_model = cls.env["ls.cosmetic.label"]
        cls.pif_model = cls.env["ls.cosmetic.pif"]
        cls.dz_model = cls.env["ls.cosmetic.dz_authorization"]

        cls.user_reader = new_test_user(
            cls.env,
            login="ls_cosmetics_reader",
            groups="ls_cosmetics.group_ls_cosmetics_user",
        )
        cls.user_formulator = new_test_user(
            cls.env,
            login="ls_cosmetics_formulator",
            groups="ls_cosmetics.group_ls_cosmetics_formulator",
        )
        cls.user_assessor = new_test_user(
            cls.env,
            login="ls_cosmetics_assessor",
            groups="ls_cosmetics.group_ls_cosmetics_safety_assessor",
        )
        cls.user_manager = new_test_user(
            cls.env,
            login="ls_cosmetics_manager",
            groups="ls_cosmetics.group_ls_cosmetics_regulatory_manager",
        )

        cls.assessor_partner = cls.partner_model.create(
            {
                "name": "Dr Test Assessor",
                "street": "1 Assessment Street",
                "city": "Algiers",
            }
        )
        cls.responsible_partner = cls.partner_model.create(
            {
                "name": "Test Responsible Person SARL",
                "street": "2 Responsibility Road",
                "city": "Algiers",
            }
        )
        cls.product = cls.env["product.template"].create(
            {"name": "Test Hydrating Cream", "ls_is_cosmetic": True}
        )

        cls.aqua = cls.ingredient_model.create(
            {"inci_name": "AQUA", "technical_function": "Solvent"}
        )
        cls.glycerin = cls.ingredient_model.create(
            {"inci_name": "GLYCERIN", "technical_function": "Humectant"}
        )
        cls.preservative = cls.ingredient_model.create(
            {
                "inci_name": "PHENOXYETHANOL",
                "regulatory_category": "preservative",
                "technical_function": "Preservative",
            }
        )
        cls.perfume = cls.ingredient_model.create(
            {
                "inci_name": "TEST FRAGRANCE COMPOSITION",
                "is_perfume_component": True,
                "perfume_term": "parfum",
                "perfume_composition_code": "FRG-001",
            }
        )
        cls.nano = cls.ingredient_model.create(
            {
                "inci_name": "TITANIUM DIOXIDE",
                "is_nanomaterial": True,
                "regulatory_category": "uv_filter",
            }
        )

        cls.formulation = cls.formulation_model.create(
            {
                "name": "Hydrating Cream Base",
                "product_tmpl_id": cls.product.id,
                "intended_use": "Applied to the face once daily.",
                "target_population": "Adults.",
                "line_ids": [
                    (0, 0, {"ingredient_id": cls.aqua.id, "concentration": 70.0}),
                    (0, 0, {"ingredient_id": cls.glycerin.id, "concentration": 25.0}),
                    (0, 0, {"ingredient_id": cls.nano.id, "concentration": 4.0}),
                    (
                        0,
                        0,
                        {"ingredient_id": cls.preservative.id, "concentration": 0.7},
                    ),
                    (0, 0, {"ingredient_id": cls.perfume.id, "concentration": 0.3}),
                ],
            }
        )

    @classmethod
    def _approve_formulation(cls, formulation=None):
        """Submit and approve a formulation with two distinct users.

        :param formulation: the formulation to approve; defaults to the one
            built by :meth:`setUpClass`.
        :return: the approved formulation.
        """
        formulation = formulation or cls.formulation
        formulation.with_user(cls.user_formulator).action_submit_review()
        formulation.with_user(cls.user_manager).action_approve()
        return formulation

    @classmethod
    def _part_a_values(cls):
        """Return a dictionary filling every Annex I Part A section.

        :return: a dictionary of field values.
        """
        return {
            field_name: f"Documented content for {label}."
            for field_name, label in cls.assessment_model._PART_A_FIELDS
        }

    @classmethod
    def _build_approved_assessment(cls, formulation=None):
        """Create and approve a safety report on an approved formulation.

        :param formulation: the formulation to assess.
        :return: the approved safety report.
        """
        formulation = formulation or cls.formulation
        if formulation.state != "approved":
            cls._approve_formulation(formulation)
        values = {
            "name": "CPSR for the hydrating cream",
            "formulation_id": formulation.id,
            "assessor_partner_id": cls.assessor_partner.id,
            "assessor_user_id": cls.user_assessor.id,
            "assessor_qualification": "Doctor of Pharmacy, University of Algiers",
            "conclusion": "safe",
            "conclusion_statement": "The product is safe under normal use.",
            "labelled_warnings": "Avoid contact with the eyes.",
            "reasoning": "Margins of safety are adequate for every substance.",
        }
        values.update(cls._part_a_values())
        assessment = cls.assessment_model.create(values)
        assessment.action_start_part_a()
        assessment.action_start_part_b()
        assessment.with_user(cls.user_assessor).action_approve()
        return assessment
