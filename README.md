# Affinities — comitedepromo2026.fr

> Full-stack matchmaking platform built for my high school's Valentine's Day event — **330+ students** 

[![Hackatime](https://img.shields.io/badge/Hackatime-98h40m-e53953?style=flat&logo=hackatime&logoColor=white)](https://hackatime.hackclub.com)
[![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)](https://golang.org/)
[![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com)


## What is this?

My school committee (Comite de promo) wanted to organize a Valentine's Day matchmaking event. So I designed and built the platform from scratch.

Deployed under real constraints: actual deadline, actual users, actual consequences if it broke.

> Built for 330 students

## Architecture

```
┌─────────────────┐        ┌──────────────────────┐
│  React Frontend │ ──────▶│   Go Backend (v2)    │
│  (TypeScript)   │        │   Gin + PostgreSQL   │
└─────────────────┘        └──────────────────────┘
                                      │
                              ┌───────▼────────┐
                              │   PostgreSQL   │
                              │  (production)  │
                              └────────────────┘
```

- **Frontend:** React + TypeScript
- **Backend v1:** Python (FastAPI) — shipped fast for the initial event
- **Backend v2:** Go (Gin) — full rewrite for better performance, security, and no more AI-generated code
- **CI/CD:** GitHub Actions
- **API Testing:** Bruno


## Why the Go Rewrite?

The Python backend did the job, but had real issues: slow response times, minimal security, and it was partially AI-generated.
I'm not interested in deploying AI spaghetti code, I am here to learn.

|                    | Python v1                | Go v2                                         |
|--------------------|--------------------------|-----------------------------------------------|
| **Code ownership** | Partially AI-generated   | 100% hand-written                             |
| **Database**       | Unoptimized queries      | Indexing & connection pooling                 |
| **Performance**    | ~100ms avg response      | ~15ms avg response                            |
| **Security**       | Minimal input validation | Strict validation, rate limiting, proper auth |
| **Concurrency**    | Single-threaded ASGI     | Native goroutines                             |

Same logic on the frontend: original HTML/CSS → React + TypeScript rewrite.


## Tech Stack

| Layer        | Tech                    |
|--------------|-------------------------|
| Frontend     | React, TypeScript, Vite |
| Backend      | Go, Gin                 |
| Database     | PostgreSQL              |
| CI/CD        | GitHub Actions          |
| Deployment   | Render                  |
| API Testing  | Bruno                   |


## Usage

To run this project for your own event, follow the setup guide:

- [Instructions](./INSTRUCTIONS.md)
- [Instructions (French)](./FRENCH_INSTRUCTIONS.md)

A Bruno collection is available in the `/bruno` folder to test all API endpoints.

Import it into Bruno and set the `baseUrl` variable to start using the API without setup.

There is also a demo data file that you can use to test the backend and the ml (and to be sure that your file format is correct).

## Impact

- **330 students** participated
- Live at [comitedepromo2026.fr](https://comitedepromo2026.fr)

## What I Learned

- Don't forget date conversion, because the server was based in UTC when Paris was in UTC+1
- No matter how many tests you run, something will break in production.
- Tradeoffs between shipping fast and owning your code
- Debugging in production when real users are affected (I don't recommend it)
- CI/CD, environment management, cloud deployment


## License

GPL-3.0 — see [LICENSE](./LICENSE)

---

Made with ❤️ by [Thomas Conchon](https://github.com/Lecloow)
