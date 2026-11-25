# F3-C — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı

> F3-B'nin tek Supervisor'ı içinde: lisansı ve erişimi incelenmiş yerel belge kaydı, güvenli çevrimdışı ayıklama, korumalı öbekleri bölmeyen parçalama, değiştirilemez dizin anlık görüntüsü, araç/pazar/yıl uygulanabilirliği ve ACL ön filtresi, BM25 ve (yerelde zaten varsa) yoğun gömme araması, RRF ile hibrit birleştirme, iddia–kaynak doğrulaması ve çelişkide çekimserlik; çoklu niyet ayrıştırma, doğrulanmış iş akışı grafiği, sınırlı paralel okumalar ve **tek tek onaylanan sıralı** yazma işlemleri. İnternet yok, yeni model indirme yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F3-C |
| Dalga | W4 |
| Öncelik | P1 |
| Önkoşullar | W2_GATE, F3-B |
| Sonraki | G2 |
| Bayrak | `f3_pipeline_v2` + M03 profilleri `f3.rag`, `f3.multi_intent` (varsayılan kapalı) + Supervisor kipi |
| Ortam | CPU, geçici DB, yerel fikstür korpus; yoğun gömme yalnız yerel model varsa |
| Eski görevler | F3-T15, F3-T16, F3-T18, F3-T19, F3-T20, F3-T21, F3-T22, F3-T23, F3-T24, F3-T30, F3-T32, F3-T33 |
| Kaynak | Bundle `W4/Freya_2_0_F3_C_Agent_Implementation_Package.md`; [F3 spec](../../../stages/F3-dialogue-intelligence/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

"2018 Qashqai 1.6 dCi'de yağ değişim aralığı nedir, ayrıca perşembe randevu var mı?" gibi bir istek iki bağımsız okuma (teknik bilgi + uygunluk) ve isteğe bağlı bir yazma içerir. Teknik yanıt yalnızca o araca, pazara ve yıla **uygulanabilir**, onaylı bir kaynaktan gelmeli; kaynak yoksa Freya uydurmamalı. Yazma işlemleri her biri için ayrı onayla, sırayla yapılmalı. F3-C bunu tek Supervisor ve M07 geçidi içinde kurar.

## 2. Başlamadan önce

- [ ] W2_GATE PASS (`w2_vertical_slice_accepted` gerçek WG kanıtıyla); F3-B kabul; onay. İzin yoksa yalnız planlama.
- [ ] Mevcut Supervisor, araç rotaları, DB, müşteri hafızası, arama/bilgi kodu izlenmiş; eşdeğer bilgi adaptörü varsa yeniden kullanılır; politikayı atlayan eski uç nokta katı etkinleştirmeyi engeller.
- [ ] **Model kuralı ([ADR-F3-02](../../../01-architecture/adr/ADR-F3-02-gomme-modeli.md), kabul edildi):** gömme modeli **yalnız `bge-m3`**, **CPU'da**; yapıt kullanıcı tarafından yerelde sağlanır ve M03 kaydına sürüm, SHA-256 ve lisansla girer (indirme yok). Yapıt yoksa veya yüklenemezse yoğun arama `HOLD`, yalnız BM25; başka modele geçilmez. Önek yok; azami 8192 belirteç, parça uzunluğu ölçümle seçilir.
- [ ] Belge kaynağı ve lisans kaydı (eski F3-T20) için kullanıcının sağladığı belgeler; internetten içerik çekilmez.

## 3. Kapsam

**Yapılacak:** Sözleşme ve kapsam; korpus bildirimi ve haklar; çevrimdışı ayıklama; parçalama ve sözcüksel ön işleme; dizin kaydı ve etkinleştirme; uygulanabilirlik ve ACL; BM25; yerel gömme araması (varsa); hibrit birleştirme ve bağlam paketleme; kanıtlama ve çelişki; çoklu niyet ayrıştırma; iş akışı grafiği doğrulayıcı; paralel bağımsız okumalar; sıralı yetkili etkiler; CRM/servis ve atölye/satış adaptörleri; makbuz, yaşam döngüsü, yanıt; gizlilik/kaynak/kip korumaları; entegrasyon ve benchmark tasarımı.

**Yapılmayacak:** İnternet araması veya uzak belge çekme; yeni model indirme/eğitim; hafıza düzeylerinin müşteri verisini kalıcılaştıran genişlemesi (yalnız mevcut onaylı hafıza ve saklama politikası); ödeme/satış siparişi yazması (onaylı sağlayıcı yoksa desteklenmiyor); LLM'in ikinci döngüsü.

## 4. Dosyalar

```
backend/supervisor/knowledge/
  corpus_manifest.py  extraction.py  chunking.py  index_registry.py  applicability_acl.py
  bm25.py  dense_retrieval.py  fusion.py  context_packing.py  grounding.py
backend/supervisor/dialogue/workflow/
  multi_intent.py  graph_validator.py  read_waves.py  ordered_effects.py
  adapters_crm_service.py  adapters_workshop_sales.py  lifecycle_response.py  safeguards.py
data/knowledge/                  # yerel korpus (git dışı, bildirimle), dizin anlık görüntüleri
tests/supervisor/knowledge/  tests/dialogue/workflow/
evidence/F3-C/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Korpus ve dizin

- **Kayıt:** izin listeli belge kaydı; yerel kaynak kökeni, lisans, erişim ve inceleme durumu, içerik hash'i. Lisans/erişim incelemesi eksik belge karantinada ve aranamaz. Aynı belge kimliği + revizyon farklı baytla → çakışma/karantina. Farklı kapsamlı yinelenen bayt → kapsam içinde güvenli tekilleştirme (erişim genişlemez, çift doğrulama sayılmaz). Bilinmeyen pazar/yıl üst verisi joker değildir. Doğrulanmamış "yerini alır" beyanı eski sürümü otomatik emekliye ayırmaz.
- **Ayıklama:** onaylı yerel ayrıştırıcı, sınırlı güvenli kök (yol geçişi/reparse point reddi), biçim kontrolü, yanıltıcı uzantı/aşırı boyut ret; özgün sayfa indeksleri ve basılı etiketler korunur; okunamaz pasaj kapsam uyarısıyla (bozuk metne dayalı iddia yok); başlığı/birimi eksik tablo veya gömülü dış talimat → güvensiz tablo bilgisi dışlanır, kod/ağ yürütmesi yok.
- **Parçalama:** arama normalizasyonu kesin kaynak aralıklarına eşlenir (Türkçe I/İ/ı/i, NFC); `P0300`, `ID.4` parça sınırında bölünmez; uyarı ve koşullu niteleyici sınırda bölünmez (birlikte tutulur veya aranamaz işaretlenir); örtüşen parçalar kararlı kimlik ve ortak köken (bağımsız kanıt değil); çok uzun bölüm → açık atlama/HOLD.
- **Dizin:** değiştirilemez anlık görüntü; hash, satır eşlemesi, revizyonlar, ACL; karşılaştır-değiştir ile değişim; kesilen yapım son iyi işaretçiyi değiştirmez; yanlış boyut/satır sayısı veya aynı boyut ama farklı model/havuzlama revizyonu reddedilir; okuyucu sabit görüntüyü kullanır (eski yapıt kirası tutulur); belge iptali sabit görüntüye rağmen kullanımı engeller; bozuk yoğun yapıt + geçerli sözcüksel görüntü → onaylıysa açık yalnız-sözcüksel, uydurma yoğun isabet yok.

### 5.2 Arama ve kanıtlama

- **Uygulanabilirlik ve ACL:** güvenilir özne/kurum/rol M07'den; uygun korpus **her iki sıralamadan önce** filtrelenir. Doğru marka/model/yıl/pazar → yalnız incelenmiş uygulanabilir yetkili parçalar. Aynı model adı farklı kuşak/motor → dışlanır. Yıla özgü soruda yıl bilinmiyorsa netleştirme. Genel soruya genel onaylı belge. Yetkisiz kiracıdaki kısıtlı belge kaynak kimliği sızdırmadan dışlanır. Vektör arka ucu ön filtreleyemiyorsa yetkili bölüm/tam arama veya HOLD (yalnız son filtre yetmez). Sonuçla yayın arasında erişim iptali → sonuç ve korunan metin atılır.
- **BM25:** onaylı sözcüksel dizin; sabit k1/b/tokenizer/istatistik; el ile hesaplanmış fikstür skorları önceden beyan edilen toleransta; boş sorgu/korpus sonlu; `P0300`/`P0301` kesin kısıt; eşit skorda kararlı parça kimliği; sınırlı top-k.
- **Yoğun (varsa):** gerçek yerel model/ağırlık/ABI/revizyon, önek/havuzlama/boyut/metrik doğrulanır; ağırlık yoksa `HOLD`, indirme yok; sahte vektörlerle bilinen kosinüs sırası (MOCK etiketi); sıfır norm/NaN reddi; sorgu/belge ön işleme veya model revizyonu uyuşmazlığı → yoğun yol reddi; CPU işçi sınırı/iptal sınırlı; onaylı M06 eşlemesi olmadan GPU gömme yok (ikinci yükleyici/zamanlayıcı yok).
- **Birleştirme:** RRF, bir tabanlı sıralar, eksik dal sıfır katkı, belirlenimci; tek listedeki yinelenen parça sıralamadan önce tekilleştirilir; ham skor toplamı veya olasılık yorumu yok; yoğun dal zaman aşımı → açık yalnız-sözcüksel/kısmi; top-k ve bağlam bütçesi, örtüşme kanıt sayılmaz; kritik niteleyici bütçeyi aşacaksa çekimserlik veya sağlam desteklenen kanıt (kesik uyarı yok); üst sıradaki ama iddiayla ilgisiz parça "SUPPORTED" etiketi almaz.
- **Kanıtlama:** onaylı uygulanabilir kaynak ve kesin tipli değer → doğrulanmış çapa değer, birim, niteleyici ve revizyonu destekler. İki uygulanabilir kılavuz önemli ölçüde çelişirse yalnız doğrulanmış öncelik çözer, aksi halde çatışma ve çekimserlik. Farklı pazar için yeni kılavuz uygulanabilir eskiyi geçersiz kılmaz. Kaynak içindeki istem enjeksiyonu veridir (sıfır araç/yetki/komut). Güvenlik kritik soruda uygulanabilir destek yoksa temkinli dürüst sınırlama ve onaylı teknisyene yönlendirme. Kaynak yok/eski/iptal → kesin iddia yok, uydurma atıf yok.

### 5.3 Çoklu niyet ve iş akışı

- Mevcut hiyerarşi sınırlı aday alt niyetlerle genişler (paylaşılan bağlam, tek LLM bütçesi). Teknik sorgu + uygunluk → iki ayrı okuma niyeti; istenmedikçe randevu önerisi yok. Koşullu "parça stokta varsa randevu" → koşul ve bağımlı etki korunur; bilinmeyen stok koşulu sağlamaz. Olumsuzlanmış iptal → iptal değişikliği yok. Bekleyen onay + konu değişimi → etkilenen soru/bağlam geçersiz, genel "evet" yorumlanmaz. Belirsiz zamir veya rakip araç adayı → hedefli netleştirme. Sınır aşan alt niyet veya yönlendiricide zorunlu LLM → sınırlı netleştirme/şablon, ikinci LLM döngüsü yok.
- **Grafik doğrulayıcı:** düğüm kimlikleri, kenarlar, desteklenen eylemler, sınırlar, bağımlılıklar, revizyonlar; döngü/öz-kenar → tüm grafik gönderimden önce reddedilir; bilinmeyen düğüm/araç → sağlayıcı erişiminden önce ret; modelin keyfi ifade koşulu → ret (yalnız onaylı tipli bildirimsel koşullar); bilinmeyen/başarısız zorunlu okuma önkoşulu → bağımlı yazma engellenir; yürütme sırasında bağlam revizyonu değişirse etkilenen düğümler yeniden doğrulanır, bayat sonuç CAS uygulayamaz.
- **Okuma dalgaları:** bariyerde iki bağımsız yetkili okuma sınır altında eşzamanlı (ayrı yetki, belirlenimci birleştirme); B, A'ya bağlıysa taze doğrulanmış A'yı bekler; biri zaman aşımına uğrarsa açık karışık sonuç; küresel okuma sınırında sınırlı kabul; sağlayıcı çağrısından önce/sonra iptal edilen okuma → yetkisiz gönderim/izdüşüm yok.
- **Sıralı etkiler:** tek turda iki değişiklik → uçuşta bir, ayrı sorular; ilk onay ikinciyi yürütemez; tek rastlantısal "evet" veya modelin iki işlem için `confirmed=true` vermesi → toplu onay reddi; sunum yarıda kesilirse taze güvenli sunum; slot/fiyat/kaynak revizyonu değişirse eski soru iptal; aynı mantıksal operasyon aynı/farklı anahtarla → yalnız yetkili mevcut makbuz; iki SQLite bağlantısı son boş saat için → tam bir commit; ilk etki UNKNOWN veya commit edilmiş sonra bağımlı başarısız → UNKNOWN sonraki yazmaları engeller, commit edilmiş korunur.

### 5.4 Sağlayıcılar ve yaşam döngüsü

Arayan numarası veya plaka tek başına geçmiş okumaz (varlık ifşası yok); yetkili kurumsal çok araçlı kapsamlı arama yalnız izinli alanlar; ertelemede yeni saat yoksa eski randevu değişmez; atölye kaynağı yoksa/yalnız tahminse açık bilinmiyor/tahmini (uydurma tamamlanma yok); stok/fiyat RAG'den değil gerçek sağlayıcıdan (yoksa bilinmiyor); onaylı sağlayıcı olmadan satış/atölye yazması desteklenmiyor/HOLD, ödeme yok. İptal operasyon kabulünden önce kazanırsa korunan etki yok; yerel commit sonrası TTS öncesi iptal → kalıcı makbuz korunur, bayat yanıt çitlenir, geri alma yok; dış zaman aşımı sonra geç yetkili sonuç → M07 çitli gözlemciyle uzlaştırma; mock commit veya outbox/AMI kabulü gerçek başarı değildir; karışık iş akışı yanıtında düğüm başına gerçek durum. Paylaşılan önbellekte telefon/VIN veya bilinmeyen gizlilik → bypass. Kiracı/bağlam değişiminde bekleyen özel sonuçlar atılır. SHADOW'da ek korunan okuma/çıkarım/etki/onay tüketimi yok. Kuyruk/iş akışı/görüntü sınırı ve kapanışta sınırlı temizlik.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F3-C.01 | Ön kontrol ve soy | Kabul edilmiş F3-B, M00–M08, gerçek CG/WG kanıtı ve planlama bildirimi | `PRECHECK`; RW01–RW04 |
| F3-C.02 | Envanter ve sahiplik | Mevcut Supervisor, araç rotaları, DB, müşteri hafızası, arama/bilgi kodu | `OWNERSHIP`; RW05–RW08 |
| F3-C.03 | Sözleşme ve kapsam | M01/M02/M03/M05/M07 ve F3-A/B türleri; giriş talepleri, bağlam CAS, kapsam | RW09–RW14 |
| F3-C.04 | Korpus bildirimi ve haklar | İzin listeli belge kaydı ve yerel kaynak kökeni; inceleme durumu | `CORPUS_MANIFEST`; RW15–RW20 |
| F3-C.05 | Çevrimdışı ayıklama | Onaylı yerel ayrıştırıcı, sınırlı güvenli kök, biçim kontrolü, bölüm/sayfa/satır çapaları | RW21–RW25 |
| F3-C.06 | Parçalama ve ön işleme | Kaynak aralıkları ve niteleyiciler; tipli korumalı tanımlayıcılar; Unicode | RW26–RW30 |
| F3-C.07 | Dizin kaydı ve etkinleştirme | Değiştirilemez görüntü sahnelenir; hash, satır eşlemesi, revizyon ve ACL; CAS değişimi | `INDEX_REGISTRY`; RW31–RW36 |
| F3-C.08 | Uygulanabilirlik ve ACL | M07'den güvenilir özne/kurum/rol; her iki sıralamadan önce uygun korpus | RW37–RW43 |
| F3-C.09 | BM25 | Onaylı sözcüksel dizin; sabit k1/b/tokenizer/istatistik; belirlenimci eşitlik | `BM25_REPORT`; RW44–RW47 |
| F3-C.10 | Yerel gömme araması | Gerçek yerel model/ağırlık/ABI/revizyon; önek/havuzlama/boyut/metrik; yoksa HOLD | RW48–RW53 |
| F3-C.11 | Hibrit birleştirme ve paketleme | Aynı yetkili evrende RRF; belirlenimci tekilleştirme/eşitlik; açık dal durumu | `FUSION_REPORT`; RW54–RW60 |
| F3-C.12 | Kanıtlama ve çelişki | İddiaları gerçek kaynak aralıklarına karşı doğrula; yalnız onaylı yerini alma/uygulanabilirlik | `CLAIM_SUPPORT`; RW61–RW66 |
| F3-C.13 | Çoklu niyet ayrıştırma | Mevcut hiyerarşi sınırlı aday alt niyetlerle; paylaşılan bağlam ve tek LLM bütçesi | `INTENT_DECOMPOSITION`; RW67–RW72 |
| F3-C.14 | İş akışı grafiği doğrulayıcı | Düğüm kimlikleri, kenarlar, desteklenen eylemler, sınırlar, bağımlılıklar, revizyonlar | `WORKFLOW_GRAPH`; RW73–RW78 |
| F3-C.15 | Paralel bağımsız okumalar | Sınırlı Supervisor yürütücüsü; her okuma erişimden önce yetkilendirilir | `READ_WAVE_REPORT`; RW79–RW83 |
| F3-C.16 | Sıralı yetkili etkiler | Operasyon başına M07 soru, özet, talep, işlem kontrolleri | RW84–RW90 |
| F3-C.17 | CRM ve servis adaptörleri | Onaylı müşteri/araç/geçmiş ve randevu işlemleri; asgari izdüşüm | RW91–RW93 |
| F3-C.18 | Atölye ve satış adaptörleri | Gerçek iş emri/kapasite/stok/teklif yetenekleri, kaynak revizyonları ve uygulanabilirlik | RW94–RW96 |
| F3-C.19 | Makbuz, yaşam döngüsü, yanıt | İptalden sonra M07 kalıcı uzlaştırma; düğüm başına gerçek durum | RW97–RW101 |
| F3-C.20 | Gizlilik, kaynak, kip korumaları | Sınırlı kuyruk, CPU işçileri, görüntüler, önbellekler ve bağlam; güvenli telemetri | RW102–RW106 |
| F3-C.21 | Entegrasyon ve benchmark tasarımı | Gerçek F2 final → F3-A/B/C → M07 → F4 noktası; benchmark manifesti | RW107–RW110 |
| F3-C.22 | Belirlenimci doğrulama | RW01–RW112, M08 gerçek koşucu, benzersiz test kimlikleri, sentetik fikstürler | Tüm testler çalıştırılmış |
| F3-C.23 | Regresyon ve geri dönüş | Etkilenen F3-A/B/M07/M02/M06/M08 ve W2/F2/F4 sözleşme regresyonları | RW111–RW112 |
| F3-C.24 | Kabul ve devir | F3-C-G00…G19 kanıt ve bağımsız gözden geçirenle; gerçek desteklenen kapsam | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| RW01 | Ön kontrolde F3-B kabulü yok | Uygulama kabulü yok; eksik kapsam kanıtıyla HOLD; yeni DAG kenarı değil |
| RW02 | Çekirdek PASS ama W2 yalnız hazır | Yürütme reddi; gerçek WG kanıtı gerekir |
| RW03 | Uyumsuz kaynak soyunda kabul edilmiş W2 | Kabulden önce etkilenen yollar uzlaştırılır ve yeniden test edilir |
| RW04 | Sahip yürütme izni yok | Kod/dizin/DB/model değişikliği yok; yalnız planlama |
| RW05 | Mevcut Supervisor'da eşdeğer bilgi adaptörü var | Sahipliği yeniden kullanılır; yinelenen gönderici yok |
| RW06 | Politikayı atlayan mevcut eski uç nokta | Engel belirlenir; katı etkinleştirme reddedilir; uyum muafiyeti yok |
| RW07 | Bilinen taban randevu yeteneği eşlenir | Gerçek yol, özellik kimliği, politika, makbuz ve regresyon vakası kaydedilir |
| RW08 | Model/işçi veya geçit yinelemesi bulunur | İkinci sahip reddedilir; testler sürmeden kompozisyon düzeltilir |
| RW09 | PARTIAL veya STABLE_PREFIX girdi | Sıfır korunan okuma, araç, onay, slot yazması, LLM iş çağrısı veya TTS gönderimi |
| RW10 | Aynı taleple final girdi tekrarı | Tek yönlendirme kabulü; yineleme tekrar gönderemez |
| RW11 | Aynı girdi kimliği ama değişmiş içerik | Çakışma; ikinci iş akışı veya etki yok |
| RW12 | Bayat oturum enkarnasyonu veya bağlam revizyonu | Bayat iş reddedilir; oturumlar arası izdüşüm yok |
| RW13 | Öneride rol/sağlayıcı/makbuz geçersiz kılma | Katı doğrulama geçit çağrısından önce reddeder |
| RW14 | Yanlış türler, yinelenen anahtarlar veya geçersiz aralıklar | Hata kapalı; önemli alanların zorlanması yok |
| RW15 | Geçerli bildirimli incelenmiş yerel fikstür kılavuz | Eşleşen içerik hash'iyle yalnız yalıtılmış sahnelemeye kabul |
| RW16 | Lisansı veya erişim incelemesi eksik belge | Karantina; etkin aranabilir korpusta yok |
| RW17 | Aynı belge kimliği ve revizyon, farklı baytlar | Çakışma/karantina; güvenilir sürümün üzerine yazılmaz |
| RW18 | Farklı kapsamlı yinelenen baytlar | Kapsam içinde güvenli tekilleştirme; erişim genişlemez veya çift doğrulama yok |
| RW19 | Bilinmeyen belge pazar/yıl üst verisi | Bilinmeyen joker değildir; özel uygulanabilirlik doğrulanmamış |
| RW20 | Doğrulanmış ilişki olmadan "yerini alır" beyanı | Eski sürüm otomatik emekliye ayrılmaz |
| RW21 | Kök dışında göreli yol geçişi/reparse point | Okumadan önce ret; dış dosya erişimi yok |
| RW22 | Yanıltıcı uzantı veya aşırı büyük dosya | Ret veya güvenli nedenle sınırlı hata |
| RW23 | Sayfa etiketleri dizinden farklı sentetik PDF benzeri fikstür | Özgün indeksler ve basılı etiketler korunur; uydurma yok |
| RW24 | Ayıklanamaz veya kısmen okunamaz pasaj | Kapsam/uyarı kaydedilir; bozuk metne dayalı desteksiz iddia yok |
| RW25 | Başlığı/birimi eksik tablo veya gömülü dış talimat | Güvensiz tablo bilgisi dışlanır; kod veya ağ yürütmesi yok |
| RW26 | Türkçe I/İ/ı/i ve NFC birleşen işaretler | Arama normalizasyonu kesin kaynak aralıklarına eşlenir; ham üzerine yazılmaz |
| RW27 | Parça sınırı yakınında korumalı `P0300` ve `ID.4` | Öbek sağlam; bulanık sayısal ikame yok |
| RW28 | Jeton sınırında uyarı artı koşullu niteleyici | Birlikte tutulur veya aranamaz işaretlenir; kritik sessiz bölme yok |
| RW29 | Aynı bölümde örtüşen parçalar | Kararlı kimlikler ve ortak köken; bağımsız kanıt değil |
| RW30 | Çok uzun bölüm veya tokenizer uyuşmazlığı | Sınırlı girdi, açık atlama/HOLD; sessiz kırpma yok |
| RW31 | Kesilen sahnelenmiş dizin yapımı | Son iyi işaretçi değişmez; sahnelenmiş kaynaklar güvenle temizlenir |
| RW32 | Yanlış gömme boyutu veya satır eşlemesi sayısı | Görüntü etkinleşmeden reddedilir |
| RW33 | Eşit boyut ama farklı model/havuzlama revizyonu | Uyumsuz vektörler reddedilir; yeniden yapım veya güvenli yalnız-sözcüksel |
| RW34 | Atomik değişim sırasında eşzamanlı okuyucu | Okuyucu sabit görüntüyü kullanır; eski yapıt kirası tutulur |
| RW35 | Görüntü sabitken belge iptali | Güvenlik iptali sabitlemeye rağmen kullanım ve çıktıyı engeller |
| RW36 | Bozuk yoğun yapıt ama geçerli sözcüksel görüntü | Onaylıysa açık yalnız-sözcüksel; uydurma yoğun isabet yok |
| RW37 | Doğru marka/model/yıl ve pazar | Yalnız incelenmiş uygulanabilir yetkili parçalar uygun |
| RW38 | Aynı model adı ama farklı kuşak/motor | Uyuşmayan teknik talimat dışlanır |
| RW39 | Yıla özgü soruda bilinmeyen araç yılı | Netleştirme; yalnız adaydan varsayım yok |
| RW40 | Genel soru için genel onaylı belge | Açık genel uygulanabilirlikle uygun; araca özgü değil |
| RW41 | Yetkisiz kiracıda kısıtlı belge | İki sıralama ve gömme aramasından önce dışlanır; kaynak kimliği sızıntısı yok |
| RW42 | Vektör arka ucu ACL ön filtreleyemiyor | Yetkili bölüm/tam arama veya HOLD; yalnız son filtre değil |
| RW43 | Sonuç ile yayın arasında erişim iptali | Sonuç ve korunan metin atılır; bayat yanıt yok |
| RW44 | El ile hesaplanmış skorlu küçük BM25 fikstürü | Gerçek uygulama beklenen skor/sırayı önceden beyan edilen toleransta eşler |
| RW45 | Boş sorgu veya korpus / sıfır ortalama uzunluk | Boş/desteklenmeyen sonuç; sonlu hesaplama, çökme yok |
| RW46 | Kesin tanımlayıcı `P0300` ile `P0301` | Kesin kısıt korunur; yanlış kod geri düşmesi yok |
| RW47 | Eşit sözcüksel skor | Kararlı belirlenimci parça kimliği eşitlik bozma; sınırlı top-k |
| RW48 | Eksik yerel gömme ağırlıkları veya uyumsuz ABI | Yoğun yetenek HOLD; indirme veya ağ geri düşmesi yok |
| RW49 | Bilinen kosinüslü sahte sorgu ve belge vektörleri | Doğru sayısal sıra; açık MOCK kökeni |
| RW50 | Sıfır norm veya NaN vektör | Geçersiz vektörler reddedilir; sonlu olmayan benzerlik asla yayılmaz |
| RW51 | Sorgu/belge ön işleme veya model revizyonu uyuşmazlığı | Sıralamadan önce yoğun yol reddedilir |
| RW52 | CPU işçi sınırı doldu veya gömme sırasında iptal | Sınırlı bekleme/atlama; erken yerel kaynak bırakma yok |
| RW53 | Onaylı M06 eşlemesi olmadan GPU gömme istenir | Red; ikinci yükleyici veya zamanlayıcı yok |
| RW54 | Bilinen RRF skorlu iki sıralı liste | Doğru bir tabanlı sıralar; eksik dal sıfır katkı; belirlenimci |
| RW55 | Bir listede yinelenen parça kimliği | Sıra atamasından önce tekilleştirme; şişirilmiş skor yok |
| RW56 | Aynı BM25/kosinüs ölçeği ama farklı anlam | Ham skor toplamı veya olasılık yorumu yok |
| RW57 | Yoğun dal zaman aşımı | Açık yalnız-sözcüksel/kısmi dal durumu; sahte sıra veya hibrit iddiası yok |
| RW58 | Top-k bütçesi ve çeşitli bölümler | Aday/bağlam sınırı; yinelenen örtüşme kanıt sayılmaz |
| RW59 | Kritik niteleyici istem bütçesini aşacak | Çekimserlik veya sağlam desteklenen kanıt; kesik uyarı yok |
| RW60 | Önemli iddiayla ilgisiz yüksek sıralı parça | Yalnız sıradan iddia SUPPORTED etiketlenmez |
| RW61 | Onaylı uygulanabilir kaynak ve kesin tipli değer | Doğrulanmış çapa değer, birim, niteleyici ve revizyonu destekler |
| RW62 | İki uygulanabilir kılavuz önemli ölçüde çelişir | Yalnız doğrulanmış öncelik çözer; aksi halde çatışma ve çekimserlik |
| RW63 | Farklı pazar için daha yeni kılavuz | Uygulanabilir eski kılavuzu geçersiz kılmaz |
| RW64 | Kaynak parçasında istem enjeksiyonu | İçerik veri olarak işlenir; sıfır keyfi araç/yetki/komut |
| RW65 | Uygulanabilir destek olmadan güvenlik kritik soru | Temkinli dürüst sınırlama ve onaylı teknisyene yönlendirme |
| RW66 | Kaynak yok veya eski/iptal edilmiş belge | Kesin iddia yok; uydurma atıf yok |
| RW67 | Genel teknik sorgu artı uygunluk | İki ayrı okuma niyeti; istenmedikçe randevu önerisi yok |
| RW68 | Koşullu parça stoku sonra randevu isteği | Koşul ve bağımlı etki korunur; bilinmeyen stok koşulu sağlamaz |
| RW69 | Olumsuzlanmış iptal isteği | İptal değişikliği yok; doğru okuma veya netleştirme |
| RW70 | Etkin bekleyen onay artı konu değişimi | Etkilenen soru/bağlam geçersiz; genel "evet" yorumu yok |
| RW71 | Belirsiz zamir veya rakip araç adayı | Hedefli netleştirme; tahmini araç/operasyon yok |
| RW72 | Sınırı aşan alt niyetler veya yönlendiricide zorunlu LLM | Sınırlı netleştirme/şablon; ikinci LLM döngüsü veya sessiz yanlış yorum yok |
| RW73 | Okuma önkoşullu geçerli döngüsüz grafik | Doğru sıralı uygunluk ve kararlı kaynak aralıkları |
| RW74 | Döngü veya öz-kenar | Gönderimden önce tüm grafik reddedilir |
| RW75 | Bilinmeyen düğüm başvurusu veya desteklenmeyen araç | Sağlayıcı erişiminden önce ret/desteklenmiyor; dinamik yürütme yok |
| RW76 | Model koşul olarak keyfi ifade verir | Ret; yalnız onaylı tipli bildirimsel koşullar |
| RW77 | Bilinmeyen/başarısız zorunlu okuma önkoşulu | Bağımlı yazma engellenir; başarı sayılmaz |
| RW78 | Grafik yürütmesi sırasında bağlam revizyonu değişir | Etkilenen düğümler yeniden doğrulanır; bayat sonuç CAS uygulayamaz |
| RW79 | Bariyerde iki bağımsız yetkili okuma | İkisi sınır altında ayrı yetkiyle eşzamanlı; belirlenimci birleştirme |
| RW80 | B okuması A okumasına bağlı | B taze doğrulanmış A'yı bekler; güvensiz paralel yürütme yok |
| RW81 | Bir okuma zaman aşımı, diğeri başarılı | Açık karışık sonuç; bağımsız bilgi güvenle raporlanabilir |
| RW82 | Birden çok oturum küresel okuma sınırını aşar | Sınırlı kabul/geri basınç; sınırsız görev veya haksız açlık yok |
| RW83 | Sağlayıcı çağrısından önce veya sonuçtan sonra okuma iptali | Yetkisiz sağlayıcı gönderimi veya izdüşüm yok; kapsam kaydedilir |
| RW84 | Tek turda iki değişiklik isteği | Uçuşta bir ve ayrı sorular; ilk onay ikinciyi yürütemez |
| RW85 | İki işlem için tek rastlantısal "evet" veya model `confirmed=true` | Toplu onay reddedilir; yetkisiz ikinci etki yok |
| RW86 | Koşullar tamamlanmadan kesilen sunum | Soru rastlantısal yanıtla onaylanmaz; taze güvenli sunum |
| RW87 | Onaydan sonra slot/fiyat/kaynak revizyonu değişir | Eski soru iptal; yeni sunum; bayat etki yok |
| RW88 | Aynı mantıksal operasyon aynı/farklı anahtarla tekrar | Yalnız yetkili mevcut makbuz; tüketilmiş soru korunur |
| RW89 | İki SQLite bağlantısı son boş saat için yarışır | Tam bir commit; kapasite aşılmaz; diğeri çakışma; gerçek DB |
| RW90 | İlk etki UNKNOWN veya commit edilmiş sonra bağımlı başarısız | Bilinmeyen sonraki yazmaları engeller; commit edilmiş korunur |
| RW91 | Yalnız arayan numarası veya plaka geçmiş ister | Korunan okuma reddedilir; varlık ifşası yok |
| RW92 | Yetkili kurumsal çok araçlı kapsamlı arama | Yalnız izinli kaynaklar/alanlar; başka müşteri verisi yok |
| RW93 | Erteleme için yeni saat boş değil | Eski randevu değişmez; işlem çakışması ve doğrulanmış sonuç |
| RW94 | Atölye kaynağı erişilemez veya yalnız tahmin | Açık bilinmiyor/tahmini durum; asla uydurma tamamlanma |
| RW95 | Parça stok/fiyat istendi ama yalnız kılavuz bulundu | RAG'den dinamik bilgi yok; gerçek sağlayıcı gerekir; bilinmiyor |
| RW96 | Onaylı sağlayıcı olmadan yeni satış siparişi veya atölye yazması | Desteklenmiyor/HOLD; sahte başarılı araç yok; ödeme yok |
| RW97 | İptal operasyon kabulünden önce kazanır | Korunan etki gönderilmez; geçici grafik iptal |
| RW98 | Yerel commit'ten sonra TTS'den önce iptal | Kalıcı doğrulanmış makbuz korunur; bayat yanıt çitlenir; geri alma yok |
| RW99 | Dış zaman aşımı sonra geç yetkili sonuç | Mevcut M07 çitli gözlemciyle uzlaştırma; kör yeniden deneme yok |
| RW100 | Mock commit veya outbox/AMI kabulü | Gerçek kapsamın ötesinde rezervasyon/teslim/köprü başarısı iddiası yok |
| RW101 | Desteklenmeyen bilgili karışık iş akışı yanıtı | Düğüm başına gerçek durum ve güvenli bilgi/makbuz başvuruları |
| RW102 | Paylaşılan önbellek isteği telefon/VIN veya bilinmeyen gizlilik içerir | Bypass; önbellek/günlükte ham veya hash'lenmiş kişisel veri yok |
| RW103 | Bekleyen sonuçlarla kiracı/bağlam değişimi | Özel sonuçlar atılır, etkilenen sorular iptal; kalıcı defter korunur |
| RW104 | Bozuk sağlayıcı yanıtı veya enjekte araç sonucu | Yetki geçersiz kılma reddedilir; güvenli sınırlı çıktı; ek eylem yok |
| RW105 | Geçerli canlı sorguyla SHADOW / kapalı profil | Ek korunan okuma, çıkarım, etki veya onay tüketimi yok |
| RW106 | Kuyruk/iş akışı/görüntü sınırı, kapanış ve geç tamamlanma | Sınırlı temizlik veya karantina; sızan görev/kira yok |
| RW107 | Gerçek kabul edilmiş final → teknik RAG → F3 yanıtı → F4 noktası | Gerçek yerel arama ve destek hattı; doğrulanmış atıflar |
| RW108 | Gerçek çoklu niyetli final → paralel okumalar → onaylı M07 yazması | Gerçek Supervisor + geçit + yalıtılmış SQLite; tek yetkili etki |
| RW109 | Kabul edilmiş finalin yanında F2-C/F1-C eylemsiz ipuçları | İpuçları iş yönlendiremez; final talebi bir kez |
| RW110 | Benchmark bildirimi ve payda doğrulaması | Sentetik/mock/yerel etiketler, sabit korpus bölünmesi, örnek sayıları |
| RW111 | Eski tek niyetli ve özellik/API/DB sözleşmelerinin regresyonu | Gerçek F3-A/B/M07/M02/M06 ve etkilenen W2 testleri geçer |
| RW112 | İncelenmiş geri dönüş ve hazırlık değerlendirmesi | Yeni profil güvenli sınırda kapatılır; kalıcı kayıtlar/kabuller korunur |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F3-C-G00 | Ön kontrol | Gerçek çekirdek/W2 ve F3-B kabulü, sahip izni, uyumlu soy; RW01–RW04 |
| F3-C-G01 | Sahiplik | Tek Supervisor, geçit, bağlam, zamanlayıcı ve korpus kaydı; taban yetenekler eşlenmiş; RW05–RW08 |
| F3-C-G02 | Sözleşmeler | Kesin kabul edilmiş giriş talebi ve yalnız-final kabul; katı özel şemalar; yetki geçersiz kılma yok; RW09–RW14 |
| F3-C-G03 | Korpus kökeni | Onaylı yerel kaynaklar ve hak/erişim/inceleme üst verisi, hash'ler ve karantina; RW15–RW20 |
| F3-C-G04 | Ayıklama ve parçalar | Güvenli yerel ayrıştırıcı, kesin çapalar, Unicode/korumalı öbekler, uyarı/niteleyici korunumu; RW21–RW30 |
| F3-C-G05 | Dizin yaşam döngüsü | Değiştirilemez uyumlu görüntü, sahnelenmiş CAS, kira ve iptal, açık bozulma; RW31–RW36 |
| F3-C-G06 | Erişim ve uygulanabilirlik | İki sıralamadan önce yetki, kesin araç/pazar/yıl filtresi, iptal yeniden kontrolü; RW37–RW43 |
| F3-C-G07 | Sözcüksel arama | Belirlenimci sınırlı gerçek BM25, kod koruması ve kesin fikstür skorları; RW44–RW47 |
| F3-C-G08 | Anlamsal arama | Gerçek yetenek doğru beyan edilmiş; sahte yapısal testler; model/boyut/normalizasyon kontrolleri; RW48–RW53 |
| F3-C-G09 | Hibrit birleştirme | Doğru RRF ve kararlı tekilleştirme/eşitlik/paketleme; sahte dal veya ham skor toplamı yok; RW54–RW60 |
| F3-C-G10 | Kanıtlama | Doğrulanmış önemli iddia–kaynak bağı, çelişki ve çekimserlik, enjeksiyon ve güvenlik; RW61–RW66 |
| F3-C-G11 | Çoklu niyet | Sınırlı ayrıştırma, olumsuzluk/koşullar ve netleştirme, paylaşılan LLM bütçesi; RW67–RW72 |
| F3-C-G12 | İş akışı grafiği | Gönderimden önce kimlik, bağımlılık, döngü, revizyon ve tipli koşul doğrulaması; RW73–RW78 |
| F3-C-G13 | Okuma dalgaları | Bağımsız yetkili sınırlı okumalar, belirlenimci birleştirme, bayat izdüşüm yok; RW79–RW83 |
| F3-C-G14 | Sıralı etkiler | Operasyon başına soru/özet, kalıcı idempotency, işlem yeniden doğrulaması ve bilinmeyen engeli; RW84–RW90 |
| F3-C-G15 | Uzman sağlayıcılar | Gerçek mevcut kapsamlı CRM/servis/atölye/satış adaptör kanıtı ve açık erişilemez durumu; RW91–RW96 |
| F3-C-G16 | Yaşam döngüsü, gizlilik, entegrasyon | Bayat konuşmadan bağımsız kalıcı sonuç, makbuz duyarlı yanıt, M02/M06/M07 bütünleşmesi; RW97–RW109 |
| F3-C-G17 | Doğrulama | RW01–RW112 gerçek kanıtla; fikstür kapsamı ve benchmark protokolü doğrulanmış |
| F3-C-G18 | Uyum ve geri dönüş | Özgün etkilenen testler ve M00 özellikleri korunmuş; incelenmiş geri dönüş; yıkıcı işlem yok; RW111–RW112 |
| F3-C-G19 | Bağımsız kabul | Kapsam ve sınırlamalar açık, hash'ler ve bağımsız inceleme; yalnız devir; otomatik sonraki paket yok |

## 9. Kanıt

`evidence/F3-C/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `PRECHECK.json`, `OWNERSHIP.md`, `CORPUS_MANIFEST.json` (yalnız sentetik/izinli fikstür), `INDEX_REGISTRY.json`, `BM25_REPORT.json`, `DENSE_CAPABILITY.md` (yerel model var/yok; yoksa HOLD), `FUSION_REPORT.json`, `CLAIM_SUPPORT_SPEC.md`, `INTENT_DECOMPOSITION.md`, `WORKFLOW_GRAPH_SPEC.md`, `READ_WAVE_REPORT.json`, `BENCHMARK_PROTOCOL.md` (2 000 senaryo; kanıtlama doğruluğu, çekimserlik, görev başarısı — G4), `TEST_MATRIX.json`.

## 10. Geri dönüş

`f3.rag` ve `f3.multi_intent` güvenli sınırda kapatılır: F3-B tek niyetli yol aynen. Dizin anlık görüntüleri ve kalıcı operasyon defteri silinmez. Kod `git revert`.

## 11. Devir

- **G2:** tam katman bütünleşmesi; RAG ve çoklu niyet yalnız onaylı profillerde.
- **G3:** belge kaydı/inceleme ve iş akışı görünümü için arayüz (Studio) — salt okunur izdüşümlerden.
- **Kararlar:** gömme modeli [ADR-F3-02](../../../01-architecture/adr/ADR-F3-02-gomme-modeli.md) (yalnız bge-m3, CPU). **Açık:** belge lisans/inceleme yetkilisi.

## 12. Başlatma komutu

```
F3-C paketini uygula: docs/execution/packages/W4/F3-C-coklu-niyet-rag.md.
Kuralları CLAUDE.md'den oku; W2_GATE ve F3-B kabulünü doğrula; ADR-F3-02 gömme modeli (bge-m3, CPU) yerelde yoksa yoğun aramayı HOLD bırak.
F3-B Supervisor'ı içinde incelenmiş yerel korpus, ACL ön filtreli BM25(+yerel yoğun) hibrit arama, iddia–kaynak doğrulaması,
çoklu niyet grafiği, sınırlı paralel okumalar ve tek tek onaylı sıralı yazmaları kur; internet ve model indirme yok.
RW01–RW112'yi çalıştır, F3-C-G00…G19'u değerlendir, paket/F3-C dalında PR aç ve dur.
```
