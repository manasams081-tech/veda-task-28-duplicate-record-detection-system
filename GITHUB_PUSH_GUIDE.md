# GitHub Push Guide — VEDA Task 28

GitHub username from the supplied profile screenshot: **manasams081-tech**

Recommended repository name:

`veda-task-28-duplicate-record-detection-system`

Recommended description:

`VEDA Technology Task 28 - Python duplicate record detection system with exact and fuzzy matching using Pandas and difflib.`

## 1. Create the repository

Open GitHub's **New repository** page and create a **Public** repository.

Important:
- Repository name: `veda-task-28-duplicate-record-detection-system`
- Public: Yes
- Do **not** add a README
- Do **not** add a .gitignore
- Do **not** add a license

The local project already contains these files.

## 2. Open PowerShell in this project folder

Example:

```powershell
cd "C:\path\to\veda-task-28-duplicate-record-detection-system"
```

Check that `README.md`, `app.py`, `duplicate_detector.py`, and `requirements.txt` are visible:

```powershell
dir
```

## 3. Create and activate the virtual environment

Use Python 3.12 for the most predictable setup:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## 4. Test before Git

Start the app:

```powershell
python app.py
```

Open:

`http://127.0.0.1:8000`

Test with:

`sample_data\customers_demo.csv`

When finished testing, return to PowerShell and press:

`Ctrl + C`

## 5. Initialize Git

Run these commands in this exact order:

```powershell
git init
git add .
git status
git commit -m "Add VEDA Task 28 duplicate record detection system"
git branch -M main
git remote add origin https://github.com/manasams081-tech/veda-task-28-duplicate-record-detection-system.git
git remote -v
git push -u origin main
```

## 6. If Git asks for identity

Run once:

```powershell
git config --global user.name "manasams081-tech"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

Then repeat:

```powershell
git add .
git commit -m "Add VEDA Task 28 duplicate record detection system"
git push -u origin main
```

## 7. Verify the repository

Open:

`https://github.com/manasams081-tech/veda-task-28-duplicate-record-detection-system`

You should see the Python files, `web` folder, `sample_data`, `reports`, README, and requirements file.

## Important

Do not run `git add .venv`.

The included `.gitignore` prevents the virtual environment, Python cache, editor files, and runtime output CSVs from being committed.

If you accidentally initialized Git before, check:

```powershell
git remote -v
```

If `origin` already exists and points to the wrong repository, use:

```powershell
git remote set-url origin https://github.com/manasams081-tech/veda-task-28-duplicate-record-detection-system.git
```

Then:

```powershell
git push -u origin main
```
