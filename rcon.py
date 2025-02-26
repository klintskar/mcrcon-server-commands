import time
import re
import os
import threading
from mcrcon import MCRcon

# RCON server configuration
HOST = "localhost"
PORT = 25575
PASSWORD = "Schlevden69"

# Global RCON connection
rcon_connection = None  

# Global thread variable
position_checker_thread = None  

# File paths for saved data
COORDS_FILE = os.path.join(os.path.dirname(__file__), "coords.txt") 
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "logs", "latest.log")
LAST_POSITIONS_FILE = os.path.join(os.path.dirname(__file__), "last_positions.txt") 

# Defined marked areas with names, coordinates, and messages
MARKED_AREAS = {
    "Castle of Schlevden": {"coords": ((-690, 100, -150), (-770, 130, -210)), "message": "Welcome to Schlevden's castle!"},
    "Nice": {"coords": ((69, 69, 69), (70, 70, 70)), "message": "Nice!"}
}

def send_rcon_command(command):
    """Sends an RCON command using a persistent connection."""
    global rcon_connection
    
    if rcon_connection is None:
        try:
            rcon_connection = MCRcon(HOST, PASSWORD, port=PORT)
            rcon_connection.connect()
            print("Connected to RCON")
        except Exception as e:
            print(f"Failed to connect to RCON: {e}")
            return None

    try:
        response = rcon_connection.command(command)
        if not is_thread.value:
            print(f"Executed: {command}")
        return response
    except Exception as e:
        print(f"RCON command failed: {e}")
        return None

def tail_file(filename):
    """Monitors a log file and yields new lines as they are written."""
    with open(filename, "r", encoding="utf-8") as file:
        file.seek(0, 2)  
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

def process_chat_message(line):
    """Processes player chat messages and extracts commands."""
    match = re.search(r"<(.*?)> (.*)", line)  
    if match:
        player, message = match.groups()
        if not is_thread.value:
            print(f"Detected chat: {player}: {message}")
        if message.startswith("!"):  
            handle_command(player, message[1:])  

def load_last_positions():
    """Loads the last recorded player positions and areas they entered."""
    if not os.path.exists(LAST_POSITIONS_FILE):
        return {}

    last_positions = {}
    with open(LAST_POSITIONS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(":")
            if len(parts) == 2:
                player, last_area = parts[0].strip(), parts[1].strip()
                last_positions[player] = last_area
    return last_positions

def save_last_position(player, area_name):
    """Saves the last recorded area the player entered."""
    last_positions = load_last_positions()
    last_positions[player] = area_name

    with open(LAST_POSITIONS_FILE, "w", encoding="utf-8") as file:
        for p, a in last_positions.items():
            file.write(f"{p}:{a}\n")

def check_player_positions():
    """Checks player positions and sends messages if they enter a marked area."""
    global rcon_connection
    
    last_positions = {}

    try:
        if rcon_connection is None:
            send_rcon_command("list")
            return  

        while True:
            response = rcon_connection.command("list")
            players = response.split(":")[-1].strip().split(", ") if ":" in response else []

            for player in players:
                if not player:
                    continue

                coords = get_player_coords(player)
                if not coords:
                    continue

                x, y, z = coords
                current_area = None

                for area_name, area in MARKED_AREAS.items():
                    (x1, y1, z1), (x2, y2, z2) = area["coords"]
                    if min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2) and min(z1, z2) <= z <= max(z1, z2):
                        current_area = area_name
                        break

                last_area = last_positions.get(player, None)
                if current_area and last_area != current_area:
                    rcon_connection.command(f"tell {player} {MARKED_AREAS[current_area]['message']}")
                    last_positions[player] = current_area
                    save_last_position(player, current_area)

            time.sleep(2)

    except Exception as e:
        print(f"Error in position checker: {e}")

