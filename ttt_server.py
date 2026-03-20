import socket
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

WINS = [(1,2,3),(4,5,6),(7,8,9),(7,4,1),(8,5,2),(9,6,3),(1,5,9),(3,5,7)]

def check_win(board, sym):
    return any(board[a]==board[b]==board[c]==sym for a,b,c in WINS)

def check_draw(board):
    return all(board[i] != ' ' for i in range(1,10))

def board_str(board):
    return ''.join(board[1:])  # 9 znakov, indexy 1-9

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

def send(conn, msg):
    conn.sendall((msg + '\n').encode())

def recv(conn):
    data = b''
    while not data.endswith(b'\n'):
        chunk = conn.recv(4096)
        if not chunk:
            raise ConnectionError("Spojenie stratené")
        data += chunk
    return data.decode().strip()

def print_score(s1, s2, score):
    print(f"\n[ SKORE: {s1}={score[s1]}  {s2}={score[s2]}  Remízy={score['draw']} ]")

def push_state(conn, board, event, extra=''):
    """Pošle klientovi aktuálny stav + udalosť."""
    msg = f"STATE:{board_str(board)}:{event}"
    if extra:
        msg += f":{extra}"
    send(conn, msg)

# ── ŠTART ──────────────────────────────────────────────
clear()
print("=== TICK TACK TOE — SERVER (Hráč 1) ===\n")

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(('0.0.0.0', 5050))
server_sock.listen(1)

try:
    tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tmp.connect(("8.8.8.8", 80))
    local_ip = tmp.getsockname()[0]
    tmp.close()
except:
    local_ip = "neznáma"

print(f"Tvoja IP adresa (povedz hráčovi 2): {local_ip}  |  Port: 5050")
print("Čakám na pripojenie...\n")

conn, addr = server_sock.accept()
print(f"Hráč 2 pripojený z {addr[0]}\n")

while True:
    print("Vyber si symbol (X alebo O):")
    s1 = input().strip().upper()
    if s1 in ('X','O'):
        s2 = 'O' if s1 == 'X' else 'X'
        break
    print("Neplatný vstup.")

send(conn, f"SETUP:{s2}")

score = {s1: 0, s2: 0, 'draw': 0}
first = s1

try:
    while True:
        board = [' '] * 10
        current = first

        # Hneď pošli klientovi počiatočný stav + kto začína
        push_state(conn, board, "TURN", current)

        while True:
            if current == s1:
                # Môj ťah — zobraz board a pýtaj vstup
                clear()
                print_score(s1, s2, score)
                print(f"\nTy: {s1}   Hráč 2: {s2}   Na rade: {s1} (TY)\n")
                print_board(board)
                print()

                while True:
                    print(f"Tvoj ťah ({s1}). Zadaj číslo (1-9):")
                    vstup = input().strip()
                    if vstup.isdigit() and 1 <= int(vstup) <= 9:
                        pos = int(vstup)
                        if board[pos] == ' ':
                            break
                        print("Obsadené!")
                    else:
                        print("Neplatný vstup!")

                board[pos] = s1

                if check_win(board, s1):
                    score[s1] += 1
                    push_state(conn, board, "WIN", s1)
                    clear()
                    print_score(s1, s2, score)
                    print(f"\nTy: {s1}   Hráč 2: {s2}\n")
                    print_board(board)
                    print("\n🎉 Vyhral si!\n")
                    break
                elif check_draw(board):
                    score['draw'] += 1
                    push_state(conn, board, "DRAW")
                    clear()
                    print_score(s1, s2, score)
                    print_board(board)
                    print("\nRemíza!\n")
                    break
                else:
                    current = s2
                    push_state(conn, board, "TURN", current)

            else:
                # Čakám na ťah hráča 2
                clear()
                print_score(s1, s2, score)
                print(f"\nTy: {s1}   Hráč 2: {s2}   Na rade: {s2} (čakám...)\n")
                print_board(board)
                print()

                msg = recv(conn)
                if not msg.startswith("MOVE:"):
                    raise ConnectionError(f"Neočakávaná správa: {msg}")
                pos = int(msg.split(":")[1])

                if board[pos] != ' ':
                    # Obsadené — pošli znova rovnaký stav
                    push_state(conn, board, "TURN", s2)
                    continue

                board[pos] = s2

                if check_win(board, s2):
                    score[s2] += 1
                    push_state(conn, board, "WIN", s2)
                    clear()
                    print_score(s1, s2, score)
                    print_board(board)
                    print(f"\nHráč 2 ({s2}) vyhral.\n")
                    break
                elif check_draw(board):
                    score['draw'] += 1
                    push_state(conn, board, "DRAW")
                    clear()
                    print_score(s1, s2, score)
                    print_board(board)
                    print("\nRemíza!\n")
                    break
                else:
                    current = s1
                    push_state(conn, board, "TURN", current)

        # ── REMATCH ──
        print_score(s1, s2, score)
        print()
        while True:
            print("Chceš hrať znova? (Y/N):")
            ans = input().strip().upper()
            if ans in ('Y','N'):
                break
            print("Zadaj Y alebo N.")

        send(conn, f"REMATCH:{ans}")

        if ans == 'N':
            print("Dovidenia!")
            break

        print("Čakám na odpoveď hráča 2...")
        msg = recv(conn)
        if msg == "REMATCH:Y":
            print("Hráč 2 súhlasí! Začíname...\n")
            first = s2 if first == s1 else s1
        else:
            print("Hráč 2 odmietol. Koniec hry.")
            break

except ConnectionError as e:
    print(f"\nChyba: {e}")
finally:
    conn.close()
    server_sock.close()

input("\nStlač Enter pre ukončenie...")
