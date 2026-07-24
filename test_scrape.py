import json
from scraper_raw import scrape_multiple_pages

def test():
    print("Testing crawler on https://faix.utem.edu.my/...")
    faix_data, faix_error = scrape_multiple_pages("https://faix.utem.edu.my/", max_pages=800)
    
    if faix_error:
        print(f"Error: {faix_error}")
    else:
        print(f"Successfully scraped {len(faix_data)} items from FAIX.")
        
    with open("faix_result_deep.json", "w", encoding="utf-8") as f:
        json.dump(faix_data, f, indent=4, ensure_ascii=False)
    print("FAIX results written to faix_result_deep.json\n")
    
    print("Testing crawler on https://ftmk.utem.edu.my/web/...")
    ftmk_data, ftmk_error = scrape_multiple_pages("https://ftmk.utem.edu.my/web/", max_pages=800)
    
    if ftmk_error:
        print(f"Error: {ftmk_error}")
    else:
        print(f"Successfully scraped {len(ftmk_data)} items from FTMK.")
        
    with open("ftmk_result_deep.json", "w", encoding="utf-8") as f:
        json.dump(ftmk_data, f, indent=4, ensure_ascii=False)
    print("FTMK results written to ftmk_result_deep.json")

if __name__ == "__main__":
    test()
