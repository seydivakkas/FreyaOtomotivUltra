# Riskler

> Paketler arası entegrasyon riskleri (IR), aşamalar arası riskler (CS) ve program riskleri. Tür: **Ç** = belgeler arası çelişki/belirsizlik, **U** = öngörülebilir uygulama riski. G2 aşaması ([G2-entegrasyon.md](stages/G2-entegrasyon.md), görev G2.06) her zorunlu riskin kapanış kanıtını ister. Önerilen çözüm, paketin ön kontrolünde gerçek kodla doğrulanacak bir kuraldır; doğrulanmış gerçek değildir.

## Entegrasyon riskleri (IR)

| Kimlik | Tür / önem | Risk | Çözüm ve doğrulama | Sahip |
| --- | --- | --- | --- | --- |
| IR01 | Ç / yüksek | Geri dönüş etiketi istenirken M00 commit/etiket değişikliğini yasaklar | HEAD + güvenli ağaç parmak izi; etiket yalnız kullanıcı izniyle; kirli ağaç HEAD'den yeniden üretilemez | M00 |
| IR02 | Ç / yüksek | "M03–M08 paralel" ifadesi sınırsız paralellik gibi okunabilir | Doğrudan DAG geçerlidir ([execution-order.md](execution-order.md)); tek ajan | Plan |
| IR03 | Ç / yüksek | Ön kontrolde anılan her paket zorunlu önkoşul değildir | Yalnız `Önkoşullar` satırı bağlayıcı; isteğe bağlı noktalar varsa kullanılır | M03, M05, M07, M08 |
| IR04 | Ç / kritik | M08 kabulü CG'ye, CG M00–M08'e bağlı; F6-A, WG'yi WG kabulünden önce kaydeder | CG ve WG ayrı çalıştırma düğümleri; döngüsel veya kendi kendini gerektiren PASS yok | M08, F6-A |
| IR05 | Ç / kritik | `vertical_slice_ready`, `w2_gate_ready`, `*_ready` bayrakları kabul sanılabilir | Hazırlık = uygunluk; kabul yalnız gerçek CG/WG kararıyla | M08 |
| IR06 | Ç / yüksek | Küresel G0–G5 ile paket G00–G19 karışır; test aileleri ile çalıştırmalar karışır | Önekli kapı kimlikleri (K-03); plan sayısı ≠ çalıştırma sayısı (K-09) | M08 |
| IR07 | U / yüksek | Sonradan meşru değişen kaynakta eski hash beklenir | Soy: kabul edilmiş üst commit + değişiklik; eski M00 hash'i aranmaz | M00, M08 |
| IR08 | U / kritik | `session.py`, `models.py`, `audio.py`, Supervisor/DB/aktarım/yapılandırma çok paketçe değişir | Tek yazar, seri birleştirme, bileşim sahibi, gerçek M00 yolları ([ownership.md](ownership.md)) | Plan |
| IR09 | Ç / yüksek | Kanonik ASR TurnRef ister; F1-A turu son kabulde oluşturur; F2-C kısmi sonuç turdan önce | Özel konuşma kapsamı; sahte kimlik yok; son sonuç atomik bağlanır, kısmi mühürlenir | M01, M02, F1, F2 |
| IR10 | U / kritik | F2-C kararlı önek, F1-C ipucu veya F3 beklenen slot onay gibi kullanılabilir | F3 yalnız son sonucu kabul eder; M07 onayı bağımsız; kısmi sonuç korumalı CRM okuyamaz, yanıt başlatamaz | F1, F2, F3, M07 |
| IR11 | Ç / yüksek | F1-B duraklatma son tarihi ~250 ms, F2-C ilk kısmi ≥ 800 ms, F1-A onset 64 ms | Onaylanmış kesme kısmi sonucu beklemez; geç ipucu commit'i geri almaz (SC81, SC82, SC86) | F1-B, F1-C |
| IR12 | U / yüksek | Uyarlanır endpoint uzun beklemede sondaki sessizliği alır veya sert sınırı sıfırlar | F1-A tek örnek defteri, son pay ve 20 sn aday sınırı; anlamsal gecikme ek ASR örneği değildir | F1-A, F1-C |
| IR13 | Ç / yüksek | F6-B ~200 ms referans geçmişi, F0-B gecikme+analiz+filtre ihtiyacına yetmeyebilir | Referans kapsamı doğrulanır; yetmiyorsa AEC HOLD/bypass, yakın uç korunur | F0-B, F6-B |
| IR14 | U / yüksek | DSP sonrası talep edilmiş gönderim duyulur ses değildir; saat eşlemesi eksik | Talep kapsamı, saat alanı, boşluk ve bilinmeyen kaydı; AEC uyarlaması dondurulur | F0-B, F6-B/D |
| IR15 | U / yüksek | Ham DTMF, AEC/gürültü bastırmayla bozulabilir; telefoni DTMF olayları yinelenebilir | Ham yol ve kabul edilmiş olay tekilleştirmesi; ikinci dedektör yok | F0, F6-D |
| IR16 | U / yüksek | Küresel kilide rağmen Silero tekrarlayan durumu paylaşılır | Akış/dönem başı durum yalıtımı veya HOLD; 512 örnek/32 ms pencere ve kalan korunur | H01, F1-A |
| IR17 | U / yüksek | F2-C P5 işi P1/P2'yi aç bırakır veya tembel CTranslate2 üretecini erken bırakır | Yalnız-son bekleyen sınırı; isteğe bağlı iş atlanır; kira gerçek bitişe kadar | M06, F2-C |
| IR18 | U / yüksek | F2-B alternatif çözme ile F2-C hakemliği iç içe yeniden deneme veya kısmi terfisi yapar | Tek sahip F2-B: en çok iki deneme (ilk dahil); yalnız son ifade; bilinmeyen/bayatta yeniden deneme yok | F2-B/C |
| IR19 | U / yüksek | Hotword ve kanonik düzeltme korumalı değerin üzerine yazabilir veya önceki müşteri bağlamını sızdırabilir | M05 onaylı takma adlar; ham kaynak; kapsam/TTL; olumsuzluk ve kritik değer korunur | F2-B, M05, F3 |
| IR20 | U / kritik | F3-B/C iş akışı M07 yetkisini atlar; OFF/SHADOW atlatma yolu olur | Tek geçit; paralel durum sahibi yok; gölge kipte ek korumalı okuma/etki yok | M07, F3 |
| IR21 | U / kritik | Çoklu niyetin paralel okumaları eşzamanlı yazma veya toplu onay sanılır | DAG bağımlılık doğrular; turda en çok 2 okuma / 4 aday; aynı anda tek mutasyon, işlem başı tek onay | F3-C, M07 |
| IR22 | U / kritik | RAG erişim filtresi sıralamadan sonra uygulanırsa kısıtlı belge sızar; belge içi talimat enjeksiyonu | Erişim/uygulanabilirlik sıralamadan önce; getirilen metinden araç yetkisi yok; çelişkide çekimser | F3-C |
| IR23 | U / yüksek | RAG derlem revizyonu ile canlı stok/fiyat karışır; yerel gömme yeteneği yok | Değiştirilemez dizin; kılavuzdan fiyat/stok yok; yoğun arama ayrı HOLD, BM25 tek başına hibrit PASS değil | F3-C, M03 |
| IR24 | U / kritik | Commit edilmiş DB işleminden sonra iptal; bilinmeyen sağlayıcı etkisi | Kalıcı makbuz generation'dan bağımsız uzlaştırılır; kör yeniden deneme/geri alma yok | M02, M07, F3, F6-D |
| IR25 | U / yüksek | F4-B/C morfolojisi ikinci normalizasyona yol açar veya kritik değeri değiştirir; Sezer genellemesi doğrulanmamış | Tek F4 normalizasyonu; değiştirilemez metin/aralık; incelenmiş istisnalar; desteklenmeyen IPA/SSML yok | F4-A/B/C |
| IR26 | Ç / yüksek | F4-C önerdiği 0,90/0,93 hız F6-C WSOLA aralığı (0,94–1,06) dışında | Tek hız sahibi; desteklenmiyorsa açık geri düşme; sessiz kırpma veya çift hız yok | F4-C, F5-C, F6-C |
| IR27 | Ç / yüksek | Eski ekleme tipi duraklama ile TOPLAM sınır anlamı, doğal sessizlik ve çapraz geçiş çakışır | Açık kip ve tek sınır defteri; yalnız ölçülmüş doğal sessizlik kredilenir; eksik kadar eklenir | F4-C, F6-C |
| IR28 | U / yüksek | Toplu dolgu geçerli latent'i etkiler; seed 9 tek başına bit eşdeğerliği veya kimlik kanıtı değil | Öğe başı gerçek uzunluk RNG; maske/dolgu doğrulaması; tekil geri düşme; akustik tolerans ayrı kalibre | F5-B/C |
| IR29 | U / kritik | Sürümlü önbellek anahtarında çözücü/model/telaffuz/kontrol/uyarlayıcı eksik; oturumlar arası özel yeniden kullanım | Etkin tanımlayıcı; eşitlik + kapsam; yalnız güvenli herkese açık izin listesi; telemetride hash yok | F5-B/C/D, M03, M07 |
| IR30 | U / yüksek | M06 rezervasyonları ile gözlenen bellek çift sayılır; yerel dönüş terminal sanılır; dış Ollama | Tek zamanlayıcı; cihaz/süreç/ayırıcı kapsamları; gerçek terminal/karantina; zorla öldürme yok | M06, F2, F3, F5 |
| IR31 | U / yüksek | F5-C ODE seçici son tarih altında kalibrasyonsuz kaliteyi değiştirir | Euler32 taban; yalnız onaylı ayrık profiller; gerçek ızgara/NFE; donmuş kalite karşılaştırması | F5-C |
| IR32 | U / yüksek | F5-C mikro toplu iş ile M06 zamanlama ikisi de toplu iş oluşturur; önbellek isabeti GPU bekler | Tek toplu iş koordinatörü; doğrulanmış CPU isabetine kira yok; yerel bitişten sonra GPU tutulmaz | M06, F5-C, F6-B |
| IR33 | U / kritik | F6-B uçuştaki yazma geri almadan uzun sürer; yerel boşaltma duyulur değildir | Atomik talep; talepten önce bayat yok; sonra bilinmiyor, tekrar yok; sunucu/PBX/uç kapsamları ayrı | M02, F6-B/D |
| IR34 | U / yüksek | Yeniden örnekleme, çapraz geçiş ve duraklama uzunlukları değiştirir; dolgu yanlış sayılır | Rasyonel örnek defteri; gerçek geçerli ile terminal dolgu ayrı; parçalar arası durum korunur | F0-A, F6-A/C |
| IR35 | Ç / yüksek | PCM16 AudioSocket ile G.711/G.722/Opus laboratuvarı; G.722 PCM hızı ile RTP saati | Canlı PCM tabanı korunur; örnekleme hızı, saat hızı ve yük türü ayrı; müzakere doğrulanır | F6-C/D |
| IR36 | Ç / kritik | chan_websocket FLUSH_MEDIA kanal kapsamlıdır, generation değil; XOFF ~900 çerçeve ≈ 18 sn düşük gecikmeye uygun değil | Değiştirmeden önce özel sıralı yazıcı bariyeri; muhafazakâr uzak ön süre (öneri 3–5 çerçeve) gerçek krediyle | F6-D |
| IR37 | U / kritik | Belirsiz çağrı oluşturulduktan sonra yeniden bağlanma/geri düşme çift çağrı veya eski medya üretir | Eski kanal/köprü/etki uzlaştırılır; yeni yetkili bağlama/dönem; TLS hatasında düşüş yok | F6-D, M07 |
| IR38 | U / yüksek | M04 kayıplı olayları iş denetimi veya saatler arası gecikme sanılır | M07 kalıcı denetim bağımsız; saat alanları; eksik = null; doğrudan uç ölçümü | M04, M07, F6 |
| IR39 | Ç / yüksek | Yerel model/kodek/RNNoise/sözcük dağarcığı yeteneği ile sahte yapısal kanıt karışır | Sahte yalnız yapısal davranışı doğrular; zorunlu gerçek yetenek yoksa HOLD | Tüm F paketleri |
| IR40 | Ç / yüksek | Paket kabulü içinde geniş ürün benchmark hedefleri ile küresel G2→G5 sırası | Pakette yapısal test; gerçek model ölçümü G4; insan/SIP G5; sahte eşik geçişi yok | M08 |
| IR41 | U / yüksek | Önerilen WER/MOS/ECAPA/perde ölçütleri doğrulanmış kalite sanılır; tarihsel %48,04 | Aşama/metrik kapsamı ayrı; eşli taban; bağımsız insan incelemesi; evrensel ECAPA eşiği yok; p95 toplanmaz | F2, F5, G4, G5 |
| IR42 | Ç / kritik | F5-D son paket gibi görünür ama gerçek F5-C kabulü ve gerçek akustik kanıt ister | Araştırma G5 kanıtına kadar ertelenir; R1–R6 ayrı onaylar | F5-D |
| IR43 | U / kritik | LoRA hakları, bölüm sızıntısı, desteklenmeyen eğitim hedefi, 8 GB fizibilite, taban/kimlik kayması | Haklar + rıza + donmuş taban + gerçek hedef; gruplu bölümler; ölçülmüş ileri/geri/adım; bilinmiyorsa eğitim yok | F5-D |
| IR44 | U / yüksek | Plan yolları gerçek ağaçtan farklı; rapor adlarında büyük/küçük harf tutarsızlığı | Gerçek yollar M00'dan; yapıtlar yeniden adlandırılıp sahte kanıt yapılmaz; Windows harf çakışmaları denetlenir | M00, M08 |
| IR45 | U / yüksek | M00 envanter PASS'i ürün PASS'i sanılır | Eksik/başarısız durum taşınır; zorunlu bilinmeyen HOLD | M00, M08 |
| IR46 | U / kritik | Git ve DB geri dönüşü kullanıcı düzenlemelerini veya commit edilmiş etkileri yok edebilir | Ayrı izin; ters yama/ileri migration; yalıtılmış geri yükleme testi; kalıcı uzlaştırma | M07 |
| IR47 | U / yüksek | Bayraklar/UI kontrolleri doğrulanmamış deneysel profili veya güvensiz eski yolu açar | M03 istenen/etkin; M07 uygulama; UI yetenek kapısı; aşamalı yayılım | G2, G3, M03, M07 |
| IR48 | U / yüksek | Test satırları birden çok parametreleştirmeye eşlenir; plan sayıları çalıştırılmış sanılır | Kayıt satırı + nitelikli kimlik; gerçek test bağlaması ve payda; ek testler ayrı | M08 |

