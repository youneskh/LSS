# Installation and Configuration Guide

## 16.1 Prerequisites

| Item | Requirement |
|---|---|
| Odoo | 19.0 Community Edition |
| Modules | `base`, `mail`, `product`, `stock`, `mrp` installed or installable |
| Database | PostgreSQL, as required by your Odoo build |
| Python packages | None beyond what Odoo itself requires |

The module has **never been installed against a live Odoo 19 instance**.
Treat the first installation as a test, on a copy of your database, and
record the outcome as activity IQ-2 of the validation report.

## 16.2 Installation

```bash
# 1. place the module on the addons path
cp -r ls_pharma /path/to/addons/

# 2. restart the Odoo service

# 3. update the module list
odoo-bin -d <database> -u base --stop-after-init

# 4. install
odoo-bin -d <database> -i ls_pharma --stop-after-init
```

Or, through the interface: Apps ▸ Update Apps List ▸ search "Pharmaceutical
Manufacturing" ▸ Install.

To install with the demonstration master data, install the database with demo
data enabled. The demo set is two active ingredients and four excipients; see
deviation D-4 for why it is no larger.

## 16.3 Verifying the installation

Run the checks that correspond to activity IQ-3 and IQ-4:

```bash
odoo-bin -d <database> -i ls_pharma --test-enable --stop-after-init
```

`tests/test_installation.py` asserts that the module is installed, that the
five sequences exist, that the four storage conditions and the 108 template
sections were created, that both scheduled actions exist and run, that both
reports exist, that the root menu exists, that every view combines, and that
every model carries access rules.

Record the full output. If any test fails, do not proceed to configuration;
report the failure.

## 16.4 First configuration

### Step 1 — Assign groups

Settings ▸ Users. Give each user exactly one primary role from Viewer,
Production Operator, Production Manager, Quality Assurance, Regulatory
Affairs and Manager.

Plan for two people per separation: a batch record cannot be approved by the
person who executed it, and a batch cannot be released by the person who
manufactured it. If one person holds both roles, the system will block them
at the moment it matters, which is correct but inconvenient.

### Step 2 — Company settings

Pharmaceutical ▸ Configuration ▸ Company Settings.

Enter your **GS1 company prefix** as issued by your GS1 Member Organisation.
Do not invent one; a key built on a prefix that is not yours is not yours to
use. Set the SSCC extension digit, the default serial length and the expiry
alert window.

### Step 3 — Storage conditions

Pharmaceutical ▸ Configuration ▸ Storage Conditions.

The four general-case conditions of ICH Q1A(R2) are already there. Add
refrigerated, frozen or zone-specific conditions if you need them, recording
the guidance you followed in the Source Reference field.

### Step 4 — CTD template

Pharmaceutical ▸ Configuration ▸ CTD Section Template.

Review the 108 shipped sections. Add your authority's Module 1 structure, and
the sub-sections of 2.6, 2.7, 4.2 and 5.3 if your submissions need them.

### Step 5 — Products

Pharmaceutical ▸ Materials ▸ Pharmaceutical Products.

For each product you manufacture, mark it as pharmaceutical and record its
dosage form, strength, shelf life, storage condition, marketing
authorisation, product code and, importantly, its theoretical yield and yield
limits. Those three come from your master production record under
21 CFR 211.186(b)(6) and are proposed onto every batch of the product.

### Step 6 — Materials

Pharmaceutical ▸ Materials ▸ APIs and Excipients.

Register each active ingredient and excipient, its pharmacopoeial standard,
its monograph reference, its approved manufacturers and its retest period.
Qualify each one. A material of animal origin needs its supplier statement
reference before it can be qualified.

### Step 7 — Sequences, if your quality system requires it

Settings ▸ Technical ▸ Sequences. Change the prefix if you need a
site-specific one. **Do not change the code**; the models look sequences up
by code.

### Step 8 — Scheduled actions

Settings ▸ Technical ▸ Scheduled Actions. Confirm that both pharmaceutical
jobs are active and note their next run time.

## 16.5 Upgrading the module

```bash
odoo-bin -d <database> -u ls_pharma --stop-after-init
```

All four data files are `noupdate="1"`, so your edits to storage conditions,
template sections, sequences and crons are preserved.

## 16.6 Uninstalling

Uninstalling removes the models and, with them, every batch, batch record and
release decision. **A release decision is the evidence that your quality unit
reviewed and approved a batch.** Export or archive that data before
uninstalling, and treat the operation under your change control procedure.

## 16.7 Troubleshooting

| Symptom | Likely cause |
|---|---|
| Installation fails on `security/ls_pharma_security.xml` | `res.groups.privilege` differs in your build. Residual risk RR-1. |
| A report raises on printing | `web.external_layout` differs in your build. Residual risk RR-2. |
| A user sees no Pharmaceutical menu | The user is in no group of this module |
| A user cannot approve a record | They executed it; that is the intended refusal |
| A batch cannot be released | Check the four gate conditions: unapproved records, an unreferenced yield investigation, a missing expiry date, or the user having manufactured the batch |
| A serial number is refused | The product code check digit is wrong, or the value exceeds twenty characters |
