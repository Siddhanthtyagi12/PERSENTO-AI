# Fly.io Deployment Guide for Presento

Aapne is project ko Fly.io pe deploy karne ke liye ye directory use kar sakte hain.

### Pre-requisites:
1.  **Flyctl Install karein:** [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) download karein.
2.  **Login karein:** Terminal me command chalayein: `fly auth login`

### Deployment Steps:
1.  Open Terminal/PowerShell.
2.  Command: `cd d:\sidprojects\deploy_fly`
3.  Launch App: `fly launch`
    - (App name choose karein, region choose karein).
    - Database (Postgres) ke liye "No" bol sakte hain kyunki hum Supabase use kar rahe hain.
4.  **Secrets Set karein (IMPORTANT):**
    Supabase ka connection string set karne ke liye ye command chalayein:
    `fly secrets set DB_CONNECTION_STRING="your_supabase_connection_url"`
    `fly secrets set USE_CLOUD="true"`

5.  Deploy: `fly deploy`

### Note:
Ye server sirf **Dashboard**, **Reports**, **User Management**, aur **Browser Attendance** ke liye hai. Laptop camera (Local Monitoring) hamesha aapke laptop (`app.py`) se hi chalega.
