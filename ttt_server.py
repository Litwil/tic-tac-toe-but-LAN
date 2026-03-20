import socket
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

WINS = [
    (1,2,3),(4,5,6),(7,8,9),
    (7,4,1),(8,5,2),(9,6,3),
    (1,5,9),(3,5,7)
]

def new_board():
    return [' '] * 10

def check_win(board, symbol):
    return any(board[a]==board[b]==board[c]==symbol for a,b,c in WINS)

def check_draw(board):
    return all(board[i] != ' ' for i in range(1,10))

def print_board(board):
    b = board
    print(f'''
+---+---+---+     +---+---+---+
| {b[7]} | {b[8]} | {b[9]} |     | 7 | 8 | 9 |
+---+---+---+     +---+---+---+
| {b[4]} | {b[5]} | {b[6]} |     | 4 | 5 | 6 |
+---+---+---+     +---+---+---+
| {b[1]} | {b[2]} | {b[3]} |     | 1 | 2 | 3 |
+---+---+---+     +---+---+---+
''')

def send(conn, msg):
    conn.sendall((msg + '\n').encode())

def recv(conn):
    data = b''
    while not data.endswith(b'\n'):
        chunk = conn.recv(1024)
        if not chunk:
            raise ConnectionError("Spojenie prerušené")
        data += chunk
    return data.decode().strip()

def print_score(s1, s2, score):
    print(f"[ SKORE:  {s1} = {score[s1]}  |  {s2} = {score[s2]}  |  Remízy = {score['draw']} ]\n")

def play_game(conn, s1, s2, first_to_move, score):
    board = new_board()
    current = first_to_move

    clear()
    print_score(s1, s2, score)
    print(f"Ty: {s1}  |  Hráč 2: {s2}  |  Začína: {current}\n")
    print_board(board)

    while True:
        if current == s1:
            while True:
                print(f"Tvoj ťah ({s1}). Zadaj číslo (1-9):")
                vstup = input().strip()
                if vstup.isdigit() and 1 <= int(vstup) <= 9:
                    pos = int(vstup)
                    if board[pos] == ' ':
                        board[pos] = s1
                        send(conn, f"MOVE:{pos}")
                        break
                    else:
                        print("Toto miesto je už obsadené!")
                else:
                    print("Neplatný vstup!")
        else:
            print(f"Čakám na ťah hráča 2 ({s2})...")
            msg = recv(conn)
            if msg.startswith("MOVE:"):
                pos = int(msg.split(":")[1])
                board[pos] = s2

        clear()
        print_score(s1, s2, score)
        print_board(board)

        if check_win(board, current):
            send(conn, f"WIN:{current}")
            if current == s1:
                print("Vyhral si! Gratulujeme!\n")
            else:
                print(f"Hráč 2 ({s2}) vyhral.\n")
            return current

        if check_draw(board):
            send(conn, "DRAW")
            print("Remíza!\n")
            return None

        current = s2 if current == s1 else s1

def ask_rematch(conn):
    while True:
        print("Chceš hrať znova? (Y/N):")
        ans = input().strip().upper()
        if ans in ('Y', 'N'):
            break
        print("Zadaj Y alebo N.")

    send(conn, f"REMATCH:{ans}")

    if ans == 'N':
        print("Ukončuješ hru. Dovidenia!")
        return False

    print("Čakám na odpoveď hráča 2...")
    msg = recv(conn)
    if msg.startswith("REMATCH:"):
        other = msg.split(":")[1]
        if other == 'Y':
            print("Hráč 2 súhlasí! Začíname znova...\n")
            return True
        else:
            print("Hráč 2 odmietol. Koniec hry.")
            return False
    return False

# ========================
# ŠTART
# ========================
clear()
print("=== TICK TACK TOE - SERVER (Hráč 1) ===\n")

HOST = '0.0.0.0'
PORT = 5050

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((HOST, PORT))
server_sock.listen(1)

try:
    tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tmp.connect(("8.8.8.8", 80))
    local_ip = tmp.getsockname()[0]
    tmp.close()
except Exception:
    local_ip = "nepodarilo sa zistiť"

print(f"Čakám na pripojenie hráča 2...")
print(f"Tvoja IP adresa: {local_ip}")
print(f"Port: {PORT}\n")

conn, addr = server_sock.accept()
print(f"Hráč 2 sa pripojil z {addr[0]}\n")

while True:
    print("Vyber si symbol - zadaj X alebo O:")
    s1 = input().strip().upper()
    if s1 in ('X', 'O'):
        s2 = 'O' if s1 == 'X' else 'X'
        break
    print("Neplatný vstup.")

send(conn, f"SYMBOL:{s2}")

score = {s1: 0, s2: 0, 'draw': 0}
first_to_move = s1

try:
    while True:
        winner = play_game(conn, s1, s2, first_to_move, score)

        if winner == s1:
            score[s1] += 1
        elif winner == s2:
            score[s2] += 1
        else:
            score['draw'] += 1

        # Striedanie kto začína
        first_to_move = s2 if first_to_move == s1 else s1

        if not ask_rematch(conn):
            send(conn, "QUIT")
            break

except ConnectionError as e:
    print(f"\nChyba spojenia: {e}")
finally:
    conn.close()
    server_sock.close()

input("\nStlač Enter pre ukončenie...")
