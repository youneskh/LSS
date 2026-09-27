This module requires Odoo 19.0 Community Edition. It depends only on modules
shipped with the Community Edition: ``base``, ``web``, ``mail`` and
``maintenance``. No Enterprise module and no third party module is required.

The Python library ``python-dateutil`` is required. It is already a
dependency of Odoo itself, therefore no additional installation is normally
needed.

To install the module:

#. Copy the ``ls_calibration`` directory into a directory of the
   ``addons_path`` of the Odoo instance.
#. Restart the Odoo service.
#. Open :menuselection:`Apps`, click :guilabel:`Update Apps List`, search for
   *Calibration* and click :guilabel:`Install`.

The installation creates four number sequences, three security groups, six
multi-company record rules, two scheduled actions and one system parameter.
