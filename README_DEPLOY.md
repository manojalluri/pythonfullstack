# Vercel Deployment Instructions

This project is configured for deployment on Vercel.

## Environment Variables
You MUST set the following environment variables in the Vercel Dashboard (Settings > Environment Variables):

1. `SECRET_KEY`: A long, random string for Django security.
2. `DEBUG`: Set to `False` for production.
3. `DATABASE_URL`: Your PostgreSQL connection string (e.g., from Vercel Postgres, Supabase, or Neon).
4. `ALLOWED_HOSTS`: Set to your Vercel domain (e.g., `your-app.vercel.app`) or leave as default (the project is configured to allow `.vercel.app`).

## Deployment Settings
1. **Framework Preset**: Other (Vercel will detect `vercel.json`).
2. **Root Directory**: Leave as `./` (the root of the repository).
3. **Build Command**: `sh build.sh`
4. **Output Directory**: `staticfiles` (though Whitenoise handles this).

## Static Files
Whitenoise is configured to serve static files. During the build process, `python manage.py collectstatic` will run automatically via `build.sh`.

## Database
Ensure you have a PostgreSQL database ready and the `DATABASE_URL` is correctly formatted:
`postgres://user:password@host:port/dbname`
