# M07 — Güvenlik, yetki ve işlem politikası

> Korunan okuma, yazma ve dış yan etkiler için tek bir politika ve geçit yolu kurar: güvenilir aktör/kanal bağlamı, varsayılan red, katı araç doğrulaması, operasyona bağlı onay, kalıcı idempotency, işlem öncesi yeniden doğrulama, M02 iptal/commit çiti, makbuz anlamı, uzlaştırma ve kalıcı denetim. Mevcut `backend/supervisor/` genişletilir; her ajanda kopyalanmaz.

| Alan | Değer |
| --- | --- |
| Kimlik | M07 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M01, M02, M04 (M03/M05/M06 isteğe bağlı uyum noktaları) |
| Sonraki | CORE_GATE, F3-A, F3-B |
| Bayrak | Supervisor kipleri: `OFF` (eski) / `SHADOW` (yalnız gözlem, ek etki yok) / `GUARDED` (politika zorunlu, hata kapalı); mevcut varsayılan korunur |
| Ortam | CPU, geçici test DB'si, sahte sağlayıcı |
| Eski görevler | F3-T26, F3-T28, F3-T29 |
| Kaynak | Bundle `W1/Freya_2_0_M07_Agent_Implementation_Package.md`; [security-and-privacy](../../../cross-cutting/security-and-privacy.md) |
| Durum | NOT_RUN |

## 1. Amaç

Sesli asistan randevu alıyor, müşteri kaydı okuyor, bildirim gönderiyor. Bu etkiler bugün farklı yollardan ve farklı kontrollerle tetiklenebiliyor; çift randevu, sahte fiyat, onaysız yazma ve kişisel veri sızıntısı (KVKK) riskleri M00/H01'de kayıtlı. M07 bunları **tek bir zorlanan yola** bağlar. F3 diyalog paketleri bu yolu kullanır, atlamaz.

## 2. Başlamadan önce

- [ ] M01, M02, M04 kabul edilmiş; H01'deki P4/P5/P7 düzeltmeleri birleştirilmiş.
- [ ] Her korunan okuma/yazma/dış etki, giriş noktası, rol, kaynak, sağlayıcı ve atlama yolu özellik kimlikleriyle eşlenmiş (web rotaları, DTMF, işçiler, CLI, AMI/ARI sahte yolları).
- [ ] Tehdit kaydı ve güven sınırları çizilmiş; açık izin listesi ve geçiş planı yazılmış.

## 3. Kapsam

**Yapılacak:** Güvenlik sözleşmeleri; aktör ve kanal bağlamı; kaynak yetkilendirme; müşteri doğrulaması noktası; araç politika kataloğu; katı öneri/sonuç doğrulaması; onay yaşam döngüsü; operasyon özeti; kalıcı idempotency; işlem yeniden doğrulaması; iptal/commit çiti; makbuz ve sağlayıcı anlamı; uzlaştırma ve outbox; kalıcı güvenlik denetimi; kişisel veri ve saklama temeli; Supervisor ve eski kod bütünleşmesi; testler; atlama denetimi.

**Yapılmayacak:** Gerçek SMS/e-posta/arama/aktarım, gerçek CRM yazması, canlı silme/temizleme, paket kurma, model yükleme. Diyalog akışı tasarımı (F3). Kimlik bilgisi üretimi.

## 4. Dosyalar

Mevcut `backend/supervisor/` (politika, geçit, kayıt, çalışma zamanı) genişletilir. Yeni modüller (gerekirse):

```
backend/supervisor/security/
  contracts.py  principal.py  authorization.py  verification.py  tool_catalog.py
  proposal_validation.py  confirmation.py  operation_digest.py  idempotency_store.py
  transaction.py  commit_fence.py  receipts.py  reconciliation.py  outbox.py
  audit.py  privacy.py  legacy_modes.py
tests/security/
evidence/M07/<run_id>/
```

Kalıcı idempotency ve denetim için mevcut veritabanına **ekleme** yapılır (yeni tablolar); var olan tablolar değişmez. Göç betiği geri alınabilir olmalı ve operasyon defteri geri dönüşte korunur.

## 5. Tasarım ve sözleşmeler

### 5.1 Değişmez kurallar

1. **Tek politika/geçit yolu.** Yönetilen kipte korunan her okuma, yazma ve dış yan etki aynı karar ve zorlama noktasından geçer; zorlama etkinin hemen önünde yapılır.
2. Mevcut meşru davranış, durum kodları, yanıt biçimleri ve rotalar korunur; mevcut kip varsayılanları değişmez. Yeni korumalı özellikler uyum ve güvenlik kapıları geçene kadar isteğe bağlıdır. `OFF` eski yönlendirmedir, zorunlu kontrolleri atlama izni değildir.
3. **Kimlik bilgisi olmayanlar:** arayan numarası, telefon, plaka, araç adı, ses seed'i, transkript, müşteri adı, jeton benzeri metin, LLM beyanı, RAG metni, araç çıktısı. Arayüzde görünürlük ve geçerli bir AudioSocket UUID'si iş yetkisi kanıtı değildir.
4. **Varsayılan red:** eksik/bilinmeyen izin, bayat/uyuşmayan kapsam, süresi dolmuş onay, geçersiz argüman, belirsiz kimlik, erişilemez politika veya denetim deposu. Genel bilgiler onaylı genel yoldan sunulabilir.
5. **FINAL ASR gerekli ama yeterli değildir.** `PARTIAL` ve `STABLE_PREFIX` yalnızca geçici bağlamı günceller. Kimliği doğrulanmış arayüz eylemleri kendi güvenilir istek/onay yolunu kullanır; sahte ASR finali üretilmez.
6. **Onay dardır:** eylem + doğrulanmış kanonik yük + kesin aktör/kaynak kapsamı + durum/önkoşul revizyonu + onay sorusu + son geçerlilik + uygun tur bağı. Saat, araç, hizmet, fiyat, müşteri değişirse yeni onay gerekir.
7. **İdempotency kalıcıdır.** Bellek içi sözlük yeniden başlatmada korumaz. Anahtar ve özet kapsamlıdır; aynı anahtar farklı içerik = çakışma. Yerel işlemlerde atomik talep ve kalıcı sonuç.
8. Yürütme sınırında yetki ve önkoşullar yeniden doğrulanır; yerel işlem benzersizlik/kapasite kısıtları ve denetim/outbox tutarlılığı sağlanır. Uzak sağlayıcı çağrısı boyunca küresel oturum kilidi veya DB işlemi tutulmaz.
9. **Makbuz:** `PENDING / COMMITTED / FAILED / UNKNOWN / BLOCKED`. `COMMITTED` kapsamlı operasyonun yetkili kanıtını ister; HTTP 200 veya araç önerisi yetmez. `provider_mode` `MOCK / REAL / UNKNOWN`; mock başarı gerçek gibi sunulmaz.
10. **İptal ve commit:** commit kabulünden önce iptal yazmayı engelleyebilir. Commit kabulü yarışı kazandıysa operasyon uçuştadır ve uzlaştırılır; sonraki tur iptali onu geri almaz.
11. Tüm model çıktısı, transkript, RAG belgesi, kullanıcı metni, araç yanıt metni ve URL güvenilmeyen içeriktir. İzin listeli tipli araç şemaları; sınırlı JSON ayrıştırma; açık enum ve anlamsal doğrulama; bilinmeyen/yinelenen alan reddi; keyfi SQL/komut/URL/yol yürütmesi yok.
12. Kişisel veri ve gizli bilgi en aza indirilir: genel günlük, metrik, rapor, fikstür ve olay yolunda ham ad, telefon, plaka, transkript, ses, istem, erişim jetonu, parola, ham istisna, tam araç yükü veya sağlayıcı yanıtı yok.
13. Güvenlik açısından kritik kararlar ve değişiklik yaşam döngüsü kalıcı, kısıtlı bir denetim deposuna yazılır (sınırlı boyut, güvenli olay kodları, opak başvurular). Hash zinciri kurcalamayı **gösterir**, engellemez. Zorunlu "niyet" denetim kaydı yazılamazsa yeni korunan değişiklik yapılmaz. M04 olay yolu denetim değildir.
14. Politika modüllerini içe aktarmak DB'ye bağlanmaz, gizli bilgi okumaz, kalıcı dosya oluşturmaz, iş parçacığı başlatmaz, PBX'e bağlanmaz, model yüklemez.

### 5.2 Operasyon yaşam döngüsü

