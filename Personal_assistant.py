from collections import UserDict, defaultdict, OrderedDict
from datetime import datetime, timedelta
import re
from pathlib import Path
import pickle


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        super().__init__(value)

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if value:
            self.__value = value
        else:
            raise ValueError("Name is a required field.")


class InvalidNumberError(ValueError):
    pass


class Phone(Field):
    def __init__(self, value):
        super().__init__(value)

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if re.fullmatch(r"\d{10}", value):
            self.__value = value
        else:
            raise InvalidNumberError("Invalid number format.")


class DateFormatError(ValueError):
    pass


class UnrealDateError(ValueError):
    pass


class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self,value):
        if re.fullmatch(r"\d{2}.\d{2}.\d{4}", value):
            try:
                value = datetime.strptime(value, "%d.%m.%Y").date()
                self.__value = value
            except ValueError:
                raise UnrealDateError()
        else:
            raise DateFormatError()


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        if phone not in [p.value for p in self.phones]:
            self.phones.append(Phone(phone))

    def edit_phone(self, phone):
        self.phones.clear()
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def find_phone(self, phone):
        return next((p.value for p in self.phones if p.value == phone), None)

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def show_birthday(self):
        if self.birthday:
            return f"{self.name.value}'s birthday is on {self.birthday.value.strftime("%d %B %Y")}"
        return f"No information about {self.name.value}'s date of birth"


class AddressBook(UserDict):
    def add_record(self, record):
        if record not in self.data:
            self.data[record] = Record(record)
        return self.data[record]

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        self.data.pop(name, None)

    def birthdays(self):
        birthdays_per_week = defaultdict(list)
        today = datetime.today().date()
        if (today.weekday() == 0):  # якщо сьогодні понеділок, поточний день зміщуємо назад на 2 дні, і функція виведе імена тих, у кого був день народження на попередніх вихідних
            today -= timedelta(days=2)
        else:
            for name, user_record in self.data.items():
                if user_record.birthday is not None:
                    birthday = user_record.birthday.value
                    birthday_this_year = birthday.replace(year=today.year)
                    if birthday_this_year < today:
                        birthday_this_year = birthday.replace(year=today.year + 1)
                    delta_days = (birthday_this_year - today).days
                    if delta_days < 7:
                        birthday_weekday = birthday_this_year.strftime("%A")
                        if birthday_weekday in ["Saturday", "Sunday"]:
                            birthday_weekday = "Monday"
                        birthdays_per_week[birthday_weekday].append(name)
        if birthdays_per_week:
            sorted_birthdays_per_week = OrderedDict(sorted(birthdays_per_week.items()))
            for day, names in sorted_birthdays_per_week.items():
                print(f"{day}: {', '.join(names)}")
        else:
            print(f"There aren't any birthdays next week")

    def save_to_file(self, filename):
        try:
            with open(filename, "wb") as file:
                pickle.dump(self.data, file)
                print("Address book is saved to file")
        except FileNotFoundError:
            print("File not found. Address book isn't saved")
        except PermissionError:
            print("Access to file is denied. Address book isn't saved.")
        except Exception:
            print("Error! Address book isn't saved")

    def read_from_file(self, filename):
        try:
            with open(filename, "rb") as file:
                data = pickle.load(file)
                self.data = data
                print("Adress book is loaded from file")
        except FileNotFoundError:
            print("File not found. Creating a new address book.")
        except PermissionError:
            print("Access to file is denied. Creating a new address book.")
        except Exception:
            print("Error by loadind file. Creating a new address book.")


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DateFormatError:
            return "Please use correct date format DD.MM.YYYY."
        except UnrealDateError:
            return "Please wrire correct date"
        except InvalidNumberError:
            return "Phone number must be 10 digits"
        except ValueError:
            return "Write name and information to work on"
        except IndexError:
            return "Write name for searching"
        except KeyError:
            return "Contact not found"
        except Exception:
            return "An error occurred. Try again"

    return inner


@input_error
def add_contact(args, book):
    name, phone = args
    if name in book.data:
        book.data[name].add_phone(phone)
        return f"Phone added to existed contact {name}"
    else:
        new_contact = book.add_record(name)
        new_contact.add_phone(phone)
        return f"Contact {name} is added."


@input_error
def change_contact(args, book):
    name, phone = args
    if name in book.data:
        changed_contact = book.data[name]
        changed_contact.edit_phone(phone)
        return f"Contact {name} is changed."
    return f"Contact {name} not found."


@input_error
def remove_phone(args, book):
    name, phone = args
    if name in book.data:
        changed_contact = book.data[name]
        if phone in [p.value for p in changed_contact.phones]:
            changed_contact.remove_phone(phone)
            return f"Phone {phone} is removed from {name}'s list of phones."
        return f"Contact {name} does not have phone {phone}."
    return f"Contact {name} not found."


@input_error
def show_contact(args, book):
    name = args[0]
    contact = book.find(name)
    if contact:
        return str(contact)
    return f"Contact {name} not found."


@input_error
def delete_contact(args, book):
    name = args[0]
    contact = book.find(name)
    if contact:
        book.delete(name)
        return f"Contact {name} is deleted"
    return f"Contact {name} not found."


def print_contacts(book):
    if book.data:
        for contact in book.data.values():
            print(contact)
    else:
        print("Contact list is empty")


@input_error
def add_birthday(args, book):
    name, birthday = args
    if name in book.data:
        contact = book.data[name]
        if contact.birthday is None:
            contact.add_birthday(birthday)
            return f"{name}'s date of birth is added"
        elif contact.birthday.value != Birthday(birthday).value:
            contact.add_birthday(birthday)
            return f"{name}'s date of birth is changed"
    return f"Contact {name} not found."


@input_error
def show_birthday(args, book):
    name = args[0]
    contact = book.find(name)
    return contact.show_birthday()


def print_birthdays(book):
    book.birthdays()


def main():
    print("Welcome to the assistant bot!")
    book = AddressBook()
    filename = Path(".") / "Address_book.bin"
    if filename.exists():
        book.read_from_file(filename)
    else:
        print("Creating a new address book")

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            book.save_to_file(filename)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "remove-phone":
            print(remove_phone(args, book))

        elif command == "phone":
            print(show_contact(args, book))

        elif command == "delete":
            print(delete_contact(args, book))

        elif command == "all":
            print_contacts(book)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print_birthdays(book)

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
