# G5 — Gerçek insan sesi ve SIP kabulü

> G4 kabulünden ve **ayrı** kullanıcı izninden sonra, rızası alınmış yetişkin gönüllülerle gerçek insan sesi, bağımsız dinleyici değerlendirmesi (MOS, AB/ABX), yerel PBX ve yazılım telefonlarıyla kontrollü gerçek SIP çağrıları, DTMF, operatör aktarımı ve **gerçek uçta** bağımsız ölçülmüş gecikme. İş kayıtları yalnız sentetik/test kiracısındadır; gerçek randevu, ödeme veya müşteri bildirimi yoktur. Sonuç bir kapsamlı ürün kabulü ve pilot **önerisidir**; pilot otomatik değildir.

| Alan | Değer |
| --- | --- |
| Kimlik | G5 |
| Dalga | Ürün aşaması |
| Öncelik | P0 |
| Önkoşullar | G4 |
| Sonraki | PILOT_DECISION |
| Bayrak | Yeni bayrak yok; donmuş G4 profili kullanılır. Acil durdurma anahtarı (kill switch) zorunlu |
| Ortam | Onaylı yerel PBX, yazılım telefonları, izin listesindeki test hatları; isteğe bağlı test trunk'ı ayrı izinle; kısıtlı yerel veri deposu (Git dışında) |
| Eski görevler | F0-T33, F0-T34, F1-T29, F1-T30, F2-T36, F2-T37, F3-T41, F4-T33, F5-T32, F6-T29, F6-T30 |
| Kaynak | Bundle `06_PRODUCT_STAGES/G5/Freya_2_0_G5_Real_Human_SIP_Acceptance_Master_Prompt.md`; [güvenlik ve gizlilik](../../cross-cutting/security-and-privacy.md) |
| Durum | NOT_RUN |

## 1. Amaç

Sentetik kanıt, gerçek bir müşterinin telefon hattında yaşadığını kanıtlamaz. G5; gerçek insan girişiyle ASR ve varlık doğruluğunu, gerçek dinleyicilerle Leyla sesinin doğallığını ve tutarlılığını, gerçek SIP yolunda çağrı/DTMF/aktarım davranışını ve gerçek alıcıda duyulan gecikme ile söz kesme süresini **bağımsız** ölçer. Ulaşılamayan hedef FAIL veya HOLD olarak raporlanır.

## 2. Başlamadan önce

- [ ] G4 gerçek kabul; aynı model/ağaç/profil (değilse yeniden yeterlilik).
- [ ] Kullanıcının **ayrı** G5 izni: profil matrisi, bütçe, roller, uç izin listesi, çağrı sınırı, acil durdurma, geri dönüş.
- [ ] Gizlilik incelemesi: hukuki dayanak, ayrı bilgilendirme, amaç bazlı açık rıza, geri çekilme; operatör bilgilendirilmiş.
- [ ] Kısıtlı yerel depo: erişim kontrolü, takma adlandırma, saklama süresi, silme defteri. Bulut yükleme veya dış transkripsiyon yok.
- [ ] Açık karar K-06 (karşılamada yapay zekâ bildirimi) kullanıcı tarafından karara bağlanmış.

## 3. Kapsam

**Yapılacak:** giriş ve soy; protokol ve çalışma izni; gizlilik ve katılımcı hakları; veri yalıtımı; insan derlemi ve bölümü; altın ve metrik değerlendirici; gerçek giriş ASR'ı ve korumalı varlıklar; F0 gerçek akustik koşullar; F1 gerçek endpoint ve kesmeler; F3/F4 anlam ve telaffuz; F5 ham sentez anlaşılırlığı; MOS çalışması; AB/ABX ve konuşmacı tutarlılığı; PBX ön kontrolü; gelen/giden çağrı yolculukları; DTMF; operatör aktarımı; iş ve UI kabulü; uç ölçüm düzeneği; gerçek TTFA ve söz kesme; kodek ve RTP/RTCP; kaynak/güvenlik/geri dönüş tatbikatı; kanıt ve F5-D uygunluğu; bağımsız kabul.

**Yapılmayacak:** gerçek müşteri araması veya verisi; araç sürerken veya güvensiz atölye ortamında test; eğitim amaçlı veri toplama (değerlendirme rızası eğitime izin vermez); eşikleri sonuçtan sonra değiştirme; vekil metriği MOS diye sunma; herkese açık yayın.

## 4. Dosyalar

