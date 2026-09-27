#!/bin/bash
# Patch Odoo core modules: tree view references → list (Odoo 19 renamed tree views to list)
# Fix specific known problematic references
sed -i 's/view_move_line_tree_detailed/view_move_line_list_detailed/g' /usr/lib/python3/dist-packages/odoo/addons/stock_delivery/views/delivery_view.xml
sed -i 's/module_tree/module_list/g' /usr/lib/python3/dist-packages/odoo/addons/delivery/views/ir_module_module_views.xml
echo "Patched tree view references"
