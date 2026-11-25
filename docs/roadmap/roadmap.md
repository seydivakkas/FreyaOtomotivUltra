# Yol haritası — AP01–AP13 eşlemesi

Proje açıklamasındaki geliştirme modülleri (AP01–AP12) ile aşama sprintleri ve [yürütme planı](../execution/master-plan.md) paketleri arasındaki eşleme. **AP13 Dialogue Orchestration** bu planda eklendi: F3 özgün listede ayrı bir modül değildi ama 41 görevle en büyük katmanlardan biri.

Uygulama sırası için [execution-order.md](../execution/execution-order.md) geçerlidir; bu tablo yalnızca eşlemedir. Eski AIP/Faz planı emekliye ayrıldı ([legacy-mapping.md](../execution/legacy-mapping.md)).

| Modül | Geliştirme | Öncelik | Aşama sprintleri (teknik ayrıntı) | Paketler |
| --- | --- | --- | --- | --- |
| AP01 | Adaptive Audio Enhancement | Çok yüksek | F0-S02 … F0-S04, F0-S06 | F0-A, F0-B |
| AP02 | Echo Cancellation | Yüksek | F0-S05 | F0-B |
| AP03 | Semantic Turn Detection | Çok yüksek | F1-S02 … F1-S07 | H01, F1-A, F2-A, F1-B, F2-C, F1-C |
| AP04 | Streaming ASR | Çok yüksek | F2-S12 … F2-S14 | F1-A, F2-A, F2-C, F1-C |
| AP05 | Automotive Entity Resolver | Çok yüksek | F2-S04 … F2-S11 | M05, F2-A, F2-B, F2-C |
| AP06 | Turkish Linguistic Frontend | Çok yüksek | F4-S02 … F4-S18 | M05, F4-A, F4-B, F4-C |
| AP07 | Prosody & Audio Stitching | Yüksek | F4-S15 … F4-S16, F4-S19, F5-S19 … F5-S20, F6-S03 … F6-S06 | F4-A, F5-A, F6-A, F4-B, F4-C, F6-C |
| AP08 | GPU Resource Scheduler | Çok yüksek | F5-S11, F2-S14, F3-S20 | M06, F2-A, F5-A |
| AP09 | Telephony Media Reliability | Yüksek | F1-S08 … F1-S09, F6-S13 … F6-S22 | F5-A, F6-A, F1-B, F6-B, F5-B, F1-C, F6-C, F6-D |
| AP10 | Audio Quality Evaluation | Çok yüksek | F0-S07, F2-S16, F5-S15, F5-S17 … F5-S18, ortak gözlem | H01, M04, F0-A, F5-A, F4-B, F5-B, F5-C, G4, G5 |
| AP11 | Acoustic Test Laboratory | Yüksek | F0-S09, F1-S12, F2-S16 … F2-S17, F3-S22, F4-S21 … F4-S22, F5-S22 … F5-S23, F6-S24 … F6-S25 | M08, F1-A, F4-B, G4 |
| AP12 | Human Voice & SIP Acceptance | Son aşama | F0-S11, F1-S14, F2-S19, F3-S25, F4-S23, F5-S25, F6-S27 … F6-S28 | G5 |
| **AP13** | **Dialogue Orchestration** (yeni) | Çok yüksek | F3-S01 … F3-S21, F3-S23 … F3-S24 | H01, M07, F3-A, F3-B, F3-C |

## Beş ana geliştirme alanı ile ilişki

| Alan | Katmanlar | Dalgalar |
| --- | --- | --- |
| 01 — Audio Signal Processing | F0, F6 DSP | W2 (F0-A, F6-A), W4 (F0-B, F6-C) |
| 02 — Speech Intelligence | F1, F2 | W2, W3 (F1-B, F2-B), W4 (F1-C, F2-C) |
| 03 — Turkish Linguistic Intelligence | F4, ortak sözlük | W1 (M05), W2 (F4-A), W3 (F4-B), W4 (F4-C) |
| 04 — Neural Speech Rendering | F5, F6 birleştirme | W2 (F5-A), W3 (F5-B), W4 (F5-C, F6-C), W5 (F5-D) |
| 05 — Real-Time Media Engine | Ortak GPU, F6 aktarım, oturum ve kesinti | W1 (M02, M06), W2 (F6-A), W3 (F1-B, F6-B), W5 (F6-D) |
| (eklendi) Dialogue Intelligence | F3 | W0 (H01), W1 (M07), W2 (F3-A), W3 (F3-B), W4 (F3-C) |

## Aşama başına iş hacmi

| Aşama | Eski görev | Sprint | Bayraktan bağımsız düzeltme (H01) |
| --- | --- | --- | --- |
| F0 | 34 | 11 | (öneri) F0-T14 |
| F1 | 30 | 14 | F1-T03, F1-T05 |
| F2 | 37 | 19 | — |
| F3 | 41 | 25 | F3-T03, F3-T05 |
| F4 | 33 | 23 | F4-T04, F4-T05 |
| F5 | 33 | 26 | F5-T11, F5-T17 (iptal filtresi) |
| F6 | 30 | 28 | F6-T03 |
| Ortak | 4 (CC-T01…T04) + aşama görevlerinde sahiplenilen ortak bileşenler | — | — |
| **Toplam** | **242** | **146** | |
