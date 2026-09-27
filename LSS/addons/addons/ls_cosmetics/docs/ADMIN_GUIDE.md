# Administrator Guide

---

## 1. Groups

Four groups, created through the Odoo 19 `res.groups.privilege` model
(which replaced `category_id` on `res.groups`). Assign users under
**Settings → Users**, in the *Cosmetics* privilege.

| Group | Implies | Intended holder |
|---|---|---|
| Cosmetics: Read Only | — | Anyone who needs visibility |
| Cosmetics: Formulator | Read Only | R&D formulators |
| Cosmetics: Safety Assessor | Read Only | The qualified person under Art. 10(2) |
| Cosmetics: Regulatory Manager | Formulator + Safety Assessor | Regulatory affairs |

Membership of *Cosmetics: Safety Assessor* does **not** establish the
Article 10(2) qualification. The qualification is evidenced on each safety
report, and approval is bound to the specific user account named in
section B4 of that report.

### Segregation of duties

Enforced in the ORM, so it survives API access and cannot be clicked around:

| Rule | Implemented in |
|---|---|
| Formulation submitter ≠ approver | `ls.cosmetic.formulation.action_approve` |
| Claim substantiator ≠ approver | `ls.cosmetic.claim.action_approve` |
| CPSR approver = named assessor | `ls.cosmetic.safety_assessment.action_approve` |

---

## 2. Scheduled actions

Three daily crons, all of which **only post notices** — none of them mutates a
regulatory decision.

| Scheduled action | Method | Effect |
|---|---|---|
| Cosmetics: monitor product information file retention | `ls.cosmetic.pif._cron_monitor_retention` | Chatter notice when the ten years elapse |
| Cosmetics: notify safety report reviews due | `ls.cosmetic.safety_assessment._cron_notify_review_due` | Chatter notice when a review date passes |
| Cosmetics: monitor Algerian authorisation deadlines | `ls.cosmetic.dz_authorization._cron_monitor_deadlines` | Chatter notice on the 45-day and 1-month deadlines |

They post to the record chatter rather than sending mail, so the module works
without a configured mail server.

**On `numbercall` / `doall`.** These legacy `ir.cron` repetition fields are
reported as removed from Odoo 18 onwards, but this could not be confirmed from
official Odoo 19 documentation. Writing a field that does not exist makes a
module fail to install, so they are **not** written in the data file. Instead
`post_init_hook` in `hooks.py` inspects `env["ir.cron"]._fields` at install
time and sets them only if the running server still declares them. If it does,
`numbercall` is set to `-1` so the crons repeat indefinitely; the historical
default of `1` would have deactivated them after a single run.

---

## 3. Loading annex data

The `ls.cosmetic.restriction` register ships empty. This is deliberate — see
README §1.

Keep the register under change control:

1. Take entries from the current consolidated text of Regulation (EC)
   No 1223/2009.
2. Record `source_reference` and `consolidation_date` on every entry. Both are
   required fields; the module will not accept an entry of unknown provenance.
3. Use `date_from` / `date_to` where an amendment has a transitional period.
   `_is_applicable_on(date)` filters by that window.
4. Re-check the register whenever an amending regulation is published.

Only *Cosmetics: Regulatory Manager* can write to this register.

---

## 4. Residual risks and their remediation

Three Odoo 19 API facts could not be confirmed from official documentation.
In each case the module is engineered to avoid depending on the unverified
fact, so it installs either way. Once you have confirmed the field name on
your server, each can be tightened with a one-line change.

### 4.1 Record rules carry no groups

**File:** `security/ls_cosmetics_record_rules.xml`

The Many2many from `ir.rule` to `res.groups` is named `groups` up to Odoo 18
and may have been renamed in Odoo 19 alongside the other group fields. All ten
rules are therefore **global** (no group assigned), which scopes records by
company for every user and is the intended behaviour for multi-company
scoping. Segregation of duties does not rely on these rules — it is enforced
by the ACL and the workflow methods.

*To tighten:* once the field name is confirmed, add
`<field name="groups" eval="[(4, ref('group_ls_cosmetics_user'))]"/>`
(or `group_ids`, whichever your server declares) to the relevant rules.

### 4.2 Menus carry no groups

**File:** `views/ls_cosmetics_menus.xml`

Same reasoning for `ir.ui.menu`. Menu visibility currently follows from the
ACL: Odoo hides a menu whose action targets a model the user cannot read, and
hides a parent with no visible child. In practice every menu here targets a
model that all four groups can read, so the menus are visible to all four —
which matches the intent, since the read-only group is meant to see them.

*To tighten:* add `groups="ls_cosmetics.group_ls_cosmetics_..."` to the
`<menuitem>` elements once confirmed.

### 4.3 Inherited product view

**File:** `views/product_template_views.xml`

The module extends `product.template` through exactly two anchors: the button
box (`//div[@name='button_box']`) and `//notebook`. Both have been stable
across Odoo versions. Anchors on individual product fields were deliberately
avoided, because the product type fields were reworked recently and an xpath
that fails to resolve makes the whole module fail to install. The
`product.template` **list** view is not inherited at all, because its external
identifier could not be confirmed for Odoo 19.

The one remaining unverified reference is `product.product_template_form_view`
itself. If installation fails on that identifier, correct it to whatever your
server uses, or remove this single data file from the manifest — nothing else
in the module depends on it.

---

## 5. Backup and retention

Article 11(1) requires the Product Information File to be retained for ten
years after the last batch was placed on the market. The module blocks
deletion of a PIF outside the draft state and blocks archiving before the
retention end date, but **it cannot protect against database-level deletion**.
Your backup and retention policy has to cover that, and should be part of the
validation package.
