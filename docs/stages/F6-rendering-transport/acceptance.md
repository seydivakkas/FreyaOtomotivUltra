# F6 — Kabul Kriterleri ve Testler

> **Bunlar henüz ölçülmüş sonuçlar değildir.** Bir kutu yalnızca test çalıştırılıp sonucu laboratuvar raporuna (`data/f6/lab-report-*.json`) yazıldıktan sonra işaretlenir. Telefon bandı MOS ve Leyla kimliği gerçek dinleyicilerle değerlendirilir. Ağ ve telefon operatörü kaynaklı gecikmeler ayrıca değerlendirilir.

**Ölçüm kuralları:**
- Her deney ve testte ayrı kaydedilir: ham 48 kHz, işlenmiş 48 kHz, 16 kHz web çıkışı, 8 kHz PCM, codec gidiş-dönüşü sonrası ses.
- Gecikmeler T1–T6 noktalarıyla ayrıştırılır (spec §6). F6 DSP süresi oynatma süresini içermez.
- "Sunucu gönderdi / flush etti" ile "müşteri duydu / duymayı bıraktı" ayrı metriklerdir.

---

## 1. Kalite kapısı

### 1.1 Plandaki hedefler

| # | Metrik | Önerilen hedef | Ölçüm tanımı | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K01 | DSP işlem süresi p95 | ≤ 10 ms / 20 ms eşdeğer çerçeve | T2 − T1, 20 ms ses başına normalize | T16, T47 | ☐ |
| K02 | Çerçeve süresi | 20 ms | Çerçeve başına örnek: 160 (8 kHz) / 320 (16 kHz) | T26 | ☐ |
| K03 | Çerçeve biçimi doğruluğu | %100 | PCM16 LE, boyut, AudioSocket başlığı | T23, T26 | ☐ |
| K04 | Gönderim zaman sapması p95 | ≤ 5 ms (kontrollü yerel ağ) | Planlanan − gerçekleşen gönderim | T28, T29 | ☐ |
| K05 | Geçersiz PCM örneği | 0 | NaN/Inf, aralık dışı | T02 | ☐ |
| K06 | Uygulama kaynaklı örnek kaybı | 0 | Giriş/çıkış örnek sayısı oranı (dolgu hariç) | T22, T27 | ☐ |
| K07 | Eski generation ses gönderimi | 0 | Transport'a yazılan eski generation çerçevesi | T05, T38 | ☐ |
| K08 | Çıkış tepe değeri | ≤ −1 dBFS | Kanal çıkışında | T17 | ☐ |
| K09 | Playback underrun | Kontrollü testte 0 | Sentez zamanında hazırken çerçeve boşluğu | T33 | ☐ |
| K10 | Barge-in sonrası duyulabilir kesilme p95 | ≤ 200 ms (F1 K07 ile aynı) | Web: istemci makbuzu; telefon: loopback kaydı | T37, T38 | ☐ |
| K11 | DTMF doğruluğu | Kontrollü testlerde %100 | F0 K08 ile ortak; tekilleştirme dahil | T39 | ☐ |
| K12 | Codec sonrası anlaşılabilirlik | Referansa göre ölçülür | G.711 gidiş-dönüşünde Whisper geri tanıma ve terim doğruluğu farkı | T24, T25 | ☐ |
| K13 | Telefon bandı MOS | İnsan değerlendirmesiyle belirlenir | Kör test | AŞAMA 4 | ☐ |
| K14 | Leyla ses kimliği | Kanal bazlı referansla doğrulanır (F5 eşikleri) | Speaker similarity 16 kHz ve 8 kHz | T10, AŞAMA 4 | ☐ |
| K15 | Ek GPU tüketimi | 0 MB | — | T47 | ☐ |

### 1.2 PoC incelemesine dayanan ek kriterler (öneri)

| # | Metrik | Önerilen hedef | Gerekçe | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K16 | Parça sınırı süreksizliği | Parçalı ve tümleşik işleme arasındaki fark ≤ −60 dB (sınır ±5 ms) | Durumsuz filtreler sınırda genliğin ~%29'u kadar sapma üretiyor (spec §3.2 R2) | T22 | ☐ |
| K17 | Limiter eşik altı bozulma | Eşik altındaki sinyalde kazanç değişimi ≤ 0,1 dB ve THD ≤ −60 dB | `tanh` tüm seviyelerde +1,2 dB kazanç ve −6 dBFS'de %2,5 THD ekliyor (R3) | T17 | ☐ |
| K18 | Ağ yazması bloklanma süresi | ≤ zaman aşımı (başlangıç 60 ms) | `drain()` zaman aşımsız (R6) | T32 | ☐ |
| K19 | Pacer uygulaması sayısı | 1 | Üç ayrı uygulama (R4) | T28 | ☐ |
| K20 | Web ve telefon DSP zinciri | Tek pipeline, iki profil | Web'de EQ/limiter yok (R1) | T13–T17 | ☐ |
| K21 | Duraklama doğruluğu | Uygulanan sessizlik = plan ± 10 ms; F5 kaynaklı ek sessizlik 0 | F5 ve F6 çakışması (R12) | T11, T12 | ☐ |
| K22 | Barge-in sonrası duyulan eski ses üst sınırı | ≤ önden gönderim sınırı (kanal başına raporlanır) | AudioSocket'te gönderilen ses geri alınamaz; chan_websocket kuyruğu 20 s tutabilir | T38, T44 | ☐ |
| K23 | Parçalar arası loudness farkı | Ardışık parçalar arasında ≤ 2 dB (öneri) | Seviye tutarlılığı | T16 | ☐ |

## 2. Test senaryoları (T01–T48)

**F6 test kontrol listesi: 0 / 48**

### Doğrulama ve birleştirme

| Test | Geçme koşulu |
| --- | --- |
| ☐ T01 — 48 kHz Float32 ses doğrulaması | Yanlış örnekleme hızı/tür reddedilir |
| ☐ T02 — Geçersiz NaN/Inf örneklerinin reddi | K05 |
| ☐ T03 — AudioChunk sıralaması | Yanlış sırada gelen parça beklenen gelene kadar tutulur; zaman aşımında eksik parça olayı |
| ☐ T04 — Yanlış session ID izolasyonu | Başka oturumun parçası reddedilir |
| ☐ T05 — Eski generation ID reddi | K07 |
| ☐ T06 — Cümlecik birleştirme | Plan sırası ve duraklamalar doğru |
| ☐ T07 — Crossfade sınır sürekliliği | Duraklamasız sınırda tık yok (sınır çevresinde spektral süreksizlik ölçümü) |
| ☐ T08 — İlk ve son fonem korunumu | Fade/crossfade sessiz kısımda; Whisper geri tanımada ilk/son sözcük korunur |

### Zaman ölçekleme ve duraklama

| Test | Geçme koşulu |
| --- | --- |
| ☐ T09 — WSOLA hız dönüşümü | 0,94–1,06× aralığında süre hedefe ±%1 |
| ☐ T10 — WSOLA perde sapması | Median F0 sapması ve speaker similarity F5 eşikleri içinde |
| ☐ T11 — Prozodik duraklama doğruluğu | K21 |
| ☐ T12 — Duraklamanın çift uygulanmaması | K21 (F5 çıkışında sondaki sessizlik yok) |

### DSP

| Test | Geçme koşulu |
| --- | --- |
| ☐ T13 — High-Pass Filter | Kanal profiline uygun kesim; durumlu |
| ☐ T14 — Presence Equalizer | Ölçülen kazanç profile ±0,5 dB |
| ☐ T15 — Dynamic De-Esser | Web'de sibilans azalır, Whisper geri tanıma kötüleşmez; telefon kararı ölçüme dayalı |
| ☐ T16 — Loudness Controller | K23; K01 |
| ☐ T17 — Peak Limiter ve clipping | K08; K17 |
| ☐ T18 — Comfort Noise seviyesi | Kapalıyken 0; açıkken −58 dBFS ± 2 dB ve oynatma referansında |

### Yeniden örnekleme ve kodlama

| Test | Geçme koşulu |
| --- | --- |
| ☐ T19 — 48 → 16 kHz resampling | 1 kHz ton genliği ±0,1 dB |
| ☐ T20 — 48 → 8 kHz resampling | Aynı |
| ☐ T21 — Anti-aliasing frekans taraması | Yeni Nyquist üstü bileşenler ≥ 60 dB bastırılır |
| ☐ T22 — Parçalar arası örnek sürekliliği | K06; K16 |
| ☐ T23 — PCM16 little-endian formatı | K03 |
| ☐ T24 — G.711 A-law codec döngüsü | K12 raporlanır |
| ☐ T25 — G.711 μ-law codec döngüsü | K12 raporlanır |

### Çerçeve ve zamanlama

| Test | Geçme koşulu |
| --- | --- |
| ☐ T26 — 20 ms frame sözleşmesi | K02; K03; AudioSocket paketi 323 bayt |
| ☐ T27 — Son frame padding kontrolü | Dolgu miktarı kaydedilir; K06 |
| ☐ T28 — Precision Pacing | K19; deadline re-clamp korunur (paket yağmuru yok) |
| ☐ T29 — Gönderim zaman sapması | K04 |
| ☐ T30 — TCP bölünmüş ve birleşmiş paketler | AudioSocket okuyucu parçalı/birleşik paketleri doğru ayrıştırır |

