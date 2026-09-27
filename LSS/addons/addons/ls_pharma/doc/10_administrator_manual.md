# Administrator Manual

## 10.1 Groups and what they may do

| Group | XML identifier | Implies |
|---|---|---|
| Viewer | `group_ls_pharma_viewer` | — |
| Production Operator | `group_ls_pharma_operator` | Viewer |
| Production Manager | `group_ls_pharma_production_manager` | Operator |
| Quality Assurance | `group_ls_pharma_qa` | Viewer only |
| Regulatory Affairs | `group_ls_pharma_regulatory` | Viewer |
| Manager | `group_ls_pharma_manager` | The others |

**Quality Assurance deliberately does not imply Production Operator.** Do not
add that implication. The independence of the quality unit is expressed in
this role model, and granting a quality officer the operator role would let
one person both execute a record and approve it — which the model guards will
still refuse at the moment of approval, but the role model should not invite
the attempt.

Assigning a user both Production Manager and Quality Assurance is possible
and is sometimes unavoidable in a small organisation. The model guards still
apply per record: that user will be blocked from approving a record they
executed and from releasing a batch they manufactured. Plan the staffing so
that a second person is always available.

## 10.2 Access rights

143 rules across 26 models, generated from an explicit matrix. The rule worth
knowing: **no group carries the delete right on `ls.pharma.batch.release`.**
This agrees with the model, which raises on any deletion attempt including
under `sudo`. Do not grant it.

## 10.3 Record rules

Twenty-two global multi-company rules with the domain
`['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]`.
Records with no company remain visible so that shared reference data is not
hidden.

Two categories carry no rule, by design and documented inside the rules file:
`ls.pharma.stability.condition`, which is shared reference data with no
company field, and the three transient wizards, which the framework already
restricts to their creator.

## 10.4 Company settings

Pharmaceutical ▸ Configuration ▸ Company Settings.

| Setting | Meaning |
|---|---|
| GS1 Company Prefix | Issued to your company by your GS1 Member Organisation. It is the leading part of every key this module builds. |
| SSCC Extension Digit | The first digit of a Serial Shipping Container Code, chosen by the company that builds the code. |
| Serial Length | The default length of a generated serial number. GS1 permits up to twenty characters in the variable-length field. |
| Batch Expiry Alert Days | How far ahead the daily job looks when posting expiry notices on released batches. |

Set the GS1 company prefix before any serialisation work. A key built on a
prefix that is not yours is not yours to use.

## 10.5 Storage conditions

Pharmaceutical ▸ Configuration ▸ Storage Conditions.

Four conditions ship with the module, being the general case of ICH Q1A(R2):
long term at 25 °C / 60 % RH, long term at 30 °C / 65 % RH, intermediate at
30 °C / 65 % RH and accelerated at 40 °C / 75 % RH, each with its tolerance.

Conditions for refrigerated or frozen products, for semi-permeable
containers, or for other climatic zones are **not** shipped, because the
guideline states them together with product-specific qualifications that a
data record cannot carry. Add them here, with the reference of the guidance
you are following in the Source Reference field.

## 10.6 CTD section template

Pharmaceutical ▸ Configuration ▸ CTD Section Template.

108 sections ship, covering the five modules, sections 1.1 to 1.2, 2.1 to
2.7 with the full sub-structure of 2.3, 3.1 to 3.3 with the full
sub-structure of 3.2, 4.1 to 4.3 and 5.1 to 5.4.

The sub-sections of 2.6, 2.7, 4.2 and 5.3 are absent. Add them here if your
submissions need them, taking the headings from ICH M4S and ICH M4E.

Module 1 is region specific: only the two headings given by ICH M4(R4) ship.
Add your authority's structure here.

## 10.7 Scheduled actions

| Action | Frequency |
|---|---|
| Pharmaceutical: flag overdue stability time points | Daily |
| Pharmaceutical: notify batches approaching expiry | Daily |

Both run as the root user and call a model method directly. Both are
harmless on an empty database. If you disable one, nothing else breaks; the
overdue flag and the expiry notice simply stop being produced.

## 10.8 Sequences

| Code | Prefix | Padding |
|---|---|---|
| `ls.pharma.batch` | `BAT/YYYY/` | 5 |
| `ls.pharma.batch_record` | `EBR/YYYY/` | 5 |
| `ls.pharma.batch.release` | `REL/YYYY/` | 5 |
| `ls.pharma.stability_study` | `STB/YYYY/` | 4 |
| `ls.pharma.ctd_dossier` | `CTD/YYYY/` | 4 |

All five are company independent. If your quality system requires a
site-specific prefix, change the prefix rather than the code; the code is
what the models look up.

## 10.9 Data retention and backup

The module stores no attachment of its own; it stores references to documents
held elsewhere. Your retention obligation therefore falls on the database and
on whatever document system holds the referenced documents.

Two record types must never be deleted from the database by an administrative
script: `ls.pharma.batch.release`, which is the evidence that the quality
unit reviewed and approved a batch, and the batch records that a release
points at. The application refuses both; a direct SQL deletion would
succeed, and would destroy the evidence.

## 10.10 Upgrades

All four data files are `noupdate="1"`, so your edits to storage conditions,
template sections, sequences and crons survive a module upgrade.

One warning for any future maintainer: the order of the values covered by the
release integrity digest is fixed by `_integrity_payload`. Changing that
order would invalidate every digest already stored, and every historic
decision would report as unverified. If the payload must ever change, version
it rather than reorder it.

## 10.11 Re-running the checks

```bash
python3 ls_pharma/static_check.py ls_pharma
odoo-bin -d <database> -i ls_pharma --test-enable --stop-after-init
```

Run both after any local modification.
