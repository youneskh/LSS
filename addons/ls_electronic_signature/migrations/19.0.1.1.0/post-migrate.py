# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Remove the clear-text passwords kept by earlier versions of the wizard.

Up to 19.0.1.0.0 the signature dialog stored the typed password in the
``password`` column of ``ls_signature_wizard``. The field is no longer
stored, and Odoo does not drop the orphan column by itself, so the column
is dropped here together with the values it holds.
"""


def migrate(cr, version):
    """Drop the obsolete clear-text password column.

    :param cr: database cursor.
    :param str version: installed version before the upgrade.
    """
    if not version:
        return
    cr.execute("ALTER TABLE ls_signature_wizard DROP COLUMN IF EXISTS password")
