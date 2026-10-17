# DagShield: cPanel-এ চালু করার ধাপ (dagshield.newslensbd.com)

এই ফোল্ডারে:
- `dagshield_app/` — সার্ভারে আপলোড হয় (backend + তৈরি করা ওয়েব UI + ডেটা + `.env`)।
- `PRIVATE-credentials.txt` — অফিসার পাসওয়ার্ড ও অ্যাডমিন টোকেন। **এটা আপলোড করবেন না।**

FTP অ্যাকাউন্টটা `public_html/dagshield` ফোল্ডারে আটকানো, তাই অ্যাপ সেখানেই গেছে:
`public_html/dagshield/dagshield_app`। ভেতরের `.htaccess` ব্রাউজার থেকে সরাসরি `.env`, ডেটাবেস বা সোর্স
কোড খোলা বন্ধ করে রাখে (`/dagshield_app/.env` খুললে 403 আসার কথা)।

## ১. Python অ্যাপ তৈরি (cPanel লগইন করে)
cPanel → **Setup Python App** → **Create Application**:
- Python version: **3.11 বা তার বেশি** (কম হলে চলবে না)
- Application root: `public_html/dagshield/dagshield_app`
- Application URL: `dagshield.newslensbd.com` (পাথ ফাঁকা)
- Application startup file: `passenger_wsgi.py`
- Application Entry point: `application`

## ২. প্যাকেজ ইনস্টল
একই পেজে "Configuration files" এ `requirements.txt` যোগ করে **Run Pip Install**। তারপর **Restart**।

## ৩. HTTPS
cPanel → **SSL/TLS Status** → `dagshield.newslensbd.com` এর জন্য **Run AutoSSL**।

## ৪. দেখুন
- `https://dagshield.newslensbd.com` — Home
- `https://dagshield.newslensbd.com/check` — জমি যাচাই (সবার জন্য)
- `https://dagshield.newslensbd.com/officer` — অফিসার লগইন (পাসওয়ার্ড `PRIVATE-credentials.txt`-এ)

## সমস্যা হলে
- **500 / Internal Server Error:** অ্যাপ রুটে `stderr.log` দেখুন।
- **`ModuleNotFoundError`:** Run Pip Install আবার চালিয়ে Restart।
- **`cannot import name 'UTC'`:** Python 3.11-এর কম। ধাপ ১-এ বেশি ভার্সন বেছে নিন।
- কোড বা `.env` বদলালে সবসময় **Restart**।
- ডেটাবেস নিজে তৈরি হয় `dagshield_app/data/dagshield.db`-এ। মুছলে ডেমো ডেটা আবার শুরু থেকে হবে।
