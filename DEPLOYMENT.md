# Deployment checklist

## Render / Railway / VPS
- Push the project to a private Git repository.
- Add environment variables from `.env.example` in the hosting dashboard.
- Store Google service-account credentials using the platform's secret/file mechanism rather than committing JSON keys.
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`

## Netlify / Vercel
The supplied project uses a Flask backend, so deploy the backend as a Python web service and point the frontend/API routing to that service. Do not expose Claude or Google credentials in browser JavaScript.

## Security before real-world use
- Add authentication and authorization.
- Use HTTPS only.
- Validate and sanitize all inputs server-side.
- Encrypt sensitive data at rest and in transit.
- Add rate limiting and audit logs.
- Follow applicable Indian privacy, financial, and data-protection requirements.
- Never collect passwords, card CVVs, banking credentials, or unnecessary government identifiers.
