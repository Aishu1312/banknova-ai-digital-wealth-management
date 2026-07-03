BankNova AI — NOVA: AI Avatar Wealth Advisor

IDBI Innovate 2026 · Track 01 — Wealth Advisory Conversational AI, Mobile Banking
Team: BankNova AI · Team Lead: Aishwarya Lala

Repo: github.com/Aishu1312/banknova-ai-digital-wealth-management

NOVA is an avatar-based conversational AI wealth advisor concept, built as a working
front-end prototype that simulates the experience inside the IDBI mobile banking app.

Features


🤖 AI avatar advisor — conversational chat grounded in the customer's financial snapshot
🎙️ Voice interaction — mic input (Web Speech API) + spoken replies (speech synthesis)
📊 Spending analysis — category breakdown + weekly trend charts
🎯 Goal-based planning — Goa trip / wedding / retirement goals, with a "new goal" flow and monthly savings suggestions
📈 Risk-profile quiz → investment recommendations — 3-question quiz drives a Conservative / Moderate / Aggressive allocation and SIP/FD/MF suggestions
🔔 Personalized notifications — overspend alerts, idle-balance tips, goal milestones, bill reminders
💼 Portfolio dashboard — net worth, asset allocation, holdings


Tech stack

React 18 + Vite, Tailwind CSS, Recharts for charts,
lucide-react for icons. An optional tiny Express proxy
(/server) keeps your Anthropic API key server-side for the live chat feature.

Quick start

bashnpm install
npm run dev

Open the printed local URL — the app renders as a mobile app frame in the browser.

Without the backend proxy running, the NOVA chat tab still works using built-in
demo responses, so the whole app is clickable out of the box.

Enabling live AI responses (optional)


cd server && npm install
cp .env.example .env and add your own key from
console.anthropic.com
npm start (runs on http://localhost:8787)
In a separate terminal, from the project root: npm run dev


The frontend automatically calls /api/chat on the proxy; if it's unreachable it
quietly falls back to demo responses, so nothing breaks during a live demo.


Never put your Anthropic API key directly in frontend code or commit it to
Git — always go through a backend like the one in /server.



Project structure

├── src/
│   ├── App.jsx        # the whole NOVA app (all 5 tabs)
│   ├── main.jsx        # React entry point
│   └── index.css       # Tailwind entry
├── server/
│   ├── index.js         # optional Express proxy for the Anthropic API
│   └── .env.example
├── index.html
├── package.json
└── tailwind.config.js

Building for production

bashnpm run build
npm run preview   # preview the production build locally

Deploy the dist/ folder to any static host (Vercel, Netlify, GitHub Pages).
If you want live AI chat in production too, deploy /server separately (e.g.
Render, Railway, Fly.io) and set VITE_API_BASE to its public URL before building.

Submission links


GitHub repo: https://github.com/Aishu1312/banknova-ai-digital-wealth-management
Demo video: add link here
Final product / deployed link: add link here



Built for IDBI Innovate 2026 as a prototype accompanying the BankNova AI submission deck.
