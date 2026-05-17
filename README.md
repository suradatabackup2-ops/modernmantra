# Modern Mantra — Django port

A faithful port of the original `modernmantra-v10` static site to Django,
preserving the exact look, feel, and animations. All five public pages
work, all four submission forms (Enquiry, Booking, Review, Registration)
save to a real database, and the old browser-side admin (`admin.html`) is
replaced by Django's built-in admin with filtering, search, bulk actions,
status workflow, and CSV export.

---

## Contents

1. [Quick start (local dev)](#quick-start-local-dev)
2. [Project layout](#project-layout)
3. [What replaced what](#what-replaced-what)
4. [Deployment guides](#deployment-guides)
   - [Railway](#deploy-1-railway-easiest-5-min)
   - [Render](#deploy-2-render)
   - [Fly.io](#deploy-3-flyio)
   - [AWS Lightsail Containers](#deploy-4-aws-lightsail-containers-simplest-aws)
   - [AWS App Runner](#deploy-5-aws-app-runner-auto-scaling)
   - [AWS ECS Fargate](#deploy-6-aws-ecs-fargate-full-control)
5. [Optional upgrades](#optional-upgrades)
6. [Troubleshooting](#troubleshooting)

---

## Quick start (local dev)

You need Python 3.12+ and pip. (Docker is optional — see below.)

```bash
# 1. Get the code, install deps
cd modernmantra
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Create database + apply migrations
python manage.py migrate

# 3. Create an admin user
python manage.py createsuperuser

# 4. Run the dev server
python manage.py runserver
```

Now open:

- Site: <http://localhost:8000/>
- Admin: <http://localhost:8000/admin/>

To run with Docker locally instead:

```bash
cp .env.example .env
# (edit .env — at minimum set DJANGO_SECRET_KEY)
docker compose up --build
docker compose exec web python manage.py createsuperuser
```

---

## Project layout

```
modernmantra/
├── Dockerfile                       # multi-stage, non-root, healthcheck
├── docker-compose.yml               # local dev + optional Postgres
├── requirements.txt
├── manage.py
├── .env.example                     # copy to .env, fill in
│
├── modernmantra/                    # Django project package
│   ├── settings/
│   │   ├── base.py                  # shared settings (env-driven)
│   │   ├── dev.py                   # DEBUG=True, console email
│   │   └── production.py            # DEBUG=False, HSTS, secure cookies
│   ├── urls.py                      # / admin/, /api/, /, robots.txt
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── pages/                       # the 5 public pages
│   │   ├── views.py                 # TemplateView for each page
│   │   ├── urls.py
│   │   └── context_processors.py    # SITE_CONTACT for footer
│   └── bookings/                    # all form submissions
│       ├── models.py                # Enquiry / Booking / Review / Registration
│       ├── forms.py                 # ModelForms with validation
│       ├── admin.py                 # Django admin: filters, search, bulk actions, CSV
│       ├── views.py                 # POST endpoints, email notifications
│       ├── urls.py                  # /api/enquiry/, /api/booking/, etc.
│       └── migrations/0001_initial.py
│
├── templates/
│   ├── base.html                    # shared nav, footer, WhatsApp float, CSRF wiring
│   ├── robots.txt
│   └── pages/
│       ├── home.html  about.html  packages.html  gallery.html  contact.html
│
└── static/                          # source assets — copied as-is from your zip
    ├── css/         main.css  home.css  pages.css
    ├── js/          main.js          # patched: hits Django endpoints with CSRF
    ├── images/      (44 photos)
    └── brochures/   4 PDF brochures
```

After `python manage.py collectstatic`, all files in `static/` are
fingerprinted + gzipped into `staticfiles/` and served directly by
WhiteNoise — no nginx required for sites this size.

---

## What replaced what

| Original                              | Django port                                       |
| ------------------------------------- | ------------------------------------------------- |
| `index.html`, `about.html`, etc.      | `templates/pages/*.html` extending `base.html`    |
| `<form>` → Formspree                  | `<form>` → `/api/enquiry/`, `/api/booking/`, etc. |
| `google-apps-script.gs` + Google Sheet| Django models + SQLite/Postgres (optional Slack/Notion/Airtable mirror — see below) |
| `localStorage` offline cache          | Direct DB writes; cache no longer needed          |
| `admin.html` (custom JS dashboard)    | `/admin/` — Django admin with filters, search, bulk actions, CSV export, change-history |
| Telegram / ntfy push channels         | Email notifications via `NOTIFY_EMAILS` env var (see "Optional upgrades" for SES) |
| Hardcoded testimonials                | Reviews from `/admin/bookings/review/` once approved, falling back to hardcoded list when DB is empty |
| Local PDF brochures in `static/`      | `Package.brochure_pdf` upload field → R2/S3/B2/DO Spaces (set `MEDIA_STORAGE_BACKEND`) |
| —                                     | Newsletter signup (footer form → `NewsletterSubscriber` model with CSV export) |
| —                                     | Scroll-reveal animations, image fade-in, card tilt, back-to-top, smooth scroll, parallax hero — all respecting `prefers-reduced-motion` |
| —                                     | `/sitemap.xml` + LocalBusiness JSON-LD for SEO |
| —                                     | `/api/catalog/packages.json` for mobile/SPA reuse |

## What changed in v2 (latest)

- **`apps/catalog/` app added.** Manages travel packages, scheduled batches, and newsletter subscribers from the Django admin. Uploading a brochure PDF on a Package row sends it to whichever storage backend `MEDIA_STORAGE_BACKEND` points at (filesystem / R2 / S3 / B2 / DO Spaces). No code change required when switching backends.
- **`static/css/extras.css` + `static/js/extras.js`** layer in animations and the back-to-top button additively — they never modify existing markup or override existing classes. The legacy `.reveal` / `.reveal-right` classes from the original site are auto-upgraded by the new IntersectionObserver code so every animation works without you editing a single template.
- **Approved reviews now drive the home page testimonial carousel.** When zero reviews are approved, the original three hardcoded testimonials still show — so the site never looks empty during the first weeks.
- **Optional outbound mirrors.** `apps/bookings/webhooks.py` forwards each new submission (fire-and-forget, 4-second timeout) to any combination of Slack, Notion, Airtable, or the legacy Google Apps Script Web App. Configure via env vars — no code change. The team's existing workflow can keep working unchanged while Django becomes the source of truth.

Everything in `static/` (CSS, JS, all 44 images, all 4 PDF brochures) is
the same byte-for-byte as your zip, with two surgical edits to `main.js`:

1. `ENDPOINTS` now reads from `window.MM_ENDPOINTS` (injected by Django).
2. `sendToFormspree()` adds the CSRF header and parses Django's JSON
   error shape (`{ok: false, errors: {field: [msgs]}}`).

If you ever want to revert to plain static hosting, just delete the two
`if (window.MM_ENDPOINTS)` blocks and the Formspree fallback kicks back in.

---

## Deployment guides

All six options below run the same Docker image. Pick based on cost,
ops effort, and how much AWS you want.

| Platform                       | Approx. monthly | Effort | Best for                      |
| ------------------------------ | --------------- | ------ | ----------------------------- |
| Railway                        | $5 (with free trial) | 5 min  | Smallest team, fastest ship |
| Render                         | Free tier, then $7 | 5 min  | Free hobby tier               |
| Fly.io                         | ~$3 (256MB VM)  | 10 min | Edge regions, low latency     |
| **AWS Lightsail Containers**   | **$10**         | 10 min | Easiest AWS, predictable bill |
| AWS App Runner                 | ~$25 (auto-scale)| 15 min | Auto-scale, fully managed     |
| AWS ECS Fargate                | ~$15–40         | 1 hr   | You want full AWS control     |

> **Pricing as of late 2025 — verify on each provider's site.** All AWS
> prices assume Mumbai (`ap-south-1`).

### Pre-flight (run once before any deploy)

```bash
# Generate a real secret key
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Set these env vars on whichever platform you pick:

```
DJANGO_SECRET_KEY=<from above>
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
NOTIFY_EMAILS=youremail@example.com
DEFAULT_FROM_EMAIL=Modern Mantra <bookings@yourdomain.com>
```

---

### Deploy 1: Railway (easiest, 5 min)

1. Push the project to GitHub.
2. <https://railway.app> → "New Project" → "Deploy from GitHub repo".
3. Railway detects the Dockerfile automatically. In project settings:
   - Add the env vars from "Pre-flight" above.
   - Generate a domain (or attach yours).
4. Done.

To attach Postgres: in the project, "Add → Database → Postgres". Railway
auto-injects `DATABASE_URL` — Django picks it up on next deploy.

---

### Deploy 2: Render

1. Push to GitHub.
2. <https://render.com> → "New +" → "Web Service" → pick the repo.
3. Settings:
   - **Environment:** Docker
   - **Plan:** Free (for hobby) or Starter ($7/mo)
   - **Health check path:** `/`
4. Add the env vars from "Pre-flight".
5. Click Create.

For Postgres: "New +" → "PostgreSQL", copy the Internal Connection String
into `DATABASE_URL` on the web service.

---

### Deploy 3: Fly.io

```bash
# One-time setup
curl -L https://fly.io/install.sh | sh
fly auth login

# In the project dir
fly launch --no-deploy   # answers: app name, region (e.g. bom for Mumbai), no DB now

# Edit fly.toml: add [http_service] internal_port = 8000 if not set

# Set secrets
fly secrets set \
  DJANGO_SECRET_KEY="..." \
  DJANGO_ALLOWED_HOSTS="yourapp.fly.dev,yourdomain.com" \
  DJANGO_CSRF_TRUSTED_ORIGINS="https://yourapp.fly.dev,https://yourdomain.com" \
  NOTIFY_EMAILS="you@example.com"

fly deploy
```

For persistent SQLite, attach a volume and mount it at `/app`:

```bash
fly volumes create mm_data --size 1 --region bom
# In fly.toml:
# [mounts]
# source = "mm_data"
# destination = "/app/db_volume"
```

---

### Deploy 4: AWS Lightsail Containers (simplest AWS)

Lightsail is AWS's fixed-price tier — no surprise bills.

1. Build and push the image to a public registry (Docker Hub example):

   ```bash
   docker build -t YOUR_DOCKERHUB/modernmantra:v1 .
   docker push YOUR_DOCKERHUB/modernmantra:v1
   ```

   Or push to ECR (private):

   ```bash
   aws ecr create-repository --repository-name modernmantra --region ap-south-1
   aws ecr get-login-password --region ap-south-1 | \
     docker login --username AWS --password-stdin \
     <acct>.dkr.ecr.ap-south-1.amazonaws.com
   docker tag modernmantra:latest <acct>.dkr.ecr.ap-south-1.amazonaws.com/modernmantra:v1
   docker push <acct>.dkr.ecr.ap-south-1.amazonaws.com/modernmantra:v1
   ```

2. AWS console → Lightsail → Containers → "Create container service".
3. Region: Mumbai. Power: **Nano** ($7) is enough for low traffic, **Micro** ($10) gives breathing room.
4. Set up first deployment:
   - **Image:** `YOUR_DOCKERHUB/modernmantra:v1`
   - **Open port:** 8000 (HTTP)
   - **Public endpoint:** select this container
   - **Environment variables:** paste from "Pre-flight" above
5. Save and deploy. Lightsail gives you a free HTTPS subdomain
   (`xxx.amazonlightsail.com`); attach a custom domain in the Domains tab.

> Lightsail containers are **stateless** — SQLite resets on every deploy.
> For SQLite persistence on AWS, use Lightsail instances (VMs) with EBS
> instead, or move to Postgres (see "Optional upgrades").

---

### Deploy 5: AWS App Runner (auto-scaling)

App Runner is "Lambda for containers" — auto-scales to zero, HTTPS
included, no infrastructure to manage.

1. Push image to ECR (see step 1 of Lightsail above).
2. AWS console → App Runner → "Create service".
3. Source: ECR → pick your image.
4. Service settings:
   - **CPU:** 0.25 vCPU, **Memory:** 0.5 GB (cheapest tier)
   - **Port:** 8000
   - **Health check path:** `/`
   - **Environment variables:** paste from "Pre-flight"
5. Create.

App Runner gives you `xxx.ap-south-1.awsapprunner.com` immediately; map a
custom domain via the "Custom domains" tab (validates via Route 53 or DNS).

Same caveat as Lightsail: container filesystem is ephemeral. Use Postgres.

---

### Deploy 6: AWS ECS Fargate (full control)

Use this if you want infrastructure-as-code, autoscaling rules, VPC
integration, etc. Most ops effort, also most flexible.

High-level steps:

1. Push image to ECR (as in Lightsail step 1).
2. Create a Postgres database in RDS (or Aurora Serverless v2).
3. Store the `DATABASE_URL` and `DJANGO_SECRET_KEY` in AWS Secrets Manager.
4. Create an ECS cluster (Fargate launch type).
5. Create a task definition referencing the image, mapping container
   port 8000, injecting env vars and secrets from Secrets Manager.
6. Create a service running 1+ task behind an Application Load Balancer.
7. Point Route 53 at the ALB.

For multi-replica deployments, **remove the `migrate` step from the
Dockerfile's CMD** and run it as a one-off ECS task during deploys:

```bash
aws ecs run-task --cluster modernmantra \
  --task-definition modernmantra-migrate:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

If you want, I can produce a Terraform module or CloudFormation template
for this stack in a follow-up.

---

## Optional upgrades

### Move PDF brochures to object storage (Cloudflare R2 — recommended)

By default media files (PDFs, package images) live on the container's
filesystem. On stateless platforms (App Runner, Fargate, Lightsail
Containers) that means they vanish on every deploy. Fix by pointing
`MEDIA_STORAGE_BACKEND` at a real object store.

**Cloudflare R2 is the best value** for this workload: S3-compatible
API (so `boto3` just works), ~$0.015/GB/month, and crucially **zero
egress fees** — which matters when travellers download brochures.

1. Sign up at <https://dash.cloudflare.com/sign-up>.
2. R2 → Create bucket → name it (e.g. `modernmantra-media`).
3. R2 → Manage API tokens → create token with R/W on that bucket.
4. (Optional) Connect a custom domain via R2 → bucket → Settings →
   Public access → Connect domain. This is your CDN.
5. Set these env vars on your deploy platform:
   ```
   MEDIA_STORAGE_BACKEND=r2
   MEDIA_BUCKET_NAME=modernmantra-media
   MEDIA_ACCESS_KEY_ID=<from step 3>
   MEDIA_SECRET_ACCESS_KEY=<from step 3>
   MEDIA_ENDPOINT_URL=https://<your_account_id>.r2.cloudflarestorage.com
   MEDIA_REGION=auto
   MEDIA_CUSTOM_DOMAIN=cdn.modernmantra.com    # optional, from step 4
   ```
6. Redeploy. From now on, every PDF / image you upload through the
   admin lands directly in R2.

Same pattern works for **AWS S3** (`MEDIA_STORAGE_BACKEND=s3`,
`MEDIA_REGION=ap-south-1`), **Backblaze B2** (`b2`, set `MEDIA_ENDPOINT_URL`),
or **DigitalOcean Spaces** (`do`, set `MEDIA_ENDPOINT_URL`). Comparison:

| Backend          | Storage   | Egress   | Notes                                 |
| ---------------- | --------- | -------- | ------------------------------------- |
| Cloudflare R2    | $0.015/GB | **free** | Best for downloads                    |
| AWS S3 (Mumbai)  | $0.025/GB | $0.109/GB| Cheapest if you already use AWS       |
| Backblaze B2     | $0.006/GB | $0.01/GB | Cheapest for cold storage             |
| DigitalOcean     | $5/250GB  | bundled  | Predictable flat-rate pricing         |

> The brochure URLs render the storage backend's public URL — once you
> move to R2, links like `https://cdn.modernmantra.com/packages/spiti-6d5n/brochures/itinerary.pdf`
> work everywhere unchanged.

### Mirror submissions to your team's existing tools (Slack / Notion / Airtable / Sheets)

If the team is used to a tool besides Django admin, mirror each new
submission there. Each is independent and fire-and-forget — failures
log but never break the user-facing flow.

**Slack** (5 minutes):
1. <https://api.slack.com/apps> → Create New App → From scratch.
2. Activate "Incoming Webhooks" → "Add New Webhook to Workspace".
3. Pick a channel, copy the URL.
4. Set `SLACK_WEBHOOK_URL=...` in env. Done.

**Notion** (10 minutes):
1. <https://www.notion.so/my-integrations> → New integration. Copy token.
2. Create two databases ("Enquiries", "Bookings") with `Name` (title),
   `Phone`, `Email`, `Status` (select) columns at minimum.
3. In each database: "..." menu → Connections → add your integration.
4. Copy each database ID from its URL.
5. Set:
   ```
   NOTION_API_TOKEN=secret_...
   NOTION_ENQUIRY_DB_ID=...
   NOTION_BOOKING_DB_ID=...
   ```

**Airtable** (10 minutes):
1. Get your personal access token from <https://airtable.com/create/tokens>.
2. Create base with two tables — "Enquiries" and "Bookings" — matching
   the column names in `apps/bookings/webhooks.py::mirror_*`.
3. Set:
   ```
   AIRTABLE_API_KEY=pat...
   AIRTABLE_BASE_ID=app...
   AIRTABLE_ENQUIRY_TABLE=Enquiries
   AIRTABLE_BOOKING_TABLE=Bookings
   ```

**Legacy Google Apps Script Web App** (zero migration cost):
Keep `google-apps-script.gs` deployed exactly as before, just set:
```
SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/AKfycb.../exec
SHEETS_SECRET=modernmantra2026
```
Every new enquiry/booking/review still appears in your existing Google
Sheet, alongside the Django admin.

### Switch to Postgres on RDS

1. Create an RDS instance (Aurora Postgres Serverless v2 is the
   easiest — scales from 0.5 ACU at ~$45/month minimum, but no manual
   tuning. For lowest cost, use `db.t4g.micro` at ~$15/month).
2. Uncomment in `requirements.txt`:
   ```
   psycopg[binary]==3.2.3
   ```
3. Set `DATABASE_URL=postgres://USER:PASS@HOST:5432/modernmantra`.
4. Redeploy. The Dockerfile's `migrate` step will create tables on first run.

### Email via AWS SES (production-grade)

1. AWS console → SES → Verify your sending domain (DKIM, SPF).
2. Create SMTP credentials in SES.
3. Set in env:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=email-smtp.ap-south-1.amazonaws.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=1
   EMAIL_HOST_USER=AKIA...
   EMAIL_HOST_PASSWORD=<SES SMTP password>
   ```

Alternative: install `django-anymail` (already in commented `requirements.txt`)
to use the SES API directly with better deliverability and logs.

### Serve images from S3 + CloudFront

Your 28MB of trip photos load faster from CloudFront edge than from your
app server. Add to `requirements.txt`:

```
django-storages[s3]==1.14.4
boto3==1.35.0
```

Then in `modernmantra/settings/production.py`, set:

```python
STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}
STORAGES["staticfiles"] = {"BACKEND": "storages.backends.s3.S3Storage"}
AWS_STORAGE_BUCKET_NAME = "modernmantra-static"
AWS_S3_REGION_NAME = "ap-south-1"
AWS_S3_CUSTOM_DOMAIN = "cdn.modernmantra.com"   # CloudFront distribution
AWS_QUERYSTRING_AUTH = False
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
```

Then `python manage.py collectstatic` uploads everything to S3.

### Better admin (django-unfold, django-jazzmin)

The default Django admin is functional but plain. For a more designed
look matching your site's aesthetic, drop in `django-unfold` (Tailwind-
based, modern) or `django-jazzmin` (Bootstrap-based, more familiar).
Both are single-package installs that take 10 minutes.

### Add user accounts / payments / search

Pluggable upgrades for later:

- **Razorpay/Stripe payments:** `django-razorpay` or `dj-stripe`
- **User accounts:** `django-allauth` (email login, social login, etc.)
- **Full-text search across packages:** Postgres `SearchVector` or `django-haystack`
- **Real-time admin notifications:** add Telegram bot back via a single `requests.post()` call in `bookings/views.py`

---

## Troubleshooting

**`CSRF verification failed` on form submit**

Make sure `DJANGO_CSRF_TRUSTED_ORIGINS` includes the full origin with
scheme: `https://modernmantra.com`, not just `modernmantra.com`.

**Static files 404 in production**

Ensure `collectstatic` ran (it's baked into the Dockerfile). Locally:
`DJANGO_DEBUG=0 python manage.py runserver --insecure` doesn't serve
static files — that's by design; use `gunicorn` with WhiteNoise.

**Form POSTs return 403**

The CSRF token isn't being sent. Check that `base.html` is being
extended (look at the rendered HTML — `window.MM_CSRF_TOKEN` should be
present). If you've added a new form template that doesn't extend
`base.html`, make sure to render `{{ csrf_token }}` somewhere on the
page so the cookie gets set.

**Emails aren't arriving**

By default `EMAIL_BACKEND` is `django.core.mail.backends.console.EmailBackend` —
emails print to stdout. To actually send, set `EMAIL_BACKEND` to the SMTP
backend and provide credentials (see ".env.example").

**SQLite database keeps resetting**

You're on a stateless container platform (App Runner, Fargate, Lightsail
Containers). Either mount a persistent volume or switch to Postgres.

**`collectstatic` fails in Docker build with "SECRET_KEY"**

The Dockerfile passes a throwaway key for the build step. If you're
running `collectstatic` manually outside Docker, set
`DJANGO_SECRET_KEY` first.

---

## License & contact

This repo is for the Modern Mantra business. Contact:
ziyaziu17@gmail.com / +91 77368 55515.
