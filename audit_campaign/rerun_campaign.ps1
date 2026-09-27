<#
  Rerun of the steps that failed in the first campaign because of the audit's own scripts
  (PowerShell BOM on piped code; probe collection).  About 25-35 minutes.
  Run from the project root:   powershell -ExecutionPolicy Bypass -File .\audit_campaign\rerun_campaign.ps1
  Same safety rules: scratch databases only (t_c_*); the production database is not touched.
#>
$ErrorActionPreference = "Continue"
$C   = "odoo19Claude_ls"
$DBC = "odoo19Claude_ls-db"
$LOG = "logs\campaign"
$PORTS = @("--http-port=8099", "--gevent-port=8098")
$ADDONS = "--addons-path=/mnt/extra-addons,/mnt/test-addons,/tmp/audit_addons"
$MODS = @("ls_qms","ls_document_management","ls_audit","ls_audit_trail","ls_calibration","ls_capa",
          "ls_change_control","ls_complaint","ls_cosmetics","ls_deviation","ls_electronic_signature",
          "ls_electronic_signature_test","ls_environmental_monitoring","ls_lab","ls_medical_device",
          "ls_medical_plastics","ls_pharma","ls_recall","ls_risk_management",
          "ls_supplier_qualification","ls_training","ls_validation","ls_import_export")
New-Item -ItemType Directory -Force $LOG | Out-Null
$start = Get-Date
function Step($t) { Write-Host ("[{0:HH:mm:ss}] {1}" -f (Get-Date), $t) -ForegroundColor Cyan }

Step "A. Copying probe module and scripts into the container (/tmp only)"
docker exec -u root $C rm -rf /tmp/audit_addons /tmp/audit_scripts *> $null
docker cp "audit_campaign\addons" "${C}:/tmp/audit_addons"
docker cp "audit_campaign\scripts" "${C}:/tmp/audit_scripts"
docker exec -u root $C chmod -R a+rX /tmp/audit_addons /tmp/audit_scripts

$i = 0
foreach ($m in $MODS) {
    $i++
    Step "B. [$i/23] uninstall $m"
    docker exec -e AUDIT_MOD=$m $C sh -c "odoo shell -c /etc/odoo/odoo.conf -d t_c_demo_$m < /tmp/audit_scripts/uninstall_probe.py" *> "$LOG\04_${m}_3_uninstall.log"
}

Step "C. Retry: upgrade of ls_validation (first attempt hit a concurrent cron update)"
docker exec $C odoo -c /etc/odoo/odoo.conf -d t_c_demo_ls_validation @PORTS -u ls_validation --stop-after-init *> "$LOG\04_ls_validation_2_upgrade_retry.log"

Step "D. Probes (fixed collection)"
docker exec $DBC dropdb -U odoo --if-exists t_c_probe2 *> $null
docker exec $C odoo -c /etc/odoo/odoo.conf -d t_c_probe2 @PORTS $ADDONS -i ls_audit_probe --test-enable --test-tags /ls_audit_probe --log-level=test --stop-after-init *> "$LOG\05_probes_v2.log"

Step "E. Performance and concurrency"
docker exec $C sh -c "odoo shell -c /etc/odoo/odoo.conf -d t_c_probe2 $ADDONS < /tmp/audit_scripts/perf_concurrency.py" *> "$LOG\06_perf_concurrency_v2.log"

$elapsed = (Get-Date) - $start
Step ("Finished in {0:hh\:mm\:ss}. Tell Claude the rerun is done." -f $elapsed)
