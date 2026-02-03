import json
import os
import csv
from datetime import datetime

# ANSI color codes
RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"

SALDO_FILE = "saldo.json"

CSV_FILE = "transactions.csv"


def format_time():
    """Format current datetime as readable string."""
    return datetime.now().strftime("%d %b %Y %H:%M:%S")


def parse_amount(s: str):
    """Parse user input amount tolerant to formats like 'Rp 10.000.000', '10000000', '10,000,000.50', '10.000.000,50'."""
    if not isinstance(s, str):
        raise ValueError("Invalid input")
    s = s.strip()
    if s == "":
        raise ValueError("Kosong")
    # remove currency symbol and spaces
    s = s.replace("Rp", "").replace("rp", "").strip()
    # keep only digits and separators
    allowed = set("0123456789,.")
    s = ''.join(ch for ch in s if ch in allowed)

    # If both '.' and ',' present, assume '.' thousands and ',' decimal (ID style): remove dots, replace comma with dot
    if '.' in s and ',' in s:
        s = s.replace('.', '')
        s = s.replace(',', '.')
    elif ',' in s and '.' not in s:
        # ambiguous: if comma likely decimal separator when there is one comma and <=2 decimals
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(',', '.')
        else:
            # treat comma as thousand separator
            s = s.replace(',', '')
    else:
        # only dots or only digits: remove dots used as thousand separators
        s = s.replace(',', '')
        s = s.replace('.', '')

    try:
        return float(s)
    except Exception:
        raise ValueError("Tidak bisa mengurai jumlah")


def load_data():
    if os.path.exists(SALDO_FILE):
        try:
            with open(SALDO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                saldo = float(data.get("saldo", 0))
                transactions = data.get("transactions", [])
                return saldo, transactions
        except Exception:
            return 0.0, []
    return 0.0, []


def save_data(current_saldo, transactions):
    try:
        with open(SALDO_FILE, "w", encoding="utf-8") as f:
            json.dump({"saldo": current_saldo, "transactions": transactions}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Gagal menyimpan data:", e)


saldo, transactions = load_data()


def tambah_pemasukan():
    global saldo
    try:
        raw = input("Masukkan jumlah pemasukan (boleh pakai Rp/.,): ")
        jumlah = parse_amount(raw)
        if jumlah <= 0:
            print("Jumlah harus lebih dari 0.")
            return
    except ValueError:
        print("Input tidak valid. Masukkan angka, contoh: 100000 atau Rp 10.000.000")
        return

    saldo += jumlah
    note = input("Keterangan (opsional): ").strip() or "-"
    note = note.capitalize()
    transactions.append({
        "type": "pemasukan",
        "amount": jumlah,
        "note": note,
        "time": format_time()
    })
    save_data(saldo, transactions)
    print(GREEN + f"✅ Pemasukan sebesar Rp {jumlah:,.2f} berhasil ditambahkan." + RESET)
    print(BLUE + f"Saldo sekarang: Rp {saldo:,.2f}" + RESET)

def tambah_pengeluaran():
    global saldo
    try:
        raw = input("Masukkan jumlah pengeluaran (boleh pakai Rp/.,): ")
        jumlah = parse_amount(raw)
        if jumlah <= 0:
            print("Jumlah harus lebih dari 0.")
            return
    except ValueError:
        print("Input tidak valid. Masukkan angka, contoh: 50000 atau Rp 50.000")
        return

    if jumlah > saldo:
        print(YELLOW + "⚠️ Saldo tidak cukup untuk pengeluaran ini." + RESET)
        print(BLUE + f"Saldo saat ini: Rp {saldo:,.2f}" + RESET)
        return

    saldo -= jumlah
    note = input("Keterangan (opsional): ").strip() or "-"
    note = note.capitalize()
    transactions.append({
        "type": "pengeluaran",
        "amount": jumlah,
        "note": note,
        "time": format_time()
    })
    save_data(saldo, transactions)
    print(RED + f"✅ Pengeluaran sebesar Rp {jumlah:,.2f} berhasil dikurangi." + RESET)
    print(BLUE + f"Saldo sekarang: Rp {saldo:,.2f}" + RESET)

def lihat_saldo():
    bar = "═" * 30
    print(f"\n💰  SALDO ANDA\n{bar}")
    print(f"Rp {saldo:,.2f}")
    print(bar + "\n")


def laporan():
    if not transactions:
        print(YELLOW + "\n⚠️  Tidak ada transaksi untuk ditampilkan.\n" + RESET)
        return

    total_in = sum(t.get("amount", 0) for t in transactions if t.get("type") == "pemasukan")
    total_out = sum(t.get("amount", 0) for t in transactions if t.get("type") == "pengeluaran")
    net = total_in - total_out

    # Header
    print("\n" + BLUE + "╔════════════════════════════════════════════╗" + RESET)
    print(BLUE + "║" + RESET + "       📊 REKAP TRANSAKSI" + " " * 17 + BLUE + "║" + RESET)
    print(BLUE + "╚════════════════════════════════════════════╝" + RESET)
    
    # Summary box
    print(BLUE + "┌────────────────────────────────────────────┐" + RESET)
    print(f"│ {GREEN}🟢 Pemasukan   {RESET}: {GREEN}Rp {total_in:>16,.2f}{RESET} │")
    print(f"│ {RED}🔴 Pengeluaran {RESET}: {RED}Rp {total_out:>16,.2f}{RESET} │")
    net_color = GREEN if net >= 0 else RED
    print(f"│ {net_color}💰 Saldo Bersih{RESET}: {net_color}Rp {net:>16,.2f}{RESET} │")
    print(BLUE + "└────────────────────────────────────────────┘" + RESET)
    
    # Transactions table
    print("\n" + BLUE + "╔═════╦═══════════╦══════════════════╦═════════════════╦═══════════════════════╗" + RESET)
    print(BLUE + "║ No  ║   Tipe    ║     Jumlah       ║   Keterangan    ║       Waktu           ║" + RESET)
    print(BLUE + "╠═════╬═══════════╬══════════════════╬═════════════════╬═══════════════════════╣" + RESET)
    for i, t in enumerate(transactions, start=1):
        tipe = t.get("type", "-")
        emoji = "🟢" if tipe == "pemasukan" else "🔴"
        amt = t.get("amount", 0)
        waktu = t.get("time", "-")[:21]
        note = t.get("note", "-")
        
        # Format tipe
        tipe_fmt = f"{emoji} {tipe}".ljust(10)[:10]
        
        # Format amount with color
        amt_str = f"Rp {amt:,.2f}"
        amt_colored = GREEN + f"{amt_str:>15}" + RESET if tipe == "pemasukan" else RED + f"{amt_str:>15}" + RESET
        
        # Format note
        note_display = (note[:14] + "...") if len(note) > 17 else note.ljust(15)
        
        # Format waktu
        waktu_display = waktu.ljust(21)
        
        print(f"║{i:>4} ║ {tipe_fmt} ║ {amt_colored} ║ {note_display:<15} ║ {waktu_display:<21} ║")
    
    print(BLUE + "╚═════╩═══════════╩══════════════════╩═════════════════╩═══════════════════════╝" + RESET)
    print("")


def summary_by_note():
    if not transactions:
        print("\nTidak ada transaksi.\n")
        return
    summary = {}
    for t in transactions:
        key = t.get("note", "-")
        summary.setdefault(key, {"in": 0.0, "out": 0.0})
        if t.get("type") == "pemasukan":
            summary[key]["in"] += float(t.get("amount", 0))
        else:
            summary[key]["out"] += float(t.get("amount", 0))

    print(BLUE + "\n📚 Ringkasan per Keterangan" + RESET)
    print("Keterangan               | Total Masuk      | Total Keluar     | Saldo Bersih")
    print("-------------------------+------------------+------------------+------------------")
    for k, v in summary.items():
        in_s = f"Rp {v['in']:,.2f}"
        out_s = f"Rp {v['out']:,.2f}"
        net = v['in'] - v['out']
        net_s = f"Rp {net:,.2f}"
        color_net = GREEN + net_s + RESET if net >= 0 else RED + net_s + RESET
        k_display = (k[:23] + '...') if len(k) > 26 else k
        print(f"{k_display:<25} | {in_s:>16} | {out_s:>16} | {color_net:>16}")
    print("")


def search_transactions():
    q = input("Masukkan kata kunci untuk mencari (tipe/keterangan/waktu): ").strip().lower()
    if not q:
        print("Kata kunci kosong.")
        return
    matches = []
    for i, t in enumerate(transactions, start=1):
        hay = f"{t.get('type','')} {t.get('note','')} {t.get('time','')} {t.get('amount','') }".lower()
        if q in hay:
            matches.append((i, t))

    if not matches:
        print("Tidak ada transaksi yang cocok.")
        return

    print(BLUE + f"\n🔎 Hasil Pencarian: {len(matches)} transaksi" + RESET)
    print("No  | Tipe        | Jumlah           | Keterangan           | Waktu")
    print("----+-------------+------------------+----------------------+--------------------------")
    for i, t in matches:
        tipe = t.get("type")
        emoji = "🟢" if tipe == "pemasukan" else "🔴"
        amt = t.get("amount", 0)
        waktu = t.get("time", "-")
        note = t.get("note", "-")
        note_display = (note[:20] + "...") if len(note) > 23 else note
        amt_str = f"Rp {amt:,.2f}"
        amt_colored = GREEN + amt_str + RESET if tipe == "pemasukan" else RED + amt_str + RESET
        print(f"{i:>2}.  | {emoji} {tipe:<10} | {amt_colored:>16} | {note_display:<20} | {waktu}")
    print("")


def clear_all_data():
    print(YELLOW + "\n⚠️  PERINGATAN: Ini akan menghapus semua transaksi dan mengatur saldo ke 0." + RESET)
    ok = input("Ketik 'DELETE' untuk konfirmasi: ")
    if ok.strip() == "DELETE":
        global saldo, transactions
        saldo = 0.0
        transactions = []
        save_data(saldo, transactions)
        print(GREEN + "✅ Semua data berhasil dihapus." + RESET)
    else:
        print("Batal menghapus data.")


def view_last_transactions(n=5):
    recent = transactions[-n:]
    if not recent:
        print("\nTidak ada transaksi.\n")
        return
    print(BLUE + f"\n🕘  {len(recent)} Transaksi Terakhir" + RESET)
    print("No  | Tipe        | Jumlah           | Keterangan           | Waktu")
    print("----+-------------+------------------+----------------------+--------------------------")
    offset = len(transactions) - len(recent)
    for i, t in enumerate(recent, start=1 + offset):
        tipe = t.get("type", "-")
        emoji = "🟢" if tipe == "pemasukan" else "🔴"
        amt = t.get("amount", 0)
        waktu = t.get("time", "-")
        note = t.get("note", "-")
        note_display = (note[:20] + "...") if len(note) > 23 else note
        amt_str = f"Rp {amt:,.2f}"
        amt_colored = GREEN + amt_str + RESET if tipe == "pemasukan" else RED + amt_str + RESET
        print(f"{i:>2}.  | {emoji} {tipe:<10} | {amt_colored:>16} | {note_display:<20} | {waktu}")
    print("")


def export_csv():
    try:
        with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["no", "type", "amount", "note", "time"])
            for i, t in enumerate(transactions, start=1):
                writer.writerow([i, t.get("type"), t.get("amount"), t.get("note"), t.get("time")])
        print(GREEN + f"✅ Transaksi diekspor ke {CSV_FILE}" + RESET)
    except Exception as e:
        print("Gagal ekspor CSV:", e)


def confirm_exit():
    ans = input("Yakin ingin keluar? (y/n): ").strip().lower()
    return ans in ("y", "yes")


def edit_transaction():
    if not transactions:
        print(YELLOW + "\n⚠️  Tidak ada transaksi untuk diedit.\n" + RESET)
        return
    
    # Tampilkan daftar transaksi
    print(BLUE + "\n📝 Daftar Transaksi:" + RESET)
    for i, t in enumerate(transactions, start=1):
        tipe = t.get("type", "-")
        emoji = "🟢" if tipe == "pemasukan" else "🔴"
        amt = t.get("amount", 0)
        note = t.get("note", "-")
        print(f"{i}. {emoji} {tipe:>11} | Rp {amt:>12,.2f} | {note}")
    
    try:
        idx = int(input("\nMasukkan nomor transaksi yang akan diedit (0 untuk batal): ").strip())
        if idx == 0:
            print("Batal edit.")
            return
        if idx < 1 or idx > len(transactions):
            print("Nomor transaksi tidak valid.")
            return
        
        idx -= 1
        t = transactions[idx]
        
        print(BLUE + f"\n📝 Edit Transaksi #{idx + 1}" + RESET)
        print(f"Tipe saat ini: {t.get('type')}")
        print(f"Jumlah saat ini: Rp {t.get('amount', 0):,.2f}")
        print(f"Keterangan saat ini: {t.get('note')}")
        
        # Edit jumlah
        new_amt_raw = input("\nMasukkan jumlah baru (tekan Enter untuk skip): ").strip()
        if new_amt_raw:
            try:
                new_amt = parse_amount(new_amt_raw)
                if new_amt <= 0:
                    print("Jumlah harus lebih dari 0.")
                    return
                t["amount"] = new_amt
            except ValueError:
                print("Input jumlah tidak valid.")
                return
        
        # Edit keterangan
        new_note = input("Masukkan keterangan baru (tekan Enter untuk skip): ").strip()
        if new_note:
            t["note"] = new_note.capitalize()
        
        save_data(saldo, transactions)
        print(GREEN + "✅ Transaksi berhasil diupdate." + RESET)
    except ValueError:
        print("Input tidak valid.")


def delete_transaction():
    if not transactions:
        print(YELLOW + "\n⚠️  Tidak ada transaksi untuk dihapus.\n" + RESET)
        return
    
    # Tampilkan daftar transaksi
    print(BLUE + "\n🗑️ Daftar Transaksi:" + RESET)
    for i, t in enumerate(transactions, start=1):
        tipe = t.get("type", "-")
        emoji = "🟢" if tipe == "pemasukan" else "🔴"
        amt = t.get("amount", 0)
        note = t.get("note", "-")
        print(f"{i}. {emoji} {tipe:>11} | Rp {amt:>12,.2f} | {note}")
    
    try:
        idx = int(input("\nMasukkan nomor transaksi yang akan dihapus (0 untuk batal): ").strip())
        if idx == 0:
            print("Batal hapus.")
            return
        if idx < 1 or idx > len(transactions):
            print("Nomor transaksi tidak valid.")
            return
        
        idx -= 1
        t = transactions[idx]
        
        # Konfirmasi
        print(f"\n⚠️  Akan menghapus: {t.get('type')} | Rp {t.get('amount', 0):,.2f} | {t.get('note')}")
        confirm = input("Yakin? (y/n): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Batal hapus.")
            return
        
        # Update saldo jika perlu
        global saldo
        if t.get("type") == "pemasukan":
            saldo -= t.get("amount", 0)
        else:
            saldo += t.get("amount", 0)
        
        transactions.pop(idx)
        save_data(saldo, transactions)
        print(GREEN + "✅ Transaksi berhasil dihapus." + RESET)
    except ValueError:
        print("Input tidak valid.")


def menu():
    header = f"{BLUE}=== 💼 Aplikasi Pengelola Uang Saku 💰 ==={RESET}"
    print(header)
    print(f"{GREEN}1.{RESET} ➕ Tambah pemasukan")
    print(f"{RED}2.{RESET} ➖ Tambah pengeluaran")
    print(f"{YELLOW}3.{RESET} 💰 Lihat saldo")
    print(f"{BLUE}4.{RESET} 📊 Laporan (rekap & daftar)")
    print(f"{BLUE}5.{RESET} 📚 Ringkasan per keterangan")
    print(f"{GREEN}6.{RESET} 🔎 Cari transaksi")
    print(f"{YELLOW}7.{RESET} ✏️ Edit transaksi")
    print(f"{RED}8.{RESET} 🗑️ Hapus transaksi")
    print(f"{YELLOW}9.{RESET} ⚠️ Hapus semua data")
    print(f"{YELLOW}10.{RESET} 🚪 Keluar")

while True:
    menu()
    pilihan = input("Pilih menu: ")

    if pilihan == "1":
        tambah_pemasukan()
    elif pilihan == "2":
        tambah_pengeluaran()
    elif pilihan == "3":
        lihat_saldo()
    elif pilihan == "4":
        laporan()
    elif pilihan == "5":
        summary_by_note()
    elif pilihan == "6":
        search_transactions()
    elif pilihan == "7":
        edit_transaction()
    elif pilihan == "8":
        delete_transaction()
    elif pilihan == "9":
        clear_all_data()
    elif pilihan == "10":
        if confirm_exit():
            print("Terima kasih!")
            break
        else:
            print("Batal keluar.")
    else:
        print("Pilihan tidak valid")