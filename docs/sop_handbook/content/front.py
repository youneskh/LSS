# -*- coding: utf-8 -*-
"""Front matter: about the handbook, anatomy of a SOP sheet, foundations."""

ABOUT = {
    "kind": "chapter", "id": "about",
    "en": {"title": "About this handbook", "blocks": [
        ("p", "This handbook gathers the Standard Operating Procedures (SOPs) that the Life Sciences Suite can support. "
              "Each SOP rests on a workflow, a control or a record that really exists in the modules. The workflows, "
              "buttons, menus, roles and controls quoted in this book were read from the module source code and from a "
              "database in which the 22 LS modules were installed on Odoo 19.0 Community Edition."),
        ("box", "warn", "What this handbook is — and is not", [
            "It is a **working basis** for your quality assurance: every sheet has blank fields (version, effective date, approval) to be completed under your own document control.",
            "The SOP codes (SOP-QA-001, etc.) are a **proposed numbering**, to be adapted to your document system.",
            "The **regulatory content** of each SOP (criteria, time limits, acceptance levels, local requirements) remains the responsibility of your QA and regulatory functions. The software helps to apply a procedure; it does not replace it and does not make an organisation compliant.",
            "References to regulations and standards are given at chapter or article level. Check the version in force before approval.",
        ]),
        ("h3", "How the book is organised"),
        ("ul", [
            "**Foundations** — GMP principles, document hierarchy, the quality cycle, how the modules hand over to each other, data integrity (ALCOA+), segregation of duties, and how to write an SOP in ls_qms.",
            "**Part I — Quality management system**: documents, training, deviations and CAPA, change control, complaints, audits, risk, suppliers.",
            "**Part II — Data integrity and compliance**: audit trail, electronic signatures, validation, calibration, environmental monitoring, recalls.",
            "**Part III — Industry modules**: pharmaceutical, cosmetics, medical devices, medical plastics, laboratory.",
            "**Part IV — Regulatory affairs**: import-export (phase 1).",
            "**Part V — Procedures supported by OCA modules**.",
            "**Part VI — Procedures needed but not covered by the suite**, with guidance on what they must contain.",
            "**Annexes** — SOP register, glossary, known limitations observed while preparing this book.",
        ]),
        ("h3", "Screenshots, diagrams and demonstrations"),
        ("p", "Screenshots are captures of the running software (Odoo 19.0 Community, LS modules, demonstration data). "
              "The interface is in English: the modules ship no French translation, so the French handbook quotes the "
              "English button labels and gives their meaning. Lifecycle diagrams are drawn from the states actually "
              "defined by each module; explanatory diagrams (pyramids, V-model, charts) illustrate a concept and use "
              "illustrative values, which are labelled as such. Each SOP ends with a worked demonstration describing a "
              "realistic case step by step; the people and values in these demonstrations are fictitious."),
        ("h3", "Anatomy of a SOP sheet"),
        ("table", ["Section", "Content"], [
            ["Header", "Code, title, module, menu, suggested owner, related SOPs; blank version, effective date and approval fields."],
            ["1 Objective · 2 Scope", "Why the procedure exists and what it covers."],
            ["3 Responsibilities", "Roles named after the security groups of the module, so that access rights and the SOP match."],
            ["4 Definitions", "Terms used in the SOP."],
            ["5 Workflow in the software", "Lifecycle diagram generated from the module states, and explanatory diagrams."],
            ["6 Procedure", "Numbered steps. Buttons are shown as [[Button]]; menus as {{Menu ▸ Sub-menu}}."],
            ["7 Controls enforced by the software", "Rules the system refuses to break (it blocks the action and shows a message). The SOP does not need to police them, but users must know them."],
            ["8 Good practices · 9 Pitfalls", "Experience-based advice and frequent errors."],
            ["10 Records · 11 Indicators", "Evidence produced and suggested KPIs."],
            ["12 References · 13 Demonstration", "Regulatory basis and a worked example."],
        ], "anatomy"),
    ]},
    "fr": {"title": "À propos de ce manuel", "blocks": [
        ("p", "Ce manuel rassemble les procédures opératoires normalisées (SOP) que la Life Sciences Suite peut outiller. "
              "Chaque SOP repose sur un workflow, un contrôle ou un enregistrement qui existe réellement dans les modules. "
              "Les workflows, boutons, menus, rôles et contrôles cités ont été relevés dans le code source des modules et "
              "dans une base où les 22 modules LS ont été installés sur Odoo 19.0 Community Edition."),
        ("box", "warn", "Ce que ce manuel est — et n'est pas", [
            "C'est une **base de travail** pour votre assurance qualité : chaque fiche comporte des champs vides (version, date d'application, approbation) à compléter dans votre propre maîtrise documentaire.",
            "Les codes (SOP-QA-001, etc.) sont une **proposition de numérotation**, à adapter à votre système documentaire.",
            "Le **contenu réglementaire** de chaque SOP (critères, délais, niveaux d'acceptation, exigences locales) reste de la responsabilité de votre assurance qualité et de vos affaires réglementaires. Le logiciel aide à appliquer la procédure ; il ne la remplace pas et ne rend pas une organisation conforme.",
            "Les références réglementaires et normatives sont données au niveau du chapitre ou de l'article. Vérifiez la version en vigueur avant approbation.",
        ]),
        ("h3", "Organisation du manuel"),
        ("ul", [
            "**Fondamentaux** — principes BPF, hiérarchie documentaire, cycle qualité, passages de relais entre modules, intégrité des données (ALCOA+), séparation des tâches, rédaction d'une SOP dans ls_qms.",
            "**Partie I — Système de management de la qualité** : documents, formation, déviations et CAPA, maîtrise des changements, réclamations, audits, risques, fournisseurs.",
            "**Partie II — Intégrité des données et conformité** : piste d'audit, signatures électroniques, validation, étalonnage, surveillance de l'environnement, rappels.",
            "**Partie III — Modules métier** : pharmaceutique, cosmétique, dispositifs médicaux, plastiques médicaux, laboratoire.",
            "**Partie IV — Affaires réglementaires** : import-export (phase 1).",
            "**Partie V — Procédures apportées par les modules OCA**.",
            "**Partie VI — Procédures nécessaires mais non couvertes par la suite**, avec ce qu'elles doivent contenir.",
            "**Annexes** — registre des SOP, glossaire, limites constatées lors de la préparation du manuel.",
        ]),
        ("h3", "Captures d'écran, schémas et démonstrations"),
        ("p", "Les captures d'écran proviennent du logiciel en fonctionnement (Odoo 19.0 Community, modules LS, données de "
              "démonstration). L'interface est en anglais : les modules ne livrent pas de traduction française ; le manuel "
              "français cite donc les libellés anglais des boutons et en donne le sens. Les diagrammes de cycle de vie sont "
              "générés à partir des états réellement définis par chaque module ; les schémas explicatifs (pyramides, cycle en V, "
              "graphiques) illustrent un concept avec des valeurs illustratives, signalées comme telles. Chaque SOP se termine "
              "par une démonstration pas à pas sur un cas réaliste ; les personnes et valeurs citées sont fictives."),
        ("h3", "Anatomie d'une fiche SOP"),
        ("table", ["Rubrique", "Contenu"], [
            ["En-tête", "Code, titre, module, menu, propriétaire suggéré, SOP liées ; champs vides pour la version, la date d'application et l'approbation."],
            ["1 Objet · 2 Domaine", "Raison d'être de la procédure et périmètre."],
            ["3 Responsabilités", "Rôles nommés d'après les groupes de sécurité du module, pour que droits d'accès et SOP concordent."],
            ["4 Définitions", "Termes utilisés dans la SOP."],
            ["5 Déroulement dans le logiciel", "Diagramme de cycle de vie généré à partir des états du module et schémas explicatifs."],
            ["6 Mode opératoire", "Étapes numérotées. Les boutons sont notés [[Bouton]] ; les menus {{Menu ▸ Sous-menu}}."],
            ["7 Contrôles imposés par le logiciel", "Règles que le système refuse d'enfreindre (il bloque l'action et affiche un message). La SOP n'a pas à les surveiller, mais les utilisateurs doivent les connaître."],
            ["8 Bonnes pratiques · 9 Erreurs à éviter", "Conseils issus de l'expérience et erreurs fréquentes."],
            ["10 Enregistrements · 11 Indicateurs", "Preuves produites et indicateurs suggérés."],
            ["12 Références · 13 Démonstration", "Base réglementaire et exemple commenté."],
        ], "anatomy"),
    ]},
}

