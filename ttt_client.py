import socket
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def parse_board(s):
    # s = 9 znakov, vráti list [' ', s[0]..s[8]]
    return [' '] + list(s)

def print_board(board):
    b = board
    print(f"""
+---+---+---+     +---+---+---+
| {b[7]} | {b[8]} | {b[9]} |     | 7 | 8 | 9 |
+---+---+---+     +---+---+---+
| {b[4]} | {b[5]} | {b[6]} |     | 4 | 5 | 6 |
+---+---+---+     +---+---+---+
| {b[1]} | {b[2]} | {b[3]} |     | 1 | 2 | 3 |
+---+---+---+     +---+---+---+""")

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

def print_score(s1, s2, score):
    print(f"\n[ SKORE: {s1}={score[s1]}  {s2}={score[s2]}  Remízy={score['draw']} ]")

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

msg = recv(sock)
if not msg.startswith("SETUP:"):
    print("Chybný handshake.")
    exit()

s2 = msg.split(":")[1]        # môj symbol
s1 = 'O' if s2 == 'X' else 'X'

print(f"Ty hráš ako: {s2}  |  Hráč 1 hrá ako: {s1}\n")

score = {s1: 0, s2: 0, 'draw': 0}

try:
    while True:
        # ── HERNÁ SLUČKA ──
        # Každú iteráciu čítame STATE správu od servera
        msg = recv(sock)

        # ── REMATCH ──
        if msg.startswith("REMATCH:"):
            ans = msg.split(":")[1]
            if ans == 'N':
                print("\nHráč 1 ukončil hru. Dovidenia!")
                break

            # Hráč 1 chce hrať znova
            print_score(s1, s2, score)
            print()
            while True:
                print("Hráč 1 chce hrať znova! Súhlasíš? (Y/N):")
                my_ans = input().strip().upper()
                if my_ans in ('Y','N'):
                    break
                print("Zadaj Y alebo N.")

            send(sock, f"REMATCH:{my_ans}")

            if my_ans == 'N':
                print("Odmietol si. Koniec hry.")
                break
            # Inak pokračuj — server pošle nový STATE
            continue

        # ── STATE správa ──
        # Formát: STATE:<9znakov>:TURN:<sym>
        #         STATE:<9znakov>:WIN:<sym>
        #         STATE:<9znakov>:DRAW
        if not msg.startswith("STATE:"):
            continue

        parts = msg.split(":")
        board = parse_board(parts[1])
        event = parts[2]

        clear()
        print_score(s1, s2, score)
        print(f"\nTy: {s2}   Hráč 1: {s1}\n")
        print_board(board)
        print()

        if event == "WIN":
            winner = parts[3]
            if winner == s2:
                score[s2] += 1
                print("🎉 Vyhral si! Gratulujeme!\n")
            else:
                score[s1] += 1
                print(f"Hráč 1 ({s1}) vyhral.\n")
            # Čakaj na REMATCH správu (príde v ďalšej iterácii)

        elif event == "DRAW":
            score['draw'] += 1
            print("Remíza!\n")
            # Čakaj na REMATCH správu

        elif event == "TURN":
            whose_turn = parts[3]
            if whose_turn == s2:
                # Môj ťah
                print(f"Na rade si TY ({s2})!")
                while True:
                    print(f"Zadaj číslo (1-9):")
                    vstup = input().strip()
                    if vstup.isdigit() and 1 <= int(vstup) <= 9:
                        pos = int(vstup)
                        if board[pos] == ' ':
                            break
                        print("Obsadené! Vyber iné miesto.")
                    else:
                        print("Neplatný vstup!")
                send(sock, f"MOVE:{pos}")
                # Nezobrazuj nič — čakaj na STATE od servera
            else:
                print(f"Na rade je hráč 1 ({s1}). Čakám...")

except ConnectionError as e:
    print(f"\nChyba: {e}")
finally:
    sock.close()

input("\nStlač Enter pre ukončenie...")
