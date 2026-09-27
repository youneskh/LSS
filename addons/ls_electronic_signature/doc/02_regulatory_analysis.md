# Phase 2 — Regulatory Analysis

## 2.1 Verification basis

Every requirement quoted below was verified against a primary source during
preparation of this document:

- 21 CFR Part 11 §11.50, §11.70: eCFR and the printed CFR (govinfo,
  CFR-2020-title21-vol1-sec11-50).
- 21 CFR Part 11 §11.200, §11.300: eCFR and the printed CFR (govinfo,
  CFR-2018-title21-vol1-sec11-200).
- 21 CFR Part 11 §11.100: eCFR, Subpart C.

Quotations are short and given only where the exact wording drives a design
decision.

## 2.2 Applicability screening

Each framework named in the suite specification was screened for relevance to
*this* module. Frameworks are listed as applicable only where a specific clause
bears on electronic signatures.

| Framework | Applicable to this module | Basis |
|---|---|---|
| **FDA 21 CFR Part 11** | **Yes — primary** | Subpart B (§11.50, §11.70) and the whole of Subpart C govern electronic signatures directly. |
| **EU GMP Annex 11** | **Yes** | Annex 11 addresses computerised systems and electronic signatures in the EU GMP context. **This information could not be verified from official documentation** for the purposes of this document: the EudraLex Volume 4 Annex 11 text was not retrieved during preparation. Organisations must map their own Annex 11 requirements before citing this module against it. |
| **ISO 13485:2016** | **Yes — indirect** | The standard requires control of documented information, including approval and re-approval. **This information could not be verified from official documentation**: the ISO text is not publicly available. Clause references in this document are therefore omitted rather than guessed. |
| **ISO 9001:2015** | Yes — indirect | Same reasoning and same limitation as ISO 13485. |
| **ANPP requirements (Algeria)** | **Could not be verified** | No ANPP publication addressing electronic signature technical controls was retrieved during preparation. **This information could not be verified from official documentation.** The module makes no claim regarding ANPP requirements. |
| **WHO GMP** | Not directly | Addresses manufacturing practice; signature technology is not specified at the level this module operates. |
| **ISO 14971:2019** | No | Risk management for medical devices; no signature requirement. |
| **ISO 15378, ISO 22716** | No | No electronic signature clause identified. |
| **EU MDR 2017/745** | No direct requirement | Signature technology is not prescribed. |
| **GS1 standards** | No | Identification and barcoding; unrelated. |

The suite specification's Regulatory Traceability Matrix (§14) marks
`ls_electronic_signature` as supporting GMP, ISO 13485, 21 CFR Part 11 and
EU MDR. This analysis confirms 21 CFR Part 11 as the only framework whose
specific technical requirements could be verified and implemented against a
primary source. The others are retained as indirect, and no clause number is
asserted for any framework whose text was not verified.

## 2.3 Requirement-by-requirement analysis: 21 CFR Part 11

### §11.50 Signature manifestations

The regulation requires a signed electronic record to contain information
clearly indicating the printed name of the signer, the date and time the
signature was executed, and the meaning associated with the signature; and
requires those items to be subject to the same controls as electronic records
and to be included in any human readable form.

**How the module supports implementation.** `ls.signature.log` stores
`signer_name`, `signed_at` and `meaning_name` as **snapshots taken at signing
time**, not as live relations. Renaming a user or a meaning afterwards cannot
rewrite what a past signature said — a test asserts this. The same three items
are reproduced by the `signature_manifestation` QWeb template, which any report
of a signable model includes, and by the standalone signature certificate PDF.
Being columns of the append-only log, they are under exactly the same controls
as the record itself, which is what paragraph (b) demands.

### §11.70 Signature/record linking

The regulation requires signatures to be linked to their records so that they
cannot be excised, copied, or otherwise transferred to falsify a record by
ordinary means.

**How the module supports implementation.** Three mechanisms combine:

1. *Excision* — each entry carries a monotonic per-company sequence number and
   the chain hash of its predecessor. Removing an entry leaves a sequence gap
   and breaks the successor's linkage; both are reported by chain verification.
2. *Copying and transfer* — the digest is computed over a payload that includes
   the model, the record id, the signer's login and id, the meaning code and the
   signing instant, in addition to the record content. A digest taken from one
   signature therefore cannot be valid on another record, for another signer, or
   under another meaning.
3. *Falsification of the record* — the payload includes the signed field values.
   Editing the record changes the recomputed digest, `is_current` becomes false,
   and the signature stops satisfying any policy.

The choice of SHA-256 is an architectural recommendation. Part 11 does not
prescribe an algorithm.

### §11.100 General requirements

Paragraph (a) requires each electronic signature to be unique to one individual
and never reused or reassigned. Paragraph (b) requires the organisation to
verify the individual's identity before sanctioning the signature. Paragraph (c)
requires the organisation to certify to the agency that its electronic
signatures are intended as the legally binding equivalent of handwritten ones.