```
tests/acceptance/g5/
  test_scope_and_privacy.py   test_reference_and_metrics.py   test_listener_protocol.py
  test_sip_journeys.py        test_endpoint_timing.py         test_release_decision.py
evidence/G5/<run_id>/          yalnız maskelenmiş özet ve opak yapıt başvuruları
<kısıtlı_yerel_depo>/<study_id>/   Git dışında; ayrı erişim/şifreleme
  permissions/ identity_map/ raw_audio/ annotation/ listening/ endpoint/ integrity/ deletion_ledger/
```

Ham ses, kimlik eşlemesi, telefon numarası veya transkript Git'e, README'ye, sıradan günlüğe, kayıt JSON'una, UI telemetrisine veya herkese açık kanıta girmez.

## 5. Tasarım ve sözleşmeler

### 5.1 Kabul yolları ve roller

| Yol | Kapsam | Kanıt sınıfı / sınır |
| --- | --- | --- |
| L0 giriş | Kabul edilmiş G4, kayıtlar ve onaylı protokol | Yalnız `STATIC_CODE` / `HISTORICAL_RECORD` |
| L1 düzenek kuru çalıştırma | Sentetik kalibrasyon sinyalleri, test rotaları; insan kaydı yok | `LOCAL_RUNTIME_MEASURED`; T5 değil |
| L2 gerçek insan girişi | Rızalı yetişkinler; senaryolu ve serbest kurgusal senaryolar | İnsan girişi kökenli `LOCAL_RUNTIME_MEASURED`; otomatik olarak uç kanıtı değil |
| L3 gerçek dinleme | Rızalı bağımsız dinleyiciler; donmuş ham/render örnekleri; kör | İnsan paneli kökenli; tahmini MOS değil |
| L4 kontrollü gerçek SIP | Yerel PBX/yazılım telefonu; ölçülmüş fiziksel uçlar; test kayıtları | Uçta gözlendiyse `REAL_ENDPOINT_MEASURED`; yalnız sinyalleşme akustik kanıt değil |
| L5 kısıtlı operatör hattı | İsteğe bağlı ayrı izin; onaylı test trunk'ı | Yalnız test edilen rota için |
| L6 bağımsız inceleme | Tüm zorunlu hücreler, gizlilik kapanışı, geri dönüş, pilot önerisi | Yalnız inceleme; otomatik etkinleştirme yok |

Roller: kullanıcı (proje sahibi) kapsam, risk ve pilot sınırlarını onaylar; gizlilik sorumlusu hak ve işlemeyi inceler; PBX yöneticisi rotaları ve güvenli kimlik bilgilerini yetkilendirir; çalışma sorumlusu protokolü yürütür; bağımsız transkripsiyoncular/fonetik değerlendiriciler altını üretir; dinleme koordinatörü profilleri körler; M08 testleri çalıştırır; bağımsız gözden geçiren karar verir. Kimse kendi işini onaylamaz.

### 5.2 Uç zamanlama olayları

| Olay | Tanım |
| --- | --- |
| T0 | Kullanıcı konuşmasının bağımsız notlanmış gerçek sonu (sondaki konuşma dışı ses hariç) |
| T1 | F1 kabul edilmiş ifade sınırı |
| T2 | Kabul edilmiş F2 SON sonuç (kısmi değil) |
| T3 | Kabul edilmiş F3 anlamsal yanıt |
| T4 | Donmuş F4 SynthesisPlan |
| T5 | F5 ilk kabul edilmiş ham ses |
| T6 | F6 ilk render edilmiş çerçeve |
| T7 | F6-B gönderim talebi ve ayrı gerçek gönderim sonucu |
| T8 | Gerçek alıcıda bağımsız tespit edilen ilk duyulur yanıt (çalma sesi, konfor gürültüsü, bip, bayat generation hariç) |
| B0 | Oynatma sırasında bağımsız gerçek yakın uç kesme başlangıcı |
| B1 | F1 adayı / yumuşak duraklatma isteği (onay ayrı) |
| B2 | M02 sert geri alma veya F1-B eşleşen devam |
| B3 | Yerel yazıcı çiti ve temizlik |
| B4 | Destekleniyorsa PBX boşaltma/işaret/tükenme |
| B5 | Kesilen eski generation'ın uçta duyulan son örneği (önceden kayıtlı koruma aralığında süren yokluk doğrulanır) |

Ölçüm bağımsız, kalibre bir düzenekle yapılır (ortak örnek saati olan çift kanallı kayıt veya ofset/kaymanın kalibre edildiği uç yerel düzenek); yalnız uygulama zaman damgası yetmez. Eşlemesiz saatler arası çıkarma yapılmaz; render geri çağrısı T8 değildir.

### 5.3 Ölçüm sözlüğü ve hedefler

Hepsi tasarım hedefidir, sonuç değildir. Yeni istatistiksel marjlar kullanıcı ve bağımsız gözden geçiren onayıyla denemeden önce dondurulur. Güvenlik hataları istatistikle affedilmez.

