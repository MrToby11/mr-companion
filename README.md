# Mr. Companion

This is a student project built for CIS 270 Analysis and Design by:
Shivani
Zaid Al-Obaidi
Toby
Matthew
Jaspreet

A cloud-based companion robot management system for elderly users. Built for ABC Tech Ltd.


-----


## How It Works

The system is a web application with three user roles — **Client** (elderly user), **Caregiver** (family/friend), and **Admin** (ABC Tech staff). It lets clients pair and manage their companion robot, register emergency contacts, and manage their subscription. If the robot detects an emergency, it notifies caregivers in order of priority. If no one responds, it escalates to emergency services.

The backend is a **FastAPI** Python app that exposes a REST API. The frontend is plain **HTML/CSS** served by the same app.

Put database info here:

### Project Structure

```
mr-companion/
├── main.py                   # App entry point — starts the server, registers all routes
├── requirements.txt          # Python dependencies
├── app/
│   ├── models/               # Python data classes (one file per domain)
│   │   ├── store.py          # Temporarily replaces the database
│   │   ├── user.py           # User, Client, Caregiver, Admin
│   │   ├── device.py         # Device
│   │   ├── subscription.py   # Subscription, Payment
│   │   └── emergency.py      # EmergencyContact, Event, EventType, EventContact, CaregiverClient
│   └── routers/              # API route handlers (one file per domain)
│       ├── users.py          # /api/users/...
│       ├── devices.py        # /api/devices/...
│       ├── subscriptions.py  # /api/subscriptions/...
│       └── emergency.py      # /api/emergency/...
├── templates/
│   ├── user.html             # Client-facing app (served at /)
│   └── admin.html            # Admin portal (served at /admin)
└── static/
    └── css/style.css         # Shared styles
```

A request follows this path: **browser → main.py → router → store → response**. The routers read and write to `store.py` (which will be swapped out for a real database later).


-----


## Installation

### Prerequisites

Make sure you have the following installed before starting:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10 or higher | https://www.python.org/downloads/ |
| Git | Any recent version | https://git-scm.com/downloads |
| pip | Comes with Python | — |

To check if they are already installed, open a terminal and run:

```bash
python --version
git --version
pip --version
```

### Setup Steps

**1. Clone the repository**

This will download all the files to whatever directory you are in so make sure you are in the place you want to save them.

```bash
git clone https://github.com/MrToby11/mr-companion.git
cd mr-companion
```

**2. (Optional) Create a virtual environment**

This keeps the project's dependencies isolated from the rest of your system.

```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You should see `(venv)` appear at the start of your terminal prompt. Run this activation command every time you open a new terminal for this project.

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, Jinja2, and everything else the project needs.

**4. Run the app**

Make sure you are in the mr-companion directory then:

```bash
uvicorn main:app --reload
```

`--reload` makes the server automatically restart whenever you save a file, which is useful during development.

**5. Open in any web browser**

- User app: http://localhost:8000
- Admin portal: http://localhost:8000/admin


-----


## GitHub Workflow for Teammates

The `main` branch is protected — you cannot push directly to it. All changes must go through a **Pull Request** so I (Toby) can review them before they are merged. This is just to make sure your changes don't conflict with someone elses. Follow these steps every time you work on something.

### Step 1 — Make sure your local copy is up to date

Before starting any new work, pull the latest changes from main:

```bash
git checkout main
git pull
```

### Step 2 — Create a branch for your work

A branch is your own isolated copy of the code. You can just put your name for the name.

```bash
git checkout -b your-branch-name
```

### Step 3 — Make your changes and commit them

After editing files, save your work to git:

```bash
git add .
git commit -m "Short description of what you changed"
```

Write commit messages in plain English describing *what* you did, e.g.:
- `"Add users table to database schema"`
- `"Create login page HTML"`
- `"Fix broken link in navbar"`

You can make multiple commits on the same branch as you work — it's good practice to commit often.

Also while we're on the subject put comments in your code please!

### Step 4 — Push your branch to GitHub

```bash
git push -u origin your-branch-name
```

### Step 5 — Open a Pull Request

1. Go to the repository on GitHub
2. You will see a banner saying your branch was recently pushed — click **"Compare & pull request"**
3. Write a short description of what you changed and why
4. Click **"Create pull request"**

I (Toby) will review it, leave comments if anything needs changing, and merge it when it's ready.

### Step 6 — After your PR is merged

Once your changes are in main, update your local copy:

```bash
git checkout main
git pull
```

I will try to check for your pull requests a couple times every day.