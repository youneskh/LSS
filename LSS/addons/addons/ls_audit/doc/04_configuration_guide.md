# 04 — Configuration Guide

Audience: Quality Manager or system administrator with the
**Audit Manager** group.

Configuration lives under **Quality → Configuration**. Work through it in the
order below; each step depends on the one before.

---

## 1. Audit types

**Quality → Configuration → Audit Types**

| Field | Notes |
|---|---|
| Name | Free text |
| Code | Short, unique per company. Enforced by a database constraint |
| External Audit | Tick for supplier and third-party audits; leave clear for internal |
| Default Checklist | Optional. Pre-selects a checklist when an audit of this type is created |
| Sequence | Display order |

Start with two: an internal system audit and a supplier audit. Add more only
when they genuinely drive different behaviour.

---

## 2. Auditable areas — the important one

**Quality → Configuration → Auditable Areas**

Areas are hierarchical and they carry the **owner** that the impartiality
check uses.

| Field | Notes |
|---|---|
| Name / Code | Code is unique per company |
| Parent Area | Builds the hierarchy. Cycles are refused |
| Responsible | **The area owner. A user set here can never join the audit team for this area.** |
| Department | Optional link to `hr.department` |

### 2.1 Choosing granularity

This is the decision that determines whether the module helps or fights you.

- **Too coarse** ("Manufacturing", owned by the Plant Manager) means the Plant
  Manager can never audit anything under it. On a small site this can lock you
  out entirely.
- **Too fine** creates administrative noise.

Aim for the level at which you would actually scope an audit: a line, a
laboratory, a warehouse, a process.

### 2.2 Leaving the owner empty

An area with no owner imposes **no** ownership restriction. This is a
legitimate configuration for a small site, but understand the trade: you have
switched off one of the two impartiality controls for that area. The
team-versus-auditee control still applies. Record the decision in your quality
system.

---

## 3. Auditor qualifications

**Quality → Configuration → Auditors**

Nothing can be scheduled until this is populated.

| Field | Effect |
|---|---|
| User | One qualification per user per company |
| Lead Auditor | **At least one user must have this, or no audit can ever be scheduled** |
| Qualification Date | Required |
| Expiry Date | Optional. Empty means the qualification never lapses |
| Qualified Scope | Areas this auditor may audit. **Empty means every area** |
| Certificate Reference | Free text, e.g. your training record number |

**Status** is computed, not typed:

| Status | Meaning |
|---|---|
| Valid | Expiry is more than 60 days away, or empty |
| Expiring Soon | Expiry is within 60 days |
| Expired | Expiry has passed. **Blocks scheduling** |

A weekly scheduled action reports expiring and expired qualifications. It
recomputes status before filtering, because status depends on today's date.

---

## 4. Finding categories

**Quality → Configuration → Finding Categories**

Five are shipped. They are a **starting point, not a normative
classification** — align them with your own procedure.

| Category | Severity | Default deadline | Root cause | CAPA |
|---|---|---|---|---|
| Critical | critical | Short | Required | Required |
| Major | major | Medium | Required | Required |
| Minor | minor | Longer | Required | Not required |
| Observation | observation | Longest | Not required | Not required |
| Opportunity for Improvement | improvement | Longest | Not required | Not required |

| Field | Effect |
|---|---|
| Response Deadline (days) | Drives the computed response due date, from the issue date |
| Requires Root Cause | The response wizard refuses to submit without one |
| Requires CAPA | The response wizard refuses to submit without a CAPA reference |
| Sequence | **Also sets the sort order of findings.** Lowest sequence first, so keep the most severe categories at the lowest numbers |

These are loaded with `noupdate="1"`: your edits survive module upgrades.

---

## 5. Checklists

**Quality → Configuration → Checklists**

A checklist is a controlled document with a lifecycle.

### 5.1 Creating one

1. Create with a **Code** and **Version** (unique together per company).
2. Add questions. Each has a sequence, text, an optional reference clause, an
   optional guidance note, and a **Mandatory** flag.
3. **Mandatory** questions block audit completion until answered. Optional
   ones do not.
4. Click **Approve**.

### 5.2 What approval does

The checklist becomes **immutable**. Questions cannot be added, changed or
deleted. This is deliberate: an approved checklist is the reviewed and
approved set of questions.

### 5.3 Changing an approved checklist

Click **New Version**. This copies the questions into a fresh draft at
version + 1. Edit and approve it, then set the old version **Obsolete**.

Obsolete checklists cannot be loaded into new audits. Audits that already
loaded them are untouched — question text was copied at load time.

### 5.4 Reference clauses

Free text. **ISO standard text is copyrighted and is not shipped.** Enter your
own references — your SOP numbers, or clause numbers without the clause text.

---

## 6. Sequences

**Settings → Technical → Sequences**, only in Developer Mode.

| Code | Prefix | Used for |
|---|---|---|
| `ls.audit.program` | `APG/%(year)s/` | Programmes |
| `ls.audit.schedule` | `AUD/%(year)s/` | Audits |
| `ls.audit.finding` | `FND/%(year)s/` | Findings |
| `ls.audit.report` | `ARP/%(year)s/` | Reports |

Padding is 4 digits. Change prefixes only before going live; changing them
later produces a reference scheme that is inconsistent across time, which is
awkward to explain to an inspector.

---

## 7. Multi-company

Configuration records carry a **required** company. The shipped finding
categories therefore belong to the company that was active at install time.

**A second company starts with no finding categories.** Create them, and its
own audit types, areas, auditors and checklists. Transactional records are
isolated by global record rules that no group membership can bypass.

---

## 8. Configuration checklist before going live

- [ ] Every user who will touch the module is in exactly one audit group
- [ ] At least one audit type exists
- [ ] The area hierarchy reflects how you actually scope audits
- [ ] Area owners are set, or the decision to leave them empty is recorded
- [ ] At least one auditor is flagged **Lead Auditor**
- [ ] No qualification is already expired
- [ ] Finding category deadlines match your procedure
- [ ] Finding category sequences put the most severe first
- [ ] At least one checklist is approved
- [ ] The three scheduled actions are active
- [ ] A programme exists covering the current period
- [ ] Demo data is **not** present in production
