# F2-B — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme

> Otomotiv terim doğruluğunu artırmanın ana paketi: önceki commit edilmiş diyalog bağlamından yetkili ipucu izdüşümü, incelenmiş terimlerle bütçeli hotword planı, korumalı tanımlayıcıların (plaka, VIN, arıza kodu, motor tanımı) taranması, M05 üzerinden tam/takma ad/çekimli/fonetik aday üretimi, sınırlı belirlenimci sıralama, güven kanıtlarının ayrı tutulması, yanlış düzeltme ve halüsinasyon koruması, uyarlanır beam profili ve en fazla iki ardışık çözme denemesi. **Ham transkript asla değişmez**; düzeltme ayrı, aday olarak taşınır.

| Alan | Değer |
| --- | --- |
| Kimlik | F2-B |
| Dalga | W3 |
| Öncelik | P0 |
| Önkoşullar | W2_GATE, F2-A, F3-A, M05 |
| Sonraki | F3-B, F4-B, F2-C |
| Bayrak | `f2_pipeline_v2` + M03 profilleri `f2.context_hotwords`, `f2.adaptive_beam`, `f2.alternate_decode` (alternatif çözme varsayılan kapalı) |
| Ortam | CPU (sahte Whisper, sahte sağlayıcı); benchmark ölçümleri G4 |
| Eski görevler | F2-T09, F2-T10, F2-T11, F2-T12, F2-T13, F2-T14, F2-T15, F2-T16, F2-T17, F2-T18, F2-T19, F2-T20, F2-T21, F2-T30, F2-T33 |
| Kaynak | Bundle `W3/Freya_2_0_F2_B_Agent_Implementation_Package.md`; [F2 spec](../../../stages/F2-speech-recognition/spec.md), [shared-lexicon](../../../cross-cutting/shared-lexicon.md) |
| Durum | NOT_RUN |

## 1. Amaç

Ölçülen otomotiv terim doğruluğu %48,04 (hedef %95). "Nisan kaş kay iki bin yirmi" gibi bir çıktı, katalog ve bağlamla **Nissan / Qashqai / 2020** adaylarına çözülmeli; ama "nisan ayında" tarih ifadesi bozulmamalı, `1.6` `1.5`'e dönmemeli, plaka değişmemeli, belirsizse müşteriye sorulmalı. F2-B bu çözümü **aday ve kanıt** olarak üretir; doğrulama ve onay F3/M07'dedir.

## 2. Başlamadan önce

- [ ] W2_GATE, F2-A, F3-A, M05 kabul edilmiş; onay.
- [ ] ASR, hotword, sağlayıcı bayrakları, eşleyici (mapper), sözcük ve bağlam yolları M00 kimlikleri ve istenen/etkin varsayılanlarla envanterde.
- [ ] Kalibrasyon ve test kümeleri ayrı (eski F2-T33); eşik ayarı yalnızca kalibrasyon kümesinde. Metin hattı veri kümesi (eski F2-T30) sürümlü manifestle.

## 3. Kapsam

**Yapılacak:** Sahiplik ve dar kapsam; sözleşme eşlemesi; önceki durumdan bağlam izdüşümü; bağlam/model/sözlük/profil sabitleme; hotword planlayıcı ve sağlayıcı yeteneği; korumalı tanımlayıcı taraması; türetilmiş metin eşlemesi ve Unicode; M05 tam/takma ad eşleyicisi; çekim ve fonetik adaptör; aday sıralama ve belirsizlik; güven kanıtı ayrımı; yanlış düzeltme/halüsinasyon koruması; uyarlanır beam; sınırlı ardışık alternatif çözme; deneme hakemliği; F3 netleştirme ve final sonuç; iptal/temizlik/gizlilik; testler; benchmark protokolü.

**Yapılmayacak:** Akış/kısmi tanıma (F2-C); yeni ASR modeli veya ince ayar; güven kalibrasyonunun gerçek veriyle yapılması (G4 kalibrasyon kümesi); katalog doğrulaması (F3); M05 sözlük içeriği onayı (sözlük onay yetkilisi açık kararı).

## 4. Dosyalar

