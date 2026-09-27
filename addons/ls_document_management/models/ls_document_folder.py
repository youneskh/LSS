# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Hierarchical folders holding controlled documents.

Folders carry the role-based access configuration that record rules apply to
the documents they contain, and supply the default retention policy for those
documents.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsDocumentFolder(models.Model):
    """Storage folder for controlled documents."""

    _name = "ls.document.folder"
    _description = "Life Sciences Document Folder"
    _check_company_auto = True
    _order = "complete_name"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"

    name = fields.Char(
        string="Folder Name",
        required=True,
        translate=True,
    )
    complete_name = fields.Char(
        string="Full Path",
        compute="_compute_complete_name",
        recursive=True,
        store=True,
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    parent_id = fields.Many2one(
        comodel_name="ls.document.folder",
        string="Parent Folder",
        index=True,
        ondelete="restrict",
        check_company=True,
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        comodel_name="ls.document.folder",
        inverse_name="parent_id",
        string="Sub-folders",
    )
    child_count = fields.Integer(
        string="Sub-folder Count",
        compute="_compute_child_count",
    )
    document_ids = fields.One2many(
        comodel_name="ls.document.document",
        inverse_name="folder_id",
        string="Documents",
    )
    document_count = fields.Integer(compute="_compute_document_count",)
    retention_policy_id = fields.Many2one(
        comodel_name="ls.document.retention_policy",
        string="Default Retention Policy",
        check_company=True,
        help=(
            "Retention policy proposed by default to documents created in "
            "this folder. It can be overridden on each document."
        ),
    )
    group_read_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="ls_document_folder_group_read_rel",
        column1="folder_id",
        column2="group_id",
        string="Read Groups",
        help=(
            "Groups allowed to read the documents of this folder. "
            "When left empty, every user holding a Life Sciences Document "
            "role may read them, subject to the model access rights."
        ),
    )
    group_write_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="ls_document_folder_group_write_rel",
        column1="folder_id",
        column2="group_id",
        string="Write Groups",
        help=(
            "Groups allowed to create, modify and delete the documents of "
            "this folder. When left empty, every user holding a Life "
            "Sciences Document role with write access may modify them."
        ),
    )
    default_approver_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_document_folder_approver_rel",
        column1="folder_id",
        column2="user_id",
        string="Default Approvers",
        help=(
            "Users proposed as approvers on documents created in this "
            "folder. The list can be adjusted on each document while it is "
            "in the Draft state."
        ),
    )

    _name_parent_company_uniq = models.Constraint(
        "UNIQUE(name, parent_id, company_id)",
        "A folder with this name already exists under the same parent folder.",
    )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        """Build the slash-separated full path of the folder."""
        for folder in self:
            if folder.parent_id:
                folder.complete_name = "%s / %s" % (
                    folder.parent_id.complete_name,
                    folder.name,
                )
            else:
                folder.complete_name = folder.name

    @api.depends("child_ids")
    def _compute_child_count(self):
        """Count the direct sub-folders."""
        for folder in self:
            folder.child_count = len(folder.child_ids)

    @api.depends("document_ids")
    def _compute_document_count(self):
        """Count the documents directly stored in the folder."""
        for folder in self:
            folder.document_count = len(folder.document_ids)

    @api.constrains("parent_id")
    def _check_folder_hierarchy(self):
        """Forbid cycles in the folder hierarchy.

        The check walks the parent chain of every record and stops as soon as
        an already visited folder is met. It relies only on ``parent_id`` and
        therefore does not depend on framework helper methods whose names have
        changed between Odoo versions.
        """
        for folder in self:
            visited = set()
            current = folder
            while current:
                if current.id in visited:
                    raise ValidationError(
                        _(
                            "The folder hierarchy is recursive: folder "
                            "'%(name)s' is its own ancestor.",
                            name=folder.name,
                        )
                    )
                visited.add(current.id)
                current = current.parent_id

    @api.constrains("company_id", "parent_id")
    def _check_company_consistency(self):
        """A sub-folder must belong to the company of its parent folder."""
        for folder in self:
            if folder.parent_id and folder.parent_id.company_id != folder.company_id:
                raise ValidationError(
                    _(
                        "Folder '%(name)s' must belong to the same company as "
                        "its parent folder.",
                        name=folder.name,
                    )
                )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_document_folder(self):
        """Prevent deletion of folders that still hold content."""
        for folder in self:
            if folder.document_ids:
                raise ValidationError(
                    _(
                        "Folder '%(name)s' cannot be deleted because it still "
                        "contains %(count)s document(s). Move or archive them "
                        "first.",
                        name=folder.name,
                        count=len(folder.document_ids),
                    )
                )
            if folder.child_ids:
                raise ValidationError(
                    _(
                        "Folder '%(name)s' cannot be deleted because it still "
                        "contains sub-folders.",
                        name=folder.name,
                    )
                )

    def action_open_documents(self):
        """Open the list of documents contained in the folder."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_document_management.action_ls_document_document"
        )
        action["domain"] = [("folder_id", "=", self.id)]
        action["context"] = {
            "default_folder_id": self.id,
            "search_default_folder_id": self.id,
        }
        return action
