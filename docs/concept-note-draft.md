# Concept note draft (at most 3 pages as PDF, per rule book v1.2)

_Draft text to edit. Keep it to 3 pages. The finished PDF is `DagShield-Concept-Note.pdf`. Fill the blanks, then export to PDF._

## 1. Chosen problem
**P3: Fraud and Double-Selling Detection**, Digital Land Records track.

## 2. Why it matters in Bangladesh
Land disputes are among the most common civil cases. Many trace back to forged deeds, conflicting khatians across survey
generations (CS, SA, RS, BS) and records split between the sub-registry office (registration) and the AC Land office
(mutation). A viewer that only displays records does not reveal relationships or arithmetic conflicts between them.
_Add one or two sources you have checked and can cite._

## 3. Our solution: DagShield
DagShield links parcel lineage, ownership entitlements, deed and transfer events and mutation entries in one model.
Deterministic, versioned rules flag **potential** conflicts and prove each flag with evidence record IDs and arithmetic.

| Rule | Finds |
| --- | --- |
| R1 | Same portion transferred to different recipients |
| R2 | Transfer larger than the entitlement available just before it |
| R3 | Registered deed with no linked mutation, or fields that do not align |
| R4 | Uncertain parent-child link, or child areas exceeding the parent |
| R5 (heuristic) | Three or more transfers within 30 days |

A second part, the **deed integrity check**, signs each synthetic deed (SHA-256 and Ed25519) and prints a QR code. The verify
page shows whether a copy matches the signed record and names the changed field. A hash-chained log makes edits to history detectable.

DagShield is a screening aid for human review. It is not a title search or a legal opinion.

## 4. Architecture and stack
React and TypeScript web UI; FastAPI (Python) API; PostgreSQL; rules, signing and audit log as separate, independently tested modules.
_Insert the architecture diagram from the PRD or draw one._ No AI model at run time.

## 5. Key features
Officer portal (login, dashboard, new-deed form with a green / yellow / red check and the reason, plot history, alert list); parcel search with explicit lineage and a timeline; evidence-linked alerts; clean, conflict and ambiguous scenarios; deed QR verification;
evaluation page with actual TP/FP/FN on labeled synthetic fixtures; Bangla and English UI.

### Future plans (not in the demo)
The demo is a hand-entered, synthetic registry with one sub-registrar login. These are planned, not built:
owner login and consent, real SMS and OTP, NID-based identity checks, map and GIS boundary checks, and OCR of scanned deeds.
Each needs written authorisation and a data-sharing agreement before it touches real records.

## 6. Countrywide plan (authorised, phased, human in the loop)
1. **Pilot design** with the relevant land authorities, one upazila. Gate: written authorisation and a data-sharing agreement.
2. **Read-only data link** to registration and mutation records through an authorised API or scheduled export. Gate: security review.
3. **Identity of a portion:** replace the synthetic `portion_key` with a key derived from the deed's described area and boundaries and the mutation split. Gate: measured match rate against records reconciled by hand.
4. **Rules tuned with reviewers** in shadow mode beside the current process. Gate: an agreed false-alarm rate.
5. **Signing and verification:** key custody by the registration authority with hardware-protected storage, plus a legal review. Gate: written legal opinion.
6. **Scale out** upazila by upazila, with offline-capable QR checks and a full Bangla interface.

Cross-cutting: role-based access, audit logging, personal-data protection, reviewer training.
_Open items for mentors, left blank on purpose: realistic integration points, cost and staffing, legal basis for signatures._

## 7. Limits we state openly
Synthetic data cannot prove readiness for real records. A deed forged at the source and signed passes the QR check, so R1 to R4 are the second line of defence.

## 8. Team and mentors
Team stratifyX Global: Gulam Sakaria (Team Leader), Md Abdur Rahim. Faculty mentor: Nushrat Jahan Oyshi (Lecturer, CSE). Industry support mentor: Shafin Ahmed (CSE-TECH).
