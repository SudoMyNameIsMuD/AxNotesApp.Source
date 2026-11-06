import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style


def get_color_style():
    if os.getenv("NO_COLOR"):
        return Style.from_dict(
            {
                "prompt": "bold",
                "note": "",
                "command": "",
                "line-number": "",
            }
        )
    return Style.from_dict(
        {
            "prompt": "fg:#00ff00 bold",
            "note": "bg:#eee #000",
            "command": "bg:#222 #fff",
            "line-number": "fg:#888",
        }
    )


slash_commands = WordCompleter(
    [
        "/save",
        "/load",
        "/clear",
        "/exit",
        "/help",
        "/toggle_color",
        "/edit",
        "/delete",
        "/search",
    ],
    ignore_case=True,
)

history = InMemoryHistory()
session = PromptSession(history=history, completer=slash_commands)

kb = KeyBindings()


@kb.add("c-c")
def _(event):
    event.app.exit(exception=KeyboardInterrupt)


@kb.add("c-d")
def _(event):
    event.app.exit(exception=EOFError)


@kb.add("c-l")
def _(event):
    event.app.current_buffer.reset()
    print("Input line cleared.")


@kb.add("c-z")
def _(event):
    event.app.current_buffer.undo()
    print("Undo.")


@kb.add("c-y")
def _(event):
    event.app.current_buffer.redo()
    print("Redo.")


@kb.add("c-s")
def _(event):
    event.app.current_buffer.validate_and_handle()
    notes = history.get_strings()
    if notes:
        filename = "notes.txt"
        with open(filename, "w") as file:
            for note in notes:
                file.write(note + "\n")
        print(f"Notes saved to {filename}")
        sys.exit(0)


def main():
    print("Welcome to the Rich Terminal Note-taking App!")
    print("Type '/save <filename>' to save notes.")
    print("Type '/load <filename>' to load notes.")
    print("Type '/clear' to clear all notes.")
    print("Type '/exit' to exit the app.")
    print("Type '/help' to see available commands.")

    notes = []
    style = get_color_style()

    while True:
        try:
            user_input = session.prompt(">>> ", style=style, key_bindings=kb)
            if user_input.startswith("/"):
                handle_command(user_input, notes, style)
            else:
                notes.append(user_input)
        except Exception as e:
            print(f"An error occurred: {e}")


def handle_command(command, notes, style):
    parts = command.split()
    if not parts:
        return

    cmd = parts[0]
    args = parts[1:]

    if cmd == "/save":
        if len(args) != 1:
            print("Usage: /save <filename>")
            return
        save_notes(args[0], notes)
    elif cmd == "/load":
        if len(args) != 1:
            print("Usage: /load <filename>")
            return
        notes[:] = load_notes(args[0])
    elif cmd == "/clear":
        notes.clear()
        print("Notes cleared.")
    elif cmd == "/exit":
        print("Exiting the application.")
        sys.exit(0)
    elif cmd == "/help":
        print("Available commands:")
        print("/save <filename> - Save notes to a file.")
        print("/load <filename> - Load notes from a file.")
        print("/clear - Clear all notes.")
        print("/exit - Exit the application.")
        print("/help - Show this help message.")
        print("/toggle_color - Toggle color on/off.")
        print("/edit <index> - Edit a note at the given index.")
        print("/delete <index> - Delete a note at the given index.")
        print("/search <query> - Search for notes containing the query.")
    elif cmd == "/toggle_color":
        os.environ["NO_COLOR"] = "1" if "NO_COLOR" not in os.environ else ""
        print("Color toggled.")
    elif cmd == "/edit":
        if len(args) != 1:
            print("Usage: /edit <index>")
            return
        try:
            index = int(args[0])
            if 0 <= index < len(notes):
                new_note = session.prompt(
                    f"Edit note {index}: ",
                    style=style,
                    default=notes[index],
                )
                notes[index] = new_note
            else:
                print("Invalid index.")
        except ValueError:
            print("Please provide a valid index.")
    elif cmd == "/delete":
        if len(args) != 1:
            print("Usage: /delete <index>")
            return
        try:
            index = int(args[0])
            if 0 <= index < len(notes):
                notes.pop(index)
                print(f"Note {index} deleted.")
            else:
                print("Invalid index.")
        except ValueError:
            print("Please provide a valid index.")
    elif cmd == "/search":
        if len(args) != 1:
            print("Usage: /search <query>")
            return
        query = args[0]
        matching_notes = [note for note in notes if query in note]
        if matching_notes:
            print("Matching notes:")
            for note in matching_notes:
                print(note)
        else:
            print("No matching notes found.")
    else:
        print(f"Unknown command: {cmd}")


def save_notes(filename, notes):
    try:
        with open(filename, "w") as file:
            for note in notes:
                file.write(note + "\n")
        print(f"Notes saved to {filename}")
    except IOError as e:
        print(f"Error saving notes: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def load_notes(filename):
    try:
        with open(filename, "r") as file:
            return [line.strip() for line in file.readlines()]
    except IOError as e:
        print(f"Error loading notes: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


if __name__ == "__main__":
    main()
