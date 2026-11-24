# Kabul kapıları

Her aşamanın `acceptance.md` dosyası dört aşamalı bir kapı tanımlar. Bu belge kapıları ve gerçek koşul laboratuvarının L0–L6 seviyelerini birleştirir.

## 1. Aşama kapıları (her katman için aynı yapı)

| Kapı | Kapsam | Geçiş koşulu |
| --- | --- | --- |
| **Aşama 1** — Özellikler | Özellik sprintleri | Görevler bitti; bayraktan bağımsız düzeltmeler canlıda; mevcut testler geçiyor |
| **Aşama 2** — Arayüz | Studio sprinti | Studio gerçek backend'e bağlı; simülasyonlar etiketli |
| **Aşama 3** — Sentetik laboratuvar | Test, ablation, regresyon sprintleri | T-testleri çalıştırıldı; K tablosu ölçümle dolu; ablation yayımlandı; uçtan uca regresyon geçti |
| **Aşama 4** — Gerçek koşul | Gerçek ses ve SIP sprintleri | İnsan sesi ve telefon hattı kanıtları |

Bir katmanın `fN_pipeline_v2` bayrağı **Aşama 3** kapısı geçmeden varsayılan olarak açılmaz.

## 2. Gerçek koşul laboratuvarı (L0–L6)

| Seviye | İçerik | Ortam | İlgili görevler |
| --- | --- | --- | --- |
| L0 Offline DSP | Dosya tabanlı sentetik sesler, codec dönüşümleri | CPU | F0-T30, F6-T14, F6-T26 |
| L1 Local Loopback | Yerel gönderim/alım, süreklilik | CPU | F6-T29 |
| L2 Browser Acceptance | Gerçek FreyaTTS + sanal mikrofon (bugünkü `voice_acceptance`) | GPU | F1-T28, F6-T28 |
| L3 Synthetic PBX | Taklit telefon medya bağlantısı (sentetik AudioSocket istemcisi) | CPU | F6-T29 |
| L4 Real Asterisk | Gerçek PBX + softphone, MixMonitor kayıtları | PBX | F6-T29, F1-T29 |
| L5 SIP Trunk | Gerçek gelen/giden arama ve aktarım; AMI/ARI olayları | PBX | F6-T29, F3-T41 |
| L6 Human Acceptance | İnsan sesi, telaffuz, MOS, kimlik, görüşme kalitesi | İnsan | F0-T34, F1-T30, F2-T37, F4-T33, F5-T32, F6-T30 |

**Kural:** Bir seviye, altındaki seviyeler geçmeden kabul edilmez. PoC `VERIFICATION.md` dosyasındaki HOLD kalemleri yalnızca bu seviyelerin kanıtıyla değiştirilir.

## 3. Freya 2.0 sürüm kapısı (M7)

| Kriter | Kaynak |
| --- | --- |
| Terim doğruluğu %95 (tanıma ve seslendirme ayrı raporlanmış) | F2, F4, [shared-lexicon](../cross-cutting/shared-lexicon.md) |
| TTFA hedefleri yol bazında karşılanmış veya gerekçeli güncellenmiş | [latency-budget](../01-architecture/latency-budget.md) |
| Duyulabilir barge-in kesilmesi ≤ 200 ms p95 (kanal başına) | F1 K07, F6 K10 |
| Doğrulanmamış başarı iddiası 0, yetkisiz özel kayıt erişimi 0 | F3 |
| OOM kaynaklı düşen görüşme 0; 60 dk sızıntı testi geçti | Ortak, F0/F1/F6 |
| Leyla kimliği referans eşikleri içinde (insan ABX dahil) | F5 |
| L0–L6 kanıtlı | §2 |
