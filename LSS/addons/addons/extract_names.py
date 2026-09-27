import os
import logging

_logger = logging.getLogger(__name__)


# Path to the directory containing all your downloaded modules
# '.' means it scans the current folder where this script is placed
addons_path = '.'

module_list = []

for folder_name in os.listdir(addons_path):
    folder_path = os.path.join(addons_path, folder_name)

    # Check if it's a directory and contains an Odoo manifest file
    if os.path.isdir(folder_path):
        has_manifest = os.path.exists(os.path.join(folder_path, '__manifest__.py')) or \
                       os.path.exists(os.path.join(folder_path, '__openerp__.py'))

        # Exclude packaging/system folders like 'setup' or hidden git folders
        if has_manifest and folder_name != 'setup' and not folder_name.startswith('.'):
            module_list.append(folder_name)

# Sort alphabetically to keep it organized
module_list.sort()

# Print the formatted text ready for copy-pasting
_logger.info("    'depends': [")
for module in module_list:
    _logger.info("        '%s',", module)
_logger.info("    ],")
