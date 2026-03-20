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

# --- Hlavná logika ---
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

print("Pripojený! Čakám na nastavenie hry...\n")

# Prijmi symbol od servera
msg = recv(sock)
if msg.startswith("SYMBOL:"):
    s2 = msg.split(":")[1]
    s1 = 'O' if s2 == 'X' else 'X'

msg = recv(sock)
if msg.startswith("INFO:"):
    print(msg.split("INFO:")[1])

clear()
print(f"Ty hráš ako: {s2}")
print(f"Hráč 1 hrá ako: {s1}")
print(f"Hráč {s1} začína!\n")
print_board()

current = s1  # s1 začína vždy (server/hráč 1)

try:
    while True:
        if current == s2:
            # Môj ťah
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
            # Čakám na ťah hráča 1
            print(f"Čakám na ťah hráča 1 ({s1})...")
            msg = recv(sock)

            if msg.startswith("WIN:"):
                winner_sym = msg.split(":")[1]
                clear()
                print_board()
                if winner_sym == s2:
                    print(f"🎉 Vyhral si! Gratulujeme!\n")
                else:
                    print(f"Hráč 1 ({s1}) vyhral. Skús znova!\n")
                break

            if msg == "DRAW":
                clear()
                print_board()
                print("Remíza! Nikto nevyhral.\n")
                break

            if msg.startswith("MOVE:"):
                pos = int(msg.split(":")[1])
                board[pos] = s1

        clear()
        print_board()

        if check_win(current):
            winner_sym = current
            if winner_sym == s2:
                print(f"🎉 Vyhral si! Gratulujeme!\n")
            else:
                print(f"Hráč 1 ({s1}) vyhral. Skús znova!\n")
            break

        if check_draw():
            print("Remíza! Nikto nevyhral.\n")
            break

        # Prepni hráča
        current = s2 if current == s1 else s1

except ConnectionError as e:
    print(f"\nChyba spojenia: {e}")
finally:
    sock.close()

input("\nStlač Enter pre ukončenie...")
