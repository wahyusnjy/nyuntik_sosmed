import uiautomator2 as u2

# 1. Hubungkan ke device (pastikan HP sudah terhubung via ADB)
d = u2.connect() 

# 2. Buka aplikasi (ganti dengan package name aplikasi lo)
# package_name = "com.contoh.app"
# d.app_start(package_name, stop=False)

# 3. XPath Sederhana (Relative Path)
# Kita langsung lompat ke RecyclerView, lalu masuk ke kontainer ke-4 (ViewGroup[4])
# dan ambil View pertama (index 1 di XPath)
xpath_sederhana = "//androidx.recyclerview.widget.RecyclerView//android.view.ViewGroup[4]//android.widget.Button[1]"

try:
    # 4. Cari elemen berdasarkan XPath
    element = d.xpath(xpath_sederhana)
    
    if element.exists:
        # 5. Ambil data 'text' atau 'content-description' (username biasanya di sini)
        info = element.info

        click = element.click()
        
        # Coba ambil text dulu, kalau kosong ambil description
        # username = info.get('text') or info.get('contentDescription')
        
        # if username:
        #     print(f"Username ditemukan: {username}")
        # else:
        #     print("Elemen ketemu, tapi text & description kosong.")
    else:
        print("Waduh, elemen nggak ketemu. Cek lagi jalurnya di Weditor.")

except Exception as e:
    print(f"Terjadi error: {e}")

# Next step: Mau gue bantu bikinin loop kalau usernamenya ada banyak di dalam list itu?