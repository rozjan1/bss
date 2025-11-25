import json

with open("test.json") as f:
    parsed_json = json.load(f) 

# The list of individual product items is deeply nested
results_list = []
try:
    # Path: [0] -> "data" -> "category" -> "results"
    results_list = parsed_json[0]["data"]["category"]["results"]
except (IndexError, KeyError) as e:
    print(f"Could not find the 'results' list. Check JSON structure. Error: {e}")

all_titles = []

# Iterate through each item in the results list
for item in results_list:
    try:
        # Path for each item: "node" -> "title"
        title = item["node"]["title"]
        all_titles.append(title)
    except KeyError:
        # Handle cases where an item might be missing the expected structure
        print("Warning: Found an item without a 'title' in its 'node'. Skipping.")
        
# Output the extracted titles
for title in all_titles:
    print(title)