import struct

OPCODE_JOIN_REQUEST = 0x00  # Client->Server
OPCODE_PLAYER_MOVEMENT = 0x01  # Client->Server
OPCODE_QUIT = 0x0F  # Client->Server
OPCODE_GAME_STATE_UPDATE = 0x80  # Server->Client
OPCODE_GAME_END = 0x8F  # Server->Client
OPCODE_ERROR = 0xFF  # Server->Client
MOVE = 'move'
JOIN = 'join'
QUIT = 'quit'
ERROR = 'error'
UPDATE = 'update'
GAMEEND = 'gameend'


def create_join_message(role):
    if not (0 <= role <= 2):
        raise ValueError("Role must be 0 (Observer), 1 (Cman), or 2 (Spirit).")
    
    return struct.pack('!BB', OPCODE_JOIN_REQUEST, role)

def create_player_movement_message(direction):
    if not (0 <= direction <= 3):
        raise ValueError("Direction must be 0 (Up), 1 (Left), 2 (Down), or 3 (Right).")
    
    return struct.pack('!BB', OPCODE_PLAYER_MOVEMENT, direction)

def create_quit_message():
    return struct.pack('!B', OPCODE_QUIT)

def create_game_state_update_message(freeze, coords_c, coords_s, attempts, collected):
    if not (0 <= freeze <= 1):
        raise ValueError("Freeze must be 0 or 1.")
    if not (0 <= collected < (1 << 40)):  # Ensure collected fits 40 bits
        raise ValueError("Collected must be a 40-bit integer.")
    
    collected_bytes = collected.to_bytes(5, byteorder='big')
    return struct.pack('!BBHHHB', OPCODE_GAME_STATE_UPDATE, freeze, coords_c[0], coords_c[1], coords_s[0], coords_s[1], attempts) + collected_bytes

def create_game_end_message(winner, score_s, score_c):
    if not (1 <= winner <= 2):
        raise ValueError("Winner must be 1 (Cman) or 2 (Spirit).")
    
    return struct.pack('!BBBB', OPCODE_GAME_END, winner, score_s, score_c)

def create_error_message(error_data):
    if len(error_data) != 11:
        raise ValueError("Error data must be exactly 11 bytes.")
    
    return struct.pack('!B', OPCODE_ERROR) + error_data


def decode_message(data):
    if len(data) == 0:
        raise ValueError("Data is empty.")
    
    # Get the first byte (opcode) from the data
    opcode = data[0]
    # Dispatch based on the opcode
    if opcode == OPCODE_JOIN_REQUEST:
        return decode_join_message(data)
    elif opcode == OPCODE_PLAYER_MOVEMENT:
        return decode_player_movement_message(data)
    elif opcode == OPCODE_QUIT:
        return decode_quit_message(data)
    elif opcode == OPCODE_GAME_STATE_UPDATE:
        return decode_game_state_update_message(data)
    elif opcode == OPCODE_GAME_END:
        return decode_game_end_message(data)
    elif opcode == OPCODE_ERROR:
        return decode_error_message(data)
    else:
        raise ValueError(f"Unknown opcode: {hex(opcode)}")
    
def decode_join_message(data):
    if len(data) != 2:
        raise ValueError("Join message must be exactly 2 bytes.")
    
    opcode, role = struct.unpack('!BB', data)
    if opcode != OPCODE_JOIN_REQUEST:
        raise ValueError("Invalid opcode for join message.")
    
    return JOIN, role

def decode_player_movement_message(data):
    if len(data) != 2:
        raise ValueError("Player movement message must be exactly 2 bytes.")
    
    opcode, direction = struct.unpack('!BB', data)
    if opcode != OPCODE_PLAYER_MOVEMENT:
        raise ValueError("Invalid opcode for player movement message.")
    
    return MOVE, direction

def decode_quit_message(data):
    if len(data) != 1:
        raise ValueError("Quit message must be exactly 1 byte.")
    
    opcode = struct.unpack('!B', data)[0]
    if opcode != OPCODE_QUIT:
        raise ValueError("Invalid opcode for quit message.")
    
    return QUIT

def decode_game_state_update_message(data):
    if len(data) < 14:
        raise ValueError("Game state update message must be at least 14 bytes.")
    
    opcode, freeze, coords_c_x, coords_c_y, coords_s_x, coords_s_y, attempts = struct.unpack('!BBHHHB', data[:9])
    if opcode != OPCODE_GAME_STATE_UPDATE:
        raise ValueError("Invalid opcode for game state update message.")
    
    # Extract the last 5 bytes for the collected value (40 bits)
    collected_bytes = data[9:14]
    collected = int.from_bytes(collected_bytes, byteorder='big')
    
    return freeze, (coords_c_x, coords_c_y), (coords_s_x, coords_s_y), attempts, collected

def decode_game_end_message(data):
    if len(data) != 4:
        raise ValueError("Game end message must be exactly 4 bytes.")
    
    opcode, winner, score_s, score_c = struct.unpack('!BBBB', data)
    if opcode != OPCODE_GAME_END:
        raise ValueError("Invalid opcode for game end message.")
    
    return winner, score_s, score_c

def decode_error_message(data):
    if len(data) != 12:
        raise ValueError("Error message must be exactly 12 bytes.")
    
    opcode = struct.unpack('!B', data[:1])[0]
    if opcode != OPCODE_ERROR:
        raise ValueError("Invalid opcode for error message.")
    
    error_data = data[1:]
    
    return error_data
