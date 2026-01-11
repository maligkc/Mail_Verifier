# Projeyi klonladıktan sonra bağımlılıkları yüklemek için:
pip install -r requirements.txt

## Genel Mimari

Proje, Flask tabanlı bir backend ve sürükle-bırak destekli modern bir HTML/JS arayüzden oluşuyor. "Hızlandırılmış Doğrulayıcı" (Fast Verifier) olarak tasarlanan bu araç, CSV dosyalarındaki binlerce e-postayı paralel işleme (multi-threading) yeteneğiyle saniyeler içinde kontrol edebiliyor.

## Öne Çıkan Teknik Özellikler
Paralel İşleme (Thread Pool Executor): Python'un ThreadPoolExecutor kütüphanesi kullanılarak aynı anda onlarca e-posta adresi sorgulanabiliyor. Bu, işlemi standart bir döngüden 10-20 kat daha hızlı hale getiriyor.

### Çok Katmanlı Doğrulama

Syntax Kontrolü: Regex ile e-postanın formatı (önek@alanadı.uzantı) kontrol ediliyor.

DNS (MX) Sorgusu: dns.resolver ile alan adının gerçekten bir mail sunucusu olup olmadığına bakılıyor.

SMTP Doğrulaması: Mail sunucusuna bağlanıp (port 25) mail göndermeden "Böyle bir kullanıcı var mı?" sorgusu yapılıyor.

Filtreleme: "Disposable" (kullan-at) mail servisleri ve "info, support" gibi rol tabanlı genel e-postalar otomatik olarak ayıklanıyor.

## Kullanıcı Deneyimi ve Arayüz
Sürükle-Bırak: index.html üzerinden dosyaları sürükleyerek yükleyebiliyorsun.

Gerçek Zamanlı Takip: İşlem sürerken frontend, backend'e her saniye progress sorgusu atarak yüzde kaçının tamamlandığını ve o an hangi satırın işlendiğini görsel bir bar ile gösteriyor.

Akıllı İndirme: İşlem bittiğinde sonuçları "Sadece Geçerli", "Riskli" veya "Tümü" şeklinde farklı CSV dosyaları olarak indirme imkanı sunuyor.

## Fortune500leads.csv Dosyası ile Uyumu
Proje, paylaşılan örnek CSV dosyasındaki ";" ayırıcısını ve sütun yapısını tanıyacak şekilde konfigüre edilmiştir.

# Kurulum ve Çalıştırma
git clone https://github.com/maligkc/Mail_Verifier.git

cd email-verifier-pro

pip install flask flask-cors dnspython

python verify-app.py
