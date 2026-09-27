# -*- coding: utf-8 -*-
"""Annexes: SOP register (generated from the sheets), glossary, known limitations, provenance."""
from . import part1a, part1b, part1c, part2a, part2b, part3a, part3b, part3c, part4_6

_SOPS = [i for m in (part1a, part1b, part1c, part2a, part2b, part3a, part3b, part3c, part4_6)
         for i in m.ITEMS if i["kind"] == "sop"]


def _register(lang):
    status = "To draft / adapt" if lang == "en" else "À rédiger / adapter"
    rows = [[s["code"], s[lang]["title"], s["module"], s[lang].get("owner", ""), status, ""] for s in _SOPS]
    head = (["Code", "Title", "Module", "Owner (suggested)", "Drafting status", "Target date"] if lang == "en" else
            ["Code", "Titre", "Module", "Propriétaire (suggéré)", "Statut de rédaction", "Échéance"])
    uncovered = [["SOP-IT-010", "Backup and restore" if lang == "en" else "Sauvegarde et restauration"],
                 ["SOP-IT-011", "Business continuity and disaster recovery" if lang == "en" else "Plan de continuité et reprise après sinistre"],
                 ["SOP-IT-012", "IT incident management" if lang == "en" else "Gestion des incidents informatiques"],
                 ["SOP-IT-013", "Physical security of servers" if lang == "en" else "Sécurité physique des serveurs"],
                 ["SOP-IT-014", "Qualification of the hosting" if lang == "en" else "Qualification de l'hébergement"],
                 ["SOP-VAL-010", "Validation of the suite (IQ, OQ, PQ)" if lang == "en" else "Validation de la suite (IQ, OQ, PQ)"]]
    for code, title in uncovered:
        rows.append([code, title, "— (" + ("not covered" if lang == "en" else "non couvert") + ")", "IT / QA", status, ""])
    return ("table", head, rows, "register")


GLOSSARY = {
    "en": [
        ["ALCOA+", "Attributable, Legible, Contemporaneous, Original, Accurate, plus Complete, Consistent, Enduring, Available — expected properties of GxP data."],
        ["Audit trail", "Secure, computer-generated, time-stamped record of creation, modification and deletion of records."],
        ["CAPA", "Corrective and Preventive Action."],
        ["CoA", "Certificate of Analysis."],
        ["CPSR", "Cosmetic Product Safety Report (Regulation (EC) No 1223/2009, Annex I)."],
        ["CSV", "Computerised System Validation."],
        ["CTD / eCTD", "Common Technical Document (ICH M4) / its electronic format."],
        ["DQ / IQ / OQ / PQ", "Design / Installation / Operational / Performance Qualification."],
        ["EM", "Environmental Monitoring."],
        ["FMEA / RPN", "Failure Modes and Effects Analysis / Risk Priority Number (S × O × D)."],
        ["FSCA", "Field Safety Corrective Action (medical devices)."],
        ["GTIN / SSCC", "Global Trade Item Number / Serial Shipping Container Code (GS1)."],
        ["GxP", "Good practices (manufacturing, laboratory, distribution, clinical…)."],
        ["INCI", "International Nomenclature of Cosmetic Ingredients."],
        ["MDR", "Regulation (EU) 2017/745 on medical devices."],
        ["OOS / OOT", "Out of specification / out of trend result."],
        ["PIF", "Product Information File (cosmetics, Article 11)."],
        ["PMCF / PMS / PSUR", "Post-Market Clinical Follow-up / Post-Market Surveillance / Periodic Safety Update Report."],
        ["QP", "Qualified Person (EU GMP Annex 16)."],
        ["Segregation of duties", "Rule that the same person cannot perform and approve (or review and approve) the same record."],
        ["SOP", "Standard Operating Procedure."],
        ["UDI (Basic UDI-DI, UDI-DI, UDI-PI)", "Unique Device Identification and its components."],
        ["VMP", "Validation Master Plan."],
    ],
    "fr": [
        ["ALCOA+", "Attribuable, lisible, contemporain, original, exact, plus complet, cohérent, durable, disponible — propriétés attendues des données GxP."],
        ["AMDE / IPR (FMEA / RPN)", "Analyse des modes de défaillance et de leurs effets / indice de priorité du risque (G × O × D)."],
        ["BPF", "Bonnes pratiques de fabrication."],
        ["CAPA", "Actions correctives et préventives."],
        ["CoA", "Certificat d'analyse."],
        ["CSV", "Validation des systèmes informatisés."],
        ["CTD / eCTD", "Document technique commun (ICH M4) / son format électronique."],
        ["DIP (PIF)", "Dossier d'information sur le produit cosmétique (article 11)."],
        ["DQ / IQ / OQ / PQ (QC / QI / QO / QP)", "Qualification de conception / d'installation / opérationnelle / de performance."],
        ["EM", "Surveillance de l'environnement (environmental monitoring)."],
        ["FSCA", "Action corrective de sécurité sur le terrain (dispositifs médicaux)."],
        ["GTIN / SSCC", "Code article international / code de colis (GS1)."],
        ["GxP", "Bonnes pratiques (fabrication, laboratoire, distribution, clinique…)."],
        ["INCI", "Nomenclature internationale des ingrédients cosmétiques."],
        ["IUD (UDI)", "Identification unique des dispositifs (IUD-ID de base, IUD-ID, IUD-IP)."],
        ["MDR", "Règlement (UE) 2017/745 relatif aux dispositifs médicaux."],
        ["OOS / OOT", "Résultat hors spécification / hors tendance."],
        ["PQ (personne qualifiée)", "Personne qualifiée certifiant les lots (BPF UE annexe 16)."],
        ["Piste d'audit", "Enregistrement sécurisé, généré par le système et horodaté, des créations, modifications et suppressions."],
        ["RSPC (CPSR)", "Rapport sur la sécurité du produit cosmétique (règlement (CE) n° 1223/2009, annexe I)."],
        ["SAC / SCAC / PSUR", "Surveillance après commercialisation / suivi clinique après commercialisation / rapport périodique actualisé de sécurité."],
        ["Séparation des tâches", "Règle selon laquelle une même personne ne peut exécuter et approuver (ou revoir et approuver) un même enregistrement."],
        ["SOP", "Procédure opératoire normalisée."],
        ["VMP", "Plan directeur de validation."],
    ],
}

