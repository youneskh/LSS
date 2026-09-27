<#
  Independent audit - runtime campaign (revision 3).
  Run from the project root:   powershell -ExecutionPolicy Bypass -File .\audit_campaign\run_campaign.ps1
  Options:  -SkipCoverage   skip the coverage measurement (saves ~45 min)
            -Cleanup        drop every scratch database created by the audit (t_c_* and t_ls_*) at the end

  Safety: every database used here is a NEW scratch database named t_c_*.
  The production database odooClaude_ls_DB is only READ (list of installed modules).
  No file under addons\ is modified. The probe module is copied into the
  container under /tmp/audit_addons and loaded from there.
#>
param([switch]$SkipCoverage, [switch]$Cleanup)

$ErrorActionPreference = "Continue"
$OutputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$C   = "odoo19Claude_ls"
$DBC = "odoo19Claude_ls-db"
$MAINDB = "odooClaude_ls_DB"
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
function DropDb($db) { docker exec $DBC dropdb -U odoo --if-exists $db *> $null }
function Odoo([string]$db, [string[]]$extra, [string]$logfile) {
    DropDb $db
    & docker exec $C odoo -c /etc/odoo/odoo.conf -d $db @PORTS @extra --stop-after-init *> $logfile
}
function OdooKeep([string]$db, [string[]]$extra, [string]$logfile) {
    & docker exec $C odoo -c /etc/odoo/odoo.conf -d $db @PORTS @extra --stop-after-init *> $logfile
}
function Shell([string]$db, [string]$code, [string]$logfile, [string[]]$extra = @()) {
    $code | & docker exec -i $C odoo shell -c /etc/odoo/odoo.conf -d $db @extra *> $logfile
}

# ---------------------------------------------------------------- 0. checks
Step "0. Checking containers"
docker ps --format "{{.Names}} {{.Status}}" | Tee-Object "$LOG\00_containers.txt"
docker exec $C odoo --version *> "$LOG\00_odoo_version.txt"

# ---------------------------------------------------------------- 1. installed modules (read only)
Step "1. Installed modules of the main database (read only)"
docker exec $DBC psql -U odoo -d $MAINDB -At -c "select name||';'||state||';'||coalesce(latest_version,'') from ir_module_module where state in ('installed','to upgrade','to install','to remove') order by 1" > "$LOG\01_installed_modules_main_db.txt"

# ---------------------------------------------------------------- 2. F-05 delivery modules
Step "2. F-05: install delivery + stock_delivery"
Odoo "t_c_delivery" @("-i", "delivery,stock_delivery") "$LOG\02_f05_delivery_install.log"

# ---------------------------------------------------------------- 3. co-installation
Step "3. Co-installation of all 23 ls_ modules in one database"
Odoo "t_c_all" @("-i", ($MODS -join ",")) "$LOG\03_coinstall_all.log"

# ---------------------------------------------------------------- 4. demo install, upgrade with data, uninstall
$i = 0
foreach ($m in $MODS) {
    $i++
    Step "4. [$i/23] $m : install with demo data, upgrade, uninstall"
    $db = "t_c_demo_$m"
    Odoo $db @("-i", $m, "--with-demo") "$LOG\04_${m}_1_install_demo.log"
    OdooKeep $db @("-u", $m) "$LOG\04_${m}_2_upgrade.log"
    $code = "MOD = '$m'`n" + (Get-Content -Raw "audit_campaign\scripts\uninstall_probe.py")
    Shell $db $code "$LOG\04_${m}_3_uninstall.log"
}

# ---------------------------------------------------------------- 5. probes
Step "5. Runtime probes (stock workflows, permissions, multi-company, quality/stock)"
docker exec -u root $C rm -rf /tmp/audit_addons *> $null
docker cp "audit_campaign\addons" "${C}:/tmp/audit_addons"
docker exec -u root $C chmod -R a+rX /tmp/audit_addons
Odoo "t_c_probe" @($ADDONS, "-i", "ls_audit_probe", "--test-enable", "--test-tags", "/ls_audit_probe", "--log-level=test") "$LOG\05_probes.log"

# ---------------------------------------------------------------- 6. performance + concurrency
Step "6. Performance and concurrency (F-10) on the probe database"
Shell "t_c_probe" (Get-Content -Raw "audit_campaign\scripts\perf_concurrency.py") "$LOG\06_perf_concurrency.log" @($ADDONS)

# ---------------------------------------------------------------- 7. coverage
if (-not $SkipCoverage) {
    Step "7. Coverage measurement"
    docker exec $C python3 -c "import coverage" *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   installing 'coverage' inside the container (temporary, lost on rebuild)"
        docker exec -u root $C pip install --break-system-packages coverage *> "$LOG\07_coverage_install.log"
    }
    $i = 0
    foreach ($m in $MODS) {
        $i++
        Step "7. [$i/23] coverage $m"
        $db = "t_c_cov_$m"
        DropDb $db
        & docker exec $C python3 -m coverage run --data-file=/tmp/cov_$m --source=/mnt/extra-addons/$m --omit="*/tests/*" /usr/bin/odoo -c /etc/odoo/odoo.conf -d $db @PORTS -i $m --test-enable --test-tags "/$m" --stop-after-init *> "$LOG\07_${m}_tests.log"
        & docker exec $C python3 -m coverage report --data-file=/tmp/cov_$m *> "$LOG\07_${m}_coverage.txt"
    }
}

# ---------------------------------------------------------------- 8. cleanup
if ($Cleanup) {
    Step "8. Dropping scratch databases"
    $dbs = docker exec $DBC psql -U odoo -d postgres -At -c "select datname from pg_database where datname like 't\_c\_%' or datname like 't\_ls\_%'"
    foreach ($d in $dbs) { if ($d) { DropDb $d; Write-Host "   dropped $d" } }
}

$elapsed = (Get-Date) - $start
Step ("Finished in {0:hh\:mm\:ss}. Logs are in {1}. Tell Claude the campaign is done." -f $elapsed, $LOG)
