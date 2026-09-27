# Configuration Guide — `ls_medical_device`

Configuration is reserved to the Manager access level.

## 1. Risk classes — Configuration → Risk Classes

Seven classes ship with the module. Each carries the post-market reporting
obligation that the device records inherit.

| Class | Notified body | Periodic report | Interval | Annual PMCF |
|---|---|---|---|---|
| I | No | PMSR (Art. 85) | not fixed | No |
| Is | Yes, sterility aspects | PMSR (Art. 85) | not fixed | No |
| Im | Yes, metrological aspects | PMSR (Art. 85) | not fixed | No |
| Ir | Yes, reuse aspects | PMSR (Art. 85) | not fixed | No |
| IIa | Yes | PSUR (Art. 86) | 24 months | No |
| IIb | Yes | PSUR (Art. 86) | 12 months | No |
| III | Yes | PSUR (Art. 86) | 12 months | Yes |

The intervals follow MDR Article 86(1): class IIa is updated when necessary
and at least every two years; classes IIb and III at least annually. Class I
devices prepare a post-market surveillance report under Article 85, which the
Regulation does not tie to a fixed interval, so the interval is zero and no
due date is derived.

**Before use**, confirm the notified body scope notes on classes Is, Im and Ir
against the applicable provisions. The shipped notes describe the limitation
of notified body involvement but should be validated against the current text.

## 2. Notified bodies — Configuration → Notified Bodies

No notified body data ships with this module. Designations change over time
and are published by the European Commission; asserting one here would risk
stating an out-of-date fact.

Record each body with its identification number, the scope of its designation,
the reference of the public source consulted, and the date of confirmation.
The *Designation Verified On* date exists so that a stale confirmation is
visible rather than assumed.

## 3. Clinical evidence sources — Configuration → Clinical Evidence Sources

Five sources ship, corresponding to the kinds of clinical evidence recognised
in MDR Annex XIV Part A: clinical investigation, scientific literature, data
from an equivalent device, post-market clinical follow-up data, and registry
or real-world data. Adapt them to the practice of the organisation.

## 4. Documentation section templates — Configuration → Documentation Section Templates

These define the section structure seeded into a new technical documentation
record. They are keyed by annex.

**Verification status, stated plainly:** the shipped Annex II section titles
were confirmed against published renderings of the Annex, not against the
Official Journal text. The title of section 6 could not be re-verified at all.
Confirm every title against the Official Journal before relying on this
structure for a submission. The templates are editable for exactly this
reason.

Mark a section `is_mandatory` when its absence should block approval of a
documentation record.

## 5. Risk scales and the risk matrix

The severity and probability scales are five-point qualitative scales defined
in `models/constants.py`. The matrix boundaries propose *acceptable* below a
risk index of 5 and *unacceptable* from 15.

**These are configuration defaults, not regulatory values.** ISO 14971:2019
requires the manufacturer to define its own severity and probability
categories in the risk management plan. The proposed acceptability is
informative; the decision recorded on each risk is the one held in the
residual acceptability field, which a user sets deliberately.

Changing the scales requires a code change to `constants.py`, because they are
selection values. Plan this as part of implementation, not afterwards: changing
a selection value after records exist requires a data migration.

## 6. Number sequences

Nine sequences allocate the references of the record types. They may be
adapted in Settings → Technical → Sequences. Changing a prefix does not affect
references already allocated.

## 7. Scheduled actions

| Action | Frequency | Effect |
|---|---|---|
| Check Post-Market Obligations | daily | Raises a to-do activity on devices whose periodic report is overdue or whose certificate has expired |
| Expire Certificates | daily | Moves certificates past their expiry date to the expired status |

The obligation check creates an activity only when no open activity with the
same summary already exists on the record, so repeated runs do not accumulate
duplicates.
