# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Import models in dependency order.

Base / registry models first, then the entities that reference them.
Phase 1 ships only the registry and the abstract engine contract;
operational models (operations, shipments, costs) are added in
later phases and must be imported here at that time.
"""

from . import constants
from . import ls_import_export_provision
from . import ls_import_export_provision_citation
from . import ls_import_export_regulatory_question
from . import ls_import_export_compliance_requirement
