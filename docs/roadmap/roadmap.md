# Yol haritası — AP01–AP13 eşlemesi

Proje açıklamasındaki geliştirme modülleri (AP01–AP12) ile bu planın aşama sprintleri ve uygulama paketleri arasındaki eşleme. **AP13 Dialogue Orchestration** bu planda eklendi: F3 özgün listede ayrı bir modül değildi ama 41 görevle en büyük katmanlardan biri.

Uygulama sırası için [master-plan.md](master-plan.md) geçerlidir; bu tablo yalnızca eşlemedir.

| Modül | Geliştirme | Öncelik | Aşama sprintleri | Uygulama paketleri | Faz |
| --- | --- | --- | --- | --- | --- |
| AP01 | Adaptive Audio Enhancement | Çok yüksek | F0-S02 … F0-S04, F0-S06 | AIP-23, AIP-24 | 3 |
| AP02 | Echo Cancellation | Yüksek | F0-S05 | AIP-31 | 3 |
| AP03 | Semantic Turn Detection | Çok yüksek | F1-S02 … F1-S07 | AIP-04, AIP-25, AIP-26 | 0, 3 |
| AP04 | Streaming ASR | Çok yüksek | F2-S12 … F2-S14 | AIP-26 | 3 |
| AP05 | Automotive Entity Resolver | Çok yüksek | F2-S04 … F2-S11 | AIP-12 … AIP-16 | 2 |
| AP06 | Turkish Linguistic Frontend | Çok yüksek | F4-S02 … F4-S18 | AIP-12, AIP-17 … AIP-19 | 2 |
| AP07 | Prosody & Audio Stitching | Yüksek | F4-S15 … F4-S16, F4-S19, F5-S19 … F5-S20, F6-S03 … F6-S06 | AIP-19, AIP-20, AIP-28 | 2, 3 |
| AP08 | GPU Resource Scheduler | Çok yüksek | F5-S11, F2-S14, F3-S20 | AIP-06, AIP-11 | 0, 1 |
| AP09 | Telephony Media Reliability | Yüksek | F1-S08 … F1-S09, F6-S13 … F6-S22 | AIP-28 … AIP-30, AIP-32 | 3 |
| AP10 | Audio Quality Evaluation | Çok yüksek | F0-S07, F2-S16, F5-S15, F5-S17 … F5-S18, ortak gözlem | AIP-10, AIP-21, AIP-27, AIP-33, AIP-42, AIP-43 | 1–6 |
| AP11 | Acoustic Test Laboratory | Yüksek | F0-S09, F1-S12, F2-S16 … F2-S17, F3-S22, F4-S21 … F4-S22, F5-S22 … F5-S23, F6-S24 … F6-S25 | AIP-22, AIP-42, AIP-43 | 3, 6 |
| AP12 | Human Voice & SIP Acceptance | Son aşama | F0-S11, F1-S14, F2-S19, F3-S25, F4-S23, F5-S25, F6-S27 … F6-S28 | AIP-45 … AIP-47 | 7 |
| **AP13** | **Dialogue Orchestration** (yeni) | Çok yüksek | F3-S01 … F3-S21, F3-S23 … F3-S24 | AIP-03, AIP-34 … AIP-39 | 0, 4 |

## Beş ana geliştirme alanı ile ilişki

| Alan | Katmanlar | Fazlar |
| --- | --- | --- |
| 01 — Audio Signal Processing | F0, F6 DSP | 3 |
| 02 — Speech Intelligence | F1, F2 | 2, 3 |
| 03 — Turkish Linguistic Intelligence | F4, ortak sözlük | 2 |
| 04 — Neural Speech Rendering | F5, F6 birleştirme | 2, 3 |
| 05 — Real-Time Media Engine | Ortak GPU, F6 transport, oturum ve kesinti | 1, 3 |
| (eklendi) Dialogue Intelligence | F3 | 0, 4 |

## Aşama başına iş hacmi

| Aşama | Görev | Sprint | Bayraktan bağımsız düzeltme |
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
