# ⚽ PredictLabs - Symmetrical Goals & xG Comparison Matrix

**PredictLabs** adalah platform analitik sepak bola dengan antarmuka minimalis, ringkas, dan bersih. Membandingkan statistik **Mean (Rata-rata)** dan **Median (Nilai Tengah)** secara simetris, didukung **Fitur Prediksi Over/Under Statistik Kredibel (Poisson & xG Distribution)**.

---

## 📐 Fitur Lengkap

1. **Header Navigasi**:
   - `Logo` | Pemilih 6 Liga Utama (`Premier League`, `La Liga`, `Bundesliga`, `Serie A`, `Ligue 1`, `Eredivisie`) | Tombol `Sync Data`.

2. **Filter Tahun Kompetisi / Musim (Terisolasi Bersih)**:
   - `[ 2026/2027 (Musim Ini) ]`: Data live Flashscore musim aktif berjalan.
   - `[ 2025/2026 (1 Musim Lalu) ]`: Data historis lengkap 1 musim sebelumnya.

3. **Pemilih Tim & Venue**:
   - **Kolom Kiri (Tim 1)**: Dropdown Tim 1 + Tombol Venue (`Home`, `Away`, `Overall`).
   - **Kolom Kanan (Tim 2)**: Dropdown Tim 2 + Tombol Venue (`Home`, `Away`, `Overall`).

4. **Filter Jumlah Pertandingan (Tengah)**:
   - Tombol pilihan rentang: `[ Last 3 ]`, `[ Last 5 ]`, `[ Last 10 ]`.

5. **Matriks Komparasi Simetris (Mean & Median)**:
   - Sisi Kiri (Tim 1) & Sisi Kanan (Tim 2): `Mean` dan `Median` untuk `HT`, `2HT`, `FT`.
   - Kolom Tengah: `Goal`, `xG`, `Bobol`, `xGA`, serta baris garis `0,25`, `0,75`, `1,25`, `1,75`, `2,25`, `2,75`, `3,25`, `3,75`, `4,25`, `4,75`, `5,25`, `5,75`.

6. **🧠 Fitur Prediksi Over / Under Statistik**:
   - **Tingkat Periode**: Babak 1 (`HT`), Babak 2 (`2HT`), dan Full Time (`FT`).
   - **Garis Prediksi**:
     - Babak 1: `Total Laga > 0.75 HT`, `Total Laga > 1.25 HT`, `Tim 1 > 0.75 HT`, `Tim 2 > 0.75 HT`.
     - Babak 2: `Total Laga > 0.75 2HT`, `Total Laga > 1.25 2HT`, `Tim 1 > 0.75 2HT`, `Tim 2 > 0.75 2HT`.
     - Full Time: `Total Laga > 1.75 FT`, `Total Laga > 2.25 FT`, `Total Laga > 2.75 FT`, `Total Laga > 3.25 FT`, `Tim 1 > 1.25 FT`, `Tim 2 > 0.75 FT`.
   - **Estimasi Skenario Taruhan**: Menang Penuh, Menang Setengah, Potensi Kalah Setengah, Seri/Dana Kembali, Kalah Penuh.

---

## 🚀 Akses Langsung

Server saat ini **sudah aktif berjalan di background**:
👉 **[http://localhost:8000](http://localhost:8000)**
