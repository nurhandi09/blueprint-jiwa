import streamlit as st
from datetime import datetime
import base64
import io
import pdfkit

# ====================================
# LOGIKA BLUEPRINT JIWA (MVP)
# ====================================

def hitung_tipe(jam):
    h = int(jam.split(":")[0])
    if 6 <= h < 12: return "Projector"
    elif 12 <= h < 18: return "Generator"
    elif 18 <= h < 22: return "Manifesting Generator"
    elif 22 <= h or h < 2: return "Manifestor"
    else: return "Reflector"

def hitung_authority(tanggal):
    d = int(tanggal.split("-")[2])
    if d % 5 == 0: return "Emotional"
    elif d % 3 == 0: return "Sacral"
    elif d % 2 == 0: return "Splenic"
    else: return "Ego"

def hitung_profile(tanggal):
    bulan = int(tanggal.split("-")[1])
    profiles = ["1/3", "2/4", "3/5", "4/6", "5/1", "6/2"]
    return profiles[(bulan - 1) % 6]

def insight_yosep(tipe):
    pesan = {
        "Generator": "Lo itu MESIN ENERGI HIDUP. Kalau lo seneng, semua orang ikut nyala.",
        "Manifesting Generator": "Multi-tasking master. Gerak cepet, lompat-lompat, tapi hasilnya selalu gila.",
        "Projector": "Lo pembaca manusia level dewa. Energi lo buat NGARAHIN, bukan ngegas sendiri.",
        "Manifestor": "Lo initiator bawaannya. Ngegas dulu, mikir belakangan — itu DNA lo.",
        "Reflector": "Lo cermin masyarakat. Lingkungan bagus = lo bersinar terang banget."
    }
    return pesan.get(tipe, "Lo langka bro. Jalur lo beda sendiri.")

# ====================================
# UI STREAMLIT
# ====================================

st.set_page_config(page_title="Blueprint Jiwa", page_icon="🔮")
st.title("🔮 BLUEPRINT JIWA")
st.caption("by Yosep × Rhea — MVP Desember 2025")

nama = st.text_input("Nama Lengkap")
tanggal = st.date_input("Tanggal Lahir", value=datetime(2000, 1, 1))
jam = st.time_input("Jam Lahir (lokal)", value=datetime.now().time())
kota = st.text_input("Kota Kelahiran")

if st.button("PROSES BLUEPRINT JIWA", type="primary"):
    if not nama or not kota:
        st.error("Nama & kota wajib diisi ya bro!")
    else:
        tgl_str = tanggal.strftime("%Y-%m-%d")
        jam_str = jam.strftime("%H:%M")
        
        tipe = hitung_tipe(jam_str)
        authority = hitung_authority(tgl_str)
        profile = hitung_profile(tgl_str)
        insight = insight_yosep(tipe)

        st.balloons()
        st.success(f"Blueprint {nama.upper()} SELESAI!")

        st.write(f"**Tipe:** {tipe}")
        st.write(f"**Authority:** {authority}")
        st.write(f"**Profile:** {profile}")
        st.write(f"**Insight Yosep:** {insight}")

        # PDF NEON MERAH
        html = f"""
        <html>
        <head>
            <style>
                body {{font-family: Arial; background:#000; color:white; padding:50px; text-align:center;}}
                h1 {{color:#ff0066; text-shadow:0 0 20px #ff0066; font-size:50px;}}
                h2 {{color:#ff3366;}}
                hr {{border:2px solid #ff0066;}}
            </style>
        </head>
        <body>
            <h1>BLUEPRINT JIWA</h1>
            <h2>{nama.upper()}</h2>
            <p>{tgl_str} | {jam_str} | {kota}</p>
            <hr>
            <h2>TIPE: {tipe}</h2>
            <h2>AUTHORITY: {authority}</h2>
            <h2>PROFILE: {profile}</h2>
            <p style="font-size:20px;">"{insight}"</p>
            <p style="color:#666; margin-top:50px;">Powered by Yosep × Rhea • 2025</p>
        </body>
        </html>
        """

        # Generate PDF
        pdf_buffer = io.BytesIO()
        pdfkit.from_string(html, pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()
        b64 = base64.b64encode(pdf_bytes).decode()

        href = f'<a href="data:application/pdf;base64,{b64}" download="Blueprint_Jiwa_{nama}.pdf"><button style="background:#ff0066; color:white; padding:15px 40px; border:none; border-radius:50px; font-size:20px; cursor:pointer;">DOWNLOAD PDF NEON</button></a>'
        st.markdown(href, unsafe_allow_html=True)
