from elasticsearch import Elasticsearch
import json

# Connect with password (ES 8.11 security)
es = Elasticsearch(
    "http://localhost:9200",
    basic_auth=("elastic", "l=PpE*3YpWge-SmEY+E9")
)

# Delete index if exists
if es.indices.exists(index="nepali_recipes"):
    es.indices.delete(index="nepali_recipes")

# Create index
mapping = {
    "mappings": {
        "properties": {
            "name": {"type": "text"},
            "description": {"type": "text"},
            "ingredients": {"type": "keyword"},
            "cuisine": {"type": "keyword"},
            "difficulty": {"type": "keyword"},
            "prep_time": {"type": "integer"},
            "cook_time": {"type": "integer"},
            "rating": {"type": "float"}
        }
    }
}
es.indices.create(index="nepali_recipes", body=mapping)

# Index recipes
with open("recipes.json", "r") as f:
    recipes = json.load(f)

for recipe in recipes:
    doc = {
        "name": recipe["name"],
        "description": recipe["description"],
        "ingredients": recipe["ingredients"],
        "cuisine": recipe["cuisine"],
        "difficulty": recipe["difficulty"],
        "prep_time": recipe["prep_time"],
        "cook_time": recipe["cook_time"],
        "rating": recipe["rating"]
    }
    es.index(index="nepali_recipes", id=recipe["id"], body=doc)

print(f"Indexed {len(recipes)} Nepali recipes!")
