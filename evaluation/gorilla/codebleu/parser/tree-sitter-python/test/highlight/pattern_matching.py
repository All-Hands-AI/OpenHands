match command.split():
# ^ keyword
    case ["quit"]:
    # ^ keyword
        print("Goodbye!")
        quit_game()
    case ["look"]:
    # ^ keyword
        current_room.describe()
    case ["get", obj]:
    # ^ keyword
        character.get(obj, current_room)
    case ["go", direction]:
    # ^ keyword
        current_room = current_room.neighbor(direction)
    # The rest of your commands go here

match command.split():
# ^ keyword
    case ["drop", *objects]:
    # ^ keyword
        for obj in objects:
            character.drop(obj, current_room)

match command.split():
# ^ keyword
    case ["quit"]: ... # Code omitted for brevity
    case ["go", direction]: pass
    case ["drop", *objects]: pass
    case _:
        print(f"Sorry, I couldn't understand {command!r}")

match command.split():
# ^ keyword
    case ["north"] | ["go", "north"]:
    # ^ keyword
        current_room = current_room.neighbor("north")
    case ["get", obj] | ["pick", "up", obj] | ["pick", obj, "up"]:
    # ^ keyword
        pass

match = 2
#   ^ variable
match, a = 2, 3
#   ^ variable
match: int = secret
#   ^ variable
x, match: str = 2, "hey, what's up?"
# <- variable
#   ^ variable

if match := re.fullmatch(r"(-)?(\d+:)?\d?\d:\d\d(\.\d*)?", time, flags=re.ASCII):
    # ^ variable
    return match
