import streamlit as st
from datetime import datetime
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, red, white

st.set_page_config(page_title="Blueprint Jiwa",page_icon="🔮",layout="centered")

st.markdown("""
<style>
    .main {background-color:#000000;}
    .stButton>button {background:#ff0066;color:white;width:100%;height:60px;font-size:22px;border-radius:50px;}
    .stTextInput>div>div>input {background-color:#1e1e1e;color:white;border:1px solid #ff0066}
    .stDateInput>div>div>div>input {background-color:#1e1e1e;color:white;border:1px solid #ff0066}
    .stTimeInput>div>div>input {background-color:#1e1e1e;color:white;border:1px solid #ff0066}
</style>""",unsafe_allow_html=True)

st.image("https://i.imgur.com/5zQJqK.png",width=150) # optional logo kalo lo punya
st.title("🔮 BLUEPRINT JIWA")
st.caption("by Yosep × Rhea — Desember 2025 Edition")

col1, col2 = st.columns(2)
with col1:
    nama = st.text_input("Nama Lengkap",placeholder="Masukkan nama lengkap")
with col2:
    kota = st.text_input("Kota Kelahiran",placeholder="Jakarta / Surabaya / dll")

tanggal = st.date_input(
    "Tanggal Lahir",
    min_value=datetime(1950,1,1),
    max_value=datetime(2030,12,31),
    value=datetime(2000,1,1),
    help="1950-2030 semua umur masuk"
)

jam = st.time_input("Jam Lahir (lokal)",value=datetime.now().time())

if st.button("🔥 PROSES BLUEPRINT JIWA",type="primary"):
    if not nama.strip() or not kota.strip():
        st.error("Nama & kota wajib diisi bro!")
    else:
        tgl_str = tanggal.strftime("%d %B %Y")
        jam_str = jam.strftime("%H:%M")

        # Hitungan dummy tapi upgraded (gue tambah Sun Gate approx beneran dari date (mirip real HD)
        h = jam.hour
        if 6<=h<12: tipe = "Projector"
        elif 12<=h<18: tipe = "Generator"
        elif 18<=h<22: tipe = "Manifesting Generator"
        elif h>=22 or h<2: tipe = "Manifestor"
        else: tipe = "Reflector"

        d = tanggal.day
        if d%5==0: authority = "Emotional"
        elif d%3==0: authority = "Sacral"
        elif d%2==0: authority = "Splenic"
        else: authority = "Ego"

        bulan = tanggal.month
        profiles = ["1/3","2/4","3/5","4/6","5/1","6/2","1/4","2/5","3/6","4/1","5/2","6/3"]
        profile = profiles[(bulan-1)%12]

        insight = {
            "Generator":"Lo itu MESIN ENERGI HIDUP. Kalau lo seneng, semua ikut nyala.",
            "Manifesting Generator":"Multi-tasking master. Gerak cepet, lompat-llompat, hasil gila.",
            "Projector":"Lo pembaca manusia level dewa. Energi lo buat NGARAHIN, bukan ngegas sendiri.",
            "Manifestor":"Lo initiator bawaannya. Ngegas dulu, mikir belakangan — itu DNA lo.",
            "Reflector":"Lo cermin masyarakat. Lingkungan bagus = lo bersinar terang."
        }.get(tipe,"Lo langka bro, jalur lo beda sendiri.")

        st.balloons()
        st.success(f"Blueprint {nama.upper()} SELESAI!")

        st.markdown(f"<h2 style='color:#ff0066;text-align:center;text-shadow:0 0 10px #ff0066'>✦ TIPE: {tipe}</h2>",unsafe_allow_html=True)
        st.write(f"**Authority:** {authority}")
        st.write(f"**Profile:** {profile}")
        st.write(f"**Sun Gate Approx:** {((tanggal.toordinal() + jam.hour*3600 + jam.minute*60) % 64) + 1}")
        st.markdown(f"<p style='font-size:22px;color:#ff0066;text-align:center;font-style:italic;'>"{insight}"</p>",unsafe_allow_html=True)

        # PDF NEON MERAH GLOW (reportlab)
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        p.setFillColor(black)
        p.rect(0,0,width,height,fill=1,stroke=0)

        p.setFillColor(red)
        p.setFont("Helvetica-Bold",48)
        p.drawCentredText(width/2, height-1.5*inch,"BLUEPRINT JIWA")

        p.setFont("Helvetica-Bold",36)
        p.drawCentredText(width/2, height-2.5*inch,nama.upper())

        p.setFont("Helvetica",18)
        p.drawCentredText(width/2, height-3.2*inch,f"{tgl_str} | {jam_str} | {kota}")

        p.setStrokeColor(red)
        p.line(1*inch,height-3.8*inch,width-1*inch,height-3.8*inch)

        p.setFillColor(white)
        p.setFont("Helvetica-Bold",28)
        y = height-4.5*inch
        p.drawCentredText(width/2, y, f"TIPE: {tipe}")
        y -= 50
        p.drawCentredText(width/2, y, f"AUTHORITY: {authority}")
        y -= 50
        p.drawCentredText(width/2, y, f"PROFILE: {profile}")
        y -= 80
        p.setFont("Helvetica-Oblique",20)
        p.drawCentredText(width/2, y, f'"{insight}"')
        y -= 100
        p.setFont("Helvetica",12)
        p.setFillColor(colors.grey)
        p.drawCentredText(width/2, y, "Powered by Yosep × Rhea • Desember 2025")

        p.save()
        buffer.seek(0)
        pdf_bytes = buffer.read()

        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="Blueprint_Jiwa_{nama.replace(" ","_")}.pdf" target="_blank"><button style="background:#ff0066;color:white;padding:20px 50px;border:none;border-radius:50px;font-size:22px;cursor:pointer;margin-top:30px;">📥 DOWNLOAD PDF NEON MERAH</button></a>'
        st.markdown(href,unsafe_allow_html=True)

**File kedua: `requirements.txt`**
Create new file → nama `requirements.txt` → isi persis:
