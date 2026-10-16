
from model import load_data
from tools import (
    show_students,
    search_students,
    show_classes,
    book_class,
    show_bookings,
    set_meeting_link,
    access_meeting,
    rate_class,
    show_class_ratings,
    create_class_notes,
    view_class_notes,
    ask_doubt_bot,
)


def main():
    data = load_data()

    while True:
        print("\n" + "=" * 48)
        print("       SKILLBRIDGE LEARNING PLATFORM")
        print("=" * 48)
        print("1.  View all students")
        print("2.  Search students by skill")
        print("3.  View available classes")
        print("4.  Book a class slot")
        print("5.  View my bookings")
        print("6.  Add/update a class meeting link")
        print("7.  Access a class meeting")
        print("8.  Rate a class and tutor")
        print("9.  View class ratings")
        print("10. Generate AI class notes from audio")
        print("11. View shared class notes")
        print("12. Ask the AI doubt chatbot")
        print("13. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            show_students(data)

        elif choice == "2":
            subject = input("Enter a skill or subject: ")
            search_students(data, subject)

        elif choice == "3":
            show_classes(data)

        elif choice == "4":
            show_classes(data)
            name = input("Enter your registered student name: ")
            class_id = input("Enter class ID: ")
            book_class(data, name, class_id)

        elif choice == "5":
            name = input("Enter your registered student name: ")
            show_bookings(data, name)

        elif choice == "6":
            class_id = input("Enter class ID: ")
            tutor = input("Enter assigned tutor name: ")
            link = input("Enter HTTPS meeting link: ")
            set_meeting_link(data, class_id, tutor, link)

        elif choice == "7":
            name = input("Enter your registered student name: ")
            class_id = input("Enter class ID: ")
            access_meeting(data, name, class_id)

        elif choice == "8":
            name = input("Enter your registered student name: ")
            class_id = input("Enter class ID: ")

            try:
                score = int(input("Rating from 1 to 5: "))
            except ValueError:
                print("Enter a whole number from 1 to 5.")
                continue

            feedback = input("Write feedback: ")
            rate_class(data, name, class_id, score, feedback)

        elif choice == "9":
            class_id = input("Enter class ID: ")
            show_class_ratings(data, class_id)

        elif choice == "10":
            print("Use a class recording with permission to transcribe.")
            class_id = input("Enter class ID: ")
            tutor = input("Enter assigned tutor name: ")
            audio_path = input("Enter audio file path: ")
            create_class_notes(data, tutor, class_id, audio_path)

        elif choice == "11":
            name = input("Enter your registered student name: ")
            class_id = input("Enter class ID: ")
            view_class_notes(data, name, class_id)

        elif choice == "12":
            question = input("Enter your doubt: ")
            ask_doubt_bot(question)

        elif choice == "13":
            print("Thank you for using SkillBridge!")
            break

        else:
            print("Invalid option. Choose a number from 1 to 13.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSkillBridge closed.")
