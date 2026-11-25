# Uçtan uca gecikme bütçesi

## 1. Tanımlar

| Metrik | Başlangıç | Bitiş |
| --- | --- | --- |
| **TTFA** (ilk ses) | Müşterinin konuşmasının **etiketli** bitişi | Freya'nın ilk sesinin müşteri tarafında başlaması (F6 T5) |
| **İçerik TTFA** | Aynı | Yanıtın bilgi taşıyan ilk parçasının başlaması (dolgu/onay cümlesi hariç) |
| **Barge-in kontrol sinyali** | Müşteri sesinin ilk örneğinin adaptöre ulaşması | Durdurma komutunun transport'a yazılması (F1 K06) |
| **Duyulabilir kesilme** | Aynı | Freya sesinin müşteri tarafında durması (F1 K07, F6 K10) |

Tüm gecikmeler p50 / p95 / p99 ve örnek sayısıyla raporlanır. Kanal (web / telefon) ve yol (önbellek / FAST / STANDARD / KNOWLEDGE / COMPLEX) ayrı raporlanır.

**Bugün:** Hedef 1,2 s. Tek çalıştırma örnekleri: karşılama 15 ms, ad turu 1,4 s, araç turu 3,2 s, onay turu 3,2 s, LLM turu 6 s ([current-state](../00-overview/current-state.md)).

## 2. Aşama hedeflerinin toplamı çatışıyor

Aşama belgelerindeki p95 hedefleri art arda eklendiğinde 1,2 s hedefi aşılır:

| Adım | Aşama hedefi (p95) | Kaynak |
| --- | --- | --- |
| Endpoint (kısa yanıt profili) | ≤ 500 ms | F1 K05 |
| Final STT | ≤ 500 ms | F2 K10 |
| F3 LLM dışı tur | ≤ 300 ms | F3 K15 |
| F4 | ≤ 50 ms | F4 K14 |
| F5 sıcak, kısa cümlecik | ≤ 500 ms | F5 K01 |
| F6 DSP + aktarım + oynatma başlangıcı | ≈ 50–100 ms (ölçülecek) | F6 §6 |
| **Toplam** | **≈ 1,9–2,0 s** | |

p95 değerleri doğrudan toplanmaz, ama bu tablo bütçenin **aşamalar arası örtüşme** olmadan karşılanamayacağını gösterir. Bu yüzden bütçe aşağıdaki gibi yola göre dağıtılır ve aşama hedefleri uçtan uca ölçümle birlikte değerlendirilir.

## 3. Yol bazında önerilen bütçe

> **Öneri** — ölçümle doğrulanacak. Değerler p95 hedefidir.

### 3.1 FAST yolu (evet/hayır, seçenek numarası) — hedef TTFA ≤ 1,2 s

| Adım | Bütçe | Nasıl |
| --- | --- | --- |
| F0 + F1 algoritmik gecikme ve blok hizalama | 60 ms | F0 20/32 ms çerçeve (F0-T22) |
| Endpoint sessizliği | 250–350 ms | `yes_no` / `option_number` profili (F1 §5.6) |
| F1.07 karar | 20 ms | Kural tabanı |
| STT (FINALIZE sonrası kalan) | ≤ 150 ms | **Spekülatif STT** endpoint adayında başlar; ses değişmediyse sonucu kullanılır (F1 §5.7, F2-T26) |
| F3 | ≤ 100 ms | Katman 0–1 kural yolu (F3 K13) |
| F4 | ≤ 20 ms | Kısa metin |
| F5 | ≤ 50 ms (önbellek) / ≤ 500 ms (ıska) | Onay cümleleri L0/L1 önbellekte; ilk cümlecik kısa |
| F6 + aktarım | ≤ 80 ms | DSP ≤ 10 ms, ilk çerçeve, ağ, tarayıcı 25 ms önden zamanlama |
| **Toplam** | **≈ 0,65–1,2 s** | Önbellek ıskasında sınırda |

### 3.2 STANDARD yolu (ad, araç marka/model, plaka) — hedef TTFA ≤ 1,2 s, içerik TTFA ≤ 2,0 s

Endpoint profili tek başına 400–1 000 ms sürer. 1,2 s ancak şu yollarla karşılanır:
- **Semantic FINALIZE:** F1.07 cümlenin tamamlandığını (ör. "2020 model Nissan Qashqai") alt sınırda (320 ms) onaylar.
- **Önbellekli kısa onay:** F3 `kind = filler` ve `cacheable` bir segmentle başlar ("Hemen bakıyorum."); içerik ikinci segmentte gelir. Bu kullanım F3 kalite ölçümünde izlenir; gereksiz dolgu cümlesi doğallığı bozar.

| Adım | Bütçe |
| --- | --- |
| Endpoint (semantic FINALIZE ile) | 320–500 ms |
| STT + entity resolver | ≤ 300 ms (spekülatif STT ile kısalır) |
| F3 | ≤ 300 ms |
| F4 + F5 (ilk cümlecik) + F6 | ≤ 600 ms |
| **İçerik TTFA** | **≈ 1,5–1,7 s** |

### 3.3 KNOWLEDGE / COMPLEX yolu (LLM) — hedef TTFA ≤ 1,2 s (onay cümlesiyle), içerik TTFA ≤ 3 s

- İlk ses önbellekli onay cümlesidir.
- LLM yanıtı cümle bazında doğrulanarak akıtılır (F3 KNOWLEDGE yolu); ilk doğrulanmış cümle F4/F5'e hemen gider.
- F3 K22: içerik TTFA önerisi ≤ 3 s (bugün ≈ 6 s).

## 4. Barge-in bütçesi

| Adım | Bütçe | Not |
| --- | --- | --- |
| Giriş tamponu + F0 gecikmesi | 32 + ≈ 28 ms | F0-T22; NS penceresi (F1 §8 seçenek A) |
| En kısa konuşma başlangıcı | 64 ms | Plan parametresi |
| Karar ve komut | ≈ 5 ms | |
| **Kontrol sinyali** | **≈ 129 ms** | Hedef ≤ 100 ms ile çatışıyor → **ADR-F1-02** |
| Önden gönderilmiş ses | ≤ önden gönderim sınırı | F6 §5.11: AudioSocket'te gönderilen ses geri alınamaz; sınır 3 çerçeve (60 ms) önerilir |
| Tarayıcı / PBX tamponu | Web ≈ 25 ms; telefon ölçülecek | chan_websocket'te `FLUSH_MEDIA` |
| **Duyulabilir kesilme** | **≤ 200 ms** hedef | Yalnızca önden gönderim sınırı küçük tutulursa |

## 5. Ölçüm altyapısı

- Ortak gecikme izleyicisi `EventEnvelope` olaylarından aşama başına süre hesaplar ([observability](../cross-cutting/observability.md)).
- F6 T1–T6 noktaları ve istemci/PBX makbuzları (F6 §6).
- Sentetik görüşme motoru etiketli konuşma sonu zamanını bilir; TTFA'nın başlangıcı bu etiketten alınır.
- Telefon kanalında T5 için loopback düzeneği (MixMonitor veya softphone kaydı).
- Uçtan uca hedefler sentetik olarak [G4](../execution/stages/G4-sentetik-kabul.md)'te, gerçek uçta [G5](../execution/stages/G5-gercek-insan-sip.md)'te ölçülür.
