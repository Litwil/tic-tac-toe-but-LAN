import socket
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_board(board):
    b = board
    print(f"""
+---+---+---+     +---+---+---+
| {b[7]} | {b[8]} | {b[9]} |     | 7 | 8 | 9 |
+---+---+---+     +---+---+---+
| {b[4]} | {b[5]} | {b[6]} |     | 4 | 5 | 6 |
+---+---+---+     +---+---+---+
| {b[1]} | {b[2]} | {b[3]} |     | 1 | 2 | 3 |
+---+---+---+     +---+---+---+
""")

def send(sock, msg):
    sock.sendall((msg + '\n').encode())

def recv(sock):
    data = b''
    while not data.endswith(b'\n'):
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Spojenie stratené")
        data += chunk
    return data.decode().strip()

def parse_board(board_str):
    # board_str je 9 znakov napr. "X O  X  O"
    b = [' '] + list(board_str)  # index 0 nevyužitý
    return b

def print_score(s1, s2, score):
    print(f"[ SKORE: {s1}={score[s1]}  {s2}={score[s2]}  Remízy={score['draw']} ]\n")

# ── ŠTART ──────────────────────────────────────────────
clear()
print("=== TICK TACK TOE — KLIENT (Hráč 2) ===\n")

while True:
    print("Zadaj IP adresu hráča 1:")
    HOST = input().strip()
    if HOST:
        break

print(f"Pripájam sa na {HOST}:5050 ...")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect((HOST, 5050))
except Exception as e:
    print(f"Nepodarilo sa pripojiť: {e}")
    input("Stlač Enter...")
    exit()

print("Pripojený!\n")

# Prijmi setup
msg = recv(sock)
if not msg.startswith("SETUP:"):
    print("Chybný handshake.")
    exit()

s2 = msg.split(":")[1]   # môj symbol
s1 = 'O' if s2 == 'X' else 'X'

print(f"Ty hráš ako: {s2}  |  Hráč 1 hrá ako: {s1}\n")

score = {s1: 0, s2: 0, 'draw': 0}

try:
    while True:
        # ── HERNÁ SLUČKA ──
        # Čakáme na STATE správy od servera
        game_over = False
        board = [' '] * 10

        while not game_over:
            msg = recv(sock)

            # ── Rematch správy (prichádzajú po konci hry) ──
            if msg.startswith("REMATCH:"):
                ans = msg.split(":")[1]
                if ans == 'N':
                    print("Hráč 1 ukončil hru. Dovidenia!")
                    exit()
                # Hráč 1 chce hrať znova
                print_score(s1, s2, score)
                while True:
                    print("Hráč 1 chce hrať znova! Súhlasíš? (Y/N):")
                    my_ans = input().strip().upper()
                    if my_ans in ('Y','N'):
                        break
                    print("Zadaj Y alebo N.")
                send(sock, f"REMATCH:{my_ans}")
                if my_ans == 'Y':
                    print("Začíname znova!\n")
                    break  # vyjdi z while not game_over → nová hra
                else:
                    print("Odmietol si. Koniec hry.")
                    exit()

            # ── STATE správy ──
            if not msg.startswith("STATE:"):
                continue

            parts = msg.split(":")
            # Formát: STATE:<9znakov>:WIN:<sym>  alebo  STATE:<9znakov>:DRAW  alebo  STATE:<9znakov>:TURN:<sym>
            board_str = parts[1]
            board = parse_board(board_str)
            event = parts[2]

            clear()
            print_score(s1, s2, score)

            if event == "WIN":
                winner = parts[3]
                print_board(board)
                if winner == s2:
                    score[s2] += 1
                    print("🎉 Vyhral si! Gratulujeme!\n")
                else:
                    score[s1] += 1
                    print(f"Hráč 1 ({s1}) vyhral.\n")
                game_over = True

            elif event == "DRAW":
                score['draw'] += 1
                print_board(board)
                print("Remíza!\n")
                game_over = True

            elif event == "TURN":
                whose_turn = parts[3]
                print(f"Ty: {s2}  |  Hráč 1: {s1}  |  Na rade: {whose_turn}\n")
                print_board(board)

                if whose_turn == s2:
                    # Môj ťah
                    while True:
                        print(f"Tvoj ťah ({s2}). Zadaj číslo (1-9):")
                        vstup = input().strip()
                        if vstup.isdigit() and 1 <= int(vstup) <= 9:
                            pos = int(vstup)
                            if board[pos] == ' ':
                                break
                            print("Obsadené!")
                        else:
                            print("Neplatný vstup!")
                    send(sock, f"MOVE:{pos}")
                else:
                    print(f"Čakám na ťah hráča 1 ({s1})...")

except ConnectionError as e:
    print(f"\nChyba: {e}")
finally:
    sock.close()

input("\nStlač Enter pre ukončenie...")
