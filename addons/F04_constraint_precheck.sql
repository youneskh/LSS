-- F-04 pre-upgrade check: rows that would prevent the database constraints
-- (restored in ls_audit, ls_capa, ls_complaint, ls_training) from being created.
-- Run on a COPY of production before upgrading. Every query must return 0 rows;
-- otherwise correct the listed records first (a UNIQUE or CHECK constraint that
-- cannot be created is skipped by Odoo with a warning in the log).

-- ls_audit: ls.audit.area code_company_uniq: UNIQUE(code, company_id)
SELECT code, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_area GROUP BY code, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.auditor user_company_uniq: UNIQUE(user_id, company_id)
SELECT user_id, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_auditor GROUP BY user_id, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.checklist code_version_company_uniq: UNIQUE(code, version, company_id)
SELECT code, version, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_checklist GROUP BY code, version, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.checklist version_positive: CHECK(version > 0)
SELECT id FROM ls_audit_checklist WHERE NOT (version > 0);

-- ls_audit: ls.audit.finding reference_company_uniq: UNIQUE(reference, company_id)
SELECT reference, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_finding GROUP BY reference, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.finding.category code_company_uniq: UNIQUE(code, company_id)
SELECT code, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_finding_category GROUP BY code, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.program reference_company_uniq: UNIQUE(reference, company_id)
SELECT reference, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_program GROUP BY reference, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.report reference_company_uniq: UNIQUE(reference, company_id)
SELECT reference, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_report GROUP BY reference, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.schedule reference_company_uniq: UNIQUE(reference, company_id)
SELECT reference, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_schedule GROUP BY reference, company_id HAVING count(*) > 1;

-- ls_audit: ls.audit.type code_company_uniq: UNIQUE(code, company_id)
SELECT code, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_type GROUP BY code, company_id HAVING count(*) > 1;

-- ls_capa: ls.capa.action name_uniq: UNIQUE(name)
SELECT name, count(*) AS duplicates, array_agg(id) AS ids FROM ls_capa_action GROUP BY name HAVING count(*) > 1;

-- ls_capa: ls.capa.category code_company_uniq: UNIQUE(code, company_id)
SELECT code, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_capa_category GROUP BY code, company_id HAVING count(*) > 1;

-- ls_capa: ls.capa.category default_due_days_positive: CHECK(default_due_days > 0)
SELECT id FROM ls_capa_category WHERE NOT (default_due_days > 0);

-- ls_capa: ls.capa.effectiveness name_uniq: UNIQUE(name)
SELECT name, count(*) AS duplicates, array_agg(id) AS ids FROM ls_capa_effectiveness GROUP BY name HAVING count(*) > 1;

-- ls_capa: ls.capa.issue name_company_uniq: UNIQUE(name, company_id)
SELECT name, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_capa_issue GROUP BY name, company_id HAVING count(*) > 1;

-- ls_capa: ls.capa.root_cause name_uniq: UNIQUE(name)
SELECT name, count(*) AS duplicates, array_agg(id) AS ids FROM ls_capa_root_cause GROUP BY name HAVING count(*) > 1;

-- ls_complaint: ls.complaint name_company_uniq: UNIQUE(name, company_id)
SELECT name, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_complaint GROUP BY name, company_id HAVING count(*) > 1;

-- ls_complaint: ls.complaint quantity_complained_positive: CHECK(quantity_complained >= 0)
SELECT id FROM ls_complaint WHERE NOT (quantity_complained >= 0);

-- ls_complaint: ls.complaint.adverse_event name_company_uniq: UNIQUE(name, company_id)
SELECT name, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_complaint_adverse_event GROUP BY name, company_id HAVING count(*) > 1;

-- ls_complaint: ls.complaint.category code_company_uniq: UNIQUE(code, company_id)
SELECT code, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_complaint_category GROUP BY code, company_id HAVING count(*) > 1;

-- ls_complaint: ls.complaint.investigation name_company_uniq: UNIQUE(name, company_id)
SELECT name, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_complaint_investigation GROUP BY name, company_id HAVING count(*) > 1;

-- ls_training: ls.training.attendance session_employee_uniq: UNIQUE(session_id, employee_id)
SELECT session_id, employee_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_training_attendance GROUP BY session_id, employee_id HAVING count(*) > 1;

-- ls_training: ls.training.certification name_company_uniq: UNIQUE(name, company_id)
SELECT name, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_training_certification GROUP BY name, company_id HAVING count(*) > 1;

-- ls_training: ls.training.competency code_company_uniq: UNIQUE(code, company_id)
SELECT code, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_training_competency GROUP BY code, company_id HAVING count(*) > 1;

-- ls_training: ls.training.competency.assessment employee_competency_date_uniq: UNIQUE(employee_id, competency_id, date_assessment)
SELECT employee_id, competency_id, date_assessment, count(*) AS duplicates, array_agg(id) AS ids FROM ls_training_competency_assessment GROUP BY employee_id, competency_id, date_assessment HAVING count(*) > 1;

-- ls_training: ls.training.course code_company_uniq: UNIQUE(code, company_id)
SELECT code, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_training_course GROUP BY code, company_id HAVING count(*) > 1;

-- ls_training: ls.training.requirement grace_days_positive: CHECK(grace_days >= 0)
SELECT id FROM ls_training_requirement WHERE NOT (grace_days >= 0);

-- ls_training: ls.training.session name_company_uniq: UNIQUE(name, company_id)
SELECT name, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_training_session GROUP BY name, company_id HAVING count(*) > 1;

-- ls_training: ls.training.session capacity_positive: CHECK(capacity >= 0)
SELECT id FROM ls_training_session WHERE NOT (capacity >= 0);
-- ls_audit_trail: ls.audit_trail.rule model_company_unique (F-38): UNIQUE NULLS NOT DISTINCT (model_id, company_id)
-- (requires PostgreSQL 15 or later)
SELECT model_id, company_id, count(*) AS duplicates, array_agg(id) AS ids FROM ls_audit_trail_rule GROUP BY model_id, company_id HAVING count(*) > 1;

-- ls_recall: ls.recall.plan code_company_uniq, widened to UNIQUE(code, version, company_id)
-- so that plan revisions can be created (relaxing a constraint cannot fail on existing data).
