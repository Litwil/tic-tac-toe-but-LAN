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

def send(sock, msg):
    sock.sendall((msg + '\n').encode())

def recv(sock):
    data = b''
    while not data.endswith(b'\n'):
        chunk = sock.recv(1024)
        if not chunk:
            raise ConnectionError("Spojenie prerušené")
        data += chunk
    return data.decode().strip()

def print_score(s1, s2, score):
    print(f"[ SKORE:  {s1} = {score[s1]}  |  {s2} = {score[s2]}  |  Remízy = {score['draw']} ]\n")

def play_game(sock, s1, s2, first_to_move, score):
    board = new_board()
    current = first_to_move

    clear()
    print_score(s1, s2, score)
    print(f"Ty: {s2}  |  Hráč 1: {s1}  |  Začína: {current}\n")
    print_board(board)

    while True:
        if current == s2:
            while True:
                print(f"Tvoj ťah ({s2}). Zadaj číslo (1-9):")
                vstup = input().strip()
                if vstup.isdigit() and 1 <= int(vstup) <= 9:
                    pos = int(vstup)
                    if board[pos] == ' ':
                        board[pos] = s2
                        send(sock, f"MOVE:{pos}")
                        break
                    else:
                        print("Toto miesto je už obsadené!")
                else:
                    print("Neplatný vstup!")
        else:
            print(f"Čakám na ťah hráča 1 ({s1})...")
            msg = recv(sock)

            if msg.startswith("WIN:"):
                winner_sym = msg.split(":")[1]
                clear()
                print_score(s1, s2, score)
                print_board(board)
                if winner_sym == s2:
                    print("Vyhral si! Gratulujeme!\n")
                else:
                    print(f"Hráč 1 ({s1}) vyhral.\n")
                return winner_sym

            if msg == "DRAW":
                clear()
                print_score(s1, s2, score)
                print_board(board)
                print("Remíza!\n")
                return None

            if msg.startswith("MOVE:"):
                pos = int(msg.split(":")[1])
                board[pos] = s1

        clear()
        print_score(s1, s2, score)
        print_board(board)

        if check_win(board, current):
            if current == s2:
                print("Vyhral si! Gratulujeme!\n")
            else:
                print(f"Hráč 1 ({s1}) vyhral.\n")
            return current

        if check_draw(board):
            print("Remíza!\n")
            return None

        current = s2 if current == s1 else s1

def handle_rematch(sock):
    # Čakaj na rozhodnutie hráča 1
    print("Čakám na rematch požiadavku od hráča 1...")
    msg = recv(sock)

    if msg == "QUIT":
        print("Hráč 1 ukončil hru. Dovidenia!")
        return False

    if msg.startswith("REMATCH:"):
        their_ans = msg.split(":")[1]
        if their_ans == 'N':
            print("Hráč 1 nechce hrať znova. Koniec hry.")
            return False

        # Hráč 1 chce hrať — opýtaj sa aj hráča 2
        while True:
            print("Hráč 1 chce hrať znova! Súhlasíš? (Y/N):")
            ans = input().strip().upper()
            if ans in ('Y', 'N'):
                break
            print("Zadaj Y alebo N.")

        send(sock, f"REMATCH:{ans}")

        if ans == 'Y':
            print("Začíname znova!\n")
            return True
        else:
            print("Odmietol si rematch. Koniec hry.")
            return False

    return False

# ========================
# ŠTART
# ========================
clear()
print("=== TICK TACK TOE - KLIENT (Hráč 2) ===\n")

PORT = 5050

while True:
    print("Zadaj IP adresu hráča 1 (napr. 192.168.1.10):")
    HOST = input().strip()
    if HOST:
        break

print(f"\nPripájam sa na {HOST}:{PORT}...")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect((HOST, PORT))
except Exception as e:
    print(f"Nepodarilo sa pripojiť: {e}")
    input("Stlač Enter pre ukončenie...")
    exit()

print("Pripojený!\n")

# Prijmi symbol
msg = recv(sock)
if msg.startswith("SYMBOL:"):
    s2 = msg.split(":")[1]
    s1 = 'O' if s2 == 'X' else 'X'

print(f"Ty hráš ako: {s2}  |  Hráč 1 hrá ako: {s1}\n")

score = {s1: 0, s2: 0, 'draw': 0}
first_to_move = s1  # Hráč 1 (server) vždy začína prvý

try:
    while True:
        winner = play_game(sock, s1, s2, first_to_move, score)

        if winner == s1:
            score[s1] += 1
        elif winner == s2:
            score[s2] += 1
        else:
            score['draw'] += 1

        # Striedanie kto začína (musí byť synchrónne so serverom)
        first_to_move = s2 if first_to_move == s1 else s1

        if not handle_rematch(sock):
            break

except ConnectionError as e:
    print(f"\nChyba spojenia: {e}")
finally:
    sock.close()

input("\nStlač Enter pre ukončenie...")
