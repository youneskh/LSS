-- VERIFY: run AFTER upgrading the module.
-- Every row must read PRESENT. A row reading ABSENT means the constraint was
-- NOT created: Odoo logged a schema WARNING and continued. Run the pre-flight
-- script to find the data that blocked it.

WITH expected(table_name, constraint_name) AS (
    VALUES
        ('ls_supplier_assessment', 'ls_supplier_assessment_name_company_uniq'),
        ('ls_supplier_assessment_line', 'ls_supplier_assessment_line_criterion_assessment_uniq'),
        ('ls_supplier_assessment_line', 'ls_supplier_assessment_line_score_positive'),
        ('ls_supplier_assessment_line', 'ls_supplier_assessment_line_weight_positive'),
        ('ls_supplier_assessment_template', 'ls_supplier_assessment_template_code_company_uniq'),
        ('ls_supplier_assessment_template_line', 'ls_supplier_assessment_template_line_criterion_template_uniq'),
        ('ls_supplier_assessment_template_line', 'ls_supplier_assessment_template_line_weight_positive'),
        ('ls_supplier_audit', 'ls_supplier_audit_name_company_uniq'),
        ('ls_supplier_audit_finding', 'ls_supplier_audit_finding_name_audit_uniq'),
        ('ls_supplier_category', 'ls_supplier_category_code_company_uniq'),
        ('ls_supplier_criterion', 'ls_supplier_criterion_code_company_uniq'),
        ('ls_supplier_criterion', 'ls_supplier_criterion_weight_positive'),
        ('ls_supplier_material', 'ls_supplier_material_product_qualification_uniq'),
        ('ls_supplier_performance', 'ls_supplier_performance_name_company_uniq'),
        ('ls_supplier_qualification', 'ls_supplier_qualification_name_company_uniq'),
        ('ls_supplier_qualification', 'ls_supplier_qualification_requalification_interval_positive'),
        ('ls_supplier_review', 'ls_supplier_review_name_company_uniq'),
        ('ls_supplier_signature', 'ls_supplier_signature_sequence_company_uniq'),
        ('ls_supplier_standard', 'ls_supplier_standard_code_uniq')
)
SELECT e.table_name,
       e.constraint_name,
       CASE WHEN c.conname IS NULL THEN 'ABSENT  <-- CONTROL MISSING'
            ELSE 'PRESENT' END AS status,
       COALESCE(pg_get_constraintdef(c.oid), '') AS definition
  FROM expected e
  LEFT JOIN pg_constraint c ON c.conname = e.constraint_name
 ORDER BY status DESC, e.table_name, e.constraint_name;


-- Summary: this must report absent = 0.
WITH expected(table_name, constraint_name) AS (
    VALUES
        ('ls_supplier_assessment', 'ls_supplier_assessment_name_company_uniq'),
        ('ls_supplier_assessment_line', 'ls_supplier_assessment_line_criterion_assessment_uniq'),
        ('ls_supplier_assessment_line', 'ls_supplier_assessment_line_score_positive'),
        ('ls_supplier_assessment_line', 'ls_supplier_assessment_line_weight_positive'),
        ('ls_supplier_assessment_template', 'ls_supplier_assessment_template_code_company_uniq'),
        ('ls_supplier_assessment_template_line', 'ls_supplier_assessment_template_line_criterion_template_uniq'),
        ('ls_supplier_assessment_template_line', 'ls_supplier_assessment_template_line_weight_positive'),
        ('ls_supplier_audit', 'ls_supplier_audit_name_company_uniq'),
        ('ls_supplier_audit_finding', 'ls_supplier_audit_finding_name_audit_uniq'),
        ('ls_supplier_category', 'ls_supplier_category_code_company_uniq'),
        ('ls_supplier_criterion', 'ls_supplier_criterion_code_company_uniq'),
        ('ls_supplier_criterion', 'ls_supplier_criterion_weight_positive'),
        ('ls_supplier_material', 'ls_supplier_material_product_qualification_uniq'),
        ('ls_supplier_performance', 'ls_supplier_performance_name_company_uniq'),
        ('ls_supplier_qualification', 'ls_supplier_qualification_name_company_uniq'),
        ('ls_supplier_qualification', 'ls_supplier_qualification_requalification_interval_positive'),
        ('ls_supplier_review', 'ls_supplier_review_name_company_uniq'),
        ('ls_supplier_signature', 'ls_supplier_signature_sequence_company_uniq'),
        ('ls_supplier_standard', 'ls_supplier_standard_code_uniq')
)
SELECT COUNT(*)                                        AS expected,
       COUNT(c.conname)                                AS present,
       COUNT(*) - COUNT(c.conname)                     AS absent
  FROM expected e
  LEFT JOIN pg_constraint c ON c.conname = e.constraint_name;
