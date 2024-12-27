import argparse
import socket
import cman_game as game
from enum import IntEnum
import json
import time
import message_util

# def reset_game():
#     pass

# def is_game_started():
#     pass

# def send_clients_game_status(clients):
#     pass

# def perform_player_move(role, move):
#     pass

# def start_game():
#     pass

# def handle_client_exit(client_address):
#     pass

# def is_role_occupied(role):
#     pass

# def send_client_role_occupied_message(role, client_address):
#     pass

# def announce_victory_to_clients(role):
#     pass


# def set_client_role(role, client_address):
#     pass

# def remove_cman_role():
#     pass

# def remove_spirit_role():
#     pass

# def remove_watcher_role(client_address):
#     pass

# def clear_client_role(client_address):
#     pass


class ClientRole(IntEnum):
    WATCHER = 0
    CMAN = 1
    SPIRIT = 2

class GameServer:
    def __init__(self, port=1337):
        self.port = port
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_udp.bind(('127.0.0.1', port))
        map_path = "map.txt"
        
        self.game = game.Game(map_path)
        
        self.clients = {}  # {address: role}
        self.role_assignments = {
            ClientRole.CMAN: None,
            ClientRole.SPIRIT: None
        }
        
        self.game_active = False
        self.last_game_end = 0

    def start_new_game(self):
        self.game.restart_game()
        self.role_assignments = {
            ClientRole.CMAN: None,
            ClientRole.SPIRIT: None
        }
        self.clients = {addr: role for addr, role
                       in self.clients.items() if role == ClientRole.WATCHER}
        self.broadcast_state()

    def handle_game_end(self):
        self.game_active = False
        self.last_game_end = time.time()
        
        for _ in range(10):
            data = self.build_end_game_message()
            for client_addr in self.clients.keys():
                self.send_message(client_addr, data)
            time.sleep(1)

        self.start_new_game()


    def broadcast_state(self):
        for client_addr in self.clients.keys():
            role = self.clients[client_addr]
            data = self.build_update_state_message(role)
            self.send_message(client_addr, data)

    def handle_disconnect(self, client_addr):
        if client_addr not in self.clients:
            data = self.build_disconnect_response("Client is not player", message_util.ERROR)
            self.send_message(client_addr, data)
            return
            
        role = self.clients[client_addr]
        del self.clients[client_addr]
        
        if role in [ClientRole.CMAN, ClientRole.SPIRIT]:
            self.role_assignments[role] = None
            if self.game_active:
                winner = game.Player.SPIRIT if role == ClientRole.CMAN else game.Player.CMAN
                self.game.declare_winner(winner)
                self.handle_game_end()
        return


    def build_disconnect_response(self, message, message_type):
        data = message_util.create_error_message(message)
        return data



    def handle_move(self, client_addr, direction):
        if not client_addr in self.clients.keys():
            data = self.build_move_response("Client is not a player", message_util.ERROR, None)

        if not client_addr in self.role_assignments.values():
            data = self.build_move_response("Client is a watcher and cannot move", message_util.ERROR, None)
        
        if not self.game_active:
            data = self.build_move_response("Game is not active", message_util.ERROR, None)
            
        client_role = self.clients[client_addr]

        player = game.Player.CMAN if client_role == ClientRole.CMAN else game.Player.SPIRIT
        
        direction = game.Direction(data.get('direction'))

        if self.game.apply_move(player, direction):
            self.broadcast_state()
            if self.game.state == game.State.WIN:
                self.handle_game_end()
        else:
            data = self.build_move_response("Move didnt apply", message_util.ERROR, None)
        
        self.send_message(client_addr, data)


    def build_move_response(self, message, message_type, role):
        if message_type == message_util.ERROR:
            data = message_util.create_error_message(message)
        return data

    def handle_join_request(self, client_addr, role):
        if not role in ClientRole.__members__:
            message = "role does not exist"
            message_type = message_util.ERROR
            data = self.build_join_response(message, message_type, role)
            return data
 
        requested_role = ClientRole(role)
        
        if requested_role in [ClientRole.CMAN, ClientRole.SPIRIT]:
            if self.game_active:
                message = "game has already started"
                message_type = message_util.ERROR
            elif self.role_assignments[requested_role] is not None:
                message = "role is taken"
                message_type = message_util.ERROR
            else:
                self.role_assignments[requested_role] = client_addr
                self.clients[client_addr] = requested_role
                message = "join accepted!"
                message_type = message_util.UPDATE

                if all(assignment is not None for assignment in self.role_assignments.values()):
                    self.game_active = True
                    self.game.state = game.State.START
        else:
            self.clients[client_addr] = requested_role
            message = "join accepted!"
            message_type = message_util.UPDATE

        data = self.build_join_response(message, message_type, role)
        self.send_message(client_addr, data)
    
    def build_end_game_message(self):
        winner = self.game.get_winner() + 1 # +1 for mapping ClientRole to Player enum according to pdf reqs
        progress = self.game.get_game_progress()
        s_score = 3 - progress[0]
        c_score = progress[1]
        return message_util.create_game_end_message(winner, s_score, c_score)


    def build_update_state_message(self, role):
        if role == ClientRole.WATCHER:
            freeze = 1
        else:
            freeze = self.game.can_move(role-1) # -1 for mapping ClientRole to Player enum
        coords_c = self.game.get_current_players_coords()[0]
        coords_s = self.game.get_current_players_coords()[1]
        attempts = 3 - self.game.lives
        collected = self.game.get_points().values()
        return message_util.create_game_state_update_message(freeze, coords_c, coords_s, attempts, collected)

    def build_join_response(self, message, message_type, role):
        if message_type == message_util.ERROR:
            data = message_util.create_error_message(message)
        elif message_type == message_util.UPDATE:
            data = self.build_update_state_message(role)
        
        return data

    def send_message(self, client_address, data):
        self.socket_udp.sendto(data.encode(), client_address)


    def run(self):        
        while True:
            try:
                data, addr = self.socket_udp.recvfrom(1024)
                message = message_util.decode_message(data)
                                
                if message[0] == message_util.JOIN:
                    self.handle_join_request(addr, message[1])
                elif message[0] == message_util.MOVE:
                    self.handle_move(addr, message[1])
                elif message[0] == message_util.QUIT:
                    self.handle_disconnect(addr)
                                
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="My great parser")
    parser.add_argument('-p', type=int, default=1337, help='Port number to use (default: 1337)')
    args = parser.parse_args()

    host = '127.0.0.1'
    port = args.port

    server = GameServer(args.port)
    server.run()

if __name__ == '__main__':
    main()