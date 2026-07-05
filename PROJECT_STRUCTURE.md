# Project Structure

This document outlines the directory structure of the BankNova AI Wealth OS repository.

```
banknova-ai-digital-wealth-management/
├── .streamlit/
│   └── config.toml           # Streamlit specific configuration (theme, server settings)
├── app.py                    # Main Streamlit application entry point
├── chat_engine.py            # AI response logic and rule-based chat engine
├── data.py                   # Mock data for portfolios, transactions, and goals
├── requirements.txt          # Python dependencies
├── README.md                 # Project overview and setup instructions
├── CONTRIBUTING.md           # Contribution guidelines
├── CHANGELOG.md              # Project history and release notes
├── SECURITY.md               # Security policy
├── PROJECT_STRUCTURE.md      # This file
├── DEPLOYMENT_GUIDE.md       # Instructions for deploying the app
└── LICENSE                   # MIT License
```

## Key Components

- **`app.py`**: The core of the application. It handles routing, UI rendering, layout, state management, and user interactions.
- **`chat_engine.py`**: Contains the logic for the `NOVA Chat` feature, parsing user input and returning formatted responses based on mock data.
- **`data.py`**: Acts as a mock database, providing structured data representing a user's financial situation. It uses type hints to ensure data consistency.
