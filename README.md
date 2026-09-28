# PocketSmart AI – Final Nan Mudhalvan Source Code

PocketSmart AI is a Flask-based student project that provides three AI-assisted budget planners:

1. Home Interior Budget Planner
2. Party Budget Planner
3. Jewelry Budget Planner with optional outfit image upload

## Included final changes

- Landing page matching the provided PocketSmart reference style
- Features, testimonials and final call-to-action sections
- Register page with username, email, password and confirm password
- Login page with forgot-password placeholder
- SQLite user storage with hashed passwords
- Dashboard with three planner cards
- Recent Activity section
- Recommendation History page and detail page
- Home planner form and recommendation result UI
- Party planner form and recommendation result UI
- Jewelry planner with outfit image preview and recommendation result UI
- Print/Save button for recommendation pages
- Gemini API integration using `google-genai`
- Automatic demo fallback when Gemini key/quota/service is unavailable
- Shopping links generated from recommendation search terms
- `.env` and local database excluded from GitHub through `.gitignore`

## Run in VS Code

### 1. Open the project folder
Open this folder in VS Code.

### 2. Create virtual environment
Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install packages

```powershell
pip install -r requirements.txt
```

### 4. Create `.env`
Copy `.env.example` to `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=YOUR_KEY_HERE
GEMINI_MODEL=gemini-3.5-flash
FLASK_SECRET_KEY=your-secret-key
```

Never upload `.env` or expose the Gemini API key.

### 5. Run

```powershell
python app.py
```

Open:

`http://127.0.0.1:5000`

## Important Gemini note

If the Gemini Free Tier returns HTTP 429 quota/rate-limit errors, PocketSmart automatically uses its built-in demo recommendation data so the student project can still be demonstrated. For live Gemini output, use a working API key and available quota.

## GitHub upload

From the project folder:

```powershell
git init
git add .
git status
git commit -m "Final PocketSmart AI project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/PocketSmart-AI.git
git push -u origin main
```

Before `git commit`, run `git status` and confirm that `.env` is NOT listed.

## Screenshot checklist

Use the provided reference screenshots to capture:

- Landing/Home page
- Testimonials and footer
- Register page
- Login page
- Dashboard
- Recent Activity
- Home Planner input
- Home Planner result
- Party Planner input
- Party Planner result
- Jewelry Planner input with outfit upload
- Jewelry Planner result
- Recommendation History
- VS Code project structure and running terminal
