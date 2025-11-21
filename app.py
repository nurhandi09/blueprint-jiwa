import streamlit as st
from datetime import datetime, date, time
import pytz
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# ============================================================
#   KONVERSI JAM LOKAL → UTC (WAJIB UNTUK HUMAN DESIGN)
# ============================================================

def to_utc(tanggal: date, jam: time, timezone: str = "Asia/Jakarta"):
    """
    Konversi tanggal & jam lokal (misal WIB) ke UTC.
    Human Design pakai waktu UTC buat hitungan posisi planet.
    """
    local_tz = pytz.timezone(timezone)
    dt_local = local_tz.localize(datetime.combine(tanggal, jam))
    dt_utc = dt_local.astimezone(pytz.utc)
    return dt_utc


# ============================================================
#   LOGIKA HITUNG HUMAN DESIGN SEDERHANA (MVP)
#   (placeholder: nanti bisa diganti engine HD beneran)
# ============================================================

def hitung_tipe(jam_str: str) -> str:
    h = int(jam_str.split(":")[0])
    if 6 <= h < 12:
        return "Projector"
    elif 12 <= h < 18:
        return "Generator"
    elif 18 <= h < 22:
        return "Manifesting Generator"
    elif 22 <= h or h < 2:
        return "Manifestor"
    else:
        return "Reflector"

def hitung_authority(date_str: str) -> str:
    d = int(date_str.split("-")[-1])
    if d % 5 == 0:
        return "Emotional"
    elif d % 3 == 0:
        return "Sacral"
    elif d % 2 == 0:
        return "Splenic"
    else:
        return "Ego"

def hitung_profile(date_str: str) -> str:
    bulan = int(date_str.split("-")[1])
    profiles = ["1/3", "2/4", "3/5", "4/6", "5/1", "6/2"]
    return profiles[(bulan - 1) % 6]

def insight_yosep(tipe: str) -> str:
    mapping = {
        "Generator": "Lo itu mesin energi hidup, Bos. Kalau lo happy, semua orang happy.",
        "Manifesting Generator": "Gerak cepat, adaptif, lompat-lompat tapi hasil selalu kenceng.",
        "Projector": "Lo itu pembaca manusia. Bukan tenaga, tapi arah.",
        "Manifestor": "Lo suka ngegas dulu, mikir belakangan. Wajar, energi lo emang buat mulai.",
        "Reflector": "Lo itu cermin hidup. Lingkungan bikin lo bersinar atau redup.",
    }
    return mapping.get(tipe, "Unik, beda, dan punya jalur sendiri.")


# ============================================================
#   FUNGSI BIKIN PDF PAKAI REPORTLAB
# ============================================================

def buat_pdf_blueprint(nama: str,
                       kota: str,
                       utc_date_str: str,
                       utc_time_str: str,
                       tipe: str,
                       authority: str,
                       profile: str,
                       insight: str) -> bytes:
    """
    Bikin PDF 1 halaman sederhana pakai reportlab.
    Return: bytes siap dikirim ke download_button.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 50
    y = height - 60

    # Judul
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin_x, y, f"Blueprint Jiwa — {nama}")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(margin_x, y, f"Tanggal (UTC): {utc_date_str}")
    y -= 18
    c.drawString(margin_x, y, f"Jam (UTC): {utc_time_str}")
    y -= 18
    if kota:
        c.drawString(margin_x, y, f"Kota Lahir: {kota}")
        y -= 24
    else:
        y -= 12

    # Garis
    c.line(margin_x, y, width - margin_x, y)
    y -= 24

    # Data HD
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Ringkasan Blueprint")
    y -= 22

    c.setFont("Helvetica", 11)
    c.drawString(margin_x, y, f"Tipe: {tipe}")
    y -= 18
    c.drawString(margin_x, y, f"Authority: {authority}")
    y -= 18
    c.drawString(margin_x, y, f"Profile: {profile}")
    y -= 24

    # Insight
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Insight Yosep Nurhandi:")
    y -= 20

    c.setFont("Helvetica", 11)

    # Bungkus teks insight kalau kepanjangan
    max_width = width - 2 * margin_x
    words = insight.split(" ")
    line = ""
    for w in words:
        calon = (line + " " + w).strip()
        if c.stringWidth(calon, "Helvetica", 11) < max_width:
            line = calon
        else:
            c.drawString(margin_x, y, line)
            y -= 16
            line = w
    if line:
        c.drawString(margin_x, y, line)
        y -= 20

    # Footer kecil
    y_footer = 40
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(margin_x, y_footer,
                 "Blueprint Jiwa — MVP | Dicetak otomatis dari aplikasi Human Design Quick Reader.")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ============================================================
#                  STREAMLIT APP
# ============================================================

st.set_page_config(page_title="Blueprint Jiwa — Quick Reader", page_icon="🔮")

st.title("🔮 Blueprint Jiwa — Quick Reader (MVP UTC Version)")
st.caption("Hitungan waktu sudah dikonversi ke UTC (standar Human Design).")

st.markdown("Masukkan data lahir, lalu klik **Proses Blueprint** untuk melihat ringkasan cepat.")

nama = st.text_input("Nama")
tanggal = st.date_input("Tanggal Lahir")
jam = st.time_input("Jam Lahir (waktu lokal, misal WIB)")
kota = st.text_input("Kota Lahir (opsional, untuk tampil di PDF)")

if st.button("Proses Blueprint"):
    if not nama:
        st.warning("Isi nama dulu, Bos.")
    else:
        # 1) Convert ke UTC
        dt_utc = to_utc(tanggal, jam, timezone="Asia/Jakarta")
        utc_time_str = dt_utc.strftime("%H:%M")
        utc_date_str = dt_utc.strftime("%Y-%m-%d")

        # 2) Hitung blueprint sederhana berbasis UTC
        tipe = hitung_tipe(utc_time_str)
        authority = hitung_authority(utc_date_str)
        profile = hitung_profile(utc_date_str)
        insight = insight_yosep(tipe)

        # 3) Tampilkan di layar
        st.subheader(f"✨ Blueprint untuk {nama}")
        st.write(f"**Tipe:** {tipe}")
        st.write(f"**Authority:** {authority}")
        st.write(f"**Profile:** {profile}")
        st.write(f"**Insight Yosep-style:** {insight}")
        st.info(f"Perhitungan waktu berdasarkan **UTC**: {utc_date_str} {utc_time_str}")

        # 4) Bikin PDF dan kasih tombol download
        pdf_bytes = buat_pdf_blueprint(
            nama=nama,
            kota=kota,
            utc_date_str=utc_date_str,
            utc_time_str=utc_time_str,
            tipe=tipe,
            authority=authority,
            profile=profile,
            insight=insight,
        )

        st.download_button(
            label="📥 Download PDF Blueprint",
            data=pdf_bytes,
            file_name=f"Blueprint_{nama}.pdf",
            mime="application/pdf",
        )
