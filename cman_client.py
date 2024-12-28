import argparse
import socket
import message_util
import cman_utils
from enum import IntEnum
import cman_game_map

class ClientRole(IntEnum):
    WATCHER = 0
    CMAN = 1
    SPIRIT = 2

class GameClient:
    def __init__(self, server_host, server_port, role):
        self.server_address = (server_host, server_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.role = ClientRole[role.upper()]
        self.can_move = False
        self.running = True
        self.map_path = "map.txt"

        self.movement_keys = {
            'w': 0,  # UP
            'a': 1,  # LEFT
            's': 2,  # DOWN
            'd': 3   # RIGHT
        }


    def send_message(self, data):
        try:
            self.socket.sendto(data, self.server_address)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.cleanup()

    def receive_message(self):
        try:
            data, _ = self.socket.recvfrom(1024)
            return message_util.decode_message(data)
        except socket.timeout:
            raise socket.timeout
        except Exception as e:
            print(f"Error receiving message: {e}")
            self.cleanup()
            return None
        
    def cleanup(self, message=""):
        if message:
            print(message)
        self.socket.close()
        self.running = False


    def handle_game_state(self, state_data):
        cman_utils.clear_print()
        cman_game_map.print_map(self.map_path, state_data)
        freeze, coords_c, coords_s, attempts, collected = state_data
        self.can_move = not freeze if self.role != ClientRole.WATCHER else False

    def join_game(self):
        join_message = message_util.create_join_message(self.role)
        self.send_message(join_message)
        
        response = self.receive_message()
        message_type = response[0]

        if message_type == message_util.OPCODE_ERROR:
            self.cleanup(response[1])
            return False

        if message_type == message_util.OPCODE_GAME_STATE_UPDATE:
            state_data = response[1:]      
            self.handle_game_state(state_data)
        return True
    
    def check_movement(self):
        if not self.can_move:
            return
            
        pressed = cman_utils.get_pressed_keys(list(self.movement_keys.keys()))
        if pressed:
            direction = self.movement_keys[pressed[0]]
            move_message = message_util.create_player_movement_message(direction)
            self.send_message(move_message)

    def check_quit(self):
        if 'q' in cman_utils.get_pressed_keys(['q']):
            quit_message = message_util.create_quit_message()
            self.send_message(quit_message)
            self.running = False
            return True
        return False

    def handle_game_end(self, end_data):
        winner, spirit_score, cman_score = end_data
        cman_utils.clear_print("\nGame Over!")
        cman_utils.clear_print(f"Winner: {'Cman' if winner == ClientRole.CMAN else 'Spirit'}")
        cman_utils.clear_print(f"Final Scores:")
        cman_utils.clear_print(f"Cman: {cman_score} points")
        cman_utils.clear_print(f"Spirit: {spirit_score} catches")
        self.running = False

    def run(self):
        if not self.join_game():
            self.cleanup()
            return

        while self.running:
            try:
                if self.check_quit():
                    break
                self.check_movement()
                self.socket.settimeout(0.1)
                try:
                    response = self.receive_message()
                    if response:
                        message_type = response[0]
                        if message_type == message_util.OPCODE_ERROR:
                            print(f"Error: {response[1]}")
                            break
                        elif message_type == message_util.OPCODE_GAME_STATE_UPDATE:
                            self.handle_game_state(response[1:])
                        elif message_type == message_util.OPCODE_GAME_END:
                            self.handle_game_end(response[1:])
                            break
                except socket.timeout:
                    pass
            except Exception as e:
                print(f"Error in game loop: {e}")
                break

        self.cleanup()

def main():
    parser = argparse.ArgumentParser(description="Client parser")
    parser.add_argument('role', choices=['cman', 'spirit', 'watcher'],
                      help='Role to play as (cman/ghost/watcher)')
    parser.add_argument('addr', type=str, help="Server address (IP or hostname)")
    parser.add_argument('-p','--port', type=int, default=1337, help='Port number to use (default: 1337)')

    args = parser.parse_args()
    
    client = GameClient(args.addr, args.port, args.role)
    client.run()

if __name__ == "__main__":
    main()