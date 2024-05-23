import re
from datetime import datetime, date, timedelta
from collections import UserDict
import pickle

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "This contact does not exist."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Insufficient arguments provided."
    return wrapper

class Field:
    def __init__(self, value):
        self.value = value

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, number):
        if not self.validate(number):
            raise ValueError("Phone number must be exactly 10 digits.")
        super().__init__(number)

    @staticmethod
    def validate(number):
        return bool(re.match(r'^\d{10}$', number))

class Birthday(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        self.value = datetime.strptime(value, "%d.%m.%Y").date()

    @staticmethod
    def validate(value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            return True
        except ValueError:
            return False

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, number):
        try:
            phone = Phone(number)
            self.phones.append(phone)
            return f"Phone number '{number}' added for {self.name.value}."
        except ValueError as e:
            return str(e)

    def remove_phone(self, number):
        for phone in self.phones:
            if phone.value == number:
                self.phones.remove(phone)
                return f"Phone number '{number}' removed for {self.name.value}."
        return f"Phone number '{number}' not found for {self.name.value}."

    def edit_phone(self, old_number, new_number):
        for phone in self.phones:
            if phone.value == old_number:
                try:
                    new_phone = Phone(new_number)
                    phone.value = new_number
                    return f"Phone number '{old_number}' edited to '{new_number}' for {self.name.value}."
                except ValueError as e:
                    return str(e)
        return f"Phone number '{old_number}' not found for {self.name.value}."

    def find_phone(self, number):
        for phone in self.phones:
            if phone.value == number:
                return phone
        return None

    def add_birthday(self, date_str):
        try:
            self.birthday = Birthday(date_str)
            return f"Birthday '{date_str}' set for {self.name.value}."
        except ValueError as e:
            return str(e)

    def show_birthday(self):
        if self.birthday:
            return self.birthday.value.strftime("%d.%m.%Y")
        else:
            return "No birthday set"

    def __str__(self):
        phones_str = ', '.join(phone.value for phone in self.phones)
        birthday_str = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "No birthday set"
        return f"Record(name: {self.name.value}, phones: [{phones_str}], birthday: {birthday_str})"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return f"Record for {name} removed from the address book."
        else:
            return f"No record found for {name}."

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                if 0 <= (birthday_this_year - today).days <= days:
                    birthday_this_year = adjust_for_weekend(birthday_this_year)

                    congratulation_date_str = date_to_string(birthday_this_year)
                    upcoming_birthdays.append({"name": record.name.value, "congratulation_date": congratulation_date_str})
        return upcoming_birthdays

def adjust_for_weekend(birthday):
    if birthday.weekday() == 5:  # Saturday
        birthday += timedelta(days=2)
    elif birthday.weekday() == 6:  # Sunday
        birthday += timedelta(days=1)
    return birthday

def date_to_string(birthday):
    return birthday.strftime("%d.%m.%Y")

@input_error
def add_birthday(args, book):
    name, birthday = args.split(maxsplit=1)
    record = book.find(name)
    if record:
        return record.add_birthday(birthday)
    else:
        return "Record not found."

@input_error
def show_birthday(args, book):
    name = args.strip()
    record = book.find(name)
    if record:
        return f"{name}'s birthday is {record.show_birthday()}."
    else:
        return "Record not found."

@input_error
def birthdays(args, book):
    days = int(args.strip()) if args.strip().isdigit() else 7
    upcoming_birthdays = book.get_upcoming_birthdays(days)
    if not upcoming_birthdays:
        return "No upcoming birthdays."
    result = "Upcoming birthdays:\n"
    for birthday in upcoming_birthdays:
        result += f"{birthday['name']}: {birthday['congratulation_date']}\n"
    return result.strip()

@input_error
def add_contact(args, book):
    name, phone = args.split(maxsplit=1)
    record = book.find(name)
    if record:
        add_phone_result = record.add_phone(phone)
        return add_phone_result
    else:
        new_record = Record(name)
        add_phone_result = new_record.add_phone(phone)
        if "Phone number must be exactly 10 digits." in add_phone_result:
            return add_phone_result
        book.add_record(new_record)
        return f"New contact '{name}' added with phone number '{phone}'.\n{add_phone_result}"

@input_error
def change_phone(args, book):
    name, phone = args.split(maxsplit=1)
    record = book.find(name)
    if record:
        old_phone = record.phones[0].value if record.phones else None
        return record.edit_phone(old_phone, phone)
    else:
        return "Record not found."

@input_error
def show_phone(args, book):
    name = args.strip()
    record = book.find(name)
    if record:
        phones = ', '.join(phone.value for phone in record.phones)
        return f"{name}'s phone number(s): {phones}"
    else:
        return "Record not found."

def show_all_contacts(book):
    if not book.data:
        return "No contacts in address book."
    result = "All contacts:\n"
    for name, record in book.data.items():
        result += f"{name}: {', '.join(phone.value for phone in record.phones)}\n"
    return result.strip()

def greet():
    return "Hello! How can I assist you today?"

def close_program():
    return "Goodbye!"

def parse_input(user_input):
    parts = user_input.split(' ', 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ''
    return command, args

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all_contacts(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