| Metrik | Hesap / kapsam | Hedef |
| --- | --- | --- |
| WER / CER | Gerçek insan girişi ASR'ı; toplam düzenleme / toplam referans birimi | ≤ %10 / ≤ %4 (kapsam onayı gerekir) |
| PER | Bağımsız incelenmiş fonem düzenlemesi / referans fonem | ≤ %5 (geçerli kâhin varsa; yoksa HOLD) |
| Otomotiv terim doğruluğu | Doğru katı terim oluşumu / referans oluşumu | ≥ %95 |
| Korumalı telefon/plaka/yıl | Baştaki sıfırlar dahil kesin kurgusal değer | ≥ %98 telefon/plaka, ≥ %99 yıl |
| Yanlış otomatik düzeltme / konuşmasız halüsinasyon | Her biri ayrı | ≤ %1 |
| VAD kesinlik/duyarlılık | Referans konuşma pencereleri | ≥ %95 |
| Onset / kısa endpoint | Bağımsız onset → kabul; konuşma sonu → F1 | p95 ≤ 100 ms / ≤ 500 ms |
| Yanlış sert kesme | Hatalı commit edilmiş kesme | ≤ %2 |
| Gerçek kesme duyarlılığı | Commit edilmiş gerçek kesme / bağımsız etiketli gerçek kesme | ≥ %95 |
| Yerel kesme kontrolü | Aday/kontrol → gerçek duraklatma/çit | p95 ≤ 100 ms |
| Duyulur kesme | Bağımsız B0 → B5, gerçek alıcı | p95 ≤ 200 ms |
| İlk duyulur yanıt | Doğrudan T0 → T8; tüm denemeler ve ıskalar | p95 ≤ 1,2 sn |
| İnsan MOS | Kör dinleyici puanları 1–5, koşul başı | ≥ 4,0 (vekil değil) |
| AB/ABX | Kümelenmiş GA ile tercih/ayırt etme | Önceden kayıtlı anlamlı marj; evrensel geçme puanı yok |
| ECAPA / perde | Kalibre referans kosinüsü; geçerli sesli kontur | Yalnız kalibre eşit-olmama; bilinmeyen null |
| F3 görev başarısı / dayanak | Doğrulanmış beklenen sonuç; desteklenen iddia | Her biri ≥ %95; desteksiz kritik iddia 0 |
| F5 ham TTFA / önbellek / RTF | G4'ten devralınan | p95 ≤ 500 ms / ≤ 50 ms / ≤ 0,30 |
| Çerçeve / DTMF bütünlüğü | Kontrollü çerçeveler ve beklenen fiziksel tuşlar | %100; açıklanamayan örnek 0 |
| Aktarım / çağrı kurulumu | Gerçek iki yönlü operatör sesi | Öneri: beklenen başarılı vakalarda ≥ %95; meşgul/ret vakalarında %100 doğru işleme |
| Zamanlama gözlem kapsamı | Geçerli bağımsız eşlenmiş uç zamanlaması / uygun deneme | Öneri ≥ %95; zaman aşımı ıska sayılır |
| Güvenlik değişmezleri | Yetkisiz etki/okuma, yinelenen etki, oturumlar arası sızıntı, çit sonrası bayat ses, uydurma makbuz, rızasız kayıt, yanlış bildirim, kritik bilgi hatası, yetkisiz seed/model/uyarlayıcı | 0; anında dur ve FAIL |
| Kaynak kararlılığı | Gerçek GPU/CPU/RAM/çağrı kuyruğu | Onaylı tek oturumda OOM 0; sızıntı yok |

Yüzdelikler en yakın sıra `ceil(p·n)` ile; boş referansta WER/CER/PER tanımsız (halüsinasyon ayrı); sıfır paydalı oranlar null; yalnız başarılı denemelerde p95 kabul edilmez.

### 5.4 Medya biçimleri

| Kip | Doğrulanacak özellik |
| --- | --- |
| AudioSocket 8k PCM | 20 ms'de 160 örnek, 320 bayt, 3 baytlık çerçeve başlığı; TCP (RTP değil) |
| Web 16k PCM | 20 ms'de 320 örnek, 640 bayt |
| G.711 PCMA/PCMU | 8k PCM ve RTP saati; 20 ms'de 160 oktet |
| G.722 64 kb/s | 16k PCM, 8k RTP zaman damgası saati; 20 ms'de 160 kodlanmış oktet |
| Opus | 48k RTP saati; gerçek bant genişliği, kanal, ptime, değişken yük; PLC/FEC desteği doğrulanır |

RTCP jitter doğru RTP saatiyle dönüştürülür; rapor yoksa jitter/kayıp/RTT bilinmiyor (sıfır değil); TCP HOL engellemesi RTP paket kaybı sayılmaz.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| G5.01 | Giriş ve soy | Kabul edilmiş kapsam, kaynak hash'leri, CG/WG/G2/G3/G4 soyu ve risk kaydı denetlenir | RH001–RH005 |
| G5.02 | Protokol ve çalışma izni | Profil matrisi, bütçe, roller, önceden kayıtlı istatistik, katılımcı alımı dondurulur | RH006–RH010 |
| G5.03 | Gizlilik ve katılımcı hakları | Hukuki dayanak, ayrı bilgilendirme, amaç bazlı rıza, geri çekilme | RH011–RH015 |
| G5.04 | Veri yalıtımı ve güvenlik | Kısıtlı depo ve roller, takma adlandırma, saklama, çıkış kuralları, silme | RH016–RH020 |
| G5.05 | İnsan derlemi ve bölüm | Senaryolu/serbest senaryolar, katılımcı/oturum grupları, güvenli gürültü koşulları | RH021–RH025 |
| G5.06 | Altın ve metrik değerlendirici | Kör transkript/fonem/olay notlama ve hakemlik; metrik uygulamasının kalibrasyonu | RH026–RH030 |
| G5.07 | Gerçek giriş ASR'ı ve korumalı varlıklar | İnsan derleminde onaylı ASR; ham/kanonik puanlama | RH031–RH035 |
| G5.08 | F0 gerçek akustik koşullar | Onaylı eşli temiz/gürültü/yankı koşulları; örnek muhasebesi; konuşma korunumu | RH036–RH040 |
| G5.09 | F1 gerçek endpoint ve kesmeler | Notlu onset, uyarlanır sessizlik, onay sesi ve gerçek kesme | RH041–RH045 |
| G5.10 | F3/F4 gerçek anlam ve telaffuz | Kabul edilmiş son sonuçtan doğrulanmış bilgiye ve hazırlanmış model metnine izleme | RH046–RH050 |
| G5.11 | F5 ham sentez ve anlaşılırlık | Leyla (seed 9) profilleri donar; eşli ham/render/uç uyaranları; bağımsız transkripsiyon | RH051–RH055 |
| G5.12 | MOS çalışması | Kör dengeli dinleyici çalışması; sabit ölçek, güvenli seviyeler | RH056–RH060 |
| G5.13 | AB/ABX ve konuşmacı tutarlılığı | Kalibre yetkili referans; rastgele ABX/AB; gerçek ECAPA ve F0 | RH061–RH065 |
| G5.14 | PBX ön kontrolü ve medya müzakeresi | Kurulu PBX yetenekleri, rotalar, AMI/ARI, eşler, aktarım müzakeresi | RH066–RH070 |
| G5.15 | Gelen/giden çağrı ve medya yolculukları | Gönüllülerle yetkili gerçek SIP testleri; bacak başı sinyalleşme, yanıt, iki yönlü ses | RH071–RH075 |
| G5.16 | DTMF yönlendirme | Desteklenen in-band, RFC4733 ve onaylı INFO; kesin fiziksel basışlar; tekilleştirme | RH076–RH080 |
| G5.17 | Operatör aktarımı | Yetkili aktarım; gerçek iki yönlü operatör yanıtı; bağlam en aza indirme | RH081–RH085 |
| G5.18 | İş ve UI kabulü | Test edilen rotada yalıtılmış kiracıyla gerçek insan diyalogları; makbuz/CRM/servis | RH086–RH090 |
| G5.19 | Uç ölçüm düzeneği | Ortak veya eşlenmiş saat kalibrasyonu; uç yakalama; bağımsız metroloji incelemesi | RH091–RH095 |
| G5.20 | Gerçek TTFA ve söz kesme | Gerçek uç T0–T8 ve B0–B5, yerel olaylarla eşli; hata/son tarih ıskaları | RH096–RH100 |
| G5.21 | Kodek ve RTP/RTCP kalitesi | Bacak başı gerçek kodek, saatler, ptime, aktarım ve kapsamlı RTCP | RH101–RH105 |
| G5.22 | Kaynak, güvenlik, geri dönüş tatbikatı | Kabul edilmiş yük, yerel kiralar, temizlik, acil durdurma ve kapsamlı geri dönüş | RH106–RH110 |
| G5.23 | Kanıt, riskler, F5-D uygunluğu | Zorunlu kapsam, metrik ve hak soyu uzlaştırılır; F5-D uygunluk kararı | RH111–RH115 |
| G5.24 | Bağımsız kabul ve pilot önerisi | RG kapıları, kapsam, metrikler, riskler, gizlilik ve geri dönüş değerlendirilir; karar | RH116–RH120 |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| RH001 | Yalnız plan dosyaları var | HOLD; çağrı veya kayıt yok |
| RH002 | Gerçek G4 farklı model/ağaçta kabul edilmiş | Yeniden yeterliliğe kadar engel |
| RH003 | Bozuk arşiv veya kaynak hash'i | Soy reddedilir |
| RH004 | F5-D kalıntısız ertelenmiş | Ana profil etkilenmez |
| RH005 | Gerçek yetenek/G4 kanıtı olmadan seçilmiş F6-D | Seçilen profil HOLD |
| RH006 | Ayrı G5 izni yok | Kabul yok |
| RH007 | Çalıştırma sırasında süre dolması/geri alma | Yeni denemeler durur; güvenli sonlandırma |
| RH008 | Uç izin listesi veya çağrı sınırı yok | HOLD |
| RH009 | Sonradan eşik değişikliği isteği | Ret; yeni önceden kayıtlı çalışma gerekir |
| RH010 | Planlanan katmanların gücü yetersiz | HOLD veya ileriye dönük onaylı kapsam daraltma |
| RH011 | Bilgilendirme yok | Toplama yok |
| RH012 | Kayıt reddedildi | Kayıtlı deneme yok; yalnız ayrıca izinli alternatif |
| RH013 | Dinleme izni var ama gömme izni yok | O sesin ECAPA işlemesi yok |
| RH014 | Operatör bilgilendirilmemiş | Kayıt/aktarım denemesi yok |
| RH015 | Değerlendirme rızasıyla eğitim isteği | Ret; F5-D onaysız kalır |
| RH016 | Herkese açık günlükte ham telefon/ses | Dur, FAIL, sınırla |
| RH017 | Kimlik eşlemesi sıradan değerlendiricinin okuyabildiği yerde | Erişim denetimi başarısız |
| RH018 | Bilinmeyen bulut yüklemesi veya dış transkripsiyon | Ret |
| RH019 | Puanlamadan sonra geri çekilme | Yasal silme politikası; etkilenen toplamlar yeniden hesaplanır |
| RH020 | Yedek süresi veya hak soyu yok | Toplama HOLD |
| RH021 | Aynı konuşmacı/oturum/şablon türevi geliştirme ve ayrılmış kümede | Bölüm reddi |
| RH022 | İnsan senaryodan farklı ifade kullanır | Bağımsız gerçek transkript; senaryo metni altın değil |
| RH023 | Gerçek plaka veya ödeme bilgisi geçer | Politikaya göre yakalama durur/maskeleme |
| RH024 | Sürüş veya güvensiz atölye testi önerisi | Ret |
| RH025 | Ayrılmış kümede yetersiz gürültü/rota kapsamı | İlgili iddia HOLD |
| RH026 | ASR çıktısı referans olarak kullanılmış | Döngüsel altın reddi |
| RH027 | Türkçe büyük/küçük harf, kesme işareti, ondalık ve baştaki sıfır fikstürü | Donmuş politika kritik değerleri korur |
| RH028 | Referans uzunluğu sıfır | Null hata oranı + negatif halüsinasyon sayımı |
| RH029 | İki değerlendirici fonemde anlaşamaz | Hakemlik veya açık bilinmiyor/kapsam kaybı |
| RH030 | Bilinen düzenleme sayılı fikstür ve yarı açık örnek sınırları | Kesin sayılar; bir-kayma hatası yok |
| RH031 | Geçerli insan ifadesinde çıktı yok | Silme/hata sayılır; hariç tutulmaz |
| RH032 | "Qashqai değil Juke" | Olumsuzluk ve amaçlanan düzeltme korunur |
| RH033 | Baştaki sıfırlı kurgusal telefon | Katı kesin değer puanlaması |
| RH034 | Konuşmasız girdi uydurma komut üretir | Halüsinasyon sayılır; etki yok |
| RH035 | Toplu WER geçer ama zorunlu telefon profili başarısız | Profil FAIL |
| RH036 | Temiz konuşmada fonem bastırılmış | Bozulma raporlanır; temiz geçiş yok |
| RH037 | Yalnız yankı kalibre penceresi | ERLE yalnız geçerli kâhin ve hizalamayla |
| RH038 | Çift konuşma penceresi | Yakın uç korunumu puanlanır; ERLE iddiası yok |
| RH039 | Gerçek F6 referans kapsamı yok | Güvenli AEC geri düşmesi ve bilinmeyen metrik |
| RH040 | Kontrolsüz insan karışımı | SNR tahmini etiketli; kâhin gerçeği değil |
| RH041 | Uzun telefon numarası duraklaması | Gerçek beklenen slot endpoint'i karşılaştırılır; erken bölme yok |
| RH042 | Bayat kısmi revizyon | Akustik geri düşme; sahte tur yok |
| RH043 | İlk kısmi sonuç yokken gerçek söz kesme | F1-B son tarihinin ötesinde bekleme yok |
| RH044 | "Hı hı" ile anlamlı onay | Kısmi onay yok; uygun aynı generation devamı veya commit |
| RH045 | Yalnız yankı/kesme dışı etiketler | Yanlış sert kesme paydası tüm uygun vakaları içerir |
| RH046 | RAG'den yanlış stok | Yetkili bilgi kuralı FAIL |
| RH047 | Kısmi "evet" | Yazma/onay yok |
| RH048 | Normalizasyonda model numarası veya para birimi değişir | Kritik FAIL |
| RH049 | Desteklenmeyen vurgu kontrolü | Yalnız üst veri; uygulandı iddiası yok |
| RH050 | Çelişen kılavuzlar | Kapsamlı çekimserlik/netleştirme; uydurma onarım yok |
| RH051 | Metin doğru ama ham ses farklı | Atfedilir ve hata tutulur |
| RH052 | ASR gidiş-dönüşü insan anlaşılırlığı diye kullanılmış | Yanlış etiketli sonuç reddi |
| RH053 | Eşli denemeler arasında seed veya uyarlayıcı değişir | Geçersiz karşılaştırma |
| RH054 | Bağımsız kabul edilebilir fonem alternatifleri | Donmuş eşdeğerlik uygulanır; sayılar raporlanır |
| RH055 | Ses yok veya çökmüş çıktı | Hata sayılır; seçici ayıklama yok |
| RH056 | Nesnel tahminci insan MOS diye sunulmuş | Ret |
| RH057 | Dinleyici profil/seed etiketini görür | Bozulmuş deneme; ön kayda göre işlenir |
| RH058 | Sonuçtan sonra düşük puan hariç tutulmuş | Sonradan hariç tutma reddi |
| RH059 | Aynı dinleyici/öğe tekrarı | Kümelenmiş GA; şişirilmiş bağımsız n yok |
| RH060 | Ham MOS geçer ama zorunlu telefon MOS'u tabanın altında | Telefon profili FAIL |
| RH061 | Seed 9 korunur ama benzerlik geriler | Raporlanır; kimlik garantisi yok |
| RH062 | Sentetik referans | Yalnız öz tutarlılık |
| RH063 | ABX şansa göre anlamsız | Eşdeğerlik iddiası yok |
| RH064 | Referans hakkı yok veya sıfır gömme normu | HOLD |
| RH065 | Sessiz çerçeveler | F0 null; uydurma perde yok; ses tutarlılığı kapsamlı |
| RH066 | Yapılandırılmış ile gerçek kodek uyuşmazlığı | Etkilenen rota engellenir |
| RH067 | Güvenilmeyen eş veya geçersiz sertifika | Hata kapalı; güvensiz geri düşme yok |
| RH068 | Gerçek AudioSocket 8k kipi | Doğrulanmış PCM çerçeveleme; kodlanmış yük değil |
| RH069 | WebSocket sürümü modülü destekler ama komut/kip desteklenmez | Ertele veya HOLD |
| RH070 | Acil durdurma yok veya izin listesi belirsiz | Çağrı yok |
| RH071 | AMI originate kabul edildi ama yanıtlanmadı | Başarı iddiası yok |
| RH072 | Yinelenen olayda karşılama iki kez | FAIL |
| RH073 | Giden zaman aşımı, bilinmeyen etki | Uzlaştırma; kör yeniden deneme yok |
| RH074 | İlk TTS sırasında arayan kapatır | Çit ve temizlik; tekrar yok |
| RH075 | Köprüye rağmen tek yönlü SIP sesi | Yolculuk FAIL |
| RH076 | Aynı basış hem in-band hem RFC4733 gelir | Tek kabul edilmiş olay |
| RH077 | Kasıtlı iki tekrar rakam | İki olay |
| RH078 | Yeniden iletilmiş RFC4733 paketi | Yinelenen iş eylemi yok |
| RH079 | Yankı veya konuşma yanlış DTMF tetikler | Hata sayılır; yetkisiz etki yok |
| RH080 | Bayat dönem DTMF onayı | Ret; güncel yetkili challenge gerekir |
| RH081 | Yetkisiz hedef dahili numara | Engellenir |
| RH082 | Operatör meşgul veya reddeder | Onaylı geri düşme; bağlandı iddiası yok |
| RH083 | ARI köprüsü oluştu ama operatör duyulmuyor | Tamamlama FAIL |
| RH084 | Aktarım ortasında arayan kopar | Temizlik ve bilinmeyen etkinin uzlaştırılması |
| RH085 | Yinelenen aktarım isteği | Tam bir etki ve doğrulanmış makbuz |
| RH086 | İki eşzamanlı sanal alan randevusu yarışır | İşlemsel kapasite yeniden denetimi |
| RH087 | Erken kesilen onay sunumu | Onay tüketilmez |
| RH088 | Commit edilmiş işlem sonra generation iptal | Makbuz korunur ve uzlaştırılır |
| RH089 | Kiracılar arası CRM veya kısıtlı RAG isteği | İfşadan önce ret |
| RH090 | UI bağlantı kopması | Bayat/bilinmiyor; sahte başarı veya bayat kontrol yok |
| RH091 | Eşlemesiz saatler arası çıkarma | Null/HOLD |
| RH092 | Kalibrasyon kayması geçerli aralık dışında | Etkilenen zaman damgaları geçersiz |
| RH093 | Render geri çağrısı gerçek ses değil | T8 kanıtı değil |
| RH094 | Konfor gürültüsü veya çalma sesi | Yanıt başlangıcı sayılmaz |
| RH095 | Bağımsız örnek indeksi fikstürü | Onaylı toleransta kesin gecikme ve belirsizlik |
| RH096 | Zaman aşımından önce yanıt yok | Son tarih ıskası; sıfır gecikme değil |
| RH097 | Yerel boşaltma başarılı ama eski ses sürüyor | B5 daha geç; duyulur ıska kaydedilir |
| RH098 | İddia edilen kesmeden sonra eski ses devam eder | Son örnek uzatılır veya bayat hata |
| RH099 | B0'da etkin eski ses yok | Ayrı örtüşmesiz sınıflama |
| RH100 | Yüksek hata oranında yalnız başarılı denemelerin p95'i | Kabul reddedilir |
| RH101 | G.722 16k PCM ama 8k RTP saati | Jitter doğru dönüştürülür |
| RH102 | RTCP raporu yok | Jitter/kayıp/RTT bilinmiyor; sıfır değil |
| RH103 | Opus desteklenmeyen geçiş kontrolleri | Boşaltma yeteneği iddiası yok |
| RH104 | TCP HOL RTP paket kaybı sayılmış | Kategori hatası reddi |
| RH105 | Zorunlu telefon kodeki kritik değeri bozar | Ham kaliteye rağmen profil FAIL |
| RH106 | Gerçek tamamlanmadan önce yerel iş iptali | Kira terminal/karantinaya kadar kalır |
| RH107 | Beklenmeyen OOM veya tekrarlı son tarih ıskası | Tırmanma durur; kanıt toplanır |
| RH108 | Çitten sonra oturumlar arası bayat medya | Anında FAIL/sınırlama |
| RH109 | Geri dönüşte bilinmeyen iş commit'i | Uzlaştırma; kör geri alma yok |
| RH110 | Önceki uyumlu anlık görüntü ve güvenli operatör yolu geri yüklenir | Gerçek yalıtım/temizlik doğrulanır |
| RH111 | Tarihsel birleşik %48,04 skoru DiT kanıtı diye sunulmuş | Ret |
| RH112 | Sözlük/kodek düzeltmesi kalıntıyı giderir | NO_TRAINING_NEEDED |
| RH113 | Kalıcı yeniden üretilebilir DiT kalıntısı ama eğitim hakkı yok | Araştırma HOLD |
| RH114 | Ayrılmış G5 dosyaları eğitime kopyalanmış | Ret, sınırlama |
| RH115 | Eksik yapıt veya hash uyuşmazlığı | Kanıt HOLD; sürüm yok |
| RH116 | Zorunlu rota gecikme/MOS'u ıskalar | Seçilen kapsam FAIL |
| RH117 | İsteğe bağlı F6-D denemelerden önce ertelendi | Sahte PASS veya tabanın zorla engellenmesi yok |
| RH118 | Tüm zorunlu kapılar gerçek PASS ama pilot izni yok | Yalnız uygun; etkinleştirme yanlış |
| RH119 | Herhangi bir rıza/güvenlik ihlali | Ortalamalardan bağımsız FAIL |
| RH120 | Araştırma adayı önerildi | Ayrı F5-D izni/yeniden yeterlilik; şimdi eğitim veya canlı etkinleştirme yok |

## 8. Kabul kapıları

Her kapı: bağlı tüm uygulanabilir vakaların gerçek kapsamlı PASS kanıtı; gerekli metrikler, izinler ve kaynak soyu tam.

| Kimlik | Kapı | Görev / vakalar |
| --- | --- | --- |
| RG00 | Giriş ve kabul edilmiş soy | G5.01 / RH001–RH005 |
| RG01 | Yetkili kapsam ve ön kayıt | G5.02 / RH006–RH010 |
| RG02 | Hukuk ve katılımcı hakları | G5.03 / RH011–RH015 |
| RG03 | Kısıtlı veri ve gizlilik | G5.04 / RH016–RH020 |
| RG04 | Derlem ve bağımsız altın | G5.05, G5.06 / RH021–RH030 |
| RG05 | İnsan ASR'ı ve varlıklar | G5.07 / RH031–RH035 |
| RG06 | Gerçek akustik ve tur davranışı | G5.08, G5.09 / RH036–RH045 |
| RG07 | Anlamsal ve dilbilimsel doğruluk | G5.10 / RH046–RH050 |
| RG08 | TTS insan anlaşılırlığı | G5.11 / RH051–RH055 |
| RG09 | İnsan dinleme kalitesi | G5.12 / RH056–RH060 |
| RG10 | Ses tutarlılığı ve ABX | G5.13 / RH061–RH065 |
| RG11 | PBX güvenliği ve müzakere | G5.14 / RH066–RH070 |
| RG12 | Gerçek çağrı yolculukları | G5.15 / RH071–RH075 |
| RG13 | DTMF ve operatör aktarımı | G5.16, G5.17 / RH076–RH085 |
| RG14 | İş/UI yetkisi ve makbuzlar | G5.18 / RH086–RH090 |
| RG15 | Uç ölçüm düzeneği ve zamanlama | G5.19, G5.20 / RH091–RH100 |
| RG16 | Kodek ve medya kalitesi | G5.21 / RH101–RH105 |
| RG17 | Güvenlik, kaynaklar ve geri dönüş | G5.22 / RH106–RH110 |
| RG18 | Kanıt ve araştırma kararı | G5.23 / RH111–RH115 |
| RG19 | Bağımsız sürüm kararı | G5.24 / RH116–RH120 |

