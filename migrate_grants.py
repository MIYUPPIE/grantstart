from grants_db import GRANTS, COUNTRY_DOCS, IMPACT_TRANSLATIONS
from grants_sqlite import init_grants_db, save_grant, save_country_docs, save_impact_translation

def migrate():
    print("🚀 Initializing Dynamic Grants Database...")
    init_grants_db()

    print(f"📦 Migrating {len(GRANTS)} grants...")
    for grant in GRANTS:
        save_grant(grant)
    
    print(f"🌍 Migrating {len(COUNTRY_DOCS)} country compliance profiles...")
    for country, data in COUNTRY_DOCS.items():
        save_country_docs(country, data)

    print(f"📊 Migrating {len(IMPACT_TRANSLATIONS)} impact translations...")
    for keyword, data in IMPACT_TRANSLATIONS.items():
        save_impact_translation(keyword, data)

    print("✅ Migration complete! GrantStar is now dynamic.")

if __name__ == "__main__":
    migrate()
