from elasticsearch import Elasticsearch

# Connect with password
es = Elasticsearch(
    "http://localhost:9200",
    basic_auth=("elastic", "l=PpE*3YpWge-SmEY+E9")
)

def search_recipes(query="", cuisine=None, difficulty=None, min_rating=None, max_prep_time=None):
    search_body = {
        "query": {
            "bool": {
                "should": [{"multi_match": {"query": query, "fields": ["name^3", "description^2", "ingredients"]}}],
                "minimum_should_match": "1"
            }
        },
        "sort": [{"rating": {"order": "desc"}}],
        "size": 10
    }
    
    filters = []
    if cuisine: filters.append({"term": {"cuisine.keyword": cuisine}})
    if difficulty: filters.append({"term": {"difficulty.keyword": difficulty}})
    if min_rating: filters.append({"range": {"rating": {"gte": min_rating}}})
    if max_prep_time: filters.append({"range": {"prep_time": {"lte": max_prep_time}}})
    
    if filters:
        search_body["query"]["bool"]["filter"] = filters
    
    response = es.search(index="nepali_recipes", body=search_body)
    return response["hits"]["hits"]

def print_results(results, title):
    print(f"\n{'='*50}")
    print(f {title}")
    print('='*50)
    for i, hit in enumerate(results, 1):
        recipe = hit["_source"]
        print(f"{i}. {recipe['name']}")
        print(f"   {recipe['rating']} |  Prep:{recipe['prep_time']}m Cook:{recipe['cook_time']}m")
        print(f"   {recipe['difficulty'].title()} | {recipe['cuisine']}")
        print(f"   {', '.join(recipe['ingredients'][:4])}...")

if __name__ == "__main__":
    print(" Nepali Recipe Finder")
    results = search_recipes("momo")
    print_results(results, "Momo search")
    results = search_recipes("chicken", difficulty="easy")
    print_results(results, "Easy chicken")