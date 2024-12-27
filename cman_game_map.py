CMAN_CHAR = 'C'
SPIRIT_CHAR = 'S'
PLAYER_CHARS = [CMAN_CHAR, SPIRIT_CHAR]
POINT_CHAR = 'P'
FREE_CHAR = 'F'
PASS_CHARS = [CMAN_CHAR, SPIRIT_CHAR, POINT_CHAR, FREE_CHAR]
WALL_CHAR = 'W'
MAX_POINTS = 40

def read_map(path):
    """

    Reads map data and asserts that it is valid.

    Parameters:

    path (str): path to the textual map file

    """
    with open(path, 'r') as f:
        map_data = f.read()

        map_chars = set(map_data)
        assert map_chars.issubset({CMAN_CHAR, SPIRIT_CHAR, POINT_CHAR, WALL_CHAR, FREE_CHAR, '\n'}), "invalid char in map."
        assert map_data.count(CMAN_CHAR) == 1, "Map needs to have a single C-Man starting point."
        assert map_data.count(SPIRIT_CHAR) == 1, "Map needs to have a single Spirit starting point."
        assert map_data.count(POINT_CHAR) == MAX_POINTS, f"Map needs to have {MAX_POINTS} score points."

        map_lines = map_data.split('\n')
        assert all(len(line) == len(map_lines[0]) for line in map_lines), "map is not square."
        assert len(map_lines) < 2**8, "map is too tall"
        assert len(map_lines[0]) < 2**8, "map is too wide"

        sbc = all(line.startswith(WALL_CHAR) and line.endswith(WALL_CHAR) for line in map_lines)
        tbc = map_lines[0] == WALL_CHAR*len(map_lines[0]) and map_lines[-1] == WALL_CHAR*len(map_lines[-1])
        bbc = map_lines[0] == WALL_CHAR*len(map_lines[0]) and map_lines[-1] == WALL_CHAR*len(map_lines[-1])
        assert sbc and tbc and bbc, "map border is open."

        return map_data
    
def print_map(path):
    visual_mapping = {
        FREE_CHAR: ' ',  # Free space
        WALL_CHAR: '█',  # Wall
        POINT_CHAR: '•',  # Point
        CMAN_CHAR: CMAN_CHAR,  # Player C start
        SPIRIT_CHAR: SPIRIT_CHAR   # Player S start
    }
    
    try:
        map_data = read_map(path)
        map_lines = map_data.split('\n')
        
        print("Game Board:")
        print("=" * 30)
        
        for line in map_lines:
            visual_line = ''.join(visual_mapping.get(char, char) for char in line)
            print(visual_line)
        
        print("=" * 30)
    
    except AssertionError as e:
        print(f"Map validation error: {e}")
    except FileNotFoundError:
        print("Error: The file does not exist.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

print_map("map.txt")