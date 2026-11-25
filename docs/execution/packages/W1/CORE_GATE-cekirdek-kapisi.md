# CORE_GATE — Çekirdek entegrasyon kapısı

> M00–M08 ve H01 ayrı ayrı kabul edildikten sonra, gerçek çekirdek modüllerin **birlikte** doğru çalıştığını kanıtlayan tek seferlik entegrasyon kapısı. Kapı yeni özellik eklemez; geçmeden hiçbir F paketi başlatılmaz.

| Alan | Değer |
| --- | --- |
| Kimlik | CORE_GATE |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M00, H01, M01, M02, M03, M04, M05, M06, M07, M08 |
| Sonraki | F0-A, F1-A, F2-A, F3-A, F4-A, F5-A, F6-A, W2_GATE |
| Bayrak | Yok |
| Ortam | CPU (sahte sağlayıcılar, geçici DB) |
| Eski görevler | — |
| Kaynak | Bundle `W1/Freya_2_0_M08_Agent_Implementation_Package.md` (Core Integration Gate bölümü); Orchestrator §D |
| Durum | NOT_RUN |

## 1. Amaç

Her M paketi kendi testleriyle geçebilir ama paketler arası noktalar (ör. M02 iptali ile M06 kirası, M05 adayı ile M07 yetkisi) ancak birlikte çalıştırıldığında doğrulanır. CORE_GATE bu birleşik doğrulamayı yapar ve sonucu bağımsız bir gözden geçirene onaylatır.

## 2. Başlamadan önce

