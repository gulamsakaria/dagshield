# AI tool disclosure

The hackathon rules allow AI tools if every tool is listed in the README with a short note on how it was used.
**Edit this file so it matches what the team actually did. Do not submit a version that is not true.**

| Tool | Used for | How it was used | Reviewed by |
| --- | --- | --- | --- |
| Claude (Anthropic) | Explaining the PRD in Bangla; drafting the technology-stack guide; generating the first scaffold of the backend, tests, frontend, Docker files and documents; later (Claude Code) redesigning the web UI, building the officer portal, the public Check Land page and the plot-adding form, and preparing the cPanel hosting package | Prompted by the team; output was run, tested and edited | _both members_ |
| _Other tool, if any_ | | | |

## No AI at run time

The shipped application uses no AI model. Rules are deterministic functions, which is what lets every alert be
reproduced from source records and a versioned rule.

## Team responsibility

Both team members have read and can explain every module, including the rules, the signing code, the audit log
chain and the API. Generated code was not accepted on trust: it is covered by the automated tests in `backend/tests/`.
