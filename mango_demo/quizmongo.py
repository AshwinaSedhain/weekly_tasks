from pymongo import MongoClient
from colorama import Fore, Style
import random

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["quizDB"]
collection = db["questions"]

# If collection is empty, insert sample questions
if collection.count_documents({}) == 0:
    collection.insert_many([
        {
            "question": "What is Python?",
            "options": ["Language", "Snake", "Car", "Game"],
            "answer": "Language",
            "hint": "It is a programming language"
        },
        {
            "question": "What is MongoDB?",
            "options": ["SQL DB", "NoSQL DB", "OS", "Browser"],
            "answer": "NoSQL DB",
            "hint": "It stores data as documents"
        },
        {
            "question": "Which one is a Python framework?",
            "options": ["Flask", "Laravel", "React", "DjangoJS"],
            "answer": "Flask",
            "hint": "It is lightweight"
        },
        {
            "question": "Which company created Python?",
            "options": ["Microsoft", "Apple", "Google", "None"],
            "answer": "None",
            "hint": "It was created by Guido van Rossum"
        },
        {
            "question": "What is pip used for?",
            "options": ["Install Packages", "Run Python", "Debug Python", "Compile Python"],
            "answer": "Install Packages",
            "hint": "It manages Python libraries"
        }
    ])

# Function to run the quiz
def take_quiz():
    questions = list(collection.find())
    random.shuffle(questions)
    score = 0

    for q in questions:
        print(Fore.CYAN + "\n" + q["question"] + Style.RESET_ALL)
        for i, opt in enumerate(q["options"]):
            print(f"{i+1}. {opt}")

        while True:
            choice = input("Enter option number (or 0 for hint): ")
            if choice == "0" and "hint" in q:
                print(Fore.YELLOW + "Hint: " + q["hint"] + Style.RESET_ALL)
            else:
                try:
                    choice = int(choice)
                    if 1 <= choice <= len(q["options"]):
                        break
                    else:
                        print(Fore.RED + "Enter a valid option!" + Style.RESET_ALL)
                except:
                    print(Fore.RED + "Enter a number!" + Style.RESET_ALL)

        if q["options"][choice-1] == q["answer"]:
            print(Fore.GREEN + "Correct! " + Style.RESET_ALL)
            score += 1
        else:
            print(Fore.RED + f"Wrong!  Answer: {q['answer']}" + Style.RESET_ALL)

    stars = "★" * score + "☆" * (len(questions)-score)
    print(Fore.MAGENTA + f"\nYour Score: {score}/{len(questions)} {stars}" + Style.RESET_ALL)

# Run the quiz
if __name__ == "__main__":
    print(Fore.BLUE + " Welcome to MongoDB Quiz Game! " + Style.RESET_ALL)
    take_quiz()