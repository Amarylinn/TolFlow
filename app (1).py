"""
TolSection - Generator Potongan Melintang Jalan Tol -> DXF (Civil 3D / AutoCAD) + Volume Galian-Timbunan
Jalankan lokal : streamlit run app.py
Deploy         : upload app.py dan requirements.txt ke GitHub, lalu deploy di share.streamlit.io
"""
import io

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from ezdxf.enums import TextEntityAlignment

st.set_page_config(page_title="TolSection", page_icon="🛣️", layout="wide")


# ----------------------------------------------------------------------------
# Utilitas
# ----------------------------------------------------------------------------
def fmt(x, d=2):
    """Angka berformat Indonesia (koma desimal)."""
    return f"{x:.{d}f}".replace(".", ",")


def sta_label(s):
    s = float(s)
    return f"{int(s // 1000)}+{s % 1000:03.0f}"


def trap(y, dx):
    return float(np.sum((y[:-1] + y[1:]) / 2.0) * dx)


# ----------------------------------------------------------------------------
# Geometri potongan melintang
# Sumbu x: offset dari sumbu median (kanan positif). Sumbu z: elevasi relatif
# terhadap tanah asli di sumbu (z = 0). Tanah asli: z = g * x.
# ----------------------------------------------------------------------------
def side_geom(p, H, gs):
    """Satu sisi (bidang cermin u >= 0). gs = kemiringan tanah asli pada sisi itu."""
    u0 = p["wm"] / 2.0
    u1 = u0 + p["wbd"]
    u2 = u1 + p["n"] * p["wl"]
    u3 = u2 + p["wbl"]
    z0 = H
    z1 = z0 - p["sp"] * p["wbd"]  # bahu dalam mengikuti kemiringan perkerasan
    z2 = z1 - p["sp"] * p["n"] * p["wl"]
    z3 = z2 - p["sb"] * p["wbl"]
    if z3 >= gs * u3:
        kind, k = "timbunan", 1.0 / p["mf"]
        den = gs + k
        if den <= 1e-9:
            return None
        ud = (z3 + u3 * k) / den
    else:
        kind, k = "galian", 1.0 / p["mc"]
        den = k - gs
        if den <= 1e-9:
            return None
        ud = (u3 * k - z3) / den
    if ud < u3 - 1e-9 or ud > 300:
        return None
    return dict(kind=kind, k=k, u=[u0, u1, u2, u3], z=[z0, z1, z2, z3], ud=ud, zd=gs * ud)


def build(p, H):
    R = side_geom(p, H, p["g"])
    L = side_geom(p, H, -p["g"])
    if R is None or L is None:
        return None
    S = dict(R=R, L=L, H=H)
    # Luas (m2) antara garis tanah asli dan garis tanah dasar + lereng
    x = np.linspace(-L["ud"], R["ud"], 4001)
    dx = x[1] - x[0]

    def fg(side, u):
        u0, u1, u2, u3 = side["u"]
        xp = [0.0, u0, u1, u2, u3]
        zp = [side["z"][0], side["z"][0], side["z"][1], side["z"][2], side["z"][3]]
        road = np.interp(u, xp, zp) - p["T"]
        sign = -1.0 if side["kind"] == "timbunan" else 1.0
        slope = side["z"][3] + sign * (u - u3) * side["k"]
        return np.where(u <= u3, road, slope)

    prof = np.where(x >= 0, fg(R, np.abs(x)), fg(L, np.abs(x)))
    f = prof - p["g"] * x
    S["x"], S["prof"], S["f"] = x, prof, f
    S["A_fill"] = trap(np.clip(f, 0, None), dx)
    S["A_cut"] = trap(np.clip(-f, 0, None), dx)
    S["pure"] = R["kind"] if R["kind"] == L["kind"] else None
    return S


def extent(p, S):
    """Batas gambar: (xmin, xmax, ymin, y_dimensi, ymax)."""
    L, R = S["L"], S["R"]
    xmin, xmax = -L["ud"] - 3, R["ud"] + 3
    u3 = R["u"][3]
    gl, gr = p["g"] * xmin, p["g"] * xmax
    yd = max(S["H"], p["g"] * u3, -p["g"] * u3) + 1.2
    ymin = min(S["H"] - p["T"], gl, gr, L["zd"], R["zd"]) - 1.0
    ymax = max(yd + 1.6, gl + 1.0, gr + 1.0)
    return xmin, xmax, ymin, yd, ymax


def outline(p, S):
    """Titik poligon tanah dasar + lereng (tertutup oleh garis tanah asli)."""
    T = p["T"]
    pts = []
    for side, s in ((S["L"], -1), (S["R"], 1)):
        u0, u1, u2, u3 = side["u"]
        z0, z1, z2, z3 = side["z"]
        seq = [(s * side["ud"], side["zd"]), (s * u3, z3), (s * u3, z3 - T), (s * u2, z2 - T), (s * u1, z1 - T), (s * u0, z0 - T)]
        if s == -1:
            pts += seq
        else:
            pts += seq[::-1]
    return pts


def design_points(p, S):
    """Daftar titik (offset, elevasi, kode) dari tepi kiri ke kanan."""
    rows = []
    L, R = S["L"], S["R"]
    names = ["TEPI_MEDIAN", "TEPI_BAHU_DALAM", "TEPI_LAJUR", "TEPI_BAHU_LUAR"]
    rows.append((-L["ud"], L["zd"], "DAYLIGHT_KIRI"))
    for i in (3, 2, 1, 0):
        rows.append((-L["u"][i], L["z"][i], names[i] + "_KIRI"))
    for i in (0, 1, 2, 3):
        rows.append((R["u"][i], R["z"][i], names[i] + "_KANAN"))
    rows.append((R["ud"], R["zd"], "DAYLIGHT_KANAN"))
    return rows


# ----------------------------------------------------------------------------
# Gambar (matplotlib)
# ----------------------------------------------------------------------------
def plot_section(p, S, vex, title):
    T, H = p["T"], S["H"]
    L, R = S["L"], S["R"]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    x, prof, f = S["x"], S["prof"], S["f"]
    g_line = p["g"] * x
    ax.fill_between(x, g_line, prof, where=f >= 0, color="#e8a33d", alpha=0.45, lw=0, label="Timbunan")
    ax.fill_between(x, g_line, prof, where=f < 0, color="#4a90d9", alpha=0.45, lw=0, label="Galian")

    col = {"bd": "#9aa5b8", "lj": "#3b4252", "bl": "#9aa5b8"}
    keys = ["bd", "lj", "bl"]
    for side, sg in ((L, -1), (R, 1)):
        for i, kk in enumerate(keys):
            ua, ub = side["u"][i], side["u"][i + 1]
            za, zb = side["z"][i], side["z"][i + 1]
            ax.fill([sg * ua, sg * ub, sg * ub, sg * ua], [za, zb, zb - T, za - T], color=col[kk], ec="black", lw=0.6, zorder=3)
        sx, sz = side["u"][3], side["z"][3]
        ax.plot([sg * sx, sg * side["ud"]], [sz, side["zd"]], color="#6b4f2a", lw=1.6, zorder=4)
    u0 = R["u"][0]
    ax.fill([-u0, u0, u0, -u0], [H, H, H - T, H - T], color="#7fae7f", ec="black", lw=0.6, zorder=3)

    xmin, xmax, ymin, yd, ymax = extent(p, S)
    ax.plot([xmin, xmax], [p["g"] * xmin, p["g"] * xmax], color="#6b4f2a", lw=1.2, ls="--", zorder=2, label="Tanah asli")
    ax.axvline(0, color="#c0392b", lw=0.8, ls="-.", zorder=1)

    # Garis dimensi
    bps = [-R["u"][3], -R["u"][2], -R["u"][1], -R["u"][0], R["u"][0], R["u"][1], R["u"][2], R["u"][3]]
    labs = [fmt(p["wbl"]), f"{p['n']} x {fmt(p['wl'])}", fmt(p["wbd"]), fmt(p["wm"]), fmt(p["wbd"]), f"{p['n']} x {fmt(p['wl'])}", fmt(p["wbl"])]
    for i in range(7):
        a, b = bps[i], bps[i + 1]
        ax.annotate("", xy=(a, yd), xytext=(b, yd), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#333"))
        ax.text((a + b) / 2, yd + 0.12, labs[i], ha="center", va="bottom", fontsize=8)
    for bx in bps:
        ax.plot([bx, bx], [yd - 0.1, yd + 0.1], color="#333", lw=0.8)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect(vex)
    ax.set_xlabel("Offset dari sumbu median (m)")
    ax.set_ylabel("Elevasi relatif (m)")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=8, frameon=False)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# Ekspor DXF
