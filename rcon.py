import time
import re
import os
from mcrcon import MCRcon
import threading

HOST = "localhost"  # Change to server IP if running remotely
PORT = 25575
PASSWORD = "Schlevden69"

COORDS_FILE = "coords.txt"

LOG_FILE_PATH = r"C:\Users\jacob\Desktop\testserver\logs\latest.log"

# Function to send RCON commands
def send_rcon_command(command):
    """Send a command to the Minecraft server via RCON."""
    with MCRcon(HOST, PASSWORD, port=PORT) as mcr:
        response = mcr.command(command)
        print(f"Executed: {command}")
        return response

# Function to monitor the chat log
def tail_file(filename):
    """Continuously reads new lines from the log file."""
    with open(filename, "r", encoding="utf-8") as file:
        file.seek(0, 2)  # Move to end of file
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

# Function to process chat messages
def process_chat_message(line):
    match = re.search(r"<(.*?)> (.*)", line)  # Matches "<PlayerName> Message"
    if match:
        player, message = match.groups()
        print(f"Detected chat: {player}: {message}")
        if message.startswith("!"):  # Only process messages that start with "!"
            handle_command(player, message[1:])  # Remove "!" and process

import time
import threading
import os

# Define marked areas: Name, Coordinates (2 corners), Message
MARKED_AREAS = {
    "Jacobs House": {"coords": ((100, 64, 200), (120, 80, 220)), "message": "Welcome to Jacob's House!"},
    "Spawn Area": {"coords": ((0, 64, 0), (20, 80, 20)), "message": "You have entered Spawn!"},
    "Hidden Cave": {"coords": ((-50, 20, -50), (-30, 40, -30)), "message": "You discovered a Hidden Cave!"}
}

LAST_POSITIONS_FILE = "last_positions.txt"  # Stores last triggered messages

