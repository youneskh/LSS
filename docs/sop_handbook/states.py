# -*- coding: utf-8 -*-
"""Lifecycle definitions used by the state diagrams.

The state keys and English labels are read from ``data/states_from_db.txt``,
an export of ``ir_model_fields_selection`` taken from a database where the
22 LS modules were installed (Odoo 19.0 Community). The French labels are
translations added for the French handbook; the software itself shows the
English label.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    states = {}
    with open(os.path.join(HERE, "data", "states_from_db.txt"), encoding="utf-8") as fh:
        for line in fh:
            model, _field, values = line.rstrip("\n").split("|", 2)
            pairs = []
            for item in values.split(" > "):
                key, label = item.split("=", 1)
                pairs.append((key, label))
            states[model] = dict(pairs)
    return states


STATES = _load()

FR = {
    "Draft": "Brouillon", "Approved": "Approuvé", "Obsolete": "Obsolète", "Issued": "Émis",
    "Response Received": "Réponse reçue", "Action In Progress": "Action en cours",
    "Pending Verification": "Vérification en attente", "Closed": "Clos", "Cancelled": "Annulé",
    "In Progress": "En cours", "Under Review": "En revue", "Planned": "Planifié",
    "Scheduled": "Programmé", "Completed": "Terminé", "Follow-up": "Suivi",
    "Generated": "Généré", "Superseded": "Remplacé", "In Service": "En service",
    "Out of Service": "Hors service", "Retired": "Réformé", "Active": "Actif",
    "Suspended": "Suspendu", "To Review": "À revoir", "Rejected": "Rejeté", "Done": "Fait",
    "Identified": "Identifié", "Assessed": "Évalué", "Investigation": "Investigation",
    "Action Planning": "Planification des actions", "Verified": "Vérifié", "Confirmed": "Confirmé",
    "Pending": "En attente", "Impact Assessment": "Évaluation d'impact",
    "Implementation": "Mise en œuvre", "Received": "Reçue", "Assessment": "Évaluation",
    "CAPA Required": "CAPA requise", "Resolution": "Résolution", "Submitted": "Soumis",
    "Reported": "Déclarée", "Disposition": "Disposition", "To Do": "À faire",
    "Published": "Publié", "Archived": "Archivé", "Passed": "Réussi", "Failed": "Échoué",
    "Awaiting Signature": "Signature attendue", "Signed": "Signé", "Declined": "Refusé",
    "Expired": "Expiré", "Open": "Ouvert", "Pending Closure": "Clôture proposée",
    "Collected": "Prélevé", "In Analysis": "En analyse", "Results Entered": "Résultats saisis",
    "Reviewed": "Revu", "Computed": "Calculé", "In Force": "En vigueur", "Amended": "Modifié",
    "Repealed": "Abrogé", "Answered": "Répondue", "Will Not Answer": "Sans réponse",
    "Phase I - Laboratory": "Phase I – laboratoire", "Phase I Complete": "Phase I terminée",
    "Phase II - Full Investigation": "Phase II – enquête complète", "Concluded": "Conclue",
    "Testing": "Analyses", "Results Recorded": "Résultats enregistrés",
    "Ongoing": "En cours", "Terminated": "Arrêtée", "Sampled": "Échantillonné",
    "Tested": "Analysé", "Missed": "Manqué", "Entered": "Saisi",
    "Submitted to Notified Body": "Soumis à l'organisme notifié",
    "Certificate Issued": "Certificat délivré", "Valid": "Valide", "Withdrawn": "Retiré",
    "Under Development": "En développement", "Conformity Assessment": "Évaluation de conformité",
    "On the Market": "Sur le marché", "Assigned": "Attribué",
    "Published to Database": "Publié dans la base", "Released": "Libéré", "On Hold": "En attente",
    "Setup": "Réglage", "Start-up Verification": "Vérification de démarrage", "Running": "En production",
    "Under Maintenance": "En maintenance", "Quarantined": "En quarantaine",
    "Decommissioned": "Mis au rebut", "Blocked": "Bloquée", "Removed": "Retirée",
    "Packed": "Conditionné", "Shipped": "Expédié", "Disaggregated": "Désagrégé",
    "Qualified": "Qualifié", "Restricted": "Restreint", "In Production": "En production",
    "Manufacturing Complete": "Fabrication terminée", "Quarantine": "Quarantaine",
    "QA Record Review": "Revue AQ du dossier", "In Execution": "En exécution",
    "Execution Complete": "Exécution terminée", "Under QA Review": "En revue AQ",
    "Under Investigation": "En investigation", "Not Applicable": "Sans objet",
    "Not Started": "Non commencée", "In Preparation": "En préparation", "Ready": "Prête",
    "Deficiency": "Objection", "Complete": "Terminée", "Ready for Submission": "Prêt à soumettre",
    "Deficiency Received": "Objections reçues", "Commissioned": "Activé", "Aggregated": "Agrégé",
    "Decommissioned ": "Désactivé", "Destroyed": "Détruit", "Returned": "Retourné",
    "In Storage": "En stockage", "Pulled": "Sorti", "Consumed": "Consommé", "Discarded": "Éliminé",
    "Out of Specification": "Hors spécification", "Under Revision": "En révision",
    "Achieved": "Atteint", "Not Achieved": "Non atteint", "Disposed": "Détruit",
    "Sent": "Envoyé", "Acknowledged": "Accusé de réception", "Performed": "Réalisée",
    "Escalated": "Relancée", "Initiated": "Lancé", "Communication": "Communication",
    "Effectiveness Check": "Vérification d'efficacité", "Risk Control": "Maîtrise du risque",
    "Monitoring": "Surveillance", "Registered": "Enregistré", "Under Assessment": "En évaluation",
    "Under Audit": "En audit", "Pending Approval": "En attente d'approbation",
    "Conditionally Approved": "Approuvé sous conditions", "Disqualified": "Disqualifié",
    "Under Qualification": "En qualification", "Report Drafted": "Rapport rédigé",
    "Report Issued": "Rapport émis", "Action Agreed": "Action convenue", "Implemented": "Mis en œuvre",
    "Valid ": "Valide", "Expiring Soon": "Expire bientôt", "Revoked": "Révoqué",
    "Under Substantiation": "En justification", "Deposit Receipt Issued": "Récépissé de dépôt délivré",
    "Authorisation Granted": "Autorisation accordée", "Refused": "Refusée",
    "Formal Notice Issued": "Mise en demeure", "Part A in Preparation": "Partie A en préparation",
    "Part B in Assessment": "Partie B en évaluation", "Retention Period": "Période de conservation",
    "Sent ": "Envoyé",
}

# flow id -> (model, nominal path, other outcomes)
FLOWS = {
    "qms_doc": ("ls.qms.sop", ["draft", "under_review", "approved", "published"], ["under_revision", "obsolete"]),
    "qms_objective": ("ls.qms.objective", ["draft", "in_progress", "achieved"], ["not_achieved", "cancelled"]),
    "qms_record": ("ls.qms.quality_record", ["draft", "confirmed", "archived", "disposed"], []),
    "dms_doc": ("ls.document.document", ["draft", "under_review", "approved", "published", "archived"], []),
    "training_course": ("ls.training.course", ["draft", "review", "approved"], ["obsolete"]),
    "training_session": ("ls.training.session", ["draft", "confirmed", "in_progress", "done"], ["cancelled"]),
    "training_cert": ("ls.training.certification", ["valid", "expiring", "expired"], ["revoked"]),
    "deviation": ("ls.deviation", ["reported", "assessed", "investigation", "disposition", "closed"], ["capa_required", "cancelled"]),
    "capa": ("ls.capa.issue", ["identified", "assessed", "investigation", "action_planning", "in_progress", "completed", "verified", "closed"], []),
    "capa_eff": ("ls.capa.effectiveness", ["draft", "planned", "done"], []),
    "change": ("ls.change_control.request", ["draft", "under_review", "impact_assessment", "approved", "implementation", "verified", "closed"], ["rejected", "cancelled"]),
    "complaint": ("ls.complaint", ["received", "assessment", "investigation", "resolution", "closed"], ["capa_required", "cancelled"]),
    "adverse_event": ("ls.complaint.adverse_event", ["draft", "assessed", "submitted", "closed"], []),
    "audit_program": ("ls.audit.program", ["draft", "approved", "in_progress", "closed"], ["cancelled"]),
    "audit": ("ls.audit.schedule", ["planned", "scheduled", "in_progress", "completed", "follow_up", "closed"], ["cancelled"]),
    "audit_finding": ("ls.audit.finding", ["draft", "open", "responded", "in_progress", "verification", "closed"], ["cancelled"]),
    "audit_report": ("ls.audit.report", ["draft", "under_review", "approved", "issued"], ["cancelled"]),
    "risk_register": ("ls.risk.register", ["draft", "assessed", "control", "monitoring", "closed"], ["cancelled"]),
    "risk_fmea": ("ls.risk.fmea", ["draft", "in_progress", "review", "approved", "closed"], ["cancelled"]),
    "risk_mitigation": ("ls.risk.mitigation", ["draft", "approved", "in_progress", "implemented", "verified"], ["cancelled"]),
    "supplier_dossier": ("ls.supplier.qualification", ["draft", "assessment", "audit", "approval", "approved"], ["conditional", "suspended", "expired", "disqualified"]),
    "supplier_audit": ("ls.supplier.audit", ["draft", "planned", "in_progress", "report_draft", "report_issued", "response_received", "closed"], ["cancelled"]),
    "supplier_finding": ("ls.supplier.audit.finding", ["open", "response_received", "action_agreed", "implemented", "verified", "closed"], ["cancelled"]),
    "supplier_perf": ("ls.supplier.performance", ["draft", "confirmed"], ["cancelled"]),
    "evidence_pack": ("ls.audit_trail.evidence_pack", ["draft", "generated"], []),
    "sig_request": ("ls.signature.request", ["draft", "pending", "signed"], ["declined", "expired", "cancelled"]),
    "vmp": ("ls.validation.master.plan", ["draft", "review", "approved", "active"], ["superseded", "cancelled"]),
    "protocol": ("ls.validation.protocol", ["draft", "review", "approved", "execution", "executed", "closed"], ["cancelled"]),
    "execution": ("ls.validation.execution", ["draft", "in_progress", "completed", "reviewed", "approved"], ["rejected", "cancelled"]),
    "vdiscrepancy": ("ls.validation.discrepancy", ["open", "investigation", "resolved", "closed"], ["cancelled"]),
    "vreport": ("ls.validation.report", ["draft", "review", "approved"], ["cancelled"]),
    "instrument": ("ls.calibration.instrument", ["draft", "in_service"], ["out_of_service", "retired"]),
    "cal_record": ("ls.calibration.record", ["draft", "in_progress", "to_review", "approved"], ["rejected", "cancelled"]),
    "cal_cert": ("ls.calibration.certificate", ["draft", "issued"], ["superseded"]),
    "em_plan": ("ls.env.plan", ["draft", "approved"], ["superseded", "cancelled"]),
    "em_limit": ("ls.env.limit", ["draft", "approved"], ["superseded"]),
    "em_sample": ("ls.env.sample", ["draft", "scheduled", "collected", "in_analysis", "results_entered", "reviewed", "approved"], ["cancelled"]),
    "em_excursion": ("ls.env.excursion", ["open", "assessment", "investigation", "pending_closure", "closed"], ["cancelled"]),
    "em_trend": ("ls.env.trend", ["draft", "computed", "reviewed"], []),
    "recall_plan": ("ls.recall.plan", ["draft", "under_review", "approved"], ["obsolete"]),
    "recall": ("ls.recall.execution", ["planned", "initiated", "in_progress", "communication", "effectiveness_check", "closed"], ["cancelled"]),
    "recall_eff": ("ls.recall.effectiveness", ["planned", "performed"], ["escalated", "cancelled"]),
    "batch": ("ls.pharma.batch", ["draft", "in_process", "manufactured", "quarantine", "under_review", "released"], ["rejected", "cancelled"]),
    "batch_record": ("ls.pharma.batch_record", ["draft", "in_execution", "completed", "under_review", "approved"], ["rejected"]),
    "material": ("ls.pharma.api", ["draft", "qualified"], ["restricted", "obsolete"]),
    "stability": ("ls.pharma.stability_study", ["draft", "scheduled", "ongoing", "completed"], ["terminated"]),
    "serial": ("ls.pharma.serialization", ["generated", "commissioned", "aggregated", "shipped"], ["decommissioned", "destroyed", "sampled", "returned"]),
    "ctd": ("ls.pharma.ctd_dossier", ["draft", "in_preparation", "ready", "submitted", "approved"], ["deficiency", "withdrawn"]),
    "formulation": ("ls.cosmetic.formulation", ["draft", "review", "approved"], ["superseded", "cancelled"]),
    "cpsr": ("ls.cosmetic.safety_assessment", ["draft", "part_a", "part_b", "approved"], ["superseded", "cancelled"]),
    "pif": ("ls.cosmetic.pif", ["draft", "active", "retention", "archived"], []),
    "claim": ("ls.cosmetic.claim", ["draft", "substantiation", "approved"], ["rejected", "withdrawn"]),
    "label": ("ls.cosmetic.label", ["draft", "review", "approved"], ["superseded"]),
    "dz": ("ls.cosmetic.dz_authorization", ["draft", "submitted", "receipt", "granted"], ["refused", "notice", "withdrawn"]),
    "md_device": ("ls.md.device", ["draft", "development", "conformity_assessment", "on_market"], ["suspended", "withdrawn"]),
    "md_doc": ("ls.md.technical_file", ["draft", "under_review", "approved"], ["superseded", "cancelled"]),
    "udi": ("ls.md.udi", ["draft", "assigned", "published"], ["obsolete"]),
    "ce": ("ls.md.ce_marking", ["draft", "submitted", "issued", "valid"], ["suspended", "withdrawn", "expired"]),
    "mp_tool": ("ls.mp.tool", ["draft", "qualified", "in_service"], ["maintenance", "quarantined", "decommissioned"]),
    "mp_maint": ("ls.mp.tool.maintenance", ["draft", "in_progress", "done"], ["cancelled"]),
    "mp_param": ("ls.mp.molding_parameter", ["draft", "review", "approved"], ["superseded", "obsolete", "cancelled"]),
    "mp_run": ("ls.mp.injection_molding", ["draft", "setup", "startup_check", "running", "completed", "reviewed", "closed"], ["cancelled"]),
    "lab_method": ("ls.lab.test_method", ["draft", "review", "approved"], ["obsolete"]),
    "lab_sample": ("ls.lab.sample", ["received", "in_progress", "testing", "results_recorded", "reviewed", "approved", "reported"], ["cancelled"]),
    "lab_result": ("ls.lab.test_result", ["draft", "entered", "reviewed"], []),
    "oos": ("ls.lab.oos", ["open", "phase1", "phase1_done", "phase2", "concluded", "closed"], ["cancelled"]),
    "lab_stability": ("ls.lab.stability_study", ["draft", "approved", "ongoing", "completed"], ["terminated"]),
    "coa": ("ls.lab.coa", ["draft", "issued"], ["superseded", "cancelled"]),
    "provision": ("ls.import_export.provision", ["in_force", "amended", "repealed"], ["under_review"]),
    "question": ("ls.import_export.regulatory.question", ["open", "answered"], ["wont_answer"]),
}


def flow_labels(flow_id):
    model, main, side = FLOWS[flow_id]
    table = STATES[model]
    def lab(k):
        en = table[k]
        return (k, en, FR.get(en, en))
    return model, [lab(k) for k in main], [lab(k) for k in side]
