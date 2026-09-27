# User Manual

## Who this is for

Anyone who executes or requests electronic signatures: production and
laboratory personnel, supervisors, Quality Assurance.

## 1 What an electronic signature means here

When you sign, you are doing the legal equivalent of signing a paper record by
hand. The system records your printed name, the exact instant, the meaning you
selected, and a cryptographic fingerprint of precisely what you signed. None of
it can be changed afterwards — not by you, not by your manager, not by an
administrator.

Read the binding statement in the dialog. It states what your organisation has
certified to the regulator about its electronic signatures.

## 2 Signing a record

1. Open the record and click **Sign**.
2. **Meaning** — choose what your signature means (Approved by, Reviewed by,
   Performed by, and so on). Only the meanings you are authorised to use are
   offered.
3. **Reason** — required for some meanings, such as Rejected by. Say why. It is
   retained permanently with the signature.
4. Read the binding statement.
5. **Identification Code** — your own login. It is pre-filled. You cannot sign
   with somebody else's code, and attempting to does not simply fail: it is
   recorded and reported to the security unit.
6. **Password** — your own password. Occasionally it is not requested, when you
   have already signed with your password a few minutes earlier in the same
   browser session and the configuration allows it.
7. Tick the acknowledgement and click **Sign**.

## 3 When signing is refused

| Message | Meaning | What to do |
|---|---|---|
| The password is incorrect | Mistyped, or the wrong account | Retype carefully. Repeated failures block you temporarily. |
| The identification code does not match the account that is logged in | You entered someone else's code | Enter your own. If you need to sign as yourself, log in as yourself. |
| Signing is temporarily blocked for this identification code | Too many failures | Wait for the lockout to lapse, or contact the security unit. |
| You are not authorised to sign with the meaning … | Your role does not permit that meaning | Ask the person whose role does. |
| The meaning … requires a reason | The reason box is empty | Write a substantive reason. Spaces are not accepted. |
| The operation … requires N signature(s) … | The record is not yet fully signed | Obtain the missing signatures. |
| A message mentioning a system parameter or verification method | A configuration fault, **not** a wrong password | Report it to IT. Do not keep retrying. |

## 4 The "no longer covers current content" warning

A signature attests to the record **as it stood when you signed**. If the record
is edited afterwards, the signature is marked as superseded and stops counting
toward any requirement.

This is deliberate. It is what stops someone obtaining an approval and then
quietly changing the figures. If you see this warning, the record must be signed
again in its current state.

Editing a field that is not part of the signed content does not have this
effect.

## 5 Requesting a signature from someone else

1. On the record, click **Request Signature**.
2. Choose the meaning, the expected signers, and optionally a deadline and
   instructions.
3. **Send Request.** The signers are notified.

You cannot sign on another person's behalf. A request is an invitation, never a
substitute.

## 6 Answering a request

**Electronic Signatures → Signatures → Signature Requests** opens filtered to
requests awaiting you.

- **Sign** — opens the signing dialog.
- **Decline** — requires a reason, which is recorded permanently and is visible
  to the requester.

A request past its deadline moves to *Expired* automatically. Ask for a new one.

## 7 Reviewing your signatures

**Signatures → My Signatures** lists every signature you have executed. Opening
one shows the manifestation, the record you signed, and the exact content at the
moment of signing — which is what an auditor will read, independently of the
record's present state.

**Print → Signature Certificate** produces a PDF suitable for a dossier.

## 8 Rules worth remembering

1. Never share your password. Every signature made with it is attributable to
   you.
2. Never sign under another person's identification code. It is recorded and
   reported.
3. Never sign for work you did not do or did not check.
4. A signature cannot be withdrawn. To correct one, sign again with the
   appropriate meaning and state why in the reason.
5. If a record changes after you signed, your signature no longer applies.
