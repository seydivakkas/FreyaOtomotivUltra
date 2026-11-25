# W2_GATE — F0–F6 yapısal uçtan uca kapı

> Yedi A paketi (F0-A…F6-A) ayrı ayrı kabul edildikten sonra, gerçek F0→F6 zincirinin web ve telefon yollarında **sahte model sağlayıcılarıyla** uçtan uca doğru çalıştığını kanıtlar. Bu yapısal bir kabuldür; gerçek model, GPU, akustik kalite veya SIP kabulü değildir. Geçmeden hiçbir W3 paketi başlatılmaz.

| Alan | Değer |
| --- | --- |
| Kimlik | W2_GATE |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, F0-A, F1-A, F2-A, F3-A, F4-A, F5-A, F6-A |
| Sonraki | F1-B, F6-B, F2-B, F3-B, F4-B, F5-B, F0-B, F2-C, F1-C, F3-C, F4-C, F5-C, F6-C, F6-D, F5-D |
| Bayrak | Testte tüm `f0…f6_pipeline_v2` = `strict`; üretim varsayılanları değişmez |
| Ortam | CPU (sahte Whisper/Qwen/FreyaTTS, bellek içi AudioSocket, geçici DB) |
| Eski görevler | — |
| Kaynak | Bundle `W2/Freya_2_0_F6_A_Agent_Implementation_Package.md` (H bölümü); Orchestrator §E |
| Durum | NOT_RUN |

## 1. Amaç

Her A paketi kendi sınırında sahte komşularla test edildi. W2_GATE, gerçek F0…F6 uygulamalarını gerçek M01–M08 çekirdeğiyle birleştirir ve yalnızca model sağlayıcılarını ve dış aktarımı sahteyle değiştirerek tam zinciri sınar: giriş → VAD → ASR → diyalog/güvenlik → normalizasyon → sentez → render → tel çıktısı.

## 2. Başlamadan önce