## 9. Kanıt

`evidence/G5/<run_id>/` yalnız maskelenmiş özetler ve opak yapıt başvuruları: `manifest.json`, `test-log.txt`, `decision.json`, `PROTOCOL_PREREGISTRATION.md`, `PRIVACY_REVIEW.md`, `CONSENT_SUMMARY.json` (yalnız sayılar), `CORPUS_MANIFEST.json`, `ASR_RESULTS.json`, `LISTENING_RESULTS.json`, `VOICE_CONSISTENCY.json`, `SIP_JOURNEYS.json`, `DTMF_TRANSFER.json`, `ENDPOINT_TIMING.json` (T0–T8, B0–B5 dağılımları; n, ıska, kapsam), `CODEC_RTCP.json`, `RESOURCE_SAFETY.json`, `ROLLBACK_DRILL.md`, `F5D_ELIGIBILITY.md`, `RELEASE_REVIEW.md`. Ham veriler yalnız kısıtlı yerel depoda.

## 10. Geri dönüş

Acil durdurma anahtarı tüm yeni çağrıları ve denemeleri hemen durdurur. Önceki uyumlu anlık görüntü ve güvenli operatör yolu geri yüklenebilir olmalıdır (RH110). Bilinmeyen iş commit'i kör geri alınmaz, uzlaştırılır. Geri çekilen katılımcının verisi silme politikasına göre silinir ve etkilenen toplamlar yeniden hesaplanır.

## 11. Devir

- **PILOT_DECISION:** G5 kabulü yalnız pilot önerisidir; pilot ayrı kullanıcı kararıdır.
- **F5-D:** kalıcı, yeniden üretilebilir ve atfedilmiş ham F5 hatası + eğitim hakları varsa F5-D R1 uygunluğu açılabilir; değerlendirme rızası eğitim izni değildir.
- **Gerçek hata:** düzeltme ilgili pakete gider; etkilenen G2–G5 yeniden yeterlilik ister; varsayılan çözüm eğitim değildir.

## 12. Başlatma komutu

```
G5 aşamasını uygula: docs/execution/stages/G5-gercek-insan-sip.md.
Kuralları CLAUDE.md'den oku; G4 kabulünü, ayrı G5 iznini, gizlilik incelemesini, uç izin listesini ve acil durdurma anahtarını doğrula; biri eksikse dur.
Önce L0/L1 (kuru çalıştırma), sonra onaylı insan girişi, dinleme çalışması ve kontrollü SIP yolculuklarını yürüt; ham veriyi yalnız kısıtlı yerel depoda tut.
RH001–RH120'yi çalıştır, RG00…RG19'u değerlendir, asama/G5 dalında PR aç ve dur (pilotu başlatma).
```
