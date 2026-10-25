# AI Security Assistant — OpenRouter Free AI Edition

A complete Streamlit dashboard with SQLite synthetic security test data, rule-based detection, and a **real online AI assistant** via OpenRouter free models. No OpenAI billing credits required. The model and free-tier limits are controlled by OpenRouter; availability is not guaranteed.

## Included

- `app.py`: navy sidebar, priority cards, recent alerts, chart, AI chat, alerts, test data, security checker, action history, and tips.
- `database.py`, `demo_data.py`: SQLite storage and synthetic sample login, account, device, and software events.
- `event_detection.py`, `securitychecker.py`: explainable demonstration detection rules.
- `ai_assistant.py`: OpenRouter API integration; passes a bounded read-only text snapshot of test data. No database write permissions or automatic security actions.
- `tests/`: offline automated tests.

## Setup on Windows / VS Code

1. Extract this ZIP to a **new folder**, and open that folder in VS Code.
2. In the VS Code PowerShell terminal run:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Register for an OpenRouter account at https://openrouter.ai and create an API key at https://openrouter.ai/settings/keys . Choose a free model route. No paid credits are required for eligible free-model requests within provider limits; limits and policies can change.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`. In the copied file, replace `paste-your-openrouter-key-here` with your key. **Do not include the key in GitHub, screenshots, or chat.** The real secrets file is ignored by Git.
5. Start the app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

6. Open http://localhost:8501, visit **Test Data** and click **Analyze Stored Events**, then open **Ask Assistant** and ask: *What suspicious activity appears in the sample database?*

## How AI works

The app uses the existing `openai` Python SDK with OpenRouter's compatible base URL `https://openrouter.ai/api/v1` and model `openrouter/free`. OpenRouter chooses an available free model. The app sends a short read-only summary of synthetic events to the online provider. The assistant does **not** access the SQLite file directly, monitor real systems, or take corrective action. Review status does not mean an incident is resolved.

If a free model is busy or rate-limited, the app displays the actual error; try again later. If you receive 401, check your OpenRouter key. If you receive 429, check your free-tier request limits. If you receive a model/provider error, consult https://openrouter.ai/models?q=free and the OpenRouter docs; availability can change.

## Database and safety

The first run creates `security_assistant.db` and seeds synthetic events only when the event table is empty. The **Test Data** page can display/export records and analyze them to generate saved alerts. Existing SQLite demo databases can be migrated with additive tables; **back up your existing database before upgrading**.

Use only synthetic test records with this online free-tier integration. Do not send real business logs, passwords, private customer records, or secrets to the model. Responses may be inaccurate; security advice should be reviewed by a person.

## Offline tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The automated tests do not call OpenRouter. The live API connection requires a valid key and internet access.
