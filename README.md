dawn_backend/
├── .env                # secrets (api keys, project ids)
├── .python-version     # created by uv
├── pyproject.toml      # dependencies
├── pyrightconfig.json  # basedpyright settings
├── app/
│   ├── __init__.py
│   ├── main.py         # entry point & fastapi initialization
│   ├── config.py       # appwrite client & env loading
│   ├── auth.py         # signup/login logic & jwt dependency
│   └── routes/
│       ├── __init__.py
│       ├── tasks.py    # feature 1: task priority logic
│       └── grades.py   # feature 3: grade calculator
└── tests/              # (optional) simple test scripts
