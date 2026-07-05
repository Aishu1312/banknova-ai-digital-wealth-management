# Deployment Guide

This guide provides instructions on how to deploy the BankNova AI Wealth OS to Streamlit Community Cloud.

## Prerequisites

1. A GitHub account with the repository pushed to it.
2. A Streamlit Community Cloud account (you can sign up at [share.streamlit.io](https://share.streamlit.io/)).

## Deployment Steps

1. **Log in to Streamlit Community Cloud**: Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. **Create a New App**: Click on the "New app" button.
3. **Select Repository**: 
   - Choose the `Aishu1312/banknova-ai-digital-wealth-management` repository (or your fork).
   - Set the branch to `main` (or the branch you are deploying from).
   - Set the **Main file path** to `app.py`.
4. **Deploy**: Click the "Deploy!" button. Streamlit will pull your code, install the dependencies listed in `requirements.txt`, and start the application.

## Troubleshooting

- **Missing Dependencies**: Ensure all necessary packages are listed in `requirements.txt`. The current version specifies `streamlit`, `pandas`, and `plotly`.
- **Runtime Errors**: If the app crashes, check the Streamlit logs in the Community Cloud dashboard. Recent updates have added exception handling for mathematical operations like zero division.
- **State Issues**: The app uses `st.session_state` to manage mutable data (like goals). Ensure any stateful interactions correctly utilize Streamlit's session state API.