FOUNDATIONS = {
    "kind": "chapter", "id": "foundations",
    "en": {"title": "Foundations", "blocks": [
        ("h2", "Why written procedures", "found-why"),
        ("p", "Good Manufacturing Practice rests on a simple chain: **say what you do, do what you say, prove it**. "
              "A procedure says what must be done, by whom and when; the people trained on it do it; the records prove "
              "that it was done, and the quality system checks that the result is right. The suite supports each link: "
              "ls_qms and ls_document_management hold the procedures, ls_training proves the competence, each module "
              "keeps the records, and the audit, CAPA and risk modules close the loop."),
        ("schematic", "pyramid", "Document hierarchy and where each level lives in the suite."),
        ("h2", "The quality cycle", "found-pdca"),
        ("p", "ISO 9001, ISO 13485 and ICH Q10 describe a quality system as a continuous improvement cycle. The modules "
              "map onto the Plan–Do–Check–Act cycle as shown below. The cycle only works if the outputs of one stage "
              "reach the next one: an audit finding that never becomes a CAPA, or a CAPA whose action is never managed "
              "as a change, breaks the loop."),
        ("schematic", "pdca", "Plan–Do–Check–Act cycle and the modules that support each stage."),
        ("h2", "The suite at a glance", "found-map"),
        ("schematic", "suite_map", "The 22 Life Sciences Suite modules grouped by domain."),
        ("p", "Each module can be installed on its own. The price of that independence is important for the procedures: "
              "**the modules do not create records in each other**. When a deviation needs a CAPA, the deviation reaches "
              "the state *CAPA Required* and records a CAPA reference, but the CAPA itself is opened by a person in "
              "ls_capa. The SOPs of this book therefore specify who opens the downstream record, within which time, and "
              "how the reference is written back."),
        ("schematic", "handoffs", "Hand-offs between quality events, as implemented: by state and reference field, not by automatic link."),
        ("h2", "Data integrity — ALCOA+", "found-alcoa"),
        ("p", "Regulators expect GxP data to be Attributable, Legible, Contemporaneous, Original and Accurate, and also "
              "Complete, Consistent, Enduring and Available. The suite contributes technical controls — immutable "
              "records after approval, append-only logs, hash chains, mandatory reasons for change — but data "
              "integrity is first a behaviour: record at the time of the activity, never share an account, never "
              "record for someone else, and correct by a traced amendment rather than by deletion."),
        ("schematic", "alcoa", "ALCOA+ principles."),
        ("h2", "Segregation of duties (four eyes)", "found-sod"),
        ("p", "Most lifecycles in the suite separate the person who prepares or performs from the person who reviews "
              "and the person who approves. Where the rule is coded, the software refuses the forbidden combination "
              "and says why. Access rights must be designed so that every critical workflow has at least two eligible "
              "people, including during holidays."),
        ("schematic", "four_eyes", "Segregation of duties enforced by the software."),
        ("h2", "Roles and access rights", "found-roles"),
        ("p", "Each module defines its own security groups (typically Viewer, User or Operator, Reviewer or Approver, "
              "Manager). The responsibilities tables of the SOPs use these group names so that the procedure and the "
              "access matrix say the same thing. Grant the least privilege needed, review the grants periodically "
              "(see SOP-IT-001), and never give a production account a manager role \"for convenience\"."),
        ("h2", "Writing a SOP in ls_qms", "found-write"),
        ("p", "The *Standard Operating Procedure* model of ls_qms has the sections Purpose, Scope, Definitions and "
              "Abbreviations, Responsibilities, Procedure and Reference Documents. Purpose, scope and procedure are "
              "mandatory before review. The sheets of this handbook follow the same structure: copy each section into "
              "the corresponding field, adapt it, then submit it through the approval workflow described in SOP-QA-001."),
        ("box", "good", "Rules of good writing", [
            "One procedure, one process. Split when two teams or two triggers are involved.",
            "Write imperative, numbered steps; one action per step; name the role, not the person.",
            "State the time limits and the acceptance criteria as numbers, not as \"promptly\" or \"as appropriate\".",
            "Quote the exact button and menu of the software, so that training and audit use the same words.",
            "Say what to do when something goes wrong (the exception path), not only the nominal path.",
            "Keep the \"why\" in the objective and the references; keep the steps short.",
        ]),
    ]},
    "fr": {"title": "Fondamentaux", "blocks": [
        ("h2", "Pourquoi des procédures écrites", "found-why"),
        ("p", "Les bonnes pratiques de fabrication reposent sur une chaîne simple : **écrire ce que l'on fait, faire ce "
              "que l'on a écrit, le prouver**. La procédure dit quoi faire, qui le fait et quand ; les personnes formées "
              "l'appliquent ; les enregistrements prouvent qu'elle a été appliquée, et le système qualité vérifie que le "
              "résultat est bon. La suite outille chaque maillon : ls_qms et ls_document_management portent les "
              "procédures, ls_training prouve la compétence, chaque module tient ses enregistrements, et les modules "
              "d'audit, de CAPA et de risques bouclent la boucle."),
        ("schematic", "pyramid", "Hiérarchie documentaire et module qui porte chaque niveau."),
        ("h2", "Le cycle qualité", "found-pdca"),
        ("p", "L'ISO 9001, l'ISO 13485 et l'ICH Q10 décrivent le système qualité comme un cycle d'amélioration continue. "
              "Les modules se placent sur le cycle Planifier–Réaliser–Vérifier–Agir comme ci-dessous. Le cycle ne "
              "fonctionne que si les sorties d'une étape atteignent la suivante : un constat d'audit qui ne devient jamais "
              "une CAPA, ou une action CAPA jamais gérée comme un changement, rompt la boucle."),
        ("schematic", "pdca", "Cycle PDCA et modules qui soutiennent chaque étape."),
        ("h2", "La suite en un coup d'œil", "found-map"),
        ("schematic", "suite_map", "Les 22 modules de la Life Sciences Suite regroupés par domaine."),
        ("p", "Chaque module peut être installé seul. Cette indépendance a une conséquence importante pour les procédures : "
              "**les modules ne créent pas d'enregistrements les uns dans les autres**. Quand une déviation nécessite une "
              "CAPA, la déviation passe à l'état *CAPA Required* et porte une référence CAPA, mais la CAPA elle-même est "
              "ouverte par une personne dans ls_capa. Les SOP de ce manuel précisent donc qui ouvre l'enregistrement aval, "
              "dans quel délai, et comment la référence est reportée."),
        ("schematic", "handoffs", "Passages de relais entre événements qualité, tels qu'implémentés : par état et champ de référence, sans lien automatique."),
        ("h2", "Intégrité des données — ALCOA+", "found-alcoa"),
        ("p", "Les autorités attendent des données GxP qu'elles soient attribuables, lisibles, contemporaines, originales et "
              "exactes, mais aussi complètes, cohérentes, durables et disponibles. La suite apporte des contrôles techniques "
              "— enregistrements figés après approbation, journaux en ajout seul, chaînes d'empreintes, motif obligatoire des "
              "modifications — mais l'intégrité des données est d'abord un comportement : enregistrer au moment de l'activité, "
              "ne jamais partager un compte, ne jamais enregistrer pour autrui, corriger par un amendement tracé et non par "
              "suppression."),
        ("schematic", "alcoa", "Principes ALCOA+."),
        ("h2", "Séparation des tâches (quatre yeux)", "found-sod"),
        ("p", "La plupart des cycles de vie de la suite séparent la personne qui prépare ou exécute, celle qui vérifie et "
              "celle qui approuve. Lorsque la règle est codée, le logiciel refuse la combinaison interdite et explique "
              "pourquoi. Les droits d'accès doivent être conçus pour que chaque workflow critique compte au moins deux "
              "personnes habilitées, y compris pendant les congés."),
        ("schematic", "four_eyes", "Séparation des tâches imposée par le logiciel."),
        ("h2", "Rôles et droits d'accès", "found-roles"),
        ("p", "Chaque module définit ses propres groupes de sécurité (en général Viewer, User ou Operator, Reviewer ou "
              "Approver, Manager). Les tableaux de responsabilités des SOP reprennent ces noms de groupes pour que la "
              "procédure et la matrice d'accès disent la même chose. Accordez le moindre privilège nécessaire, revoyez les "
              "droits périodiquement (voir SOP-IT-001) et ne donnez jamais un rôle de manager à un compte de production "
              "« par commodité »."),
        ("h2", "Rédiger une SOP dans ls_qms", "found-write"),
        ("p", "Le modèle *Standard Operating Procedure* de ls_qms comporte les rubriques Purpose, Scope, Definitions and "
              "Abbreviations, Responsibilities, Procedure et Reference Documents. Objet, domaine et mode opératoire sont "
              "obligatoires avant la revue. Les fiches de ce manuel suivent la même structure : recopiez chaque rubrique "
              "dans le champ correspondant, adaptez-la, puis soumettez-la au circuit d'approbation décrit dans SOP-QA-001."),
        ("box", "good", "Règles de bonne rédaction", [
            "Une procédure, un processus. Scindez dès que deux équipes ou deux déclencheurs interviennent.",
            "Écrivez des étapes numérotées à l'impératif ; une action par étape ; nommez le rôle, pas la personne.",
            "Chiffrez les délais et les critères d'acceptation, au lieu de « rapidement » ou « si nécessaire ».",
            "Citez le bouton et le menu exacts du logiciel, pour que formation et audit utilisent les mêmes mots.",
            "Dites quoi faire quand quelque chose se passe mal (le chemin d'exception), pas seulement le chemin nominal.",
            "Gardez le « pourquoi » dans l'objet et les références ; gardez les étapes courtes.",
        ]),
    ]},
}

ITEMS = [ABOUT, FOUNDATIONS]
