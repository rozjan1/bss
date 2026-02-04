# Frontend static viewer

This is a lightweight, Dockerized static frontend for browsing supermarket JSON data.

How it works
- Static files (HTML/CSS/JS) are served by nginx.
- Product JSON files are read from the `data/` folder included in the image.

Build and run (from repo root)

```powershell
docker compose up --build frontend
```

Open http://localhost:8888 to view.