LIMITS = {
    "en": [
        "**OCA modules that failed to install** on a fresh Odoo 19.0 Community database (source build of the 19.0 branch dated 26 September 2026) during the preparation of this handbook: *auditlog* (external ID `auditlog.view_auditlog_http_request_tree` not found), *base_user_role* (`base_user_role.view_res_users_role_tree` not found), and *mgmtsystem_kpi* and *mgmtsystem_review* through their dependency *base_external_dbsource* (`base_external_dbsource.view_dbsource_tree` not found). In each case the view was renamed from *tree* to *list* but a `ref=` still uses the old identifier. The project's own container image (19.0-20260723) and database were not available for comparison; the production database may already contain these modules from an earlier installation. SOP-GEN-001, SOP-GEN-002, SOP-IT-001 and SOP-IT-002 describe fall-back procedures.",
        "**Electronic signatures**: no production model of the 22 LS modules inherits *ls.signature.mixin*; signature policies can therefore not yet be applied to LS records (see the Electronic signatures chapter). ls_validation re-authenticates signers; ls_lab records a signature intent that it states is not a Part 11 signature; ls_supplier_qualification keeps a chained decision log without re-authentication.",
        "**Hand-offs between modules** (deviation → CAPA, complaint → CAPA, audit finding → CAPA, excursion → deviation…) are made by typed references, not by relational links. The procedures must require the references to be written and checked.",
        "**Translations**: the LS modules ship no French translation; the interface and the screenshots are in English.",
        "**Training**: ls_training states that it does not implement 21 CFR Part 11 (no electronic signature, no field-level audit trail of its own). There is no automatic link between a published document and a training course (SOP-QA-012).",
        "**Supplier purchase control** is installed at level *warn* by default; SOP-QA-073 requires *block* for GMP companies.",
        "**quality_control_oca**: no stock integration module is present in the repository; inspections are created manually.",
        "**Demonstration data**: many LS models ship no demo records. Additional demonstration records were created by the scripts in docs/sop_handbook/scenarios, which drive the real workflows with separate demonstration users (so that segregation-of-duties rules apply). Models still without data are shown as the empty form of a new record, with its real fields and status bar.",
    ],
    "fr": [
        "**Modules OCA qui ont échoué à l'installation** sur une base Odoo 19.0 Community neuve (construction depuis la branche 19.0 datée du 26 septembre 2026) lors de la préparation de ce manuel : *auditlog* (identifiant externe `auditlog.view_auditlog_http_request_tree` introuvable), *base_user_role* (`base_user_role.view_res_users_role_tree` introuvable), et *mgmtsystem_kpi* et *mgmtsystem_review* via leur dépendance *base_external_dbsource* (`base_external_dbsource.view_dbsource_tree` introuvable). Dans chaque cas, la vue a été renommée de *tree* en *list* mais un `ref=` utilise encore l'ancien identifiant. L'image conteneur du projet (19.0-20260723) et sa base n'étaient pas disponibles pour comparaison ; la base de production peut déjà contenir ces modules issus d'une installation antérieure. Les SOP-GEN-001, SOP-GEN-002, SOP-IT-001 et SOP-IT-002 décrivent des procédures de repli.",
        "**Signatures électroniques** : aucun modèle de production des 22 modules LS n'hérite de *ls.signature.mixin* ; les politiques de signature ne peuvent donc pas encore s'appliquer aux enregistrements LS (voir le chapitre Signatures électroniques). ls_validation réauthentifie les signataires ; ls_lab enregistre une intention de signature qu'il déclare non conforme Part 11 ; ls_supplier_qualification tient un journal des décisions chaîné sans réauthentification.",
        "**Passages de relais entre modules** (déviation → CAPA, réclamation → CAPA, constat d'audit → CAPA, excursion → déviation…) : ils se font par des références saisies, pas par des liens relationnels. Les procédures doivent exiger la saisie et la vérification de ces références.",
        "**Traductions** : les modules LS ne livrent pas de traduction française ; l'interface et les captures sont en anglais.",
        "**Formation** : ls_training déclare ne pas implémenter le 21 CFR Part 11 (ni signature électronique ni piste d'audit propre au niveau des champs). Il n'existe pas de lien automatique entre un document publié et un cours (SOP-QA-012).",
        "**Contrôle des achats fournisseurs** : installé au niveau *warn* par défaut ; la SOP-QA-073 exige *block* pour les sociétés BPF.",
        "**quality_control_oca** : aucun module d'intégration stock n'est présent dans le dépôt ; les inspections sont créées manuellement.",
        "**Données de démonstration** : de nombreux modèles LS ne livrent pas de données de démonstration. Des enregistrements supplémentaires ont été créés par les scripts de docs/sop_handbook/scenarios, qui déroulent les workflows réels avec des utilisateurs de démonstration distincts (pour que les règles de séparation des tâches s'appliquent). Les modèles encore sans données sont montrés par le formulaire vide d'un nouvel enregistrement, avec ses champs et sa barre d'état réels.",
    ],
}

