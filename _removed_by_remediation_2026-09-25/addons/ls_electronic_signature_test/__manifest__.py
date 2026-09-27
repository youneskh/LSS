# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
{
    "name": "Life Sciences - Electronic Signatures (test fixture)",
    "summary": (
        "Signable fixture model and integration tests for the electronic "
        "signature module. Not for production installation."
    ),
    "version": "19.0.1.0.0",
    "category": "Hidden/Tests",
    "license": "AGPL-3",
    "author": "Life Sciences Suite Architecture Team",
    "depends": ["ls_electronic_signature"],
    "data": [
        "security/ir.model.access.csv",
        "views/ls_signature_test_record_views.xml",
    ],
    "demo": [
        "demo/ls_signature_test_demo.xml",
    ],
}