## Aşamalar arası riskler (CS)

| Kimlik | Risk | Karşılık / sahip |
| --- | --- | --- |
| CS01 | Eski orkestratör/arşiv sayıları G3–G5'i içermez | Tek kayıt: [registry.json](registry.json); M08 |
| CS02 | Küresel G2–G5 etiketleri UG/SG/RG ile çift sayılır | Ayrı aşama kararları; M08 |
| CS03 | Eski plan hash'leri gerçek repo checkpoint'i sanılır | Kabul edilmiş ağaçtan bağımsız doğrulama |
| CS04 | Kaynakta açık test bağlantısı olmayan görev karşılanmış sanılır | M00/M08 gerçek testleri kabulden önce bağlar |
| CS05 | G3 sahte API kullanır veya M07'yi atlar | Gerçek sunucu yetkisi ve makbuz; G3, M07 |
| CS06 | G3, arka uç sahibi zorunlu boşluğu kapatmadan başlar | Sahibe dönülür; etkilenen G2 yeniden yeterlilik |
| CS07 | Sentetik model girdisi bağımsız insan ASR'ı sanılır | Köken ayrımı; gidiş-dönüş vekili; gerçek bağımsız altın; G4, G5 |
| CS08 | Sahte gecikme, MOS veya kapasite gerçek sonuca terfi eder | Kanıt sınıfları; M04, M08 |
| CS09 | Tekrarlanan vakalar/derlem öğeleri test sayısını şişirir | Benzersiz vaka ile çalıştırma ve örnek paydası ayrı; M08 |
| CS10 | G4 yalıtılmış PBX'i gerçek SIP kabulü sanılır | Ayrı topoloji/kanıt; F6-D, G5 |
| CS11 | Sunucu kuyruğu/boşaltma veya p95 toplamı duyulur gecikme sanılır | Bağımsız aynı saatli uç yakalama; F6, M04, G5 |
| CS12 | G5 yetkisiz kayıt veya canlı iş etkisi kullanır | Haklar, test hatları, yalıtılmış DB, test aktörleri; M07, G5 |
| CS13 | G5 katılımcı rızası sessizce eğitim hakkına dönüşür | Ayrı araştırma veri hakkı ve gözden geçiren; F5-D |
| CS14 | F5-D, G5 PASS'i beklerken G5 LoRA'yı bekler | F5-D isteğe bağlı; zorunlu bağımlılık yok |
| CS15 | Sonradan seçilen F6-D taban G5'i devralır | Kapsama özgü yeniden yeterlilik ve ayrı etkinleştirme |
| CS16 | G5 PASS pilotu otomatik açar | Ayrı açık karar, acil durdurma ve geri dönüş; kullanıcı |
| CS17 | Sonraki kaynak/değerlendirici/profil değişikliği eski kabul kanıtını yeniden kullanır | Etkilenen kapılar geçersiz; sürüm ve yeniden çalıştırma; M08 |
| CS18 | İsteğe bağlı/ertelenmiş satırlar PASS işaretlenir | Kapsam kararı durumdan ayrı; donmuş payda; M08 |

## Program riskleri

| Risk | Önlem |
| --- | --- |
| Kapsam çok büyük | W0–W2 (dikey dilim) tek başına en büyük değeri üretir; W4 P1, W5 isteğe bağlı/araştırma |
| GPU, PBX ve insan gerektiren işler bulut ajanında yapılamaz | [execution-order.md §Ortam gereksinimi](execution-order.md#ortam-gereksinimi); birim testleri sahte motorla CPU'da |
| Ölçümsüz ilerleme iddiası | Kanıt kuralları ([evidence.md](evidence.md)); `null` = ölçülmedi |
| Bayraklı iki hattın uzun süre birlikte yaşaması | G2 kip doğrulaması; PILOT sonrası eski yol uyumluluk sarmalayıcısına indirgenir |
| VRAM taşması | M06 ölçümü ve bütçesi; ADR-X-02 (`num_gpu`) |
| Leyla sesinin fark edilmeden değişmesi | Seed 9 değişmezi; F5-C kimlik ölçümü; G5 ABX |
| Asterisk/SIP ortamının hazır olmaması | AudioSocket loopback ve sentetik PBX önden; gerçek SIP G5'te |