### Kuyruk, backpressure ve barge-in

| Test | Geçme koşulu |
| --- | --- |
| ☐ T31 — Ağ backpressure | Yavaş tüketicide kuyruk sınırlı; üretici bekler; eski çerçeve atılmaz |
| ☐ T32 — Yazma zaman aşımı | K18; kontrollü kapanış |
| ☐ T33 — Playback underrun | K09 |
| ☐ T34 — Playback queue taşması | Backpressure devreye girer; olay kaydı |
| ☐ T35 — Soft pause | Gönderim durur; konum kaydedilir |
| ☐ T36 — Rollback ve resume | Konumdan veya (1 s'den uzun duraklamada) cümlecik başından devam |
| ☐ T37 — Hard flush | Kuyruk temizlenir; transport flush komutu (chan_websocket) veya gönderim durur (AudioSocket); K10 |
| ☐ T38 — Barge-in sırasında eski ses reddi | K07; K22 |

### Protokol ve hata

| Test | Geçme koşulu |
| --- | --- |
| ☐ T39 — DTMF protokolü ve olay tekilleştirme | K11 |
| ☐ T40 — Geçersiz AudioSocket UUID | Bağlantı reddedilir (mevcut) |
| ☐ T41 — Bağlantı kopması ve kapanış | Görüşme güvenli kapanır; F3 bilgilendirilir; kaynaklar serbest |
| ☐ T42 — Simüle SIP trunk kesintisi | Yeni çağrı güvenli reddedilir/yönlendirilir |
| ☐ T43 — AMI mock / gerçek mod ayrımı | Mock modda gerçek aktarım iddiası yok; Studio mod gösterir |
| ☐ T44 — Chan WebSocket kuyruk kontrolü | XOFF'ta gönderim durur; FLUSH_MEDIA ve MARK_MEDIA çalışır; mesaj biçimi Asterisk yapılandırmasıyla uyumlu |
| ☐ T45 — Oturumlar arası medya izolasyonu | Bir oturumun çerçevesi başka oturuma gitmez |

### Sözleşme ve süreklilik

| Test | Geçme koşulu |
| --- | --- |
| ☐ T46 — F5–F6 veri sözleşmesi | `AudioChunk` girişi, `RenderedFrame` ve `PlaybackEvent` şemaya uyar |
| ☐ T47 — Uzun süreli bellek ve tampon testi | 60 dk, 4 oturum: RSS artışı ≤ 20 MB; K01; K15 |
| ☐ T48 — F0–F6 sentetik görüşme regresyonu | Uçtan uca senaryolar geçer; TTFA ve barge-in ölçümleri raporlanır |

## 3. Aşama kapıları

| Aşama | Kapsam | Geçiş koşulu |
| --- | --- | --- |
| **Aşama 1** — Özelliklerin tamamlanması | F6-S01 … F6-S22 | Görevler bitti; F6-T03 canlıda; mevcut testler geçiyor |
| **Aşama 2** — F6 arayüzü | F6-S23 | Studio gerçek backend'e bağlı; dürüstlük kuralı |
| **Aşama 3** — Sentetik test laboratuvarı | F6-S24 … F6-S26 | T01–T48 çalıştırıldı; K01–K23 dolduruldu; ablation yayımlandı |
| **Aşama 4** — Gerçek telefon hattı kabulü | F6-S27, F6-S28 | Aşağıdaki tablo L0–L6 için kanıtlarla dolu |

### Aşama 4 — Asterisk ve SIP kabul laboratuvarı (ölçüldükçe doldurulur)

| Seviye | Kapsam | Kanıt | Sonuç |
| --- | --- | --- | --- |
| L0 Offline DSP | Dosya tabanlı sentetik ses ve codec dönüşümleri | Lab raporu | ☐ |
| L1 Local Loopback | Yerel gönderim/alım, süreklilik | Kayıt + ölçüm | ☐ |
| L2 Browser Acceptance | Gerçek FreyaTTS + sanal mikrofon | İstemci makbuzları | ☐ |
| L3 Synthetic PBX | Taklit telefon medya bağlantıları | Sentetik AudioSocket raporu | ☐ |
| L4 Real Asterisk | Gerçek PBX + softphone | MixMonitor kayıtları | ☐ |
| L5 SIP Trunk | Gerçek gelen/giden arama ve aktarım | Çağrı kayıtları, AMI/ARI olayları | ☐ |
| L6 Human Acceptance | İnsan sesi, telaffuz, görüşme kalitesi | MOS, kimlik, anlaşılabilirlik | ☐ |
