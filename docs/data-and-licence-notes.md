# Data and licence notes

## Data used

| Item | Source | Licence / status |
| --- | --- | --- |
| `fixtures/scenarios/*.json` | Created by the team for this hackathon | Same licence as the code (see `LICENSE`) |
| Organizer-provided samples | _None used yet. If you receive any, list the file, date and conditions here_ | |
| Public datasets | _None used_ | |

## What the data contains

- Parcel IDs, dag numbers and areas are invented. Identities are tokens (`OWNER-A`, `BUYER-B`).
- No real names, NIDs, phone numbers, addresses, deed numbers or khatian numbers.
- Dates are invented.

## What the project did not do

- No scraping, automated querying or bulk download from any government portal.
- No security or penetration testing against any live government or third-party system.
- No real private land records anywhere in the repository, demo, screenshots or video.

## How this is enforced

- `backend/app/privacy.py` rejects non-token identities, NID-like numbers, phone numbers and emails.
- It runs when fixtures load, in `tests/test_privacy_guard.py`, in CI, and via `python scripts/check_synthetic_data.py`.

## If real or organizer data is ever added

The rules allow it only if fully anonymised and approved by the organizers in writing. Keep the approval
email in `docs/approvals/` and list the file above before adding anything.
