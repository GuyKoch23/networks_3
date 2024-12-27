import argparse

def main():
    parser = argparse.ArgumentParser(description="Client parser")
    parser.add_argument('role', choices=['cman', 'spirit', 'watcher'], help="Role")
    parser.add_argument('addr', type=str, help="Server address (IP or hostname)")
    parser.add_argument('-p', '--port', type=int, default=1337, help='Port number to use (default: 1337)')
    args = parser.parse_args()
    print(args.role)


if __name__ == '__main__':
    main()