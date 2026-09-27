# -*- coding: utf-8 -*-
"""Additional screenshots per SOP, captured after the demonstration scenarios
(scenarios/*.py) moved records through their real workflows."""
from .helpers import tr

EXTRA = {
    "SOP-QA-011": [("ls_training_certification__list", tr("Certifications issued automatically when the session was closed.", "Certifications émises automatiquement à la clôture de la session."))],
    "SOP-QA-021": [("ls_deviation_investigation__list", tr("Deviation investigations.", "Investigations de déviation."))],
    "SOP-QA-022": [("ls_capa_root_cause__form", tr("Five Whys root cause analysis, confirmed.", "Analyse 5 Pourquoi confirmée.")),
                   ("ls_capa_action__list", tr("CAPA actions with owners, dates and states.", "Actions CAPA avec responsables, dates et états."))],
    "SOP-QA-030": [("ls_change_control_request__form", tr("Change request in Impact Assessment, with generated assessments and approvals.", "Demande de changement en évaluation d'impact, avec évaluations et approbations générées.")),
                   ("ls_change_control_assessment__list", tr("Impact assessments per area.", "Évaluations d'impact par domaine."))],
    "SOP-QA-040": [("ls_complaint_investigation__form", tr("Complaint investigation (batch record review).", "Investigation de réclamation (revue du dossier de lot)."))],
    "SOP-QA-052": [("ls_audit_schedule__list", tr("Audits of the programme.", "Audits du programme."))],
    "SOP-DI-002": [("ls_audit_trail_log__list", tr("Audit trail entries created by the audit rules.", "Entrées de piste d'audit créées par les règles d'audit.")),
                   ("ls_audit_trail_verification__list", tr("Integrity verification: Passed.", "Vérification d'intégrité : réussie."))],
    "SOP-DI-003": [("ls_audit_trail_evidence_pack__form", tr("Generated evidence pack with its SHA-256 digest.", "Dossier de preuves généré et son empreinte SHA-256."))],
    "SOP-VAL-003": [("ls_validation_execution__form", tr("Execution in progress with a failed test linked to a discrepancy.", "Exécution en cours avec un test en échec lié à un écart.")),
                    ("ls_validation_discrepancy__form", tr("Validation discrepancy.", "Écart de validation."))],
    "SOP-MET-002": [("ls_calibration_record__form", tr("Approved calibration record with test points.", "Enregistrement d'étalonnage approuvé avec points de mesure."))],
    "SOP-EM-001": [("ls_env_plan__form", tr("Approved monitoring plan with its lines.", "Plan de surveillance approuvé et ses lignes."))],
    "SOP-EM-002": [("ls_env_limit__list", tr("Approved limits per point, parameter and occupancy state.", "Limites approuvées par point, paramètre et état d'occupation."))],
    "SOP-EM-003": [("ls_env_sample__form", tr("Approved sample with its evaluated result.", "Prélèvement approuvé et son résultat évalué."))],
    "SOP-EM-004": [("ls_env_excursion__form", tr("Excursion raised automatically at sample approval, in assessment.", "Excursion ouverte automatiquement à l'approbation, en évaluation."))],
    "SOP-QA-081": [("ls_recall_execution__form", tr("Recall record.", "Fiche de rappel."))],
    "SOP-PRD-001": [("ls_pharma_batch_record__form", tr("Batch production and control record with steps performed and checked.", "Dossier de production et de contrôle avec étapes exécutées et vérifiées."))],
    "SOP-QA-090": [("ls_pharma_batch__form", tr("Released batch.", "Lot libéré.")),
                   ("ls_pharma_batch_release__form", tr("Append-only release decision with its checklist.", "Décision de libération en ajout seul et sa liste de contrôle."))],
    "SOP-COS-001": [("ls_cosmetic_formulation__form", tr("Approved formulation totalling 100 % w/w.", "Formule approuvée totalisant 100 % p/p."))],
    "SOP-MP-001": [("ls_mp_tool__form", tr("Mould in service with its cavity register and shot counters.", "Moule en service avec registre des empreintes et compteurs."))],
    "SOP-MP-003": [("ls_mp_molding_parameter__form", tr("Approved process window (author, reviewer and approver are different users).", "Fenêtre de procédé approuvée (auteur, vérificateur et approbateur distincts)."))],
    "SOP-MP-004": [("ls_mp_injection_molding__form", tr("Completed run awaiting review, with an out-of-tolerance reading and its deviation reference.", "Campagne terminée en attente de revue, avec un relevé hors tolérance et sa référence de déviation."))],
    "SOP-MP-006": [("ls_mp_material_grade__form", tr("Qualified material grade.", "Grade de matière qualifié."))],
    "SOP-QC-010": [("ls_lab_specification__form", tr("Approved specification with acceptance criteria.", "Spécification approuvée et ses critères d'acceptation."))],
    "SOP-QC-012": [("ls_lab_sample__form", tr("Approved sample: results entered, reviewed and approved by three different users.", "Échantillon approuvé : résultats saisis, revus et approuvés par trois utilisateurs différents."))],
    "SOP-QC-013": [("ls_lab_oos__form", tr("OOS investigation in Phase I with laboratory checks.", "Enquête OOS en phase I avec vérifications de laboratoire."))],
    "SOP-QC-015": [("ls_lab_coa__form", tr("Issued certificate of analysis.", "Certificat d'analyse émis."))],
}


def apply(book):
    for item in book:
        if item.get("kind") == "sop" and item["code"] in EXTRA:
            existing = {s[0] for s in item["shots"]}
            item["shots"].extend(s for s in EXTRA[item["code"]] if s[0] not in existing)
