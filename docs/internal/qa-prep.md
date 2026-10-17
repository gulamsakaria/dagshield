# Questions the judges are likely to ask

Both members should be able to answer every one of these in their own words. These are drafts, not scripts.

**1. How would `portion_key` work on real deeds?**
It is a synthetic stand-in here. Real deeds describe land by dag, area and boundaries. A production system would derive the key from the deed's described area and boundaries, mapped to the parcel split recorded at mutation. Its quality would be measured by match rate against records a pilot office has already reconciled by hand, before any alert is trusted.

**2. Why not a blockchain?**
A signed, hash-chained append-only log gives the tamper evidence this problem needs, with far less cost and complexity. The registrar already is the trusted writer; what is missing is a way for anyone else to detect a changed copy or an edited log.

**3. What happens when the registrar's own record is wrong?**
DagShield does not decide which record is right. A deed forged at the source and signed will pass the QR check. R1 to R4 are the second line of defence, since a wrong record often conflicts with others (overlapping claim, oversold share, missing mutation). Every alert goes to a human reviewer.

**4. Who holds the signing key?**
In the prototype, a demo key loaded from an environment variable and never committed. In production, the registration authority, in hardware-protected storage, with legal recognition of the signature. We say plainly that this part is outside the MVP.

**5. Does it use AI?**
No. Rules are deterministic, so the same input always gives the same output and every alert is explainable from source records and a versioned rule. AI could only help with things like Bangla name-variant matching, and then as a confidence, not a verdict.

**6. How accurate is it?**
We do not claim accuracy. The Evaluation page reports actual TP, FP and FN counts on small synthetic fixtures. That shows the rules behave as designed, not how they would perform on real records.

**7. What stops it from being used as a fraud verdict?**
Honest wording rules, enforced by tests ("potential conflict", "not found in supplied dataset", "human review needed"), and a human-review status on every alert.

**8. What about joint ownership and cancelled deeds?**
Cancellation is handled (a cancelled event stops counting from its effective date). Joint ownership and unclear timelines are documented simplifications; ambiguous input becomes "Needs review", not a conclusion.

**9. How do you protect the demo?**
See `SECURITY.md`: keys only from the environment, secret scanning, synthetic-data guard, signed deeds, hash-chained log, strict input validation, security headers, rate limit.
