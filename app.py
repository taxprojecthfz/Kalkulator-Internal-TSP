from datetime import datetime
import streamlit as st
import config
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(layout="wide", page_title="Kalkulator Pajak TSP Grup")
st.title("Kalkulator Pajak TSP Grup")

st.markdown("""
    <style>
    textarea::placeholder {
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 90% 10%, rgba(255,255,255,0.08) 0%, transparent 25%),
            radial-gradient(circle at 5% 90%, rgba(255,255,255,0.06) 0%, transparent 20%),
            linear-gradient(135deg, #1B4F72 0%, #123C57 100%);
        background-attachment: fixed;
    }

    .block-container {
        max-width: 1000px;
        margin: 1.5rem auto;
        background: #FFFFFF;
        border-radius: 16px;
        padding: 2.5rem 3rem 3rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
    }
    h1 {
        margin-bottom: 0.3rem !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.dialog("Eh, SERIUS GA ADA KTP?")
def show_popup_ktp():
    st.write("Kalo Vendornya Orang Pribadi WAJIB Ada KTP.")
    if st.button("Oke, saya cek lagi..."):
        st.rerun()


def tentukan_tarif_pph():
    if jenis_pekerjaan == "Jasa Konstruksi (Membangun Bangunan)":
        if sub_konstruksi == "Pekerjaan Konstruksi (Fisik: bangun/renovasi/bongkar)":
            return config.TARIF_PPH_KONSTRUKSI["pekerjaan_konstruksi"][status_sertifikat]
        else:
            return config.TARIF_PPH_KONSTRUKSI["konsultasi_konstruksi"][status_sertifikat]
    elif jenis_pekerjaan == "Sewa Tanah / Bangunan":
        return config.TARIF_PPH_SEWA_TANAH_BANGUNAN
    elif jenis_pekerjaan == "Sewa Lainnya (Mesin, Kendaraan, Peralatan)":
        return config.TARIF_PPH23
    elif jenis_pekerjaan == "Jasa Lainnya / Bukan Konstruksi":
        if jenis_vendor == "Badan (PT/CV/Lainnya)":
            return config.TARIF_PPH23
        else:
            return "PROGRESIF_PPH21"


def label_jenis_pajak():
    if jenis_pekerjaan == "Jasa Konstruksi (Membangun Bangunan)":
        if sub_konstruksi == "Pekerjaan Konstruksi (Fisik: bangun/renovasi/bongkar)":
            tarif = config.TARIF_PPH_KONSTRUKSI["pekerjaan_konstruksi"][status_sertifikat]
        else:
            tarif = config.TARIF_PPH_KONSTRUKSI["konsultasi_konstruksi"][status_sertifikat]
        return f"PPh 4 ayat (2) Konstruksi, tarif {tarif * 100:.2f}%".replace(".00", "")
    elif jenis_pekerjaan == "Sewa Tanah / Bangunan":
        return f"PPh 4 ayat (2) Sewa Tanah/Bangunan, tarif {config.TARIF_PPH_SEWA_TANAH_BANGUNAN * 100:.0f}%"
    elif jenis_pekerjaan == "Sewa Lainnya (Mesin, Kendaraan, Peralatan)":
        return f"PPh 23, tarif {config.TARIF_PPH23 * 100:.0f}%"
    elif jenis_pekerjaan == "Jasa Lainnya / Bukan Konstruksi":
        if jenis_vendor == "Badan (PT/CV/Lainnya)":
            return f"PPh 23, tarif {config.TARIF_PPH23 * 100:.0f}%"
        else:
            return "PPh 21, 5%-35%"


def hitung_pph21_progresif(dpp_pkp):
    pajak_total = 0
    batas_bawah = 0
    for batas_atas, tarif in config.LAPISAN_PPH21:
        if dpp_pkp > batas_bawah:
            bagian_kena_pajak = min(dpp_pkp, batas_atas) - batas_bawah
            pajak_total += bagian_kena_pajak * tarif
            batas_bawah = batas_atas
        else:
            break
    return pajak_total


def hitung_gross_up_pph21(target_netto):
    rendah = target_netto
    tinggi = target_netto * 2
    for _ in range(50):
        tengah = (rendah + tinggi) / 2
        dpp_pkp_coba = tengah * config.PERSEN_DPP_PPH21_TENAGA_AHLI
        pajak_coba = hitung_pph21_progresif(dpp_pkp_coba)
        netto_coba = tengah - pajak_coba
        if netto_coba < target_netto:
            rendah = tengah
        else:
            tinggi = tengah
    return tinggi


def buat_pdf(data):
    buffer = BytesIO()
    ukuran_halaman = (25 * cm, 14 * cm)
    c = canvas.Canvas(buffer, pagesize=ukuran_halaman)
    lebar, tinggi = ukuran_halaman

    margin_kiri = 2 * cm
    margin_kanan = lebar - 2 * cm
    y = tinggi - 1.5 * cm

    kolom_gap = 0.6 * cm
    lebar_kolom = (margin_kanan - margin_kiri - kolom_gap) / 2
    kolom1_x = margin_kiri
    kolom2_x = margin_kiri + lebar_kolom + kolom_gap

    def rupiah(angka):
        return f"Rp {angka:,.0f}".replace(",", ".")

    def tulis_baris(x, y_pos, label, isi, lebar_label=2.6 * cm):
        c.setFont("Helvetica", 9)
        c.drawString(x, y_pos, label)
        c.drawString(x + lebar_label, y_pos, ":")
        c.drawString(x + lebar_label + 0.25 * cm, y_pos, str(isi))

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(lebar / 2, y, "Kalkulator Pajak TSP Grup")
    y -= 0.6 * cm
    c.setFont("Helvetica", 9)
    c.drawCentredString(lebar / 2, y, "Lampiran Perhitungan Pajak Pembayaran Vendor")
    y -= 0.4 * cm
    c.line(margin_kiri, y, margin_kanan, y)
    y -= 0.7 * cm

    nama_gabungan = data["nama_vendor"]
    if data["nama_lain_vendor"]:
        nama_gabungan += f" ({data['nama_lain_vendor']})"
    tulis_baris(margin_kiri, y, "Nama Vendor", nama_gabungan)
    y -= 0.5 * cm
    tulis_baris(margin_kiri, y, "Deskripsi", data["deskripsi_transaksi"])
    y -= 0.5 * cm
    tulis_baris(kolom1_x, y, "Jenis Vendor", data["jenis_vendor"])
    tulis_baris(kolom2_x, y, "Pekerjaan", data["jenis_pekerjaan"])
    y -= 0.6 * cm
    c.line(margin_kiri, y, margin_kanan, y)
    y -= 0.7 * cm

    tulis_baris(margin_kiri, y, "Jenis Pajak", data["jenis_pajak"])
    y -= 0.5 * cm
    tulis_baris(kolom1_x, y, "Metode", data["metode"])
    tulis_baris(kolom2_x, y, "Cara Bayar", data["cara_bayar"])
    y -= 0.6 * cm
    c.line(margin_kiri, y, margin_kanan, y)
    y -= 0.8 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_kiri, y, "Hasil Perhitungan")
    y -= 0.6 * cm

    if data["no_bukti"]:
        c.setFont("Helvetica", 9)
        c.drawString(margin_kiri, y, f"No. Bukti: {data['no_bukti']}")
        y -= 0.6 * cm

    if not data["tampilkan_tabel"]:
        nilai_x = margin_kiri + 9 * cm

        c.setFont("Helvetica", 10)
        c.drawString(margin_kiri, y, "Harga Disepakati")
        c.drawRightString(nilai_x, y, rupiah(data["harga_disepakati"]))
        y -= 0.9 * cm

        baris_hasil = [
            (data["label_dpp"], data["dpp_seharusnya"]),
            ("PPN", data["ppn"]),
        ]
        if data["dpp_kena_pph"] is not None:
            baris_hasil.append(("DPP Kena PPh", data["dpp_kena_pph"]))
        baris_hasil.append(("PPh", data["pph"]))
        for label, isi in baris_hasil:
            if label == "PPh":
                c.saveState()
                c.setFillColorRGB(0.106, 0.310, 0.447, alpha=0.12)
                c.rect(margin_kiri - 0.2 * cm, y - 0.15 * cm, (nilai_x - margin_kiri) + 0.4 * cm, 0.45 * cm, fill=1, stroke=0)
                c.restoreState()

            c.setFont("Helvetica", 10)
            c.drawString(margin_kiri, y, label)
            c.drawRightString(nilai_x, y, rupiah(isi))
            y -= 0.5 * cm

        y -= 0.2 * cm
        c.line(margin_kiri, y, nilai_x, y)
        y -= 0.6 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_kiri, y, "Dibayarkan")
        c.drawRightString(nilai_x, y, rupiah(data["dibayarkan"]))
    else:
        lebar_no = 0.9 * cm
        lebar_bukti = 4 * cm
        lebar_kolom_angka = (margin_kanan - margin_kiri - lebar_no - lebar_bukti) / 4

        x_no = margin_kiri
        x_bukti = x_no + lebar_no
        x_harga = x_bukti + lebar_bukti
        x_dpp = x_harga + lebar_kolom_angka
        x_pph = x_dpp + lebar_kolom_angka
        x_bayar = x_pph + lebar_kolom_angka

        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_no, y, "No")
        c.drawString(x_bukti, y, data["label_kolom_bukti"])
        c.drawRightString(x_harga + lebar_kolom_angka, y, "Harga")
        c.drawRightString(x_dpp + lebar_kolom_angka, y, "DPP")
        c.drawRightString(x_pph + lebar_kolom_angka, y, "PPh")
        c.drawRightString(x_bayar + lebar_kolom_angka, y, "Dibayarkan")
        y -= 0.35 * cm
        c.line(margin_kiri, y, margin_kanan, y)
        y -= 0.45 * cm

        c.setFont("Helvetica", 8)
        for baris in data["baris_tabel"]:
            c.drawString(x_no, y, str(baris["no"]))
            c.drawString(x_bukti, y, str(baris["label_bukti"])[:20])
            c.drawRightString(x_harga + lebar_kolom_angka, y, rupiah(baris["nilai"]))
            c.drawRightString(x_dpp + lebar_kolom_angka, y, rupiah(baris["dpp"]))
            c.drawRightString(x_pph + lebar_kolom_angka, y, rupiah(baris["pph"]))
            c.drawRightString(x_bayar + lebar_kolom_angka, y, rupiah(baris["dibayarkan"]))
            y -= 0.45 * cm

        y -= 0.15 * cm
        c.line(margin_kiri, y, margin_kanan, y)
        y -= 0.8 * cm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_kiri, y, "Total DPP")
        c.drawRightString(lebar / 2 - 0.3 * cm, y, rupiah(data["dpp_seharusnya"]))
        y -= 0.7 * cm
        c.drawString(margin_kiri, y, "Total PPh")
        c.drawRightString(lebar / 2 - 0.3 * cm, y, rupiah(data["pph"]))
        y -= 0.7 * cm
        c.drawString(margin_kiri, y, "Total Dibayarkan")
        c.drawRightString(lebar / 2 - 0.3 * cm, y, rupiah(data["dibayarkan"]))

    c.setFont("Helvetica", 8)
    tanggal_cetak = datetime.now().strftime("%d %B %Y, %H:%M")
    c.drawRightString(margin_kanan, 1 * cm, f"Dicetak: {tanggal_cetak} - Pajak TSP")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ========================= FORM =========================

with st.container(border=True):
    st.subheader("1. Identitas Vendor & Transaksi")
    col1, col2 = st.columns(2)
    with col1:
        nama_vendor = st.text_input("Nama Vendor Sesuai Identitas")
    with col2:
        nama_lain_vendor = st.text_input(
            "Nama Lain Vendor (Brand/Merk/Alias)",
            help="Opsional - kosongkan jika vendor tidak punya nama lain"
        )
    col_deskripsi, _ = st.columns(2)
    with col_deskripsi:
        deskripsi_transaksi = st.text_area(
            "Deskripsi Singkat Transaksi",
            placeholder="Pekerjaan Apa? Di Lokasi Mana? Membuat Apa?"
        )

with st.container(border=True):
    st.subheader("2. Skema Pajak")
    col1, col2 = st.columns(2)
    with col1:
        metode = st.selectbox(
            "Metode Disepakati", ["Potong PPh", "Gross Up"],
            index=None, placeholder="Pilih Salah Satu!"
        )
        jenis_vendor = st.selectbox(
            "Jenis Vendor", ["Orang Pribadi", "Badan (PT/CV/Lainnya)"],
            index=None, placeholder="Pilih Salah Satu!"
        )
        status_pkp = st.radio("Apakah Vendor Ber-PPN (PKP)?", ["Ya", "Tidak"], index=None)

    with col2:
        jenis_pekerjaan = st.selectbox(
            "Jenis Pekerjaan",
            [
                "Jasa Konstruksi (Membangun Bangunan)",
                "Jasa Lainnya / Bukan Konstruksi",
                "Sewa Tanah / Bangunan",
                "Sewa Lainnya (Mesin, Kendaraan, Peralatan)",
            ],
            index=None, placeholder="Pilih Salah Satu!"
        )
        if jenis_pekerjaan == "Jasa Konstruksi (Membangun Bangunan)":
            sub_konstruksi = st.radio(
                "Jenis Layanan Konstruksi",
                ["Pekerjaan Konstruksi (Fisik: bangun/renovasi/bongkar)", "Konsultasi Konstruksi (Perencanaan/Pengawasan)"],
                index=None
            )
            if sub_konstruksi == "Pekerjaan Konstruksi (Fisik: bangun/renovasi/bongkar)":
                status_sertifikat = st.radio(
                    "Status Sertifikat Vendor",
                    [
                        "Bersertifikat - Kualifikasi Kecil / Perseorangan",
                        "Bersertifikat - Kualifikasi Menengah / Besar / Spesialis",
                        "Tidak Bersertifikat",
                    ],
                    index=None
                )
            elif sub_konstruksi == "Konsultasi Konstruksi (Perencanaan/Pengawasan)":
                status_sertifikat = st.radio(
                    "Status Sertifikat Vendor",
                    ["Bersertifikat", "Tidak Bersertifikat"],
                    index=None
                )

        if jenis_vendor == "Orang Pribadi":
            col_ktp, _ = st.columns(2)
            with col_ktp:
                status_ktp = st.radio("Apakah sudah ada KTP?", ["Sudah", "Belum"], index=None)
                if status_ktp == "Sudah":
                    no_ktp = st.text_input("Masukkan 16 digit Nomor KTP", max_chars=16)
                    st.session_state.ktp_popup_shown = False
                elif status_ktp == "Belum":
                    if not st.session_state.get("ktp_popup_shown", False):
                        st.session_state.ktp_popup_shown = True
                        show_popup_ktp()
                else:
                    st.session_state.ktp_popup_shown = False
        else:
            st.session_state.ktp_popup_shown = False

with st.container(border=True):
    st.subheader("3. Nilai & Pembayaran")

    jumlah_transaksi_mode = st.radio(
        "Jumlah Transaksi", ["1 Transaksi", "Lebih dari 1 Transaksi"], index=None
    )

    daftar_transaksi = []

    if jumlah_transaksi_mode == "1 Transaksi":
        col1, col2 = st.columns(2)
        with col1:
            no_bukti = st.text_input("No. Nota/Invoice/Faktur Pajak")
        with col2:
            nilai_disepakati = st.number_input(
                "Nilai Disepakati (Rp)", min_value=0, step=100000, format="%d"
            )
            nilai_format = f"{nilai_disepakati:,.0f}".replace(",", ".")
            st.caption(f"Rp {nilai_format}")
        daftar_transaksi.append({"no_bukti": no_bukti, "nilai": nilai_disepakati})

    elif jumlah_transaksi_mode == "Lebih dari 1 Transaksi":
        jumlah_transaksi = st.number_input(
            "Jumlah Transaksi", min_value=2, max_value=10, step=1, value=2
        )
        for i in range(jumlah_transaksi):
            st.write(f"**Transaksi ke-{i + 1}**")
            col1, col2 = st.columns(2)
            with col1:
                no_bukti_i = st.text_input(
                    f"No. Nota/Invoice/Faktur Pajak ke-{i + 1}", key=f"nobukti_{i}"
                )
            with col2:
                nilai_i = st.number_input(
                    f"Nilai Disepakati ke-{i + 1} (Rp)",
                    min_value=0, step=100000, format="%d", key=f"nilai_transaksi_{i}"
                )
            daftar_transaksi.append({"no_bukti": no_bukti_i, "nilai": nilai_i})

        nilai_disepakati = sum(item["nilai"] for item in daftar_transaksi)
        nilai_format = f"{nilai_disepakati:,.0f}".replace(",", ".")
        st.caption(f"Total Nilai Disepakati: Rp {nilai_format}")
    else:
        nilai_disepakati = 0
    if jenis_pekerjaan in ["Sewa Lainnya (Mesin, Kendaraan, Peralatan)", "Jasa Lainnya / Bukan Konstruksi"]:
        komposisi_transaksi = st.radio(
            "Komposisi Transaksi",
            ["Murni Jasa", "Campuran Barang & Jasa"],
            index=None
        )
        if komposisi_transaksi == "Campuran Barang & Jasa":
            nilai_jasa = st.number_input(
                "Nilai Jasa (Dasar Pengenaan PPh)",
                min_value=0,
                max_value=nilai_disepakati,
                step=100000,
                format="%d"
            )
            nilai_jasa_format = f"{nilai_jasa:,.0f}".replace(",", ".")
            st.caption(f"Rp {nilai_jasa_format} dari total akan dikenakan PPh, sisanya (Rp {nilai_disepakati - nilai_jasa:,.0f}".replace(",", ".") + ") dianggap komponen Barang")
        else:
            nilai_jasa = nilai_disepakati
    else:
        komposisi_transaksi = "Murni Jasa"
        nilai_jasa = nilai_disepakati

    col_bayar, _ = st.columns(2)
    with col_bayar:
        cara_bayar = st.selectbox(
            "Cara Bayar", ["Sekali Bayar", "Termin Pekerjaan"],
            index=None, placeholder="Pilih Salah Satu!"
        )

    if cara_bayar == "Termin Pekerjaan":
        jumlah_termin = st.number_input(
            "Jumlah Termin", min_value=2, max_value=5, step=1, value=2
        )
        nilai_per_termin = []
        for i in range(jumlah_termin):
            is_termin_terakhir = (i == jumlah_termin - 1)
            if is_termin_terakhir:
                sisa = nilai_disepakati - sum(nilai_per_termin)
                sisa = max(sisa, 0)
                sisa_format = f"{sisa:,.0f}".replace(",", ".")
                st.caption(f"Sisa maksimal untuk termin terakhir: Rp {sisa_format}")
                nominal = st.number_input(
                    f"Nominal Termin ke-{i + 1} (Rp)",
                    min_value=0, max_value=sisa, step=100000, format="%d", key=f"termin_{i}"
                )
            else:
                nominal = st.number_input(
                    f"Nominal Termin ke-{i + 1} (Rp)",
                    min_value=0, step=100000, format="%d", key=f"termin_{i}"
                )
            nilai_per_termin.append(nominal)
            if nilai_disepakati > 0:
                persen = (nominal / nilai_disepakati) * 100
                st.caption(f"≈ {persen:.1f}% dari nilai disepakati")

# ========================= VALIDASI =========================

semua_lengkap = True
if not nama_vendor:
    semua_lengkap = False
if not deskripsi_transaksi:
    semua_lengkap = False
if metode is None:
    semua_lengkap = False
if jenis_vendor is None:
    semua_lengkap = False
if jenis_pekerjaan is None:
    semua_lengkap = False
if jumlah_transaksi_mode is None:
    semua_lengkap = False
elif jumlah_transaksi_mode == "1 Transaksi":
    if not no_bukti or nilai_disepakati <= 0:
        semua_lengkap = False
else:
    for item in daftar_transaksi:
        if not item["no_bukti"] or item["nilai"] <= 0:
            semua_lengkap = False
if cara_bayar is None:
    semua_lengkap = False
if status_pkp is None:
    semua_lengkap = False

if jenis_vendor == "Orang Pribadi":
    if status_ktp is None:
        semua_lengkap = False
    elif status_ktp == "Sudah":
        if not no_ktp or len(no_ktp) != 16 or not no_ktp.isdigit():
            semua_lengkap = False
    elif status_ktp == "Belum":
        semua_lengkap = False

if jenis_pekerjaan == "Jasa Konstruksi (Membangun Bangunan)":
    if sub_konstruksi is None:
        semua_lengkap = False
    elif status_sertifikat is None:
        semua_lengkap = False

if cara_bayar == "Termin Pekerjaan":
    if sum(nilai_per_termin) != nilai_disepakati:
        semua_lengkap = False

klik_hitung = st.button("Lanjut Hitung Pajak", disabled=not semua_lengkap, type="primary")

# ========================= HASIL =========================

if klik_hitung:
    st.divider()
    st.subheader("Hasil Perhitungan")
    daftar_notes = []
    tarif_pph = tentukan_tarif_pph()
    dpp = nilai_disepakati

    if status_pkp == "Tidak":
        daftar_notes.append("Karena Vendor bukan PKP Maka PPN tidak dipungut pada transaksi ini.")
    if jenis_vendor == "Orang Pribadi":
        daftar_notes.append("Vendor Orang Pribadi: pastikan NIK terbaca JELAS karena Coretax perlu input tersebut.")
    if metode == "Gross Up":
        daftar_notes.append("Skema Gross Up: nilai PPh jadi tanggungan perusahaan. Pastikan skema ini sudah disepakati dengan vendor.")
    if cara_bayar == "Termin Pekerjaan":
        daftar_notes.append(f"Pembayaran dibagi {jumlah_termin} termin. Total seluruh termin telah divalidasi sama dengan Nilai Disepakati.")
    if komposisi_transaksi == "Campuran Barang & Jasa":
        nilai_jasa_fmt = f"{nilai_jasa:,.0f}".replace(",", ".")
        daftar_notes.append(f"Transaksi campuran Barang & Jasa: PPh hanya dihitung dari Nilai Jasa (Rp {nilai_jasa_fmt}), bukan dari total nilai transaksi.")
    daftar_notes.append("APABILA RAGU DENGAN HASIL PERHITUNGAN DI SINI, HUBUNGI BAGIAN PAJAK.")

    if tarif_pph != "PROGRESIF_PPH21":
        if metode == "Potong PPh":
            dpp_seharusnya = dpp
            pph = nilai_jasa * tarif_pph
        else:
            nilai_jasa_seharusnya = nilai_jasa / (1 - tarif_pph)
            pph = nilai_jasa_seharusnya * tarif_pph
            dpp_seharusnya = (dpp - nilai_jasa) + nilai_jasa_seharusnya
    else:
        if metode == "Potong PPh":
            dpp_seharusnya = dpp
            dpp_pkp = nilai_jasa * config.PERSEN_DPP_PPH21_TENAGA_AHLI
            pph = hitung_pph21_progresif(dpp_pkp)
        else:
            nilai_jasa_seharusnya = hitung_gross_up_pph21(nilai_jasa)
            dpp_pkp_seharusnya = nilai_jasa_seharusnya * config.PERSEN_DPP_PPH21_TENAGA_AHLI
            pph = hitung_pph21_progresif(dpp_pkp_seharusnya)
            dpp_seharusnya = (dpp - nilai_jasa) + nilai_jasa_seharusnya

    if status_pkp == "Ya":
        ppn = dpp_seharusnya * config.TARIF_PPN
    else:
        ppn = 0

    dibayarkan = dpp_seharusnya - pph + ppn
    if komposisi_transaksi == "Campuran Barang & Jasa":
        dpp_kena_pph = nilai_jasa if metode == "Potong PPh" else nilai_jasa_seharusnya
    else:
        dpp_kena_pph = None
    label_dpp = "DPP" if metode == "Potong PPh" else "DPP (Gross-Up)"

    tampilkan_tabel = False
    baris_tabel = []
    label_kolom_bukti = "No. Bukti"

    if jumlah_transaksi_mode == "Lebih dari 1 Transaksi":
        tampilkan_tabel = True
        label_kolom_bukti = "No. Bukti"
        for item in daftar_transaksi:
            rasio = item["nilai"] / nilai_disepakati
            baris_tabel.append({
                "label_bukti": item["no_bukti"],
                "nilai": item["nilai"],
                "dpp": dpp_seharusnya * rasio,
                "pph": pph * rasio,
                "dibayarkan": dibayarkan * rasio,
            })
    elif cara_bayar == "Termin Pekerjaan":
        tampilkan_tabel = True
        label_kolom_bukti = "Termin"
        for i, nominal in enumerate(nilai_per_termin):
            rasio = nominal / nilai_disepakati
            baris_tabel.append({
                "label_bukti": f"Termin ke-{i + 1}",
                "nilai": nominal,
                "dpp": dpp_seharusnya * rasio,
                "pph": pph * rasio,
                "dibayarkan": dibayarkan * rasio,
            })

    harga_format = f"{dpp:,.0f}".replace(",", ".")
    dpp_seharusnya_format = f"{dpp_seharusnya:,.0f}".replace(",", ".")
    ppn_format = f"{ppn:,.0f}".replace(",", ".")
    pph_format = f"{pph:,.0f}".replace(",", ".")
    dibayarkan_format = f"{dibayarkan:,.0f}".replace(",", ".")

    if data_no_bukti := (no_bukti if jumlah_transaksi_mode == "1 Transaksi" else None):
        st.write(f"No. Bukti: {data_no_bukti}")

    if not tampilkan_tabel:
        st.write(f"Harga Disepakati: Rp {harga_format}")
        st.write("")
        st.write(f"{label_dpp}: Rp {dpp_seharusnya_format}")
        st.write(f"PPN ({config.TARIF_PPN * 100:.0f}%): Rp {ppn_format}")
        if dpp_kena_pph is not None:
            dpp_kena_pph_format = f"{dpp_kena_pph:,.0f}".replace(",", ".")
            st.write(f"DPP Kena PPh: Rp {dpp_kena_pph_format}")
        st.write(f"PPh: Rp {pph_format}")
        st.write(f"**Dibayarkan: Rp {dibayarkan_format}**")
    else:
        tabel_tampil = []
        for i, baris in enumerate(baris_tabel):
            tabel_tampil.append({
                "No": i + 1,
                label_kolom_bukti: baris["label_bukti"],
                "Harga Disepakati": f"Rp {baris['nilai']:,.0f}".replace(",", "."),
                "DPP": f"Rp {baris['dpp']:,.0f}".replace(",", "."),
                "PPh": f"Rp {baris['pph']:,.0f}".replace(",", "."),
                "Dibayarkan": f"Rp {baris['dibayarkan']:,.0f}".replace(",", "."),
            })
        st.dataframe(tabel_tampil, hide_index=True, use_container_width=True)
        kolom1, kolom2, kolom3 = st.columns(3)
        kolom1.metric("Total DPP", f"Rp {dpp_seharusnya_format}")
        kolom2.metric("Total PPh", f"Rp {pph_format}")
        kolom3.metric("Total Dibayarkan", f"Rp {dibayarkan_format}")

    if daftar_notes:
        st.divider()
        st.subheader("Notes / Peringatan")
        for catatan in daftar_notes:
            st.warning(catatan)

    data_pdf = {
        "nama_vendor": nama_vendor,
        "nama_lain_vendor": nama_lain_vendor,
        "deskripsi_transaksi": deskripsi_transaksi,
        "jenis_pajak": label_jenis_pajak(),
        "metode": metode,
        "jenis_vendor": jenis_vendor,
        "jenis_pekerjaan": jenis_pekerjaan,
        "cara_bayar": cara_bayar,
        "harga_disepakati": dpp,
        "label_dpp": label_dpp,
        "dpp_seharusnya": dpp_seharusnya,
        "ppn": ppn,
        "pph": pph,
        "dpp_kena_pph": dpp_kena_pph,
        "dibayarkan": dibayarkan,
        "tampilkan_tabel": tampilkan_tabel,
        "label_kolom_bukti": label_kolom_bukti,
        "no_bukti": no_bukti if jumlah_transaksi_mode == "1 Transaksi" else None,
        "baris_tabel": [
            {"no": i + 1, **baris}
            for i, baris in enumerate(baris_tabel)
        ],
    }

    pdf_buffer = buat_pdf(data_pdf)
    st.download_button(
        "Download PDF",
        data=pdf_buffer,
        file_name="perhitungan_pajak.pdf",
        mime="application/pdf",
        key="download_pdf_final"
    )