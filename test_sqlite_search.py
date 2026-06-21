from grantstar_engine import search_grants

def test():
    print("🔍 Testing Dynamic Grant Search...")
    # Test for a Nigerian startup in Tech
    results = search_grants(country="Nigeria", sector="Tech", org_type="Startup", stage="Idea", registered=True)
    
    print(f"📊 Found {len(results)} matches.")
    if results:
        top = results[0]
        print(f"🏆 Top Match: {top['name']} ({top['match_score']} points)")
        for reason in top['match_reasons']:
            print(f"   - {reason}")
        
        # Verify it's from SQLite
        print(f"💾 ID: {top['id']}")
    else:
        print("❌ No results found. Check migration!")

if __name__ == "__main__":
    test()
