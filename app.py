import streamlit as st
from datetime import datetime, date, time
import pdfkit
import tempfile
import base64
import pytz

# ============================================================
#   KONVERSI JAM LOKAL → UTC (WAJIB UNTUK HUMAN DESIGN)
# ============================================================

def to_utc(tanggal: date, jam: time, timezone="Asia/Jakarta"):
    local = pytz.timezone(timezone)
    dt_local = local.localize(datetime.combine(tanggal, jam))
    dt_utc = dt_local.astimezone(pytz.utc)
    return dt_utc


# ============================================================
#   LOGIKA HITUNG HUMAN DESIGN SEDERHANA (MVP)
#   (nanti bisa kita upgrade ke kalkulasi gate-channel)
# ============================================================

def hitung_tipe(jam_str):
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

def hitung_authority(date_str):
    d = int(date_str.split("-")[-1])
    if d % 5 == 0:
        return "Emotional"
    elif d % 3 == 0:
        return "Sacral"
    elif d % 2 == 0:
        return "Splenic"
    else:
        return "Ego"

def hitung_profile(date_str):
    bulan = int(date_str.split("-")[1])
    profiles = ["1/3", "2/4", "3/5", "4/6", "5/1", "6/2"]
    return profiles[(bulan - 1) % 6]

def insight_yosep(tipe):
    mapping = {
        "Generator": "Lo itu mesin energi hidup, Bos. Kalau lo happy, semua orang happy.",
        "Manifesting Generator": "Gerak cepat, adaptif, lompat-lompat tapi hasil selalu kenceng.",
        "Projector": "Lo itu pembaca manusia. Bukan tenaga, tapi arah.",
        "Manifestor": "Lo suka ngegas dulu, mikir belakangan. Wajar, energi lo emang buat mulai.",
        "Reflector": "Lo itu cermin hidup. Lingkungan bikin lo bersinar atau redup."
    }
    return mapping.get(tipe, "Unik, beda, dan punya jalur sendiri.")


# ============================================================
#                  STREAMLIT APP
# ============================================================

st.title("🔮 Blueprint Jiwa — Quick Reader (MVP UTC Version)")
st.caption("Hitungan Blueprint sudah dikoreksi pakai UTC (standar Human Design)")

nama = st.text_input("Nama")
tanggal = st.date_input("Tanggal Lahir")
jam = st.time_input("Jam Lahir (Lokal)")
kota = st.text_input("Kota Lahir (opsional)")

if st.button("Proses Blueprint"):
    # =====================
    #   Convert ke UTC
    # =====================
    dt_utc = to_utc(tanggal, jam)
    
    utc_time_str = dt_utc.strftime("%H:%M")
    utc_date_str = dt_utc.strftime("%Y-%m-%d")

    # =====================
    #   HITUNG HD (MVP)
    # =====================
    tipe = hitung_tipe(utc_time_str)
    authority = hitung_authority(utc_date_str)
    profile = hitung_profile(utc_date_str)
    insight = insight_yosep(tipe)

    # =====================
    #   TAMPILKAN
    # =====================
    st.subheader(f"✨ Blueprint untuk {nama}")
    st.write(f"**Tipe:** {tipe}")
    st.write(f"**Authority:** {authority}")
    st.write(f"**Profile:** {profile}")
    st.write(f"**Insight Yosep-style:** {insight}")
    st.info(f"⏱ Perhitungan berdasarkan waktu **UTC**: {utc_date_str} {utc_time_str}")

    # =====================
    #   GENERATE PDF
    # =====================
    html = f"""
    <h2>Blueprint Jiwa — {nama}</h2>
    <p><b>Tanggal (UTC):</b> {utc_date_str}</p>
    <p><b>Jam (UTC):</b> {utc_time_str}</p>
    <p><b>Kota:</b> {kota}</p>
    <hr>
    <p><b>Tipe:</b> {tipe}</p>
    <p><b>Authority:</b> {authority}</p>
    <p><b>Profile:</b> {profile}</p>
    <p><b>Insight Yosep:</b> {insight}</p>
    """

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        pdfkit.from_string(html, f.name)
        pdf_bytes = f.read()

    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="Blueprint_{nama}.pdf">📥 Download PDF</a>'
    st.markdown(href, unsafe_allow_html=True)