```
backend/speech_recognition/contextual/
  context_projection.py  pinning.py  hotword_planner.py  provider_capability.py
  protected_scan.py  text_mapping.py  alias_mapper.py  inflection_phonetic.py
  ranking.py  confidence_evidence.py  correction_guard.py  beam_policy.py
  alternate_decode.py  arbitration.py  clarification.py  telemetry.py
tests/speech_recognition/contextual/
tests/speech_recognition/lab/            # benchmark protokolü (G4'te çalışır)
evidence/F2-B/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Hat

```
F2-A ham sonuç (FINAL) ─► bağlam izdüşümü (yalnız aynı oturumun önceki commit edilmiş F3 durumu)
  ─► korumalı öbek taraması ─► M05 aday üretimi (tam → onaylı takma ad → çekimli → fonetik, sınırlı)
  ─► sıralama + belirsizlik ─► yanlış düzeltme/halüsinasyon koruması
  ─► [uygunsa, profil açıksa] alternatif çözme (en fazla 2 deneme toplam) ─► hakemlik
  ─► M01 ASRResult: raw_transcript aynen, entities = adaylar, requires_confirmation, netleştirme ipucu ─► F3
```

### 5.2 Bağlam ve hotword

- Bağlam yalnızca **aynı oturumun önceki commit edilmiş** F3 durumundan, revizyon ve tazelik kontrolüyle. Başka oturum (aynı görünen ad dahil), doğrulanmamış arayan numarası kimlik olarak, süresi dolmuş veya yabancı saat bağlamı reddedilir. Bağlam yoksa taban yol; uydurma revizyon yok. Güncel turun bağlamı gerekirse döngüsel bekleme yok. Gönderimden sonra bağlam değişirse sabitlenmiş istek bozulmaz; bayat bağlamdan türetilen aday düşürülür. Yeni açık araç, eski onaylı ipucunun üzerine yazılmaz; çatışma korunur.
- Hotword: yalnız etkin incelenmiş genel terimler; `PROPOSED/REJECTED` etkinleşmez; eşdeğerler tekilleştirilir, farklı kimlikler ayrı kalır; öğe ve karakter/jeton bütçesi (çok kelimeli terim asla kısmi); tokenizer yeteneği bilinmiyorsa onaylı güvenli sınır veya kapalı; istem benzeri kontrol/satır sonu/ayırıcı terimler reddedilir; telefon/plaka/VIN/ad/randevu kimliği hotword ve önbelleğe girmez. Sağlayıcı gelişmiş hotword desteklemiyorsa açık taban veya HOLD. Mevcut `initial_prompt`/hotword etkileşiminde çift enjeksiyon yok. Eski profil ve önbellek TTL'si korunur; sözlük revizyonu değişince bayat küresel önbellek yok.

### 5.3 Metin ve korumalı öbekler

- Ham metin harfi harfine; eski izdüşüm ayrı. Türkçe noktalı/noktasız I doğru kapsamda. NFC birleşik/ayrışık (Škoda/Citroën) geçerli kaynak aralıklarıyla. Kesme işareti varyantları ve birleşen işaretlerde kök/ek eşlemesi; grafem bölünmez. Fikstür: `"nissan kaş kay"` içinde `kaş kay` aralığı `[7,14)`.
- Sıradan bir sözcüğün içindeki marka alt dizgisi zorla değiştirilmez. Baştaki sıfırlı telefon grubu, belirsiz plaka/VIN (korunur + netleştirme), `P0300`/`P0301`, `1.6 TDI`/`1.5 TDI`, `ID.4`/`T10X`/`C4`/`3008`, para/negatif ondalık/tarih-saat korunur. Örtüşmede belirlenimci koruma önceliği; çift düzenleme yok. "değil", "hayır" kutupluluğu ve açıkça yeni bahis korunur. Bilinmeyen konuşulan rakam yorumu uydurulmaz → netleştirme. Ortak ayrıştırıcı, Freya'nın kendi okuduğu biçimleri de geri çözer: doğal saat ([ADR-F4-02](../../../01-architecture/adr/ADR-F4-02-saat-tarih-okuma.md); "öğleden sonra iki buçuk" → 14:30, "sabah ona çeyrek var" → 09:45) ve telefon numarası hangi gruplamayla söylenirse söylensin ([ADR-F4-03](../../../01-architecture/adr/ADR-F4-03-telefon-numarasi-okuma.md); ikili, üçlü, rakam rakam). Gün dilimi söylenmemiş saat ("iki buçuk") tipli belirsiz değer olarak F3'e gider; tahmin edilmez.

### 5.4 Adaylar, sıralama, güven

- Tam kanonik eşleşme kararlı kimlikli **aday**dır; müşteri/katalog onayı değildir. İncelenmiş ASR takma adı aday kanıtıdır. Yalnız TTS telaffuzu olan terim ASR'de etkinleşmez. Modeller arası takma ad çakışmasında alternatifler + belirsizlik (ekleme sırasıyla çözüm yok). Çekimli (`Peugeot'ya`, `DSG'li`) kök/ek aralığıyla. Onaylı fonetik anahtar yalnız sınırlı aday, sahte olasılık yok. Alan dışı Türkçe eşsesli → KEEP. Bilinmeyen yabancı model adı korunur. Marka–model çelişkisi ve çoklu araç bahsi → çatışma ve netleştirme.
- Sıralama sınırlı ve belirlenimci; yakın eşitlik → netleştirme (görüntü sırası kazanan değildir); aday havuzu/aralık sınırı → açık eksik sonuç; girdi/dizin sırası değişince aynı sonuç; CPU aramasında son tarih/iptal → sınırlı iş, bayat yayın yok.
- Güven kanıtları ayrı: `avg_logprob` ve `no_speech_prob` yerel türleriyle; eksik sözcük puanı/SNR `null`; NaN/Inf/aralık dışı reddedilir; sözcüksel 0,95 `RANKING_SCORE`'dur, "%95 doğruluk" değil; ikinci aday araması eksikse marj `null`; kalibrasyon yoksa `null`.

### 5.5 Koruma, beam ve alternatif çözme

- Korumalı çatışmalı yüksek güven bile izdüşümü engeller; alanla benzeşen doğru sıradan sözcük KEEP; şüpheli üst veriyle yalnız-hotword tekrarı → şüpheli/netleştir, uydurma düzeltilmiş cümle yok; meşru tekrarlanan sayı/sözcük koşulsuz silinmez; `NO_SPEECH` ile sağlayıcı `ERROR` ayrı; geçersiz aralık → izdüşüm atılır, ham korunur.
- Beam: taban uyum çözmesi tarihsel etkin ayarlarla; onaylı zor profil gönderimden önce izinli kümeden (laboratuvarda 1/3/5) seçilir, M06 **P1**; desteklenmeyen seçenek → açık taban veya HOLD.
- Alternatif çözme **varsayılan kapalı**; açıkken: doğrulanmış tamamlanma + bütçe → taze M06 kabulü/kirası, aynı mantıksal söz; son tarih yetmezse veya maliyet bilinmiyorsa atlanır; yerel yineleyici hâlâ çalışıyorsa alternatif yok; **toplam en fazla iki deneme**; model/yıl/olumsuzluk çelişkisinde ham birleştirilmez, birincil korunur ve netleştirilir; seçilen alternatifte ham metin alternatifinki olur, birincil köken özel olarak saklanır, tek FINAL; alternatif başarısızsa politika güvenli birinciyi veya açık hatayı seçer; denemeler arası iptalde yeni gönderim yok.

### 5.6 F3 ve diğer katmanlar

Belirsiz aday F3'e ulaşır ve genel "evet" gelse bile netleştirme gerekir; yetkisiz eylem yok (M07). F1-B eski TTS generation'ını kesince yeni giriş ASR'si uygun kalır; F6-B duraklat/devam ASR'yi çoğaltmaz. İki oturum aynı sözlük görüntüsünü yalnız değiştirilemez olarak paylaşır.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F2-B.01 | Ön kontrol | Çekirdek/W2 ve F2-A/F3-A/M05 kabulü, soy, onay | Kanıt başvurulu ön kontrol; eksikse HOLD |
| F2-B.02 | Envanter | ASR, hotword, sağlayıcı bayrakları, eşleyici, sözcük ve bağlam rotaları | M00 özellik haritası; istenen/etkin varsayılanlar |
| F2-B.03 | Sahiplik ve kapsam | Tek tanıma/sözlük/zamanlayıcı sahibi; yeni DAG kenarı yok | İncelenmiş fark |
| F2-B.04 | Sözleşme eşlemesi | M01/M02/M03/M05/M06/F3 | Eksik zorunlu alanda HOLD |
| F2-B.05 | Bağlam izdüşümü | Yetkili önceki durum adaptörü; aynı oturum, tazelik, revizyon; yoksa geri düşme | AE07–AE15 |
| F2-B.06 | Sabitleme | Bağlam/model/sözlük/profil gönderimden önce doğrulanır; döngüsel bekleme yok | AE12–AE14 |
| F2-B.07 | Hotword planlayıcı | Onaylı terimler, sıralama, bütçeler; enjeksiyon/kişisel veri dışlama; eski liste korunur | AE16–AE23 |
| F2-B.08 | Sağlayıcı yeteneği | Gerçek destek, etkin jeton sınırları; yinelenen istem eğilimi yok | AE24–AE27 |
| F2-B.09 | Korumalı tarama | Kesin rakam/kutupluluk; örtüşme politikası; belirsizse koru | AE34–AE42 |
| F2-B.10 | Metin eşlemesi | Ham değişmez; yarı açık aralık yeniden kurma; TTS normalizasyonu yok | AE28–AE33 |
| F2-B.11 | Takma ad eşleyicisi | M05 tam ve incelenmiş; kararlı kimlikler; belirsizlik korunur | AE43–AE46 |
| F2-B.12 | Çekim ve fonetik | Kök/ek kanıtı; onaylı dizin; keyfi kod düzenlemesi yok | AE47–AE52 |
| F2-B.13 | Sıralama | Belirlenimcilik, sınırlar, açık kırpma, eşitlikte çekimserlik | AE53–AE56 |
| F2-B.14 | Güven kanıtı | Yerel puanlar, sözcüksel sıralar, kalibrasyon null olabilir; geçersizler reddedilir | AE57–AE62 |
| F2-B.15 | Yanlış düzeltme koruması | Olumsuz/bilinmeyen/sıradan sözcük; sahte kesinlik yok | AE63–AE68 |
| F2-B.16 | Uyarlanır beam | Onaylı etkin ayarlar; laboratuvarda beam 1/3/5; eski varsayılanlar değişmez | AE69–AE72 |
| F2-B.17 | Alternatif çözme | Varsayılan kapalı; en fazla iki deneme; taze M06 kirası ve son tarih; üçüncü yok | AE73–AE76 |
| F2-B.18 | Hakemlik | Dizgi birleştirme yok; çelişkide netleştirme; tek final | AE77–AE79 |
| F2-B.19 | F3 ve final sonuç | Yalnız aday anlamı; M07 sınırları; araç etkisi yok | AE84 |
| F2-B.20 | İptal ve gizlilik | M02 atomik teslim; yerel kira tutulur; sınırlı özel veri | AE80–AE83, AE85–AE86 |
| F2-B.21 | Entegrasyon | Gerçek F2-A/F3-A/M05/M06; F1-B/F6-B ve mevcut arayüzler korunur | AE87 |
| F2-B.22 | Testler | AE01–AE88, M08 kanıtı | Gerçek komutlar, fikstür hash'leri, iddialar ve durumlar |
| F2-B.23 | Regresyon, benchmark, geri dönüş | Özellik korunumu, bağımsız bölünmeler, güvenli geri alma; gelecek metrikler NOT_RUN | AE88; `BENCHMARK_PROTOCOL.md` |
| F2-B.24 | Kabul ve devir | F2-B-G00…G19; hazırlık koşullu; dur | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| AE01 | W2 yok veya yalnız plan kabulü | Kaynak/etkinleştirme değişikliğinden önce HOLD |
| AE02 | Kabul edilmiş W2 ama bayat soy | Etkilenen önkoşullar yeniden doğrulanır veya HOLD |
| AE03 | F2-A/F3-A/M05 kabulü yok | Yürütme engellenir; yeni bağımlılık çıkarılmaz |
| AE04 | Çevrimdışı yalnız CPU ortamında içe aktarma | Model yükleme/ağ/GPU başlatma yok |
| AE05 | Gerçek sözleşme uyuşmazlığı | Açık eşleme/HOLD; yinelenen M01 türü yok |
| AE06 | Birden çok eski/katı çağrı yolu | Tüm gerçek yollar envanterde; tek katı sağlayıcı otoritesi |
| AE07 | Geçerli önceki commit edilmiş aynı oturum bağlamı | Doğru sınırlı izdüşüm; revizyon kökeni |
| AE08 | Aynı görünen adlı başka oturum bağlamı | Ret; sızan ipucu yok |
| AE09 | Bağlam kimliği olarak doğrulanmamış arayan numarası | Yeni yetki veya özne aşırı okuma yok |
| AE10 | Bağlam yok | Taban/bağlamsız yol; uydurma revizyon yok |
| AE11 | Süresi dolmuş veya yabancı saatli bağlam | Ret veya onaylı güvenli geri düşme; saatler arası çıkarma yok |
| AE12 | Gönderimden önce bağlam revizyonu değişir | Sınırlı taze izdüşüm veya bağlamsız geri düşme |
| AE13 | Yerel çözme sırasında bağlam değişir | Sabit istek bozulmaz; bayat bağlam adayı düşürülür |
| AE14 | İpucu için güncel tur gerekir | Döngüsel bekleme yok; yalnız önceki commit edilmiş bağlam |
| AE15 | Açık yeni araç önceki onaylı ipucuyla çelişir | Harfi harfine ve çatışma korunur; eski araç üzerine yazılmaz |
| AE16 | Bağlamda etkin incelenmiş genel terimler | Belirlenimci ilgili terim sırası ve köken |
| AE17 | Etkin olmayan/önerilen/reddedilmiş takma adlar | Hotword veya izdüşümde etkinleşmez |
| AE18 | Yinelenen ve eşsesli terimler | Yalnız eşdeğerler tekilleşir; farklı kimlikler ayrı kalır |
| AE19 | Öğe sınırına ulaşıldı | Sınırda durur; kırpma kaydedilir |
| AE20 | Çok kelimeli takma adla karakter/jeton bütçesi | Ayırıcılar dahil; asla kısmi terim |
| AE21 | Bilinmeyen tokenizer yeteneği | Onaylı güvenli sınır/kapalı; tahmini jeton sayısı yok |
| AE22 | İstem benzeri kontrol/satır sonu/ayırıcı terim | Güvensiz girdi reddedilir; istem enjeksiyonu yok |
| AE23 | İpucunda telefon/plaka/VIN/ad/randevu kimliği | Hotword ve önbellekten dışlanır |
| AE24 | Sağlayıcıda gelişmiş hotword yok | Açık desteklenen taban veya HOLD; gizli değişiklik yok |
| AE25 | Mevcut `initial_prompt`/hotword etkileşimi | Çift enjeksiyon yok; etkin parametreler kaydedilir |
| AE26 | Eski profil ve önbellek TTL'si | Gözlenen özgün davranış korunur |
| AE27 | Turlar arası sözlük revizyonu/önbellek değişimi | Bayat küresel önbellek yok; sabit eski deneme etkilenmez |
| AE28 | Ham baştaki/sondaki boşluk ve noktalama | Sağlayıcı ham metni aynen; eski izdüşüm ayrı |
| AE29 | Türkçe noktalı/noktasız I | Doğru kapsamlı eşleşme; birleştirme yok |
| AE30 | NFC birleşik/ayrışık Škoda/Citroën | Geçerli ham Unicode aralıkları; yazım korunur |
| AE31 | Kesme işareti varyantları ve birleşen işaretler | Kök/ek eşlemesi doğru; grafem bölünmez |
| AE32 | Çok jetonlu `kaş kay` | Fikstürde kesin ham aralık [7,14); sınırlı arama |
| AE33 | Marka alt dizgisi içeren sıradan sözcük | Zorla alt dizgi değiştirme yok |
| AE34 | Baştaki sıfırlı telefon rakam grubu | Yaklaşık düzeltme veya kayıp yok |
| AE35 | Biçimi belirsiz plaka/VIN benzeri metin | Korunur + netleştirme; bulanık değişiklik yok |
| AE36 | `P0300` ile `P0301` | Kod ikamesi yok |
| AE37 | `1.6 TDI` ile `1.5 TDI` | Sayı ve birim korunur; yalnız kesin kapsamlı terim |
| AE38 | `ID.4`, `T10X`, `C4`, model `3008` | Harfi harfine kod/rakam; belirsizlik korunur |
| AE39 | Para, negatif ondalık, tarih/saat (doğal saat biçimleri dahil) | İşaret, büyüklük ve anlamsal temsil korunur; "öğleden sonra iki buçuk" → 14:30; gün dilimsiz "iki buçuk" belirsiz kalır |
| AE40 | Motor kodu/ondalık ve takma ad örtüşmesi | Belirlenimci koruma önceliği; çift düzenleme yok |
| AE41 | Olumsuzluk ve düzeltme "değil", "hayır" | Kutupluluk ve açık yeni bahis korunur |
| AE42 | Bilinmeyen konuşulan rakam yorumu | Uydurma tipli değer yok; netleştirme |
| AE43 | Belirsiz olmayan tam kanonik varlık | Kararlı kimlikli aday; müşteri/katalog onayı değil |
| AE44 | İncelenmiş tam ASR takma adı | Aday kanıtı; yalnız onaylı isteğe bağlı izdüşüm |
| AE45 | Yalnız TTS telaffuzu, onaylı ASR takma adı yok | Otomatik ASR etkinleşmesi yok |
| AE46 | Modeller arası tam takma ad çakışması | Alternatifler ve belirsizlik; ekleme sırasıyla çözüm yok |
| AE47 | Çekimli `Peugeot'ya` / `DSG'li` | Kök/ek aralığı korunur; ilgisiz gövdeleme yok |
| AE48 | Onaylı fonetik anahtar en yakın aday | Yalnız sınırlı aday; sahte olasılık yok |
| AE49 | Alan dışı sıradan Türkçe eşsesli | KEEP; zorla otomotiv adayı yok |
| AE50 | Bilinmeyen yabancı model adı | Bilinmiyor korunur; keyfi en yakın marka yok |
| AE51 | Üst marka model adayıyla çelişir | Çatışma ve netleştirme; uydurma uyumluluk yok |
| AE52 | Birden çok araç bahsedilir | Ayrı aralık/varlıklar ve seçim korunur |
| AE53 | Adaylarda yakın eşitlik | Netleştirme; kararlı görüntü sırası kazanan değil |
| AE54 | Aday havuzu veya aralık sınırı doldu | Açık eksik sonuç; tekil seçim yok |
| AE55 | Rastgele girdi/dizin sırası | Aynı sınırlı sonuç ve puan kökeni |
| AE56 | CPU araması sırasında son tarih/iptal | Sınırlı iş, güvenli temizlik, bayat yayın yok |
| AE57 | Negatif `avg_logprob` ve `no_speech_prob` | Yerel türler/aralıklar korunur; kalibre güven değil |
| AE58 | Eksik sözcük puanları veya SNR | Null/eksiklik; uydurma sıfır yok |
| AE59 | NaN/Inf/aralık dışı puanlar | Gerçek sözleşmeye göre ret veya güvenli nedenle atlama |
| AE60 | Sözcüksel puan 0,95 | RANKING_SCORE; "%95 doğruluk" değil |
| AE61 | Eksik ikinci aday araması | Marj null; uydurma sonsuz yok |
| AE62 | Kalibre olmayan model üst verisi | Kalibrasyon null; yüzde olasılık yok |
| AE63 | Korumalı çatışmalı yüksek güven | Sert koruma izdüşümü engeller |
| AE64 | Takma ada benzeyen doğru sıradan sözcük | Yanlış düzeltme koruması KEEP |
| AE65 | Şüpheli üst verili yalnız-hotword tekrarı | Şüpheli/netleştir; uydurma düzeltilmiş ifade yok |
| AE66 | Meşru tekrarlanan sayı/sözcük | Koşulsuz halüsinasyon silmesi yok |
| AE67 | NO_SPEECH ile sağlayıcı ERROR | Ayrı sonuçlar; diyalog yazma yolu yok |
| AE68 | Geçersiz aralık veya izdüşüm kapsamı | İzdüşüm atılır; ham ve neden korunur |
| AE69 | Taban uyum çözmesi | Kesin etkin tarihsel ayarlar |
| AE70 | Onaylı gönderim öncesi zor profil | İzinli kümeden doğrulanmış beam; M06 P1 |
| AE71 | Desteklenmeyen beam/sağlayıcı seçeneği | Gönderimden önce açık taban geri düşme veya HOLD |
| AE72 | Alternatif kapalı | Düşük puana rağmen tam bir yerel deneme |
| AE73 | Doğrulanmış tamamlanma ve bütçeyle uygun alternatif | Taze kabul/kira; aynı mantıksal söz |
| AE74 | Toplam son tarih yetmez / maliyet bilinmiyor | Alternatif atlanır; güvenli karar |
| AE75 | Yerel yineleyici hâlâ çalışıyor / terminal bilinmiyor | Alternatif yok; kira tutulur/karantina |
| AE76 | Alternatif deneme sınırını aşar | Üçüncü deneme veya özyinelemeli çözme yok |
| AE77 | Alternatif model/yıl/olumsuzlukta ayrışır | Ham birleştirilmez; birincil korunur ve netleştirilir |
| AE78 | Onaylı seçilen alternatif | Kesin alternatif ham metni; birincil köken özel olarak saklanır; tek FINAL |
| AE79 | Geçerli ilkten sonra alternatif başarısız | Politika denetimli güvenli ilk veya açık hata; kör yeniden deneme yok |
| AE80 | Denemeler arası veya yerel iş sırasında iptal | Çitten sonra yeni gönderim yok; gerçek kira temizliği |
| AE81 | Final eklemeden / tüketimden önce geç sonuç | M02 atomik ret ve F3 yeniden kontrol |
| AE82 | F1-B eski TTS generation'ını keser | Yeni giriş ASR'si uygun kalır; istenmeyen iptal yok |
| AE83 | Eşzamanlı F6-B yumuşak duraklat/devam | Yinelenen ASR yok; aktarım sahipliği değişmez |
| AE84 | Belirsiz aday F3'e ulaşır ve genel "evet" | Netleştirme gerekli kalır; yetkisiz eylem yok |
| AE85 | Aynı sözlüklü iki eşzamanlı oturum | Yalıtılmış bağlam/denemeler; yalnız paylaşılan değiştirilemez görüntü |
| AE86 | Telemetri taşması ve hassas dizgiler | Yük/kişisel veri/hash sızıntısı veya kontrol tıkanması yok |
| AE87 | Sahte yerel ve yalıtılmış sağlayıcıyla gerçek F2-A → F2-B → F3-A | Tek final teslim; aday onaylanmamış; gizli etki yok; özellik regresyonu |
| AE88 | Geri dönüş ve kanıt bildirimi | Onaylı uyum geri gelir; kesin yollar/hash/test durumu; sahte PASS yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F2-B-G00 | Ön kontrol | Gerçek CG00–CG11 ve WG00–WG11 PASS; F2-A/F3-A/M05 kabul; uyumlu soy ve onay; AE01–AE03 |
| F2-B-G01 | Tek sahip | Tek ASR/sözlük/zamanlayıcı sahibi; envanter/onaylı fark; çevrimdışı içe aktarma; paralel aktif yol yok; AE04–AE06 |
| F2-B-G02 | Sözleşmeler | Kabul edilmiş M01/M02/M03/M05/M06 arayüzleri, değiştirilemez kapsam ve şema eşlemesi; AE05, AE28, AE43, AE57–AE62 |
| F2-B-G03 | Bağlam | Yalnız yetkili önceki commit edilmiş F3 bağlamı; kapsam/revizyon/tazelik/yokluk ve döngüsüz davranış; AE07–AE15 |
| F2-B-G04 | Hotword | Belirlenimci incelenmiş hotword'ler, bütçe/gizlilik/sağlayıcı yeteneği, gözlenen uyum; AE16–AE27 |
| F2-B-G05 | Ham metin | Değiştirilemez ham metin, Unicode kaynak eşlemesi, gizli normalizasyon yok; AE28–AE33 |
| F2-B-G06 | Korumalı öbekler | Korumalı tanımlayıcılar ve kutupluluk korunur; bulanık kritik düzenleme yok; AE34–AE42 |
| F2-B-G07 | M05 araması | Tam/takma ad/çekimli/fonetik arama ve kararlı kimlikler; otomatik yükseltme yok; AE43–AE52 |
| F2-B-G08 | Sıralama | Sınırlı belirlenimci sıralama, belirsizlik/kırpma/çekimserlik; AE53–AE56, AE61 |
| F2-B-G09 | Güven | Yerel ve sözcüksel güven ayrımı, null anlamı, sahte kalibrasyon yok; AE57–AE62 |
| F2-B-G10 | Koruma | Yanlış düzeltme ve şüpheli halüsinasyon koruması; sıfır güvensiz izdüşüm; AE63–AE68 |
| F2-B-G11 | Beam | Onaylı uyarlanır beam politikası ve yeteneği; eski ayarlar değişmez; AE69–AE72 |
| F2-B-G12 | Alternatif çözme | Onaylı profilde en fazla iki ardışık deneme; doğrulanmış tamamlanma, taze kira, son tarih ve köken; AE73–AE80 |
| F2-B-G13 | Final ve netleştirme | Final M01 `ASRResult` ve netleştirme devri; tek teslim; eylem yetkisi yok; AE78, AE84, AE87 |
| F2-B-G14 | İptal | M02 iptal ve bayat sonuç reddi; F1-B/F6-B uyumlu; M06 güvenli tamamlanma; AE80–AE83, AE85 |
| F2-B-G15 | Gizlilik ve sınırlar | M04 gizlilik güvenli telemetri; sınırlı bellek/iş ve temizlik; AE23, AE56, AE85–AE86 |
| F2-B-G16 | Entegrasyon | M05/M06 ve M07 korumalı gerçek F2-A → F2-B → F3-A yolu; yalnız sahte modüller değil; AE84, AE87 |
| F2-B-G17 | Test kanıtı | AE01–AE88 gerçek hedef koda karşı M08 kanıtıyla; tüm zorunlu iddialar geçmiş |
| F2-B-G18 | Regresyon | Gerçek M00 özellik regresyonları, etkilenen W2/çekirdek testleri, kaynak bütünlüğü, geri dönüş provası; AE88 |
| F2-B-G19 | Devir | Bağımsız inceleme, benchmark planı ve aşağı akış devri; hazırlık ile etkinleştirme ayrımı açık |

## 9. Kanıt

`evidence/F2-B/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F2_B_INVENTORY.json`, `HOTWORD_POLICY.md`, `PROTECTED_SPAN_POLICY.md`, `CANDIDATE_RANKING.md`, `CONFIDENCE_EVIDENCE_SCHEMA.json`, `ALTERNATE_DECODE_POLICY.md`, `BENCHMARK_PROTOCOL.md` (kalibrasyon/test bölünmesi, metrikler: WER, CER, terim doğruluğu, yanlış otomatik düzeltme oranı — hepsi G4'te ölçülür), `TEST_MATRIX.json`.

## 10. Geri dönüş

M03 profilleri (`f2.context_hotwords`, `f2.adaptive_beam`, `f2.alternate_decode`) kapatılır: F2-A final yolu ve eski hotword listesi tek aktif. Ham metin hiç değişmediği için veri geri dönüşü gerekmez. Kod `git revert`.

## 11. Devir

- **F3-B:** belirsiz adaylar ve `requires_confirmation` netleştirme sorularına girdi; katman 0–4 yönlendirmesi adayları onaylı bilgiye dönüştürmez.
- **F4-B:** aynı M05 revizyonu ve korumalı öbek politikası telaffuz tarafında.
- **F2-C:** kısmi/kararlı revizyonlar aynı koruma ve aday kurallarıyla (P5).
- **G4:** WER ≤ %10, CER ≤ %4, terim doğruluğu ≥ %95, yanlış otomatik düzeltme ≤ %1, kısa final ASR p95 ≤ 500 ms — yalnız kalibrasyondan ayrı test kümesinde.

## 12. Başlatma komutu

```
F2-B paketini uygula: docs/execution/packages/W3/F2-B-baglamsal-duzeltme.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F2-A, F3-A ve M05 kabulünü doğrula.
Bağlamsal hotword, korumalı öbek taraması, M05 aday üretimi, sıralama ve yanlış düzeltme korumasını kur;
ham metni asla değiştirme, belirsizse netleştir; alternatif çözme varsayılan kapalı, en fazla iki deneme.
AE01–AE88'i çalıştır, F2-B-G00…G19'u değerlendir, paket/F2-B dalında PR aç ve dur.
```
