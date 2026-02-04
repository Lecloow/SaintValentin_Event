# SaintValentin

pour run le code:

### Requirements 
- Python 3.9+
- PostgreSQL (local or Render-hosted)
- Pandas
- Uvicorn
- FastApi
- Openpyxl
- psycopg2-binary
- python-dotenv

### Build

Cloner le repo

```bash
git clone https://github.com/Lecloow/SaintValentin_Event/ && cd SaintValentin_Event/backend
```

Configurer la base de données PostgreSQL

```bash
# Créer un fichier .env avec votre DATABASE_URL
cp .env.example .env
# Editer .env et définir DATABASE_URL=postgresql://user:password@localhost:5432/saintvalentin
```

Installer les dépendances

```bash
pip install -r requirements.txt
```

Puis executer cette commande

```bash
uvicorn main:app --reload
```

Enfin, ouvrir un navigateur et acceder a http://127.0.0.1:8000/docs

### Migration vers PostgreSQL

L'application utilise maintenant PostgreSQL au lieu de SQLite. Voir [backend/POSTGRESQL_MIGRATION.md](backend/POSTGRESQL_MIGRATION.md) pour les détails de la migration et le déploiement sur Render.