def get_player_coords(player):
    """Gets a player's coordinates using RCON."""
    response = send_rcon_command(f"data get entity {player} Pos")
    numbers = re.findall(r'[-+]?[0-9]*.?[0-9]+d', response)
    
    if len(numbers) < 3:
        print(f"Error: Could not extract 3 position values for {player}.")
        return None

    x, y, z = map(round, [float(num[:-1]) for num in numbers])
    if not is_thread.value:
        print(f"Extracted and rounded coordinates: {x}, {y}, {z}")
    return x, y, z

def save_coords(player, name, x, y, z):
    """Saves a coordinate under the player's name."""
    with open(COORDS_FILE, "a", encoding="utf-8") as file:
        file.write(f"{player},{name},{x},{y},{z}\n")

def get_coords(player):
    """Retrieves saved coordinates for a player."""
    coords = {}
    if not os.path.exists(COORDS_FILE):
        return coords

    with open(COORDS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(",")
            if len(parts) != 5:
                if not is_thread.value:
                    print(f"Skipping malformed line: {line.strip()}")
                continue  
            saved_player, name, x, y, z = parts
            if saved_player == player:
                coords[name] = (x, y, z)

    return coords

def remove_coords(player, name):
    """Removes a saved coordinate for a player."""
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

def handle_command(player, command_str):
    """Parses and executes commands from chat."""
    if not is_thread.value:
        print(f"Handling command: {command_str} from {player}")  

    parts = command_str.split()
    if not parts:
        return

    command = parts[0].lower()  
    args = parts[1:]  

    if command == "broadcast" and args:
        send_rcon_command(f"say {' '.join(args)}")

    elif command == "help":
        help_messages = [
            "!broadcast <message> - Send a server-wide message",
            "!coords help - Show all coords commands",
            "!weather <clear | rain | thunder> - Sets the weather",
            "!help - Show this command list"
        ]
        for msg in help_messages:
            send_rcon_command(f"tell {player} {msg}")

    elif command == "weather" and len(args) == 1:
        weather_type = args[0]
        if weather_type in ["clear", "rain", "thunder"]:
            send_rcon_command(f"weather {weather_type}")
            send_rcon_command(f"tell {player} Weather changed to {weather_type}.")
        else:
            send_rcon_command(f"tell {player} Invalid weather type.")
    
    elif command == "coords":
        
        sub_command = args[0].lower()

        if sub_command == "add" and len(args) == 5:
            name, x, y, z = args[1], args[2], args[3], args[4]
            save_coords(player, name, x, y, z)
            send_rcon_command(f"tell {player} Saved {name} at ({x}, {y}, {z}).")

        elif sub_command == "add" and len(args) == 3 and args[2] == "current":
            name = args[1]
            coords = get_player_coords(player)
            if coords:
                x, y, z = coords
                save_coords(player, name, x, y, z)
                send_rcon_command(f"tell {player} Saved {name} at your current location {coords}.")
            else:
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
                for name, (x, y, z) in coords.items():
                    send_rcon_command(f"tell {player} {name}: ({x}, {y}, {z})")
        
        elif sub_command == "help":
            help_message = [
                "Coords Command Usage:",
                "!coords add <name> <x> <y> <z> - Save a coordinate with a name",
                "!coords add <name> current - Save current currdinates with a name",
                "!coords remove <name> - Remove a saved coordinate",
                "!coords show - Show all your saved coordinates",
                "!coords help - Show this help message"
            ]
            for msg in help_message:
                send_rcon_command(f"tell {player} {msg}")

        elif not args:
            send_rcon_command(f"tell {player} Use '!coords help' for usage.")
            return

    else:
        send_rcon_command(f"tell {player} Unknown command or wrong format!")
    
is_thread = threading.local()
is_thread.value = False

def thread_function():
    """Runs the position checker in a separate thread."""
    is_thread.value = True
    check_player_positions()

if position_checker_thread is None or not position_checker_thread.is_alive():
    position_checker_thread = threading.Thread(target=thread_function, daemon=True)
    position_checker_thread.start()
    print("Position checker started. Monitoring player locations...")

print("Listening for commands in chat...")
for log_line in tail_file(LOG_FILE_PATH):
    process_chat_message(log_line)