# Contributing Guide

Glomble is a Django project, and most features live in their own app directories instead of one big app. If you want to work on the codebase effectively, start by finding the app that owns the feature you want to change, then look at its `views.py`, `models.py`, and `urls.py`.

## Good to Know

- This repository uses separate folders for major features such as `videos`, `profiles`, `comments`, `reports`, `feedback`, and `notifications`. These directories are also used for related things, for example the code that handles private messaging is stored in the profiles directory.
- Frontend files are located within the separate directories, e.g. `videos/templates/videos/detail_video.html`.
- `profiles` and `videos` both currently have a `base.html` file. The README notes that this is accidental, only the one from `videos` should be used.
- The most important backend files are usually `views.py`, `models.py`, and `urls.py`. `Views.py` is for interaction between frontend and backend, `models.py` is for the database structure, and `urls.py` is used for assigning urls to views to access them. Another important backend file is `videos/templatetags/count.py`, this is used for interacting between the frontend and backend conveniently.
- A useful helper for templates and UI logic is `videos/templatetags/count.py`.

## Local Setup

1. Create and activate a virtual environment. (Optional)
   - On Windows:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
2. Install dependencies.
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Make sure the required local secret files exist in the repository root.
   
   | File | What it is for |
   | --- | --- |
   | `secret_key.txt` | Used by Django to ensure the app has a consistent identity across runs. |
   | `email.txt` | Tells the app which mailbox to send password resets and other mail from. |
   | `email_pass.txt` | Gives the app permission to log in to that mailbox. |
   | `testing_storage_access_key.txt` | Lets local runs upload to the test storage bucket. |
   | `testing_storage_secret_key.txt` | Pairs with the test bucket access key so uploads actually work. |
   | `storage_access_key.txt` | Lets production builds talk to the live storage bucket. |
   | `storage_secret_key.txt` | Pairs with the production storage access key for live uploads. |

   If you are only running locally, the testing storage files are the important ones. The production storage files are only needed when `LOCAL = False` in `Glomble/pc_prod.py`. 
   The files aren't verified, so you can usually just make a file saying something like `TestTestTestTestTestTestTestTest` if you don't have the real credentials. The app will still run, but some features like video uploads or emails might not work properly.
   
4. Apply database migrations.
   ```powershell
   python manage.py migrate
   ```
5. Run the development server.
   ```powershell
   python manage.py runserver
   ```
6. Create an admin user if you need to test staff or moderation flows.
   ```powershell
   python manage.py createsuperuser
   ```

## Making a Pull Request

- Run the Django test suite before opening a pull request:
  ```powershell
  python manage.py test
  ```
- Verify the affected pages in the browser.
- Describe what changed in your PR description and why.

## Useful Files

- Main project overview: `README.md`
- Django settings: `Glomble/pc_prod.py`
- URL routing: `Glomble/urls.py`
- Dependency list: `requirements.txt`