- [ ] M00…M08 ve H01'in kabul edilmiş `decision.json` dosyaları ve PR'ları birleştirilmiş.
- [ ] Entegre kaynak/fikstür/yapılandırma anlık görüntüsü (commit SHA) dondurulmuş.
- [ ] Gözden geçiren belirlenmiş: kapıyı çalıştıran ajan veya kişi, kararı tek başına veremez ([master-plan §Yönetişim](../../master-plan.md#yönetişim)).

## 3. Kapsam

**Yapılacak:** Tüm zorunlu M paketi testlerinin entegre anlık görüntüde yeniden çalıştırılması; CI01–CI24 entegrasyon vakaları; M00 özellik/API/arayüz/DB/yapılandırma regresyon eşlemesi; kanıt ve kapsam doğrulaması; bağımsız inceleme.

**Yapılmayacak:** Yeni özellik; gerçek GPU, model, Asterisk, müşteri verisi. Başarısız vakayı geçirmek için test beklentisini değiştirmek. Gerçek donanım/akustik/canlı kabul iddiası (bunlar G4/G5'te).

## 4. Dosyalar

```
tests/integration/core/          # CI01–CI24 (M08.22'de yazıldı)
scripts/run_gate.py              # --gate CORE_GATE
evidence/CORE_GATE/<run_id>/
```

Kapı sırasında üretim kodu değişmez. Bir vaka başarısızsa ilgili M paketinin dalında düzeltme yapılır, PR birleştirilir ve kapı yeni anlık görüntüyle **baştan** çalıştırılır.

## 5. Tasarım ve sözleşmeler

- Komut: `python scripts/run_gate.py --gate CORE_GATE --snapshot <commit>` (profil `core_integration`).
- Zorunlu paket testleri özgün kimlikleriyle raporlanır: CT (M01), RT (M02), CR (M03), OB (M04), LX (M05), GPU (M06), SEC (M07), TH (M08), HF (H01).
- Durum birleştirme [M08 §5.5](M08-test-altyapisi.md) doğruluk tablosuna göre. Eksik nokta veya eksik paket varsa "çekirdek hazır" false olur (TH80).
- Kapsam beyanı zorunludur: bu kapı **yapısal ve sahte sağlayıcılı** bir kabuldür; canlı, GPU veya akustik kabul değildir.

## 6. Görevler

Bu kapının ayrı görevi yoktur. Yürütme sırası: anlık görüntüyü dondur → zorunlu M testlerini çalıştır → CI01–CI24 → regresyon eşlemesi → kanıt doğrulaması → bağımsız inceleme → karar.

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| CI01 | M00 → tüm paketler | Gerçek kabul edilmiş soy, kararlı özellik kimlikleri, izinsiz kaynak sapması yok |
| CI02 | M01 → M02 | Gerçek kimlik ve generation türleri çalışma zamanınca kabul edilir; geçersiz başvurular reddedilir |
| CI03 | M02 → M04 | Aynı oturum/tur/generation izi, iptal olayı korelasyonu ve güvenli üst veri |
| CI04 | Kuyruk doygunluğunda M02 → M04 | Gözlem düşse bile iptal yetkili kalır; sınırlı telemetri |
| CI05 | M03 → M02 | Aktif oturum değiştirilemez onaylı yapılandırma revizyonunu korur; yeni oturum yeni onaylı görüntüyü alır |
| CI06 | M03 → M05 | Sözlük etkinleştirmesi onaylı revizyonu kullanır; eski oturum görüntüsü kararlı |
| CI07 | M05 → M01 | Gerçek sözlük araması gerçek `EntityCandidate`'e eşlenir; bilinmeyen/belirsiz sessizce onaylanmaz |
| CI08 | M05 → M04 | Güvenli arama sayaçları ve revizyon; ham söz, özel tanımlayıcı veya metin sızıntısı yok |
| CI09 | M03 → M06 | Gerçek model tanımlayıcısı, cihaz yeteneği ve yapılandırma revizyonu kullanılır; desteklenmeyen profil reddedilir |
| CI10 | M06 → M04 | Gerçek zamanlayıcı kapsamlı kuyruk/kabul/kira metrikleri yayar; sahte cihaz gözlemi doğru etiketlidir |
| CI11 | M02 → M06 kuyrukta iptal | Kabulden önce iptal gönderimi engeller; gerçek çalışma zamanı ve zamanlayıcı uyumlu |
| CI12 | M02 → M06 çalışırken iptal | Mantıksal bayat sonuç reddedilir; kira sahte sağlayıcı bitene kadar tutulur; çift bırakma yok |
| CI13 | Bayat gözlem/OOM altında M06 | Gerçek kabul/kurtarma güvensiz işi reddeder veya politikaya göre karantinaya alır |
| CI14 | M01 → M07 | Gerçek `ToolReceipt` ve onay başvuruları; kısmi ASR korunan değişikliği yetkilendiremez |
| CI15 | M05 → M07 aday sınırı | Aday eşleşmesi kimlik doğrulamaz veya yetkilendirmez; doğrulanmış kaynak gerekir |
| CI16 | M02 → M07 iptal çiti | Kabulden önce iptal engeller; kabulden sonra bağımsız sonuçlandırma/uzlaştırma |
| CI17 | M07 yalıtılmış DB/idempotency | Eşzamanlı yinelenen talep ve yeniden başlatma en fazla bir yetkili commit edilmiş fikstür etkisi verir |
| CI18 | M07 → M04 | Kalıcı kısıtlı denetim kayıplı olay yolundan bağımsız; kişisel veri sızıntısı yok; denetim hatası gerekli yazmaları engeller |
| CI19 | M03 → M07 kip/revizyon | OFF/SHADOW/GUARDED politikası korunur; korumalı kipte açık geçiş veya gölgede çift yazma yok |
| CI20 | M02/M04/M06/M07 iki oturum yalıtımı | Oturumlar arası sonuç, kira, yetkisiz kaynak erişimi veya iz karışması yok |
| CI21 | M01/M02 sahte medya sınırı | Yanlış generation gönderimden önce reddedilir; gönderilmiş veri geri alınmış sayılmaz |
| CI22 | M00/M08 genel uyum | Güvenli eski istemci rotaları, arayüz eşlemesi, DB/yapılandırma ve protokol kontrolleri; boşluklar doğru kapsamlı |
| CI23 | M08 entegre hata tekrarı | Belirlenimci geç geri çağrı, denetim/gözlemci hatası ve temizlik; ek etki yok; kanıt yeniden üretilebilir |
| CI24 | Tüm paketler kapı doğrulayıcısı | Güncel kanıt, sayılar, zorunlu vakalar, sahiplik ve kalan ürün sınırları; eksik noktada hazırlık yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| CG00 | Paket kabulleri | M00–M08 ve H01 kabul edilmiş çalıştırma kimlikleri, hazırlık, zorunlu kapı durumları ve kanıt doğrulanmış |
| CG01 | Anlık görüntü | Entegre kaynak/fikstür/yapılandırma anlık görüntüsü ve izinli soy dondurulmuş; açıklanamayan sapma yok |
| CG02 | Kompozisyon | Tek sahiplik, uyumlu gerçek içe aktarmalar, test kompozisyonunda canlı yan etkili başlatma yok |
| CG03 | Paket testleri | CT/RT/CR/OB/LX/GPU/SEC/TH/HF zorunlu paketleri entegre anlık görüntüde çalışmış; sonuçlar özgün kimliklerle |
| CG04 | Sözleşme/yaşam döngüsü | M01/M02/M04 gerçek sözleşmeleri, yaşam döngüsü, korelasyon ve sınırlı gözlem uyumlu (CI02–CI04) |
| CG05 | Yapılandırma/sözlük | Yapılandırma ve sözlük revizyon/yetenek uyumu (CI05–CI09) |
| CG06 | Zamanlayıcı | Gerçek zamanlayıcı/çalışma zamanı/telemetri bütünleşmesi ve kira anlamı (CI10–CI13) |
| CG07 | Güvenlik | Gerçek güvenlik ve çalışma zamanı bütünleşmesi, denetim, idempotency ve kipler (CI14–CI19) |
| CG08 | Yalıtım ve hata | Yalıtım, sahte medya, koruma ve belirlenimci hata tekrarı (CI20–CI23) |
| CG09 | Regresyon | M00 özellik/API/arayüz/DB/yapılandırma regresyon eşlemesi uzlaştırılmış; çözülmemiş engelleyici regresyon veya güvensiz etkinleştirme yok |
| CG10 | Kapsam | Kanıt ve yürütme kapsamı doğrulanmış; sahte canlı/GPU/akustik kabul yok; CI01 ve CI24 tam |
| CG11 | İnceleme ve devir | Bağımsız inceleme, geri dönüş başvurusu ve F0-A devri onaylanmış; ürün kabulü ayrı kalır |

## 9. Kanıt

`evidence/CORE_GATE/<run_id>/`: `manifest.json` (anlık görüntü SHA'sı, paket çalıştırma kimlikleri), `test-log.txt`, `decision.json`, `PACKAGE_SUITE_RESULTS.json`, `INTEGRATION_RESULTS.json` (CI01–CI24), `REGRESSION_MATRIX.csv`, `REVIEW.md` (gözden geçirenin adı/rolü ve bulguları).

## 10. Geri dönüş

Kapı kod değiştirmez. FAIL durumunda: başarısız vakanın sahibi olan M paketine dönülür; o paketin dalında düzeltme yapılır, paket kabulü yenilenir, kapı yeni anlık görüntüyle tekrar çalıştırılır. Kapı sonucu kısmen kabul edilmez.

## 11. Devir

PASS ise `decision.json` → `f_packages_ready: true` ve F0-A başlatılabilir. Devir notu: bilinen sınırlamalar (gerçek GPU/akustik/SIP ölçülmedi), açık kararlar, her F paketinin kullanacağı çekirdek arayüzlerin listesi.

## 12. Başlatma komutu

```
CORE_GATE kapısını çalıştır: docs/execution/packages/W1/CORE_GATE-cekirdek-kapisi.md.
M00–M08 ve H01 kabul kanıtını doğrula, entegre commit'i dondur.
python scripts/run_gate.py --gate CORE_GATE --snapshot <commit> ile tüm zorunlu paket testlerini
ve CI01–CI24'ü çalıştır; kod değiştirme. Sonucu CG00…CG11'e göre yaz, REVIEW.md için
gözden geçirene bırak kanıtı paket/CORE_GATE dalında PR olarak aç ve dur.
```
