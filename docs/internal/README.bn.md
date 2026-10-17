# DagShield: দ্রুত শুরু (বাংলায়)

এই ফাইলটা শুধু দলের জন্য। জমার README হলো মূল `README.md` (ইংরেজিতে)।

## প্রথমবার চালানো

1. `python scripts/gen_demo_key.py` চালাও। এটা `.env` ফাইল বানায়, যেখানে demo signing key আর ডাটাবেসের পাসওয়ার্ড থাকে। এই ফাইল **কখনো Git-এ দেবে না**।
2. Docker থাকলে: `docker compose up --build`, তারপর browser-এ `http://localhost:8080` খোলো।
3. Docker ছাড়া: মূল README-র "Local development" অংশ দেখো। backend ও frontend আলাদা terminal-এ চালাতে হবে।

## কাজের আগে মাথায় রাখবে

- সব data কৃত্রিম। আসল নাম, NID, ফোন নম্বর বা আসল জমির রেকর্ড কোথাও যাবে না।
- কোনো সরকারি portal থেকে scrape বা bulk download করা যাবে না, আর কোনো live system-এ security test করা যাবে না।
- alert-এর ভাষায় "fraud confirmed" লেখা যাবে না। লিখবে "potential conflict", "not found in supplied dataset", "human review needed"।
- commit-এর history আসল রাখবে। একটা commit-এ squash করা যাবে না।
- প্রতিটা AI tool-এর নাম README-তে লিখতে হবে (`docs/ai-tool-disclosure.md` সত্য তথ্য দিয়ে ঠিক করো)।
- দুজনেই প্রতিটা অংশ ব্যাখ্যা করতে পারতে হবে। `docs/internal/qa-prep.md` পড়ে নাও।

## জমার আগে

`docs/internal/submission-checklist.md` ধরে ধরে মিলিয়ে নাও। শেষ তারিখ **১৬ অক্টোবর ২০২৬**। কয়েক ঘণ্টা হাতে রেখে জমা দাও।

## প্রজেক্টে কী আছে

পুরো রিপোর্ট (বাংলায়): `docs/project-report-bn.md`। লাইভ সার্ভারে বসানোর ধাপ: `docs/deploy-cpanel-bn.md`।