**How the module supports implementation.** Uniqueness rests on the Odoo login,
which the platform constrains to be unique. The module prevents *reassignment*
by two means: `user_id` on the signature log uses `ondelete="restrict"`, so an
account that has signed cannot be deleted and its login recycled; and the
`signer_login` snapshot preserves the code as it stood even if the account is
later renamed. A test asserts that deletion is refused while archiving is
permitted.

Paragraph (b) is an organisational obligation. Software cannot verify a human
identity. The administrator manual states it as a precondition.

Paragraph (c) is likewise an organisational obligation — a letter to the agency.
The module's contribution is to display a configurable **binding statement** in
the signature dialog which the signer must actively acknowledge before the
signature is accepted, so the record shows the signer was informed. The
statement text is configuration, because its wording must match the
organisation's certification.

### §11.200 Electronic signature components and controls

Paragraph (a)(1) requires at least two distinct identification components. Sub-
paragraph (i) permits, within a single continuous period of controlled system
access, the first signing to use all components and subsequent signings to use
at least one component executable only by the individual. Sub-paragraph (ii)
requires all components for signings outside such a period. Paragraph (a)(2)
requires signatures to be used only by their genuine owners. Paragraph (a)(3)
requires administration such that use by anyone other than the genuine owner
requires collaboration of two or more individuals.

**How the module supports implementation.**

- *(a)(1)* — the dialog requires the identification code and the password. Two
  distinct components.
- *(a)(1)(i)* — `ls.signature.session` tracks a continuous period, keyed by a
  keyed digest of the web session identifier, with a configurable idle timeout
  (default 15 minutes). Where a policy permits it, subsequent signings inside
  that period require only the identification code. **The default of every
  policy is `require_full_credentials = True`**, i.e. the module is stricter
  than the regulation permits unless an organisation deliberately relaxes it and
  documents why. Requiring more than the minimum is always acceptable.
- *(a)(1)(ii)* — when there is no web session at all (a scheduled action, an RPC
  call), no continuous period can be demonstrated and all components are
  required. When the idle timeout lapses, the session is closed by a scheduled
  action and all components are required again.
- *(a)(2)* — the submitted identification code is compared to the login of the
  authenticated session; a mismatch is refused, logged as `identity_mismatch`
  and notified. Independently, `ls.signature.log.create` overwrites the signer
  identity with the calling account, so a crafted RPC cannot attribute a
  signature to someone else. Both are tested.
- *(a)(3)* — this is predominantly organisational. The module's contribution is
  that misuse of a code requires knowledge of a password that no privileged role
  can read, that every attempt is recorded, and that the security unit is
  notified without delay. The module does not implement a two-person
  authentication scheme, and does not claim to satisfy (a)(3) by itself.

### §11.300 Controls for identification codes and passwords

Paragraph (a) requires uniqueness of each combined code and password.
Paragraph (b) requires periodic checking, recall or revision, for example
password aging. Paragraph (c) requires loss management procedures.
Paragraph (d) requires transaction safeguards to prevent unauthorised use and to
detect and report attempts in an immediate and urgent manner to the system
security unit. Paragraph (e) requires initial and periodic testing of devices
such as tokens or cards.

**How the module supports implementation.**

- *(a)* — the platform enforces login uniqueness. Nothing further is required of
  this module.
- *(b)* — **not implemented here.** Password aging is an Odoo platform and
  organisational concern, not a signature concern. The administrator manual
  names it as a precondition. Implementing it in this module would duplicate a
  control that belongs elsewhere.
- *(c)* — **not implemented here.** Loss management is a procedure. The module's
  supporting contribution is that an account can be archived, which stops
  further signing, while its past signatures remain intact and attributable.
- *(d)* — **implemented in full.** Every attempt is written to
  `ls.signature.attempt`. Because a refused attempt raises an exception that
  would roll the transaction back and destroy the evidence, attempts are written
  through an **independent database cursor that is committed before the
  exception is raised**. Attempts indicating possible misuse trigger an
  immediate e-mail to the `group_ls_signature_security` group. Repeated failures
  lock the identification code for a configurable window.
- *(e)* — not applicable. The module uses no tokens or cards.

## 2.4 What the module does not do

Stated plainly so that no reader infers more than is delivered:

1. It does not certify compliance with 21 CFR Part 11 or any other framework.
2. It does not satisfy §11.100(b) or §11.100(c); both are organisational.
3. It does not satisfy §11.300(b), (c) or (e).
4. It does not by itself satisfy §11.200(a)(3).
5. It does not implement §11.10 controls for closed systems, which span the
   whole computerised system and not one module. Several §11.10 items —
   notably (e) audit trails and (k) documentation controls — are the subject of
   sibling modules `ls_audit_trail` and `ls_document_management`.
6. It makes no claim regarding ANPP requirements, because no ANPP publication on
   this subject could be verified.

## Gate

**PASS.** Applicable requirements are identified against verified primary
sources; each is mapped to a specific mechanism; unverifiable frameworks are
declared as such rather than asserted; non-implemented paragraphs are stated
explicitly with the reason. No compliance claim is made.
