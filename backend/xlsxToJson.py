import pandas as pd
import json
import sys
import re


def parse_name(full_name: str) -> dict:
    if not full_name or pd.isna(full_name):
        return {"first_name": "", "last_name": ""}

    parts = full_name.strip().split()

    # Trouver où commence le nom (les parties en MAJUSCULES)
    last_name_parts = []
    first_name_parts = []

    # On parcourt depuis la fin pour catcher le nom en majuscules
    i = len(parts) - 1
    while i >= 0 and parts[i].isupper():
        last_name_parts.insert(0, parts[i])
        i -= 1

    # Le reste c'est le prénom
    first_name_parts = parts[: i + 1]

    first_name = " ".join(first_name_parts).strip()
    # Capitaliser proprement le nom
    last_name = " ".join(p.capitalize() for p in last_name_parts).strip()

    # Si on a rien trouvé en majuscules, on fait un split simple (moitié/moitié)
    if not last_name and len(parts) >= 2:
        first_name = parts[0]
        last_name = " ".join(parts[1:]).capitalize()
    elif not first_name and last_name:
        # Tout était en majuscules, on garde juste le dernier comme nom
        first_name = " ".join(last_name_parts[:-1])
        last_name = last_name_parts[-1].capitalize() if last_name_parts else ""

    return {"first_name": first_name, "last_name": last_name}


def convert_xlsx_to_json(input_path: str, output_path: str):
    # Lire le fichier Excel
    df = pd.read_excel(input_path)
    print(f"📋 {len(df)} entrées trouvées")

    # --- Supprimer les colonnes indésirables ---

    # Colonnes à supprimer exactement
    drop_exact = [
        "Heure de début",
        "Heure de fin",
        "Heure de la dernière modification",
        "Total points",
        "Quiz feedback",
        "Nom",  # On la remplace par first_name + last_name
    ]

    # Supprimer les colonnes "Points - ..." et "Feedback - ..."
    drop_pattern = df.columns[
        df.columns.str.startswith("Points - ")
        | df.columns.str.startswith("Feedback - ")
    ].tolist()

    all_to_drop = drop_exact + drop_pattern
    df = df.drop(columns=[c for c in all_to_drop if c in df.columns])

    print(f"🗑️  Colonnes supprimées, reste {len(df.columns)} colonnes")

    # --- Construire le JSON ---
    results = []

    for _, row in df.iterrows():
        # Séparer le nom
        name = parse_name(
            pd.read_excel(input_path)["Nom"].iloc[row.name]
        )

        entry = {
            "id": int(row["ID"]),
            "first_name": name["first_name"],
            "last_name": name["last_name"],
            "email": row["Adresse de messagerie"],
            "answers": {},
        }

        # Ajouter les réponses (tout ce qui reste sauf ID et email)
        skip_cols = ["ID", "Adresse de messagerie"]
        for col in df.columns:
            if col not in skip_cols:
                value = row[col]
                # Nettoyer les \xa0 (espace insécable) dans les clés
                clean_col = col.replace("\xa0", " ").strip()
                entry["answers"][clean_col] = (
                    str(value) if pd.notna(value) else None
                )

        results.append(entry)

    # --- Écrire le JSON ---
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON écrit dans: {output_path}")
    print(f"📄 {len(results)} entrées exportées")


# python
if __name__ == "__main__":
    from pathlib import Path

    script_dir = Path(__file__).resolve().parent
    default_input = script_dir / "input.xlsx"
    default_output = script_dir / "input.json"

    if len(sys.argv) == 3:
        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])
    elif len(sys.argv) == 2:
        input_path = Path(sys.argv[1])
        output_path = default_output
    else:
        input_path = default_input
        output_path = default_output

    convert_xlsx_to_json(str(input_path), str(output_path))
