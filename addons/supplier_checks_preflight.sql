-- PRE-FLIGHT: run BEFORE upgrading the module.
-- Any non-zero count is data that will make ADD CONSTRAINT fail.
-- Odoo will then log a WARNING and continue, leaving the constraint
-- ABSENT while the upgrade reports success. Remediate first, under
-- your change control procedure.

-- ls_supplier_assessment_name_company_uniq  (models\ls_supplier_assessment.py:158)
--    UNIQUE(name, company_id)
SELECT 'ls_supplier_assessment_name_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT name, company_id FROM ls_supplier_assessment
         GROUP BY name, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_assessment_line_criterion_assessment_uniq  (models\ls_supplier_assessment.py:539)
--    UNIQUE(assessment_id, criterion_id)
SELECT 'ls_supplier_assessment_line_criterion_assessment_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT assessment_id, criterion_id FROM ls_supplier_assessment_line
         GROUP BY assessment_id, criterion_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_assessment_line_weight_positive  (models\ls_supplier_assessment.py:544)
--    CHECK(weight > 0)
SELECT 'ls_supplier_assessment_line_weight_positive' AS constraint_name, COUNT(*) AS violating_rows
  FROM ls_supplier_assessment_line WHERE NOT (weight > 0);

-- ls_supplier_assessment_line_score_positive  (models\ls_supplier_assessment.py:549)
--    CHECK(score >= 0)
SELECT 'ls_supplier_assessment_line_score_positive' AS constraint_name, COUNT(*) AS violating_rows
  FROM ls_supplier_assessment_line WHERE NOT (score >= 0);

-- ls_supplier_assessment_template_code_company_uniq  (models\ls_supplier_assessment_template.py:76)
--    UNIQUE(code, company_id)
SELECT 'ls_supplier_assessment_template_code_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT code, company_id FROM ls_supplier_assessment_template
         GROUP BY code, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_assessment_template_line_criterion_template_uniq  (models\ls_supplier_assessment_template.py:160)
--    UNIQUE(template_id, criterion_id)
SELECT 'ls_supplier_assessment_template_line_criterion_template_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT template_id, criterion_id FROM ls_supplier_assessment_template_line
         GROUP BY template_id, criterion_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_assessment_template_line_weight_positive  (models\ls_supplier_assessment_template.py:165)
--    CHECK(weight > 0)
SELECT 'ls_supplier_assessment_template_line_weight_positive' AS constraint_name, COUNT(*) AS violating_rows
  FROM ls_supplier_assessment_template_line WHERE NOT (weight > 0);

-- ls_supplier_audit_name_company_uniq  (models\ls_supplier_audit.py:163)
--    UNIQUE(name, company_id)
SELECT 'ls_supplier_audit_name_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT name, company_id FROM ls_supplier_audit
         GROUP BY name, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_audit_finding_name_audit_uniq  (models\ls_supplier_audit.py:551)
--    UNIQUE(audit_id, name)
SELECT 'ls_supplier_audit_finding_name_audit_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT audit_id, name FROM ls_supplier_audit_finding
         GROUP BY audit_id, name HAVING COUNT(*) > 1) dup;

-- ls_supplier_category_code_company_uniq  (models\ls_supplier_category.py:94)
--    UNIQUE(code, company_id)
SELECT 'ls_supplier_category_code_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT code, company_id FROM ls_supplier_category
         GROUP BY code, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_criterion_code_company_uniq  (models\ls_supplier_criterion.py:82)
--    UNIQUE(code, company_id)
SELECT 'ls_supplier_criterion_code_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT code, company_id FROM ls_supplier_criterion
         GROUP BY code, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_criterion_weight_positive  (models\ls_supplier_criterion.py:87)
--    CHECK(default_weight > 0)
SELECT 'ls_supplier_criterion_weight_positive' AS constraint_name, COUNT(*) AS violating_rows
  FROM ls_supplier_criterion WHERE NOT (default_weight > 0);

-- ls_supplier_material_product_qualification_uniq  (models\ls_supplier_material.py:110)
--    UNIQUE(qualification_id, product_id)
SELECT 'ls_supplier_material_product_qualification_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT qualification_id, product_id FROM ls_supplier_material
         GROUP BY qualification_id, product_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_performance_name_company_uniq  (models\ls_supplier_performance.py:161)
--    UNIQUE(name, company_id)
SELECT 'ls_supplier_performance_name_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT name, company_id FROM ls_supplier_performance
         GROUP BY name, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_qualification_name_company_uniq  (models\ls_supplier_qualification.py:275)
--    UNIQUE(name, company_id)
SELECT 'ls_supplier_qualification_name_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT name, company_id FROM ls_supplier_qualification
         GROUP BY name, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_qualification_requalification_interval_positive  (models\ls_supplier_qualification.py:280)
--    CHECK(requalification_interval_months > 0)
SELECT 'ls_supplier_qualification_requalification_interval_positive' AS constraint_name, COUNT(*) AS violating_rows
  FROM ls_supplier_qualification WHERE NOT (requalification_interval_months > 0);

-- ls_supplier_review_name_company_uniq  (models\ls_supplier_review.py:138)
--    UNIQUE(name, company_id)
SELECT 'ls_supplier_review_name_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT name, company_id FROM ls_supplier_review
         GROUP BY name, company_id HAVING COUNT(*) > 1) dup;

-- ls_supplier_signature_sequence_company_uniq  (models\ls_supplier_signature.py:104)
--    UNIQUE(company_id, sequence_number)
SELECT 'ls_supplier_signature_sequence_company_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT company_id, sequence_number FROM ls_supplier_signature
         GROUP BY company_id, sequence_number HAVING COUNT(*) > 1) dup;

-- ls_supplier_standard_code_uniq  (models\ls_supplier_standard.py:45)
--    UNIQUE(code)
SELECT 'ls_supplier_standard_code_uniq' AS constraint_name, COUNT(*) AS violating_groups
  FROM (SELECT code FROM ls_supplier_standard
         GROUP BY code HAVING COUNT(*) > 1) dup;