```
öneri (LLM/kural/UI) ─► katı doğrulama ─► yetki ─► onay sorusu ─► kullanıcı onayı (FINAL/UI/DTMF bağlı)
   ─► operasyon özeti + idempotency talebi ─► yürütme sınırında yeniden doğrulama
   ─► niyet denetimi ─► commit kabulü (M02 çiti) ─► sağlayıcı/yerel işlem
   ─► makbuz (COMMITTED/FAILED/UNKNOWN) ─► sonuç denetimi ─► gerekirse uzlaştırma
```

| Aşama | Reddedilme koşulları (örnek) |
| --- | --- |
| Doğrulama | Bilinmeyen araç, yanlış tür/enum, eksik/yinelenen/bilinmeyen alan, aşırı büyük/derin JSON, sonlu olmayan değer |
| Yetki | Başka müşterinin kaydı (varlık sızdırmadan), kurum dışı kapsam, rolün eylem yetkisi yok, süresi dolmuş/iptal edilmiş kimlik |
| Onay | PARTIAL/STABLE ASR, soruya bağlı olmayan DTMF, ilgisiz "evet"/onay sesi/yankı, yarım kalmış sunum, süresi dolmuş veya başka oturumdan onay |
| Özet | Onaydan sonra değişen saat/araç/hizmet/fiyat; güvenilmeyen özet başvurusu |
| İdempotency | Aynı anahtar farklı özet; tüketilmiş onay için farklı anahtar; kalıcı depo erişilemez (yeni yazma engellenir) |
| Yeniden doğrulama | Kapasite çakışması (çift randevu), onaydan sonra değişen uygunluk (otomatik başka saat seçilmez), commit öncesi yetki iptali |
| Makbuz | Commit kanıtı olmayan sağlayıcı kabulü → `PENDING/UNKNOWN`; outbox'a eklendi ≠ teslim edildi; AMI aktarım kabulü ≠ bağlandı |

### 5.3 Kipler

| Kip | Davranış |
| --- | --- |
| `OFF` | Mevcut eski yönlendirme; mevcut meşru iş akışları ve API biçimi korunur; güvensiz boşluklar yönetilen etkinleştirme için açıkça engellenir |
| `SHADOW` | Eski yetkili etki en fazla bir kez; gölge değerlendirme sıfır ek etki üretir, onay tüketmez |
| `GUARDED` | Politika zorunlu; politika/denetim erişilemezse hata kapalı; güvensiz eski geri düşme yok |

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M07.01 | Ön kontrol | M00/M01/M02/M04 kabulü, hash'ler, güncel ağaç, isteğe bağlı noktalar | Engelde HOLD |
| M07.02 | Güvenlik ve etki envanteri | Her korunan okuma/yazma/dış etki, giriş noktası, rol, kaynak, sağlayıcı, atlama yolu | `SECURITY_EFFECT_INVENTORY.json` |
| M07.03 | Tehdit ve sahiplik tasarımı | Veri akışları, güven sınırları, tehdit kaydı, izin listesi, geçiş, tek otorite | `THREAT_REGISTER.md`, `SECURITY_DECISIONS.md` |
| M07.04 | Güvenlik sözleşmeleri | M01 uyumlu iç türler, değiştirilemez kapsam/revizyon, güvenli hata | SEC02 |
| M07.05 | Aktör ve kanal bağlamı | Sunucu tarafında güvenilir aktör/özne çözümü, kanal adaptörleri, kapsam ve süre | SEC05–SEC08 |
| M07.06 | Kaynak yetkilendirme | Varsayılan red yetenekleri, sahiplik/kurum kapsamı, korunan okuma filtresi, iptal | SEC09–SEC12, SEC15–SEC16 |
| M07.07 | Müşteri doğrulaması | Mevcut doğrulama mekanizması veya açık "yok" noktası; deneme sınırları; DTMF/UI/ses kökeni | SEC13–SEC14 |
| M07.08 | Araç politika kataloğu | Mevcut katalog → eylem sınıfları; gerekli politika/onay/denetim; bilinmeyen = red | SEC17 |
| M07.09 | Katı öneri ve sonuç doğrulaması | Sınırlı ayrıştırıcı, tipli izin listesi, güvenilmeyen LLM/RAG/araç verisi, parametreli servis | SEC18–SEC24 |
| M07.10 | Onay yaşam döngüsü | Belirli soru, sunum kanıtı, onay/süre/iptal/tek kullanım | SEC25–SEC35 |
| M07.11 | Operasyon özeti | Kanonik kodlama/sürüm, korunan kapsam bağı, değişiklikte geçersizlik | SEC36–SEC38 |
| M07.12 | Kalıcı idempotency | Atomik kapsamlı talep, anahtar/özet çakışması, yinelenen yanıt, yeniden başlatma kurtarma | SEC39–SEC46 |
| M07.13 | İşlem yeniden doğrulaması | Gerçek yerel işlem sınırı, kapsam/önkoşul tekrar kontrolü, çift randevu yok | SEC47–SEC49 |
| M07.14 | İptal ve commit çiti | M02 bütünleşmesi, kabul öncesi/sonrası anlamı, bayat yanıt reddi, bağımsız sonuç | SEC50–SEC52 |
| M07.15 | Makbuz ve sağlayıcı anlamı | M01 makbuz durumu, mock/gerçek sınıflama, doğrulanmış kanıt, güvenli yanıt | SEC53–SEC56 |
| M07.16 | Uzlaştırma ve outbox | Bilinmeyen çözümü, işçi çiti, sınırlı deneme, sağlayıcı belirsizliği, kuyruk ≠ teslim | SEC57–SEC60 |
| M07.17 | Kalıcı güvenlik denetimi | Kalıcı kısıtlı denetim, niyet/sonuç, hata işleme, M04'ten ayrım | SEC61–SEC63 |
| M07.18 | Kişisel veri ve saklama temeli | Güvenli izdüşüm, işaret testleri, veri sınıflaması, canlı silme yok | SEC64–SEC66 |
| M07.19 | Supervisor ve eski kod | OFF/SHADOW/GUARDED uyumu, tek geçit, atlama haritası, aşamalı açılış | SEC67–SEC70 |
| M07.20 | Çekirdek bütünleşme noktaları | M02/M04 gerçek başvuruları; isteğe bağlı M03/M05/M06 arayüzleri; yeni DAG kenarı yok | SEC71 |
| M07.21 | Belirlenimci güvenlik testleri | SEC01–SEC72; yalıtılmış fikstür, geçici DB, sahte sağlayıcı; canlı yan etki yok | Tüm testler çalıştırılmış |
| M07.22 | Özellik regresyonu ve atlama denetimi | M00/API/arayüz davranışı, korumalı etkinleştirme kapsamı, değişen yollar, kalan engeller | `BYPASS_AUDIT.csv` |
| M07.23 | Kanıt ve geri dönüş | Gerçek günlükler, hash'ler, göç/geri dönüş planı; uydurma PASS yok | SEC72 |
| M07.24 | Kabul ve devir | M07-G00…G19, genel durum, F3/M08 devri; dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| SEC01 | Zorunlu kabul edilmiş taban/devir eksik | HOLD; uygulama veya korumalı etkinleştirme yok |
| SEC02 | Sözleşme yeniden kullanımı ve içe aktarma güvenliği | İçe aktarmada model/ağ/DB/işçi yan etkisi yok; M01 türleri yeniden kullanılır |
| SEC03 | İzinsiz değişen yol / ikinci otorite | Bütünlük kontrolü yakalar; kabul engellenir |
| SEC04 | Bilinmeyen veya geçersiz politika revizyonu | Korunan istek reddedilir/HOLD; geri düşme yok |
| SEC05 | Yalnızca arayan numarası | Doğrulanmış değil; özel veri veya değişiklik yok |
| SEC06 | Geçerli güvenilir kapsamlı aktör | Yalnızca açıkça izinli kaynak/eylem |
| SEC07 | Süresi dolmuş/iptal edilmiş kimlik veya bilet | Red; bayat kapsam yeniden kullanılmaz |
| SEC08 | Model rol/yönetici alanı önerir | Güvenilmeyen olarak yok sayılır/reddedilir; yetki yükselmez |
| SEC09 | Müşteri A, B'nin kaydını ister | Varlık sızdırmadan red |
| SEC10 | Kurumlar arası kapsam | Açık geçerli yetki devri yoksa red |
| SEC11 | Operatör rolünün eylem yetkisi yok | Arayüzde görünse de red |
| SEC12 | Dar yetkili servis hesabı | Yalnızca sayılan işler; örtük yönetici yok |
| SEC13 | Fikstürde enjekte sahte doğrulayıcı | Yalnızca test kapsamında çalışır; istek/istemle etkinleşemez |
| SEC14 | Doğrulama erişilemez / deneme sınırı | Soru/HOLD veya red; sınırlı deneme, atlama yok |
| SEC15 | Genel okuma ile korunan okuma | Onaylı genel veri erişilebilir; özel sonuç filtrelenir |
| SEC16 | Toplu/geçmiş/dışa aktarma kapsamı | Sorgu ve izdüşüm yetkili kapsamı uygular |
| SEC17 | Bilinmeyen araç kimliği | Gönderimsiz red |
| SEC18 | Yanlış şema türü / enum / eksik zorunlu alan | Tehlikeli değere zorlamadan red |
| SEC19 | Yinelenen/bilinmeyen JSON alanları | Araç çalışmadan red |
| SEC20 | Aşırı büyük/derin JSON veya sonlu olmayan değer | Sınırlı red; çökme veya yazma yok |
| SEC21 | Kullanıcı/LLM kaynaklı SQL/komut/URL/yol | Keyfi yürütme yok; sabit parametreli servis yolu |
| SEC22 | RAG metni politikayı yok saymayı ister | Yetki yükselmez; onaylı bilgiler ayrı |
| SEC23 | Araç yanıtı talimat veya sahte makbuz dener | Güvenilmeyen metin izin/durum değiştiremez |
| SEC24 | Değişen eylem/kaynaklı zincirleme araç çağrısı | Her eylem bağımsız kontrol edilir |
| SEC25 | PARTIAL/STABLE_PREFIX değişiklik ister | Değişiklik yok; onay tüketilmez |
| SEC26 | Gerekli onay olmadan FINAL ASR | Korunan yan etki yok |
| SEC27 | Kimliği doğrulanmış arayüz eylemi kökeni | Yalnızca geçerli kapsamlı açık onay; uydurma ASR finali yok |
| SEC28 | Soruya bağlı olmayan DTMF | Rıza veya korunan yazma yok |
| SEC29 | İlgisiz "evet"/onay sesi/yankı | Onay yok |
| SEC30 | Kesilmiş/eksik onay sunumu | Görülmemiş koşullardan onay çıkarılmaz |
| SEC31 | Sonraki turda geçerli bağlamsal onay | Doğru soru onaylanır; yalnızca farklı tur kimliği yüzünden engellenmez |
| SEC32 | Onaydan sonra değişen saat/araç/hizmet/fiyat | Özet/önkoşul uyuşmazlığı; yeni onay gerekir |
| SEC33 | Süresi dolmuş veya iptal edilmiş soru | Tüketilemez veya diriltilemez |
| SEC34 | Oturumlar/müşteriler arası onay tekrarı | Red |
| SEC35 | Tek sorunun eşzamanlı kullanımı | Tam bir yetkili operasyon talebi; diğerleri yineleme veya red |
| SEC36 | Belirlenimci kanonik özet | Kararlı alan sırası, açık birim/saat dilimi/null; önemli değişiklik farklı özet |
| SEC37 | Güvenilmeyen özet/onay başvurusu enjeksiyonu | Yetkili arama gerekir; geçersiz köken reddedilir |
| SEC38 | Onay süresi için yeniden başlatma veya saat belirsizliği | Muhafazakâr yeniden doğrulama/yeni onay; süresi dolmuşun yeniden kullanımı yok |
| SEC39 | Aynı anahtar + aynı özet eşzamanlı | Desteklenen yerel işlem kapsamında en fazla bir yürütme |
| SEC40 | Aynı anahtar + farklı özet | Çakışma; ikinci etki yok |
| SEC41 | Tüketilmiş soru için farklı anahtar | Yinelenen operasyon yok |
| SEC42 | Yeni soruyla meşru yeni operasyon | İş kısıtları izin veriyorsa izinli; yanlışlıkla tekilleştirilmez |
| SEC43 | Yetkisiz tam yeniden deneme | Önceki makbuz ifşa edilmez |
| SEC44 | Yerel commit'ten önce çökme | Yalnızca etki olmadığı yetkili kanıtla yeniden deneme; sahte commit yok |
| SEC45 | Commit'ten sonra yanıttan önce çökme | Kalıcı makbuz yeniden verilir; yeni yazma yok |
| SEC46 | Kalıcı idempotency deposu erişilemez | Korunan yeni yazmalar engellenir; bellek içi açık geçiş yok |
| SEC47 | Eşzamanlı randevu kapasite çakışması | Kısıt/işlem aşırı rezervasyonu önler; kaybeden güvenli sonuç alır |
| SEC48 | Onaydan sonra değişen uygunluk | Yeniden kontrol başarısız; otomatik başka saat rezervasyonu yok |
| SEC49 | Commit kabulünden önce yetki iptali | Red; korunan gönderim yok |
| SEC50 | İptal commit kabulünden önce kazanır | Etki yok; kalıcı durum doğru |
| SEC51 | Commit kabulü kazanır, sonra tur iptal edilir | Turdan bağımsız sonuçlandır/uzlaştır; bayat yanıt yok; otomatik geri alma yok |
| SEC52 | Dış istek sırasında son tarih dolar | Yetkili kanıt yoksa UNKNOWN; kör yeniden deneme yok |
| SEC53 | Commit kanıtı olmadan sağlayıcı HTTP kabulü | PENDING/UNKNOWN, COMMITTED değil |
| SEC54 | Mock başarı | Yalnızca mock makbuz; gerçek iddiası yok |
| SEC55 | Bildirim outbox'a ekleme | Eklendi ≠ teslim edildi; gerçek gönderim yok |
| SEC56 | Aktarım isteği/AMI kabulü | Köprü bağlandı/duyuldu başarısı değil |
| SEC57 | UNKNOWN'dan sonra geç yetkili makbuz | Mevcut operasyon bir kez uzlaştırılır; yinelenen değişiklik yok |
| SEC58 | Çelişkili makbuz kanıtı | HOLD/elle inceleme; güvenilir terminal durumun üzerine yazılmaz |
| SEC59 | Sağlayıcı uzlaştıramıyor | Sınırlı elle inceleme; yeni anahtarla yeniden gönderim yok |
| SEC60 | Yarışan uzlaştırıcılar / kira süresi | Çitli güncellemeler; çift gönderim yok |
| SEC61 | Zorunlu denetim niyeti yazılamıyor | Yeni korunan değişiklik yok |
| SEC62 | Etki sonrası denetim deposu hatası | Sonuç korunur/kanıta göre UNKNOWN; uzlaştırma ve bozulmuş durum; sahte geri alma yok |
| SEC63 | M04 olay kuyruğu dolu veya abone hatalı | Kalıcı denetim ve politika anlamı etkilenmez |
| SEC64 | Günlük/istisnada iç içe kişisel veri/gizli bilgi işareti | Güvenli çıktı, metrik, rapor, kanıtta ham işaret yok |
| SEC65 | Denetim okuma yetkisi / yol geçişi | Kısıtlı kapsam ve onaylı dizin; keyfi dışa aktarma yok |
| SEC66 | Saklama sınırı / çözülmemiş operasyon | Erken silme veya yinelenen yeniden deneme yok; canlı temizleme yok |
| SEC67 | SHADOW yolu | Eski yetkili etki en fazla bir kez; gölgede sıfır ek etki veya onay tüketimi |
| SEC68 | GUARDED politika erişilemez | Hata kapalı; güvensiz eski geri düşme yok |
| SEC69 | Mevcut OFF/eski meşru iş akışları | Onaylı davranış/API biçimi korunur; güvensiz boşluklar yönetilen etkinleştirme için açıkça engellenir |
| SEC70 | Doğrudan rota/DTMF/işçi/CLI atlama denetimi | Gözlenen her etki sınıflanmış; test edilmiş zorlama veya belgeli etkinleştirme engeli |
| SEC71 | Regresyon / güvenli içe aktarma / isteğe bağlı M03–M06 noktaları | Yeni zorunlu bağımlılık yok; canlı yan etki yok; özellik kimlikleri hesaplanmış |
| SEC72 | Kanıt ve geri dönüş tamlığı | Gerçek testler/hash'ler/sınırlar; izinsiz değişiklik veya uydurma PASS yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M07-G00 | Ön kontrol | M00/M01/M02/M04 kanıtı ve repo kapsamı doğrulanmış |
| M07-G01 | Tek otorite | Tek politika/geçit otoritesi, güvenli içe aktarma, yalnız izinli değişiklik |
| M07-G02 | Aktör ve kanal | M01 sözleşme anlamı ve güvenilir aktör/kanal kapsamı doğrulanmış |
| M07-G03 | Kimlik ve yetki | Kimlik doğrulaması, süre, rol ve nesne yetkisi; bilinmeyen reddedilir |
| M07-G04 | Korunan okuma | Korunan okumalar ve güvenli çıktı kapsamı uygulanmış |
| M07-G05 | Araç doğrulaması | Katı araç doğrulaması, güvenilmeyen içerik ve enjeksiyon sınırı |
| M07-G06 | Onay | FINAL/açık güvenilir eylem ve bağlamsal onay yaşam döngüsü |
| M07-G07 | Özet | Operasyon özeti, süre, tekrar ve önemli değişiklikte geçersizlik |
| M07-G08 | İdempotency | Kalıcı kapsamlı idempotency, atomik talepler, yeniden başlatma/yineleme |
| M07-G09 | İşlem | İşlem yeniden doğrulaması ve eşzamanlı çakışma güvenliği |
| M07-G10 | Çit | M02 iptal/commit çiti, bağımsız kalıcı sonuç |
| M07-G11 | Makbuz | Doğrulanmış makbuz ve mock/gerçek/bilinmeyen sınırları |
| M07-G12 | Uzlaştırma | Uzlaştırma/outbox sınırlı davranış; kör yeniden deneme yok |
| M07-G13 | Denetim | Kalıcı güvenlik denetimi M04'ten bağımsız; zorunlu niyet hatasında kapalı |
| M07-G14 | Gizlilik | Kişisel veri/gizli bilgi maskeleme, erişim ve saklama sınırları |
| M07-G15 | Uyum ve atlama | Mevcut kipler/API/iş akışları; korumalı kipte geri düşme yok; atlama kapsamı/etkinleştirme engelleri |
| M07-G16 | Test kanıtı | SEC01–SEC72 güvenli kapsamda gerçekten geçmiş |
| M07-G17 | Bütünlük | M00 özellik korunumu ve bütünlük; izinsiz göç yok |
| M07-G18 | Geri dönüş | Geri dönüş planı operasyon defterini ve kullanıcı değişikliklerini korur |
| M07-G19 | Devir | Aşağı akış sözleşmeleri ve engeller belgelenmiş; PASS kapsamı belirtilmiş |

