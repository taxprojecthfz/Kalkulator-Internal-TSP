# ============================================================
# KAMUS ATURAN PAJAK - KALKULATOR PAJAK TSP GRUP
# PENTING: Semua angka di bawah ini WAJIB diverifikasi ulang
# ke peraturan resmi (DJP/PMK/PP terbaru) atau tax advisor
# perusahaan sebelum dipakai untuk pembayaran sungguhan.
# Terakhir dicek: September 2026
# ============================================================

# --- PPN ---
TARIF_PPN = 0.11  # 11% (tarif efektif dari DPP Nilai Lain)

# --- PPh 23 (Jasa Lainnya utk Badan, & Sewa Lainnya utk semua vendor) ---
TARIF_PPH23 = 0.02  # 2% dari jumlah bruto

# --- PPh Final Pasal 4(2) - Sewa Tanah/Bangunan ---
TARIF_PPH_SEWA_TANAH_BANGUNAN = 0.10  # 10% flat, sama utk Badan & Orang Pribadi

# --- PPh Final Pasal 4(2) - Jasa Konstruksi ---
TARIF_PPH_KONSTRUKSI = {
    "pekerjaan_konstruksi": {
        "Bersertifikat - Kualifikasi Kecil / Perseorangan": 0.0175,
        "Bersertifikat - Kualifikasi Menengah / Besar / Spesialis": 0.0265,
        "Tidak Bersertifikat": 0.04,
    },
    "konsultasi_konstruksi": {
        "Bersertifikat": 0.035,
        "Tidak Bersertifikat": 0.06,
    },
}

# --- PPh 21 Progresif (Jasa Lainnya utk vendor Orang Pribadi) ---
# DPP = 50% x jumlah bruto (khusus tenaga ahli/bukan pegawai)
PERSEN_DPP_PPH21_TENAGA_AHLI = 0.50

# Lapisan tarif progresif (Pasal 17 UU HPP), urut dari terkecil
LAPISAN_PPH21 = [
    (60_000_000, 0.05),        # sampai Rp60jt: 5%
    (250_000_000, 0.15),       # Rp60jt - Rp250jt: 15%
    (500_000_000, 0.25),       # Rp250jt - Rp500jt: 25%
    (5_000_000_000, 0.30),     # Rp500jt - Rp5M: 30%
    (float("inf"), 0.35),      # di atas Rp5M: 35%
]

# --- Catatan: sejak NIK berlaku sebagai NPWP (PMK 136/2023, efektif
# penuh 1 Juli 2024), tarif lebih tinggi untuk vendor "tanpa NPWP"
# TIDAK LAGI relevan di tools ini -- karena field KTP (16 digit NIK)
# yang wajib diisi otomatis berfungsi sebagai identitas NPWP vendor.
# Skenario "tanpa identitas sama sekali" sudah diblokir di validasi form.