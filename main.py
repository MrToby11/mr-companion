# main.py
# Entry point for the Mr. Companion FastAPI application.
# Run with: uvicorn main:app --reload

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import seed_event_types
from app.routers import admin, auth, devices, emergency, miro, subscriptions, users

app = FastAPI(title="Mr. Companion API", version="0.1.0", docs_url="/docs", redoc_url=None)


@app.on_event("startup")
def on_startup():
    seed_event_types()

# Serve everything in /static at the /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 looks for .html files in the /templates directory
templates = Jinja2Templates(directory="templates")

# Register each router under its API prefix
# All API endpoints are grouped under /api/ to keep them separate from page routes
app.include_router(admin.router,         prefix="/api/admin",         tags=["admin"])
app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(users.router,         prefix="/api/users",         tags=["users"])
app.include_router(devices.router,       prefix="/api/devices",       tags=["devices"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(emergency.router,     prefix="/api/emergency",     tags=["emergency"])
app.include_router(miro.router,          prefix="/api/miro",          tags=["miro"])


# Page routes — serve the HTML frontend
# These are not API endpoints, just HTML pages returned to the browser

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")


@app.get("/")
async def user_app(request: Request):
    # Client-facing app: Dashboard, Robot Setup, Subscription, Emergency Contacts, Emergency Alert
    return templates.TemplateResponse(request, "user.html")


@app.get("/admin")
async def admin_app(request: Request):
    # Admin portal: Dashboard, Devices, Reports, Pricing Plans
    return templates.TemplateResponse(request, "admin.html")