def load_last_positions():
    """Loads the last recorded player positions and areas they triggered."""
    if not os.path.exists(LAST_POSITIONS_FILE):
        return {}

    last_positions = {}
    with open(LAST_POSITIONS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(":")
            if len(parts) == 2:
                player = parts[0].strip()  # Ensure no extra spaces
                last_area = parts[1].strip()  # Strip any spaces around area names
                last_positions[player] = last_area
    return last_positions


def save_last_position(player, area_name):
    """Saves the last recorded area the player entered to prevent message spam."""
    last_positions = load_last_positions()
    last_positions[player] = area_name

    with open(LAST_POSITIONS_FILE, "w", encoding="utf-8") as file:
        for p, a in last_positions.items():
            file.write(f"{p}:{a}\n")

def check_player_positions():
    """Continuously checks if players enter a marked area and sends messages once."""
    last_positions = load_last_positions()  # Load saved positions at startup

    while True:
        response = send_rcon_command("list")
        if ":" in response:
            players = response.split(":")[-1].strip().split(", ")
        else:
            players = []

        for player in players:
            if not player:
                continue  # Skip empty names

            coords = get_player_coords(player)
            if not coords:
                continue  # Skip if no position found

            x, y, z = coords
            print(f"Checking {player}'s position: {x}, {y}, {z}")

            current_area = None  # Track which area the player is in

            for area_name, area in MARKED_AREAS.items():
                (x1, y1, z1), (x2, y2, z2) = area["coords"]

                x_min, x_max = min(x1, x2), max(x1, x2)
                y_min, y_max = min(y1, y2), max(y1, y2)
                z_min, z_max = min(z1, z2), max(z1, z2)

                if x_min <= x <= x_max and y_min <= y <= y_max and z_min <= z <= z_max:
                    current_area = area_name  # The player is inside this area
                    break  # Stop checking once an area is found

            last_area = last_positions.get(player, "None")  # Default to "None" if not found

            if current_area and last_area != current_area:  # Only send message if it's a new area
                send_rcon_command(f"tell {player} {MARKED_AREAS[current_area]['message']}")
                print(f"Sent message to {player}: {MARKED_AREAS[current_area]['message']}")
                last_positions[player] = current_area
                save_last_position(player, current_area)  # Save new area

            elif not current_area:  # If the player is not in any area, reset last position
                last_positions[player] = "None"

        time.sleep(2)  # Check every 2 seconds


def get_player_coords(player):
    """Gets the player's current coordinates using RCON."""
    response = send_rcon_command(f"data get entity {player} Pos")
    print(f"DEBUG: Full RCON Response -> {repr(response)}")  # Shows raw response

    numbers = re.findall(r'[-+]?[0-9]*.?[0-9]+d', response)
    cleaned_numbers = [float(num[:-1]) for num in numbers]
    x, y, z = cleaned_numbers
    x, y, z = round(float(x)), round(float(y)), round(float(z))

    print(f"Extracted and rounded coordinates: {x}, {y}, {z}")  # Debugging output
    return x, y, z

    # Return early to prevent crashing while testing
    return None

def save_coords(player, name, x, y, z):
    """Saves a coordinate under the player's name in coords.txt."""
    with open(COORDS_FILE, "a", encoding="utf-8") as file:
        file.write(f"{player},{name},{x},{y},{z}\n")

def get_coords(player):
    """Returns a dictionary of saved coordinates for a specific player."""
    coords = {}
    if not os.path.exists(COORDS_FILE):
        return coords

    with open(COORDS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(",")

            # Ensure the line has exactly 5 parts (player, name, x, y, z)
            if len(parts) != 5:
                print(f"Skipping malformed line: {line.strip()}")
                continue  # Skip this line

            saved_player, name, x, y, z = parts

            # Only add coordinates that belong to the requesting player
            if saved_player == player:
                coords[name] = (x, y, z)

    return coords

def remove_coords(player, name):
    """Removes a specific coordinate for a player."""
    if not os.path.exists(COORDS_FILE):
        return False

    new_lines = []
    removed = False

    with open(COORDS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(",")
            if len(parts) == 5 and parts[0] == player and parts[1] == name:
                removed = True
            else:
                new_lines.append(line.strip())

    if removed:
        with open(COORDS_FILE, "w", encoding="utf-8") as file:
            for line in new_lines:
                file.write(line + "\n")

    return removed

# Function to handle commands
def handle_command(player, command_str):
    """Parses and executes commands from chat."""
    print(f"Handling command: {command_str} from {player}")  # Debug line

    parts = command_str.split()
    if len(parts) == 0:
        return

    command = parts[0].lower()  # Extract command name
    args = parts[1:]  # Extract arguments

    if command == "broadcast" and len(args) > 0:
        message = " ".join(args)
        send_rcon_command(f"say {message}")

    elif command == "help":
        command_list = [
            "!broadcast <message> - Send a server-wide message",
            "!coords help - Show all coords commands",
            "!help - Show this command list"
        ]
        for cmd in command_list:
            send_rcon_command(f"tell {player} {cmd}")
    
    elif command == "coords" and len(args) > 0:
        sub_command = args[0].lower()

        if sub_command == "add" and len(args) == 5:
            name, x, y, z = args[1], args[2], args[3], args[4]
            save_coords(player, name, x, y, z)
            send_rcon_command(f"tell {player} Saved {name} at ({x}, {y}, {z}).")

        elif sub_command == "add" and len(args) == 3 and args[1] == "current":
            name = args[2]
            print(f"Command recognized: !coords add current {name} from {player}")  # Debugging

            coords = get_player_coords(player)  # This should trigger a debug message
            if coords:
                x, y, z = coords
                print(f"Coordinates fetched: {x}, {y}, {z}")  # Debugging
                save_coords(player, name, x, y, z)
                send_rcon_command(f"tell {player} Saved {name} at your current location ({x}, {y}, {z}).")
            else:
                print(f"Failed to fetch coordinates for {player}")  # Debugging
                send_rcon_command(f"tell {player} Could not get your current location.")

        elif sub_command == "remove" and len(args) == 2:
            name = args[1]
            if remove_coords(player, name):
                send_rcon_command(f"tell {player} Removed saved location '{name}'.")
            else:
                send_rcon_command(f"tell {player} No location named '{name}' found.")

        elif sub_command == "show":
            coords = get_coords(player)
            if not coords:
                send_rcon_command(f"tell {player} You have no saved locations you lobotomized ant.")
            else:
                send_rcon_command(f"tell {player} Your saved locations:")
                for name, coord in coords.items():  # coord is now a tuple (x, y, z)
                    if len(coord) == 3:  # Extra safety check
                        x, y, z = coord
                        send_rcon_command(f"tell {player} {name}: ({x}, {y}, {z})")
                    else:
                        send_rcon_command(f"tell {player} Error reading saved location '{name}'")
        
        elif sub_command == "help":
            help_message = [
                "Coords Command Usage:",
                "!coords add <name> <x> <y> <z> - Save a coordinate with a name",
                "!coords add current <name> - Save current currdinates with a name",
                "!coords remove <name> - Remove a saved coordinate",
                "!coords show - Show all your saved coordinates",
                "!coords help - Show this help message"
            ]
            for msg in help_message:
                send_rcon_command(f"tell {player} {msg}")

    else:
        send_rcon_command(f"tell {player} Unknown command or wrong format!")

# Start the position checker in a separate thread
position_checker_thread = threading.Thread(target=check_player_positions, daemon=True)
position_checker_thread.start()

print("Position checker started. Monitoring player locations...")

# Start monitoring the chat log
print("Listening for commands in chat...")
for log_line in tail_file(LOG_FILE_PATH):
    process_chat_message(log_line)