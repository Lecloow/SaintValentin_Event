# SaintValentin

pour run le code:

### Requirements 
Pandas
Uvicorn
FastApi
Openpyxl
PostgreSQL (psycopg2-binary)
Python-dotenv

### Setup

1. Cloner le repo

```bash
git clone https://github.com/Lecloow/SaintValentin_Event/ && cd SaintValentin_Event/backend
```

2. Installer les dépendances

```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement

Créer un fichier `.env` basé sur `.env.example` :

```bash
cp .env.example .env
```

Puis éditer le fichier `.env` avec vos paramètres :
- `DATABASE_URL`: URL de connexion PostgreSQL (ex: `postgresql://user:password@localhost:5432/dbname`)
- `EMAIL`: Adresse email pour l'envoi d'emails
- `PASSWORD`: Mot de passe email

### Build

Executer cette commande

```bash
uvicorn main:app --reload
```

Enfin, ouvrir un navigateur et acceder a http://127.0.0.1:8000/docs

### Database

L'application utilise PostgreSQL. Les tables sont créées automatiquement au démarrage :
- `passwords` (password TEXT PRIMARY KEY, user_id INTEGER)
- `users` (id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, currentClass TEXT)
- `matches` (id TEXT PRIMARY KEY, day1 TEXT, day2 TEXT, day3 TEXT)

Pour Render, configurez simplement la variable d'environnement `DATABASE_URL` avec l'URL fournie par votre base PostgreSQL Render.
