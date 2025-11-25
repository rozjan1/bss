# Frontend demo — Supermarket

This is a small static frontend that loads product data from `testing/tesco_products.json` and displays it like a supermarket e-shop.

How to run locally

1. From the repository root run a simple static server. Python 3 has a built-in one:

```bash
# from repo root
python3 -m http.server 8000
```

2. Open http://localhost:8000/frontend/index.html in your browser.

Notes
- The frontend reads the JSON via relative path `../testing/tesco_products.json`. Keep the file in place.
- Cart is stored in localStorage for demo persistence.
- This is a minimal demo: no backend, no authentication, no real checkout.

Docker

How to build and run the frontend with Docker (serves on port 8080):

```bash
# from repo root
docker compose up --build
```

Open http://localhost:8080 in your browser. The `docker-compose.yml` mounts `testing/tesco_products.json` into the container so you can edit it locally and refresh the page.
