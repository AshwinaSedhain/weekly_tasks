students = []

while True:
    print("\n Student Management System ")
    print("1. Add Student")
    print("2. View Students")
    print("3. Search Student")
    print("4. Exit")

    choice = input("Enter your choice: ")


    #  implementing CONTROL STRUCTURE (if-elif-else)

    if choice == "1":
        name = input("Enter student name: ")
        marks = int(input("Enter marks: "))

        students.append({"name": name, "marks": marks})
        print("Student added successfully!")

    elif choice == "2":
       
        #  implementation of FOR LOOP 
        if len(students) == 0:
            print("No students found")
        else:
            print("\nStudent List:")
            for i, student in enumerate(students):
                print(f"{i+1}. {student['name']} - {student['marks']}")

    elif choice == "3":
        search_name = input("Enter name to search: ")

        found = False

       
        # FOR LOOP and  CONTROL
        
        for student in students:
            if student["name"].lower() == search_name.lower():
                print("Found:", student)
                found = True
                break  

        if not found:
            print("Student not found")

    elif choice == "4":
        print("Exiting program...")
        break   
    else:
        print("Invalid choice, try again")
        continue  