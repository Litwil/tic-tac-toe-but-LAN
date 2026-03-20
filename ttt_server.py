import socket
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

WINS = [(1,2,3),(4,5,6),(7,8,9),(7,4,1),(8,5,2),(9,6,3),(1,5,9),(3,5,7)]

def check_win(board, sym):
    return any(board[a]==board[b]==board[c]==sym for a,b,c in WINS)

def check_draw(board):
    return all(board[i] != ' ' for i in range(1,10))

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
    print(f"[ SKORE: {s1}={score[s1]}  {s2}={score[s2]}  Remízy={score['draw']} ]\n")

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

# Vyber symbol
while True:
    print("Vyber si symbol (X alebo O):")
    s1 = input().strip().upper()
    if s1 in ('X','O'):
        s2 = 'O' if s1 == 'X' else 'X'
        break
    print("Neplatný vstup.")

# Informuj klienta o jeho symbole
send(conn, f"SETUP:{s2}")

score = {s1: 0, s2: 0, 'draw': 0}
first = s1   # kto začína toto kolo

try:
    while True:
        # ── NOVÁ HRA ──
        board = [' '] * 10
        current = first

        while True:
            clear()
            print_score(s1, s2, score)
            print(f"Ty: {s1}   Hráč 2: {s2}   Na rade: {current}\n")
            print_board(board)

            if current == s1:
                # ── Môj ťah ──
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
                # Pošli klientovi: hráč urobil ťah na pos, teraz je na rade current_next
                next_player = s2  # po mojom ťahu je na rade s2

                if check_win(board, s1):
                    score[s1] += 1
                    send(conn, f"STATE:{''.join(board[1:])}:WIN:{s1}")
                    clear()
                    print_score(s1, s2, score)
                    print_board(board)
                    print("🎉 Vyhral si!\n")
                    break
                elif check_draw(board):
                    score['draw'] += 1
                    send(conn, f"STATE:{''.join(board[1:])}:DRAW")
                    clear()
                    print_score(s1, s2, score)
                    print_board(board)
                    print("Remíza!\n")
                    break
                else:
                    send(conn, f"STATE:{''.join(board[1:])}:TURN:{s2}")
                    current = s2

            else:
                # ── Čakám na ťah hráča 2 ──
                print(f"Čakám na ťah hráča 2 ({s2})...")
                msg = recv(conn)
                # Klient posiela iba: "MOVE:pos"
                if not msg.startswith("MOVE:"):
                    raise ConnectionError(f"Neočakávaná správa: {msg}")
                pos = int(msg.split(":")[1])

                if board[pos] != ' ':
                    # Toto by nemalo nastať, ale pre istotu
                    send(conn, f"STATE:{''.join(board[1:])}:TURN:{s2}")
                    continue

                board[pos] = s2

                if check_win(board, s2):
                    score[s2] += 1
                    send(conn, f"STATE:{''.join(board[1:])}:WIN:{s2}")
                    clear()
                    print_score(s1, s2, score)
                    print_board(board)
                    print(f"Hráč 2 ({s2}) vyhral.\n")
                    break
                elif check_draw(board):
                    score['draw'] += 1
                    send(conn, f"STATE:{''.join(board[1:])}:DRAW")
                    clear()
                    print_score(s1, s2, score)
                    print_board(board)
                    print("Remíza!\n")
                    break
                else:
                    send(conn, f"STATE:{''.join(board[1:])}:TURN:{s1}")
                    current = s1

        # ── REMATCH ──
        print_score(s1, s2, score)
        while True:
            print("Chceš hrať znova? (Y/N):")
            ans = input().strip().upper()
            if ans in ('Y','N'):
                break
            print("Zadaj Y alebo N.")

        if ans == 'N':
            send(conn, "REMATCH:N")
            print("Dovidenia!")
            break

        # Pošli klientovi že chceme hrať
        send(conn, "REMATCH:Y")
        # Počkaj na jeho odpoveď
        print("Čakám na odpoveď hráča 2...")
        msg = recv(conn)
        if msg == "REMATCH:Y":
            print("Hráč 2 súhlasí! Začíname...\n")
            first = s2 if first == s1 else s1  # striedanie kto začína
        else:
            print("Hráč 2 odmietol. Koniec hry.")
            break

except ConnectionError as e:
    print(f"\nChyba: {e}")
finally:
    conn.close()
    server_sock.close()

input("\nStlač Enter pre ukončenie...")