ANNEXES = {
    "kind": "chapter", "id": "annexes",
    "en": {"title": "Annexes", "blocks": [
        ("h2", "Annex A — SOP register", "annex-a"),
        ("p", "Register of the SOPs of this handbook, to steer their drafting. Copy it into your document system and complete owners, dates and status."),
        _register("en"),
        ("pagebreak",),
        ("h2", "Annex B — Glossary", "annex-b"),
        ("table", ["Term", "Meaning"], GLOSSARY["en"]),
        ("h2", "Annex C — Known limitations observed while preparing this handbook", "annex-c"),
        ("ul", LIMITS["en"]),
        ("h2", "Annex D — How this handbook was produced", "annex-d"),
        ("p", "Workflows, buttons, menus, groups and controls were extracted from the module source code (repository youneskh/LSS, branch master) and from a database where the 22 LS modules were installed with demonstration data on Odoo 19.0 Community. State lists come from that database (file data/states_from_db.txt). Screenshots were captured from that running instance. The book is generated by docs/sop_handbook/build.py; regenerate it after module changes so that the procedures stay aligned with the software."),
    ]},
    "fr": {"title": "Annexes", "blocks": [
        ("h2", "Annexe A — Registre des SOP", "annex-a"),
        ("p", "Registre des SOP de ce manuel, pour piloter leur rédaction. Le reprendre dans votre système documentaire et compléter propriétaires, échéances et statuts."),
        _register("fr"),
        ("pagebreak",),
        ("h2", "Annexe B — Glossaire", "annex-b"),
        ("table", ["Terme", "Signification"], GLOSSARY["fr"]),
        ("h2", "Annexe C — Limites constatées lors de la préparation du manuel", "annex-c"),
        ("ul", LIMITS["fr"]),
        ("h2", "Annexe D — Comment ce manuel a été produit", "annex-d"),
        ("p", "Les workflows, boutons, menus, groupes et contrôles ont été relevés dans le code source des modules (dépôt youneskh/LSS, branche master) et dans une base où les 22 modules LS ont été installés avec données de démonstration sur Odoo 19.0 Community. Les listes d'états proviennent de cette base (fichier data/states_from_db.txt). Les captures d'écran ont été prises sur cette instance en fonctionnement. Le manuel est généré par docs/sop_handbook/build.py ; le régénérer après toute modification des modules pour que les procédures restent alignées sur le logiciel."),
    ]},
}

ITEMS = [ANNEXES]