# ----------------------------------------------------------------------------
LAYERS = [
    ("TOL_PERKERASAN", 8),
    ("TOL_BAHU", 9),
    ("TOL_MEDIAN", 3),
    ("TOL_TANAH_ASLI", 30),
    ("TOL_LERENG", 32),
    ("TOL_AREA_TIMBUNAN", 40),
    ("TOL_AREA_GALIAN", 150),
    ("TOL_AS", 1),
    ("TOL_TEKS", 7),
]


def new_doc():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = 6  # meter
    for name, color in LAYERS:
        doc.layers.add(name, color=color)
    return doc


def add_text(msp, txt, x, y, h=0.35, layer="TOL_TEKS"):
    t = msp.add_text(txt, height=h, dxfattribs={"layer": layer})
    t.set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)


def draw_section(msp, p, S, cx, label):
    T, H = p["T"], S["H"]
    L, R = S["L"], S["R"]
    for side, sg in ((L, -1), (R, 1)):
        for i, layer in enumerate(["TOL_BAHU", "TOL_PERKERASAN", "TOL_BAHU"]):
            ua, ub = side["u"][i], side["u"][i + 1]
            za, zb = side["z"][i], side["z"][i + 1]
            pts = [(cx + sg * ua, za), (cx + sg * ub, zb), (cx + sg * ub, zb - T), (cx + sg * ua, za - T)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        msp.add_lwpolyline(
            [(cx + sg * side["u"][3], side["z"][3]), (cx + sg * side["ud"], side["zd"])],
            dxfattribs={"layer": "TOL_LERENG"},
        )
    u0 = R["u"][0]
    msp.add_lwpolyline([(cx - u0, H), (cx + u0, H), (cx + u0, H - T), (cx - u0, H - T)], close=True, dxfattribs={"layer": "TOL_MEDIAN"})
    xmin, xmax, ymin, yd, ymax = extent(p, S)
    msp.add_lwpolyline([(cx + xmin, p["g"] * xmin), (cx + xmax, p["g"] * xmax)], dxfattribs={"layer": "TOL_TANAH_ASLI"})
    msp.add_line((cx, ymin), (cx, ymax), dxfattribs={"layer": "TOL_AS", "linetype": "CENTER"})
    if S["pure"]:
        layer = "TOL_AREA_TIMBUNAN" if S["pure"] == "timbunan" else "TOL_AREA_GALIAN"
        msp.add_lwpolyline([(cx + a, b) for a, b in outline(p, S)], close=True, dxfattribs={"layer": layer})
    # Teks dimensi
    bps = [-R["u"][3], -R["u"][2], -R["u"][1], -R["u"][0], R["u"][0], R["u"][1], R["u"][2], R["u"][3]]
    labs = [f"{p['wbl']:.2f}", f"{p['n']}x{p['wl']:.2f}", f"{p['wbd']:.2f}", f"{p['wm']:.2f}", f"{p['wbd']:.2f}", f"{p['n']}x{p['wl']:.2f}", f"{p['wbl']:.2f}"]
    for i in range(7):
        add_text(msp, labs[i], cx + (bps[i] + bps[i + 1]) / 2, yd)
    add_text(msp, f"POTONGAN MELINTANG STA {label}", cx, yd + 1.3, h=0.6)
    add_text(msp, f"H = {H:+.2f} m | A timbunan = {S['A_fill']:.2f} m2 | A galian = {S['A_cut']:.2f} m2", cx, ymin - 0.6, h=0.35)


def dxf_bytes(p, items):
    """items = [(label, S), ...] disusun berjajar dalam satu file."""
    doc = new_doc()
    msp = doc.modelspace()
    cx = 0.0
    prev_right = None
    for label, S in items:
        if prev_right is not None:
            cx += prev_right + 10 + S["L"]["ud"]
        draw_section(msp, p, S, cx, label)
        prev_right = S["R"]["ud"]
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


# ----------------------------------------------------------------------------
# Antarmuka
# ----------------------------------------------------------------------------
st.title("🛣️ TolSection")
st.caption("Generator potongan melintang jalan tol: atur dimensi, lihat gambarnya langsung, lalu unduh sebagai DXF untuk dibuka di Civil 3D atau AutoCAD. Ada juga hitungan volume galian dan timbunan per stasioning.")

sb = st.sidebar
sb.header("Dimensi badan jalan")
n = sb.selectbox("Jumlah lajur per arah", [2, 3, 4], index=1)
wl = sb.number_input("Lebar lajur (m)", 2.75, 4.0, 3.60, 0.05)
wbd = sb.number_input("Lebar bahu dalam (m)", 0.5, 3.0, 1.50, 0.05)
wbl = sb.number_input("Lebar bahu luar (m)", 1.0, 4.5, 3.00, 0.05)
wm = sb.number_input("Lebar median (m)", 0.5, 20.0, 3.00, 0.1)
sp = sb.number_input("Kemiringan melintang perkerasan (%)", 1.0, 4.0, 2.0, 0.5)
sbp = sb.number_input("Kemiringan bahu luar (%)", 2.0, 8.0, 4.0, 0.5)
Tp = sb.number_input("Tebal perkerasan (m)", 0.2, 1.2, 0.60, 0.05)
sb.header("Tanah asli dan lereng")
gp = sb.number_input("Kemiringan melintang tanah asli (%), positif naik ke kanan", -30.0, 30.0, 0.0, 1.0)
mf = sb.number_input("Lereng timbunan 1 : m (V : H)", 1.0, 4.0, 2.0, 0.25)
mc = sb.number_input("Lereng galian 1 : m (V : H)", 0.5, 4.0, 1.5, 0.25)
sb.header("Tampilan")
vex = sb.select_slider("Skala vertikal gambar", options=[1, 2, 3, 5], value=2)
sb.caption("Angka di atas adalah nilai awal untuk simulasi. Sesuaikan dengan pedoman dan desain proyekmu.")

P = dict(n=n, wl=wl, wbd=wbd, wbl=wbl, wm=wm, sp=sp / 100, sb=sbp / 100, T=Tp, mf=mf, mc=mc, g=gp / 100)

tab1, tab2 = st.tabs(["📐 Potongan melintang", "📊 Volume per stasioning"])

with tab1:
    c1, c2 = st.columns([3, 1])
    H = c1.slider("Tinggi jalan terhadap tanah asli di sumbu (m): positif = timbunan, negatif = galian", -8.0, 8.0, 2.0, 0.1)
    lab = c2.text_input("Label STA", "0+000")
    S = build(P, H)
    if S is None:
        st.error("Lereng tidak bertemu tanah asli. Landaikan lereng (perbesar m) atau kurangi kemiringan tanah asli.")
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Lebar badan jalan", f"{fmt(2 * S['R']['u'][3])} m")
        m2.metric("Lebar sampai kaki lereng", f"{fmt(S['L']['ud'] + S['R']['ud'])} m")
        m3.metric("Luas timbunan", f"{fmt(S['A_fill'])} m²")
        m4.metric("Luas galian", f"{fmt(S['A_cut'])} m²")
        m5.metric("Jenis", "Timbunan" if S["pure"] == "timbunan" else ("Galian" if S["pure"] == "galian" else "Campuran"))
        fig = plot_section(P, S, vex, f"Potongan melintang STA {lab}  (H = {fmt(H)} m)")
        st.pyplot(fig)
        plt.close(fig)
        d1, d2, _ = st.columns([1, 1, 2])
        d1.download_button("⬇️ Unduh DXF (Civil 3D / AutoCAD)", dxf_bytes(P, [(lab, S)]), file_name=f"potongan_tol_STA_{lab.replace('+', '_')}.dxf", mime="application/dxf")
        pts = pd.DataFrame(design_points(P, S), columns=["Offset (m)", "Elevasi relatif (m)", "Kode"]).round(3)
        d2.download_button("⬇️ Unduh titik (CSV)", pts.to_csv(index=False).encode("utf-8"), file_name="titik_potongan_tol.csv", mime="text/csv")
        with st.expander("Tabel titik potongan"):
            st.dataframe(pts, hide_index=True)
        st.caption(
            "Asumsi gambar: kedua jalur miring ke luar dari median, bahu dalam mengikuti kemiringan perkerasan, bahu luar memakai kemiringan bahu, "
            "lereng dimulai dari tepi bahu luar, volume dihitung sampai muka tanah dasar (permukaan dikurangi tebal perkerasan). "
            "Saluran tepi, superelevasi, dan lapisan perkerasan rinci belum dimodelkan."
        )

with tab2:
    st.markdown("Isi stasioning dan tinggi jalan tiap stasiun (positif = timbunan, negatif = galian). Volume antar-stasiun dihitung dengan metode luas rata-rata.")
    base = pd.DataFrame({"STA (m)": [0.0, 25.0, 50.0, 75.0, 100.0], "H (m)": [2.0, 1.0, -0.5, -1.5, 0.5]})
    ed = st.data_editor(base, num_rows="dynamic", key="sta_table")
    k_fill = st.number_input("Faktor kebutuhan timbunan (1,00 = tanpa susut)", 0.5, 2.0, 1.00, 0.05)
    df = ed.dropna().sort_values("STA (m)").reset_index(drop=True)
    if len(df) < 2:
        st.info("Isi minimal dua stasiun.")
    else:
        secs, bad = [], []
        for _, r in df.iterrows():
            s_ = build(P, float(r["H (m)"]))
            if s_ is None:
                bad.append(sta_label(r["STA (m)"]))
            secs.append(s_)
        if bad:
            st.error("Lereng tidak bertemu tanah asli pada STA: " + ", ".join(bad))
        else:
            rows, mass = [], 0.0
            for i, s_ in enumerate(secs):
                if i == 0:
                    vf = vc = 0.0
                else:
                    L_ = float(df["STA (m)"][i] - df["STA (m)"][i - 1])
                    vf = (secs[i - 1]["A_fill"] + s_["A_fill"]) / 2 * L_
                    vc = (secs[i - 1]["A_cut"] + s_["A_cut"]) / 2 * L_
                mass += vc - k_fill * vf
                rows.append(
                    {
                        "STA": sta_label(df["STA (m)"][i]),
                        "H (m)": float(df["H (m)"][i]),
                        "Luas timbunan (m²)": round(s_["A_fill"], 2),
                        "Luas galian (m²)": round(s_["A_cut"], 2),
                        "Vol. timbunan dari STA sebelumnya (m³)": round(vf, 1),
                        "Vol. galian dari STA sebelumnya (m³)": round(vc, 1),
                        "Kumulatif galian − timbunan (m³)": round(mass, 1),
                    }
                )
            res = pd.DataFrame(rows)
            tf = res["Vol. timbunan dari STA sebelumnya (m³)"].sum()
            tc = res["Vol. galian dari STA sebelumnya (m³)"].sum()
            a1, a2, a3 = st.columns(3)
            a1.metric("Total volume timbunan", f"{tf:,.0f} m³".replace(",", "."))
            a2.metric("Total volume galian", f"{tc:,.0f} m³".replace(",", "."))
            a3.metric("Selisih (galian − timbunan)", f"{mass:,.0f} m³".replace(",", "."))
            st.dataframe(res, hide_index=True)
            figm, axm = plt.subplots(figsize=(10, 3.2))
            axm.plot(df["STA (m)"], res["Kumulatif galian − timbunan (m³)"], marker="o", color="#2b6cb0")
            axm.axhline(0, color="#666", lw=0.8)
            axm.set_xlabel("STA (m)")
            axm.set_ylabel("Kumulatif (m³)")
            axm.set_title("Diagram massa sederhana", fontsize=11, fontweight="bold")
            axm.grid(alpha=0.25)
            figm.tight_layout()
            st.pyplot(figm)
            plt.close(figm)
            e1, e2, _ = st.columns([1, 1, 2])
            e1.download_button("⬇️ Unduh tabel volume (CSV)", res.to_csv(index=False).encode("utf-8"), file_name="volume_galian_timbunan.csv", mime="text/csv")
            e2.download_button(
                "⬇️ Unduh DXF semua potongan",
                dxf_bytes(P, [(sta_label(df["STA (m)"][i]), secs[i]) for i in range(len(secs))]),
                file_name="potongan_tol_semua_STA.dxf",
                mime="application/dxf",
            )
            st.caption("Volume antar-stasiun memakai rata-rata luas ujung. Pada segmen yang berganti dari galian ke timbunan, hasilnya perkiraan kasar. Faktor kebutuhan timbunan dan pembagian material belum memakai data uji tanah.")

with st.expander("Dasar nilai awal dan batasan"):
    st.markdown(
        "- Nilai awal lebar lajur 3,6 m, bahu luar 3 m, bahu dalam 1,5 m, kemiringan normal 2% dan kemiringan bahu 4% mengikuti nilai yang dipakai pada studi desain jalan tol di Indonesia "
        "yang merujuk Pedoman Bina Marga No. 007/BM/2009 (contoh: Jurnal Teknik ITS, ejurnal.its.ac.id). Cocokkan dengan naskah pedoman sebelum dipakai untuk desain.\n"
        "- Lebar median, tebal perkerasan, dan kemiringan lereng adalah asumsi awal, bukan ketentuan.\n"
        "- Hasil DXF berupa garis dan polyline biasa. Alat ini bukan pengganti desain koridor di Civil 3D."
    )
