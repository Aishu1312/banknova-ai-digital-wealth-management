# NOVA — BankNova AI Wealth OS

<p align="center">
  <b>Your personal wealth intelligence layer.</b><br/>
  Built for <b>IDBI Innovate 2026 · Track 01</b>
</p>

<p align="center">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="Status" src="https://img.shields.io/badge/Status-Live%20Demo-2ea44f?style=for-the-badge" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-informational?style=for-the-badge" />
</p>

---

## Overview

**NOVA** is an AI-powered personal wealth management platform that helps everyday Indians understand their money, plan their goals, and invest with confidence — explained in plain language, in ₹, like a private banker would.

This repository contains the **Streamlit** build of NOVA, designed for fast iteration and one-click deployment to **Streamlit Cloud**.

## ✨ Features

| Module | What it does |
|---|---|
| 🏠 **Home Dashboard** | Live portfolio snapshot — total wealth, YoY growth, savings/investments/emergency fund split |
| 💬 **NOVA Chat** | Conversational AI advisor that answers questions about spending, goals, and investments |
| 💳 **Spend Analysis** | Category-wise spending breakdown with interactive charts and transaction history |
| 📈 **Invest** | Personalized investment recommendations based on a risk-profile quiz (Conservative / Moderate / Aggressive) |
| 🎯 **Goals** | Goal planning with SIP calculator — see exactly what it takes to hit your target |
| 🔔 **Alerts** | Smart, personalized notifications about your financial health |

## 🖥️ Tech Stack

- **Frontend/App:** [Streamlit](https://streamlit.io)
- **Data & Charts:** Pandas, Plotly
- **Language:** Python 3.11

## 🚀 Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## ☁️ Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select this repository, branch `main`, main file path `app.py`.
4. Click **Deploy** — you'll get a live public URL in under a minute.

## 📂 Project Structure

```
├── app.py                # Main Streamlit app — navigation & page rendering
├── data.py                # Mock financial data (portfolio, transactions, goals)
├── chat_engine.py         # NOVA's conversational logic
├── requirements.txt       # Python dependencies
└── .streamlit/config.toml # Theme (dark + gold accent)
```

## 🏆 Hackathon

Built for **IDBI Innovate 2026**, showcasing how AI can make personal wealth management explainable, INR-native, and accessible to every Indian.

---

<p align="center"><i>Made with ❤️ for IDBI Innovate 2026</i></p>