## 9. Kanıt

`evidence/M07/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `SECURITY_EFFECT_INVENTORY.json`, `THREAT_REGISTER.md`, `SECURITY_DECISIONS.md`, `TOOL_POLICY_CATALOG.json`, `BYPASS_AUDIT.csv`, `MIGRATION_AND_ROLLBACK.md`, `TEST_MATRIX.json`, `DOWNSTREAM_HANDOFF.md`. Kanıtta gerçek müşteri verisi, gizli bilgi veya ham yük yoktur.

## 10. Geri dönüş

Kip `OFF`'a alınır. Yeni tablolar eklemelidir; geri dönüşte **operasyon defteri ve denetim kayıtları silinmez** (çözülmemiş operasyonlar uzlaştırma için gerekir). Kod değişiklikleri `git revert` ile geri alınır; göç geri alma betiği yalnızca boş/çözülmüş defterde tablo kaldırır.

## 11. Devir

- **F3-A:** diyalog durum makinesi araç önerilerini yalnızca bu geçitten yürütür; `ToolReceipt` durumlarını yanıta doğru yansıtır (UNKNOWN'u başarı gibi söylemez).
- **F3-B:** onay soruları ve bağlamsal onay; operasyon özeti değişince yeni onay.
- **F3-C / G5:** gerçek sağlayıcı, gerçek doğrulama yöntemi ve SIP aktarımı; burada yalnızca sahte.
- **M08:** geçici DB, sahte sağlayıcı ve sahte doğrulayıcı fikstürleri.
- **Açık karar:** müşteri kimlik doğrulama yöntemi (ör. DTMF PIN, SMS kodu) — karar verilene kadar doğrulama noktası "yok" döner ve korunan okuma/yazma kapalı kalır.

## 12. Başlatma komutu

```
M07 paketini uygula: docs/execution/packages/W1/M07-guvenlik-politika.md.
Kuralları CLAUDE.md'den oku; M01, M02, M04 kanıtını doğrula, tüm korunan etkileri envantere al.
Mevcut backend/supervisor/ politika ve geçidini genişleterek tek zorlanan yol kur;
mevcut kip varsayılanını değiştirme, gerçek sağlayıcı veya müşteri verisi kullanma.
SEC01–SEC72'yi çalıştır, M07-G00…G19'u değerlendir, paket/M07 dalında PR aç ve dur.
```
