# Three-minute demo script

Round 1 video is capped at **90 seconds** (rule book v1.2). The table below is the 3-minute version: for Round 1 keep only the officer portal blocked-sale clip, the Check Land page and the verify page, about 25 seconds each. The final gives 5 minutes plus 3 minutes of Q&A, so extend the same script.
Before recording: `docker compose up --build`, open the web UI, and press **Reset scenario** on every scenario you will show.

| Time | Click path | Say |
| --- | --- | --- |
| 0:00-0:20 | Dashboard | Why comparing isolated documents misses cross-record conflicts. Point at the synthetic-data banner |
| 0:20-0:45 | Press **Run audit on all scenarios**, open **Clean transfer**, show no alerts and balance 7 | The tool does not cry wolf |
| 0:45-1:20 | Open **Oversold share (R2)**, then its alert | Opening 12, prior transfers 9, available 3, attempted 5, excess 2. Change status to Under Review |
| 1:20-1:50 | Open **Duplicate claim and missing mutation (R1 + R3)** | Two records linked as evidence. A gap is reported as "not found in supplied dataset", never as fraud |
| 1:50-2:20 | **Verify a deed**: Check this copy (match), edit the area, check again (mismatch) | A genuine copy verifies. One edited character fails and the changed field is named |
| 2:20-2:45 | **Evaluation** | Actual test counts on synthetic fixtures. Small and synthetic, so it shows the rules behave as designed |
| 2:45-3:00 | Back to dashboard | Countrywide path: authorised API integration, phased pilot, human review stays |

Optional if time allows: the Bangla toggle on the alert page (the numbers do not change).

## Officer portal walk-through (about 2 minutes)

Sign in at `/officer` with the demo account shown on the login page, then press **Reset demo data** on the dashboard.
On **New registration** the four chips under "Demo scenarios" fill the form for you.

| Step | Chip | Expected result |
| --- | --- | --- |
| 1 | 1. Normal sale (Rahim Uddin to Karim Mia, dag 123) | Green. Ownership moves to Karim Mia |
| 2 | 2. Double sale (Rahim Uddin sells dag 123 again) | Red, rule R1: "This plot was already sold, current owner Karim Mia" |
| 3 | 3. Seller not the owner (unknown person, dag 124) | Red, rule R2: "The seller is not the record owner" |
| 4 | 4. Quick resale (Karim Mia to Nasir Ahmed, same day) | Yellow, rule R5 heuristic: registered but flagged for review |

Then open **Plot history** for dag 123 (timeline with the blocked attempt) and **Alerts** (why each attempt was stopped).
All names are made up.

## Public Check Land page (about 1 minute)

Open `/check` (no login). Pick **নমুনা মৌজা-১**, dag **123**, and type an owner name.

| Name typed | Expected |
| --- | --- |
| The owner on record (before any sale) | Green: "এই নামেই আছে, বিক্রির যোগ্য" |
| Rahim Uddin after the officer registered the sale to Karim Mia | Red: "এই নামে নেই। বর্তমান মালিক: করিম মিয়া", with the earlier sale date |
| Karim Mia right after that sale | Amber: registration and khatian differ, mutation pending |
| A dag that is not in the record (for example 999) | Amber: "এই দাগ রেকর্ডে পাওয়া যায়নি" |

The page shows only the owner, status, mutation status and earlier owners. No alerts, scores or officer names.

## Adding a plot (officer, English or Bangla)

Officer portal, tab **জমির তালিকা** (Plots): enter mouza, dag, owner and area. Names may be typed in English.
The new plot appears in the list and in the public page's mouza dropdown at once.

## Judge demo (the easiest path for a judge)

On the live site press the gold **Judge demo** button (top bar or home page), then **Start the demo**. It signs in as
the demo officer without a password, resets the registry, loads sample data and opens the dashboard. `/judge` lists a
twelve-step tour with the expected result of each step. Switch it off afterwards with `DAGSHIELD_JUDGE_LOGIN=false`.