- [ ] CORE_GATE ve yedi A paketinin kabul kanıtı geçerli; bayat/eksik kanıt engeller.
- [ ] Entegre kaynak/fikstür anlık görüntüsü dondurulmuş; aşama başına tek sahip; dış etki yok.
- [ ] Gözden geçiren belirlenmiş ([master-plan §Yönetişim](../../master-plan.md#yönetişim)).

## 3. Kapsam

**Yapılacak:** Çekirdek ve katman test aileleri ile M00 kontrollerinin yeniden çalıştırılması; WI01–WI24; uyum regresyon matrisi; M04 iz korelasyonu ve M08 kanıt kökeni; bağımsız inceleme.

**Yapılmayacak:** Gerçek model/GPU/PBX; ölçülmüş gecikme veya akustik metrik iddiası; kod değişikliği (başarısız vaka sahibi pakette düzeltilir, kapı baştan koşulur).

## 4. Dosyalar

```
tests/integration/w2/        # WI01–WI24 (F6-A.23'te kaydedildi)
scripts/run_gate.py          # --gate W2_GATE
evidence/W2_GATE/<run_id>/
```

## 5. Tasarım ve sözleşmeler

- Komut: `python scripts/run_gate.py --gate W2_GATE --snapshot <commit>`.
- Durum birleştirme M08 §5.5'e göre. Ertelenen kabuller (gerçek model, akustik, SIP) `NOT_RUN` kalır ve kararda açıkça yazılır.
- M06 sınıfları: final ASR P1, LLM P3, TTS ilk parça P2 / sonrakiler P4.
- Kapsam beyanı zorunlu: "yapısal, sahte sağlayıcılı; duyulan metrik yok".

## 6. Görevler

Bu kapının ayrı görevi yoktur. Yürütme sırası: önkoşul kanıtı → anlık görüntüyü dondur → çekirdek ve katman testleri → WI01–WI24 → uyum matrisi → kanıt doğrulama → bağımsız inceleme → karar.

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| WI01 | Çekirdek + tüm A paketlerinin kabulü ve güncel entegre kaynak | Tüm önkoşullar gerçek ve geçerli; bayat/eksik kanıt engeller; kaynak değişikliği yok |
| WI02 | Sentetik sinyal ve sahte model sağlayıcılarıyla gerçek F0–F6 katı web yolu | Gerçek tam zincir; son web çerçeve biçimi ve sırası doğru; gerçek oynatma iddiası yok |
| WI03 | Bellek içi AudioSocket ile gerçek F0–F6 katı telefon yolu | Gerçek giriş/DTMF ayrımı ve 8k PCM giden tel fikstürü; PBX/SIP iddiası yok |
| WI04 | Düzensiz giriş bölmeleri ve F1 aday ön kayıt işaretleri | Örnek işareti F0/F1/F2 boyunca korunur; yinelenen/dolgu konuşma sayılmaz |
| WI05 | Kısa yanlış başlangıç, sonra geçerli konuşma | Yanlış aday için ASR işi yok; geçerli tur için tek final `Utterance` |
| WI06 | Sahte Whisper tembel segmentleri ve gerçek M06 işi | P1 final çıkarım; kira gerçek sahte sağlayıcı bitişine kadar; ham metin aynen |
| WI07 | ASR NO_SPEECH/ERROR ile OK | OK dışı normal iş rotasını yürütmez; mevcut güvenli işleme; uydurma metin yok |
| WI08 | F2'den F3'e otomotiv takma adı/belirsiz aday | Ham değişmez; M05 adayı katalog veya müşteri doğrulaması değil; güvenli netleştirme |
| WI09 | Mevcut belirlenimci karşılama/basit diyalog | Gereksiz Qwen veya iş değişikliği yok; gerçek F4/F5/F6 zinciri |
| WI10 | Sahte Qwen ile mevcut LLM destekli yol | Gerçek M06 P3 isteği; öneri M07'de doğrulanır; doğrudan DB/araç atlaması yok |
| WI11 | Doğrulanmış fikstür aktörü, uygunluk ve açık onayla mevcut randevu akışı | Gerçek M07 kontrolü + yalıtılmış iş sağlayıcısı; tek kapsamlı etki; doğru MOCK makbuz yanıtı |
| WI12 | Onaydan sonra saat düzeltilir, sonra yinelenen istek | Eski onay geçersiz; yetkisiz yürütme veya yinelenen etki yok |
| WI13 | Sağlayıcı fikstür etkisini commit eder, sonra zaman aşımı / görüşme iptali | Uygunsa UNKNOWN/uzlaştırma; kör yeniden deneme veya uydurma başarı yok; bayat konuşma bağımsız engellenir |
| WI14 | Güvenilmeyen metin yetkisiz CRM veya araç eylemi ister | M07 belirlenimci red; korunan veri sızmaz; yalnız güvenli yanıt |
| WI15 | Para/model/saat korumalı öbekli F3 yanıtı | Gerçek F4 kritik değerleri korur; F4/F5 boyunca tek normalizasyon; korumalı parçalar sağlam |
| WI16 | Oturum ortasında F4 plan revizyonu/ses/profil değişimi | Sabitlenmiş model/sözlük/ses başvuruları; Leyla 9 ve onaylı deney fikstürü korunur; uyuşmazlık reddedilir |
| WI17 | F5 ham generation, gerçek M06 zamanlayıcı ve F6 render | P2/P4; gerçek yerel tamamlanma sahte sınırı; geçerli ham 48k Float32 → doğru PCM; tekrarlı DSP yok |
| WI18 | Düzensiz F5 parçaları, terminal EOS, duraklama üst verisi | Gerçek F6 durumlu yeniden örnekleme; geçerli/dolgu muhasebesi; ek terminal paket veya çift duraklama yok |
| WI19 | ASR veya TTS yerel işi sırasında iptal | M02 sonuç çiti; M06 kirayı gerçek sahte bitişe kadar tutar; bayat F3/F6 teslimi yok |
| WI20 | F6 gönderiminden önce ve sonra iptal bariyeri | Önce iptal engeller; önce gönderimde uçuşta olabilir; uzaktan geri çağırma/boşaltma iddiası yok |
| WI21 | Farklı profil ve durumlu araya girmiş iki oturum | ASR/VAD/DSP/slot/çerçeve/makbuz sızıntısı yok; sahip olunan tüm kaynaklar geri alınır |
| WI22 | Yavaş alıcı, geç saat uyanması, kuyruk/telemetri doygunluğu ve kopma | Sınırlı davranış; yakalama patlaması yok; güvenli kontrol/temizlik ve açık atma; yeni F6-B garantisi yok |
| WI23 | Gerçek mevcut API/arayüz/DB/yapılandırma/tel ve DTMF/aktarım/outbox regresyon eşlemesi | Tüm meşru taban davranışı korunur; güvenlik kusurları engellenir; sessiz varsayılan kayması veya ek etki yok |
| WI24 | M04 izi, rapor hash'leri, kapsam/köken ve kapı birleştirme | Bağlı oturum/tur/generation; gerçek test kanıtı; yalnız mock kapsamı; duyulan metrik veya sahte PASS yok; doğru hazırlık |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| WG00 | Önkoşullar | Gerçek çekirdek ve yedi A paketi kabulü, onay, doğrulanmış soy, çözülmemiş engel incelemesi |
| WG01 | Kompozisyon | Entegre kaynak/fikstür anlık görüntüsü, gerçek kompozisyon, aşama başına tek sahip, test yalıtımı, dış etki yok |
| WG02 | Test aileleri | Tüm zorunlu çekirdek/katman aileleri, M00 kontrolleri ve uygulanabilir özgün regresyonlar yeniden çalışmış ve kabul; gerçek sayı/kimlikler |
| WG03 | Tam yollar | Gerçek F0–F6 ve adaptörlerle tam web ve telefon yapısal yolları (WI02–WI03); yakalanan tel çıktısı |
| WG04 | Giriş sözleşmeleri | F0/F1/F2 giriş/örnek/durum/ham transkript/kabul sözleşmeleri (WI04–WI08) |
| WG05 | Diyalog ve güvenlik | F3 diyalog, M06 Qwen, M07 yetki/onay/makbuz ve iş korumaları (WI09–WI14) |
| WG06 | Dil ve sentez | F4/F5 korumalı değerler, tek normalizasyon, seed/revizyon, gerçek orkestrasyon ve M06 kirası (WI15–WI17) |
| WG07 | Render ve aktarım | F6 gerçek yeniden örnekleyici/PCM/çerçeve/EOS/tempo ve doğru aktarım kapsamı (WI17–WI18, WI22) |
| WG08 | İptal ve yalıtım | İptal yarışları, uçuşta ayrımı, kaynak temizliği ve iki oturum yalıtımı (WI19–WI22) |
| WG09 | Uyum | Gerçek uyum regresyon matrisi ve rota/bayrak/özellik korunumu (WI23) |
| WG10 | Test kanıtı | WI01–WI24 gerçekten geçmiş; M04 güvenli korelasyon ve M08 kanıt kökeni doğrulanmış; uydurma metrik yok (WI24) |
| WG11 | İnceleme ve devir | Bağımsız inceleme, geri dönüş başvurusu, açık W2 yapısal kararı ve yetkili sonraki dalga devri; ertelenen kabuller NOT_RUN |

## 9. Kanıt

`evidence/W2_GATE/<run_id>/`: `manifest.json` (anlık görüntü SHA'sı, paket çalıştırma kimlikleri), `test-log.txt`, `decision.json` (`w3_ready`), `SUITE_RESULTS.json`, `INTEGRATION_RESULTS.json` (WI01–WI24), `WIRE_CAPTURES/` (sentetik), `REGRESSION_MATRIX.csv`, `REVIEW.md`.

## 10. Geri dönüş

Kapı kod değiştirmez. FAIL'de başarısız vakanın sahibi olan A paketine dönülür, o pakette düzeltme yapılıp kabul yenilenir, kapı yeni anlık görüntüyle baştan çalıştırılır.

## 11. Devir

PASS ise `w3_ready: true`; W3 sırası [execution-order](../../execution-order.md)'a göre F1-B ile başlar. Devir notu: ertelenen kabuller (gerçek model, gerçek GPU, akustik, SIP), bilinen sınırlamalar, açık kararlar.

## 12. Başlatma komutu

```
W2_GATE kapısını çalıştır: docs/execution/packages/W2/W2_GATE-w2-kapisi.md.
CORE_GATE ve F0-A…F6-A kabul kanıtını doğrula, entegre commit'i dondur.
python scripts/run_gate.py --gate W2_GATE --snapshot <commit> ile çekirdek/katman testlerini ve
WI01–WI24'ü çalıştır; kod değiştirme. Sonucu WG00…WG11'e göre yaz, REVIEW.md için gözden geçirene bırak kanıtı paket/W2_GATE dalında PR olarak aç ve dur.
```
