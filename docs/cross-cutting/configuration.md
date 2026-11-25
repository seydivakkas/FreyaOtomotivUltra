# Yapılandırma ve bayraklar

**Kod:** `backend/config.py` (pydantic-settings; mevcut). Statik profiller `config/` altında JSON.

## 1. Bayraklar

| Bayrak | Varsayılan | Açılma koşulu |
| --- | --- | --- |
| `f0_pipeline_v2` | `False` | F0-S10 regresyonu |
| `f1_pipeline_v2` | `False` | F1-S13 regresyonu |
| `f2_pipeline_v2` | `False` | F2-S18 regresyonu |
| `f3_pipeline_v2` | `False` (öneri; F3 Shadow → Guarded geçişi F3 spec §6) | F3-S23/S24 |
| `f4_pipeline_v2` | `False` | F4-S22 |
| `f5_pipeline_v2` | `False` | F5-S24 |
| `f6_pipeline_v2` | `False` | F6-S26 |

**Kurallar:**
- Bayrak kapalıyken PoC davranışı değişmez (bayraktan bağımsız düzeltmeler hariç — [H01 paketi](../execution/packages/W0/H01-guvenli-zemin.md)).
- Bayraklar birbirinden bağımsız açılabilmelidir. Bir v2 katman legacy komşusuyla sözleşme adaptörü üzerinden konuşur ([pipeline-v2](../01-architecture/pipeline-v2.md) §4).
- Etkin bayrak kümesi her telemetri olayına ve her laboratuvar raporuna yazılır.
- Bayrak varsayılanı değiştiğinde `VERIFICATION.md` ve ilgili `acceptance.md` güncellenir.

## 2. Profiller (`config/`)

| Dosya | İçerik | Aşama |
| --- | --- | --- |
| `config/linguistics/automotive_lexicon.json` | Ortak sözlük | F2, F4 |
| `config/linguistics/phonology_rules.json`, `prosody_profiles.json`, `stress_exceptions.json` | Dilbilim | F4 |
| `config/voices/leyla.json`, `approved_models.json`, `solver_profiles.json`, `duration_profiles.json`, `cache_policy.json`, `identity_baseline.json` | Ses ve sentez | F5 |
| `config/media/rendering_profiles.json` | Web / telefon DSP profilleri | F6 |
| `config/resources/gpu_budget.json` | VRAM bütçesi, öncelikler | Ortak |
| F0 ortam profilleri P0–P6 | `backend/audio_frontend/profiles.py` | F0 |
| F1 konuşma profilleri | `backend/voice_activity/profiles.py` | F1 |

Ölçüm gerektiren değerler (eşikler, bütçeler) yapılandırmada `null` ile başlar ve kalibrasyon sonucuyla doldurulur; dosyada değerin kaynağı (rapor yolu) yorum veya `source` alanı olarak tutulur.

## 3. Ayar değişikliği kuralları

- Eşikler yalnızca **kalibrasyon kümesinde** ayarlanır; test kümesi ayar için kullanılmaz.
- Leyla'nın sesini etkileyebilecek her ayar (seed, ODE adımı, hız, EQ, limiter) F5 referans kümesine karşı ölçülmeden değiştirilmez.
- Studio'dan yapılan canlı ayar değişikliği oturuma özeldir ve denetim izine yazılır; kalıcı hale getirmek PR gerektirir.
- Mevcut ayar adları (`car_denoiser_*`, `stt_catalog_hotwords`, `ollama_gpu_layers` vb.) geçiş süresince takma ad olarak korunur (F0 spec §8 eşlemesi).
