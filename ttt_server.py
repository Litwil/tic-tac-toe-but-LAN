import socket
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

# --- Herný stav ---
board = [' '] * 10  # indexy 1-9

WINS = [
    (1,2,3),(4,5,6),(7,8,9),
    (7,4,1),(8,5,2),(9,6,3),
    (1,5,9),(3,5,7)
]

def check_win(symbol):
    return any(board[a]==board[b]==board[c]==symbol for a,b,c in WINS)

def check_draw():
    return all(board[i] != ' ' for i in range(1,10))

def print_board():
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

def board_str():
    return ','.join(board[1:])  # pošle stav 1-9 ako "X, ,O,..."

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

# --- Hlavná logika ---
clear()
print("=== TICK TACK TOE - SERVER (Hráč 1) ===\n")

HOST = '0.0.0.0'
PORT = 5050

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

# Zisti lokálnu IP pre info
local_ip = socket.gethostbyname(socket.gethostname())
print(f"Čakám na pripojenie hráča 2...")
print(f"Tvoja IP adresa (povedz ju hráčovi 2): {local_ip}")
print(f"Port: {PORT}\n")

conn, addr = server.accept()
print(f"Hráč 2 sa pripojil z {addr[0]}\n")

# Vyber symbol
while True:
    print("Vyber si symbol - zadaj X alebo O:")
    s1 = input().strip().upper()
    if s1 in ('X', 'O'):
        s2 = 'O' if s1 == 'X' else 'X'
        break
    print("Neplatný vstup, skús znova.")

send(conn, f"SYMBOL:{s2}")
send(conn, f"INFO:Hráč 1 si vybral {s1}. Ty hráš ako {s2}.")

clear()
print(f"Ty hráš ako: {s1}")
print(f"Hráč 2 hrá ako: {s2}")
print(f"Hráč {s1} začína!\n")
print_board()

current = s1  # kto je na rade

try:
    while True:
        if current == s1:
            # Môj ťah
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
            # Čakám na ťah hráča 2
            print(f"Čakám na ťah hráča 2 ({s2})...")
            msg = recv(conn)
            if msg.startswith("MOVE:"):
                pos = int(msg.split(":")[1])
                board[pos] = s2

        clear()
        print_board()

        if check_win(current):
            winner_sym = current
            msg = f"WIN:{winner_sym}"
            send(conn, msg)
            if winner_sym == s1:
                print(f"🎉 Vyhral si! Gratulujeme!\n")
            else:
                print(f"Hráč 2 ({s2}) vyhral. Skús znova!\n")
            break

        if check_draw():
            send(conn, "DRAW")
            print("Remíza! Nikto nevyhral.\n")
            break

        # Prepni hráča
        current = s2 if current == s1 else s1

except ConnectionError as e:
    print(f"\nChyba spojenia: {e}")
finally:
    conn.close()
    server.close()

input("\nStlač Enter pre ukončenie...")
