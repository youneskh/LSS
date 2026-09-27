# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the change control test suite."""

from odoo.tests.common import TransactionCase, new_test_user


class ChangeControlCommon(TransactionCase):
    """Base class building a complete, deterministic change control setup."""

    @classmethod
    def setUpClass(cls):
        """Create the users, the configuration and the helper references."""
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

        cls.group_viewer = "ls_change_control.group_ls_change_control_viewer"
        cls.group_requester = "ls_change_control.group_ls_change_control_requester"
        cls.group_approver = "ls_change_control.group_ls_change_control_approver"
        cls.group_manager = "ls_change_control.group_ls_change_control_manager"

        cls.user_viewer = new_test_user(
            cls.env, login="ls_cc_viewer", groups=cls.group_viewer
        )
        cls.user_requester = new_test_user(
            cls.env, login="ls_cc_requester", groups=cls.group_requester
        )
        cls.user_other_requester = new_test_user(
            cls.env, login="ls_cc_requester2", groups=cls.group_requester
        )
        cls.user_assessor = new_test_user(
            cls.env, login="ls_cc_assessor", groups=cls.group_requester
        )
        cls.user_approver_qa = new_test_user(
            cls.env, login="ls_cc_approver_qa", groups=cls.group_approver
        )
        cls.user_approver_prod = new_test_user(
            cls.env, login="ls_cc_approver_prod", groups=cls.group_approver
        )
        cls.user_manager = new_test_user(
            cls.env, login="ls_cc_manager", groups=cls.group_manager
        )

        cls.area_documentation = cls.env.ref(
            "ls_change_control.impact_area_documentation"
        )
        cls.area_process = cls.env.ref("ls_change_control.impact_area_process")

        cls.category = cls.env["ls.change_control.category"].create(
            {
                "name": "Test Category",
                "code": "TESTCAT",
                "implementation_delay": 30,
                "verification_delay": 15,
                "requires_verification": True,
                "impact_area_ids": [
                    (6, 0, [cls.area_documentation.id, cls.area_process.id])
                ],
                "approval_template_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "approval_role": "quality_assurance",
                            "user_id": cls.user_approver_qa.id,
                            "mandatory": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 20,
                            "approval_role": "production",
                            "user_id": cls.user_approver_prod.id,
                            "mandatory": True,
                        },
                    ),
                ],
            }
        )

        cls.request_model = cls.env["ls.change_control.request"]
        cls.assessment_model = cls.env["ls.change_control.assessment"]
        cls.approval_model = cls.env["ls.change_control.approval"]
        cls.implementation_model = cls.env["ls.change_control.implementation"]
        cls.verification_model = cls.env["ls.change_control.verification"]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _request_values(self, **overrides):
        """Return a valid set of values for a change request.

        :param overrides: values overriding the defaults.
        :return: dictionary usable in ``create``.
        """
        values = {
            "title": "Test change",
            "category_id": self.category.id,
            "change_type": "permanent",
            "classification": "minor",
            "current_situation": "Situation before the change.",
            "proposed_change": "Situation after the change.",
            "justification": "The change is required by a test.",
        }
        values.update(overrides)
        return values

    def _create_request(self, user=None, **overrides):
        """Create a change request, optionally as a specific user.

        :param user: ``res.users`` record creating the request.
        :param overrides: values overriding the defaults.
        :return: the created ``ls.change_control.request`` record.
        """
        model = self.request_model
        if user is not None:
            model = model.with_user(user)
        return model.create(self._request_values(**overrides))

    def _prepare_review(self, request):
        """Submit the request and set the data required by the review.

        :param request: the change request to prepare.
        :return: the same request, in the Under Review state.
        """
        request.with_user(request.requester_id).action_submit_review()
        request.with_user(self.user_manager).write(
            {
                "manager_id": self.user_manager.id,
                "impact_area_ids": [
                    (6, 0, [self.area_documentation.id, self.area_process.id])
                ],
            }
        )
        return request

    def _to_impact_assessment(self, request):
        """Bring the request to the Impact Assessment state.

        :param request: a Draft change request.
        :return: the same request, in the Impact Assessment state.
        """
        self._prepare_review(request)
        request.with_user(self.user_manager).action_start_assessment()
        return request

    def _complete_assessments(self, request):
        """Complete every assessment of the request as its assessor.

        :param request: a request in the Impact Assessment state.
        """
        for assessment in request.assessment_ids:
            assessment.with_user(self.user_manager).write(
                {
                    "assessor_id": self.user_assessor.id,
                    "impact": "none",
                    "assessment": "No impact identified on this area.",
                }
            )
            assessment.with_user(self.user_assessor).action_complete()

    def _grant_approvals(self, request):
        """Record a favourable decision on every approval of the request.

        :param request: a request in the Impact Assessment state.
        """
        for approval in request.approval_ids:
            approval.with_user(approval.user_id).action_approve()

    def _to_approved(self, request):
        """Bring the request to the Approved state.

        :param request: a Draft change request.
        :return: the same request, in the Approved state.
        """
        self._to_impact_assessment(request)
        self._complete_assessments(request)
        self._grant_approvals(request)
        return request

    def _add_implementation(self, request, **overrides):
        """Create one implementation action on the request.

        :param request: the parent change request.
        :param overrides: values overriding the defaults.
        :return: the created action.
        """
        values = {
            "request_id": request.id,
            "name": "Revise the procedure",
            "action_type": "document_update",
            "responsible_id": self.user_requester.id,
            "date_planned": "2026-12-31",
        }
        values.update(overrides)
        return self.implementation_model.with_user(self.user_manager).create(values)

    def _add_verification(self, request, **overrides):
        """Create one effectiveness verification on the request.

        :param request: the parent change request.
        :param overrides: values overriding the defaults.
        :return: the created verification.
        """
        values = {
            "request_id": request.id,
            "name": "Review of the revised procedure",
            "method": "document_review",
            "verifier_id": self.user_requester.id,
            "date_planned": "2026-12-31",
            "acceptance_criteria": "The revised procedure is effective and trained.",
        }
        values.update(overrides)
        return self.verification_model.with_user(self.user_manager).create(values)
