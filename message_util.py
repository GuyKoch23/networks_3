import struct

OPCODE_JOIN_REQUEST = 0x00  # Client->Server
OPCODE_PLAYER_MOVEMENT = 0x01  # Client->Server
OPCODE_QUIT = 0x0F  # Client->Server
OPCODE_GAME_STATE_UPDATE = 0x80  # Server->Client
OPCODE_GAME_END = 0x8F  # Server->Client
OPCODE_ERROR = 0xFF  # Server->Client


def create_join_message(role):
    return struct.pack('!BB', OPCODE_JOIN_REQUEST, role)

def create_player_movement_message(direction):
    return struct.pack('!BB', OPCODE_PLAYER_MOVEMENT, direction)

def create_quit_message():
    return struct.pack('!B', OPCODE_QUIT)

def create_game_state_update_message(freeze, coords_c, coords_s, attempts, collected):
    return struct.pack('!BBBBBBB', OPCODE_GAME_STATE_UPDATE, freeze, coords_c[0], coords_c[1], coords_s[0], coords_s[1], attempts) + collected

def create_game_end_message(winner, score_s, score_c):
    return struct.pack('!BBBB', OPCODE_GAME_END, winner, score_s, score_c)

def create_error_message(error_data):
    error_data_bytes = error_data.encode('utf-8')
    return struct.pack(f'!B36s', OPCODE_ERROR, error_data_bytes)


def decode_message(data):
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
    opcode, role = struct.unpack('!BB', data)

    return OPCODE_JOIN_REQUEST, role

def decode_player_movement_message(data):
    opcode, direction = struct.unpack('!BB', data)

    return OPCODE_PLAYER_MOVEMENT, direction

def decode_quit_message(data):
    opcode = struct.unpack('!B', data)[0]

    return OPCODE_QUIT, None

def decode_game_state_update_message(data):
    opcode, freeze, coords_c_x, coords_c_y, coords_s_x, coords_s_y, attempts = struct.unpack('!BBBBBBB', data[:7])

    # Extract the last 5 bytes for the collected value (40 bits)
    collected_bytes = data[7:12]
    collected = int.from_bytes(collected_bytes, byteorder='big')
    
    return OPCODE_GAME_STATE_UPDATE, freeze, (coords_c_x, coords_c_y), (coords_s_x, coords_s_y), attempts, collected

def decode_game_end_message(data):    
    opcode, winner, score_s, score_c = struct.unpack('!BBBB', data)

    return OPCODE_GAME_END, winner, score_s, score_c

def decode_error_message(data):
    opcode = struct.unpack('!B', data[:1])[0]
    error_data = data[1:]

    return OPCODE_ERROR, error_data
