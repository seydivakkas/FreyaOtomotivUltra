# Ortak otomotiv sözlüğü (F2 ↔ F4)

Projenin en büyük sorunu otomotiv terim doğruluğudur (%48,04, hedef %95). Aynı terim iki yönde işlenir:
- **Tanıma (F2):** "Nisan kaş kay" → Nissan Qashqai
- **Seslendirme (F4):** Nissan Qashqai → "Nissan Kaşkay"

İki yön aynı kaynaktan beslenmezse biri düzelirken diğeri bozulur. Bu belge tek sözlüğün sahipliğini ve iş akışını tanımlar.

## 1. PoC'taki durum

| Kaynak | Kullanan | Not |
| --- | --- | --- |
| `config/freyatts_automotive_lexicon.json` (üç kopya; biri repo kökünde) | F2 hotword planı, demo | Zengin içerik (151 marka, `full_models`) ama canlı TTS yolunda yok (F4 L4) |
| `config/lexicon.json` | Canlı `text.normalize` | **Tek kayıt** (Qashqai) |
| `normalizer_rules.py` sabit marka kuralları | Canlı normalizer | Kod içinde |
| `config/automotive_foreign_lexicon.json`, `lexicon_categories.json` | Kısmen | |
| `FreyaTTS_Otomotiv_Turkce_Telaffuz_Sozlugu_2026.xlsx` | Kaynak belge | Uzman telaffuz sözlüğü |
| `automotive_voice/nlp/lexicon.AutomotiveLexicon` + `operator/review_store.PronunciationReviewStore` + `contracts/approved_lexicon_rule.schema.json` | Milestone uçları | **Kanıt tabanlı onay:** onay için kayıtlı ses, insan transkripsiyonu ve lisans kapsamı gerekiyor |

## 2. Hedef

**Tek dosya:** `config/linguistics/automotive_lexicon.json` — şema F4 spec §5.4 (Lexicon 2.0).

| Alan grubu | Sahibi | Kullanan |
| --- | --- | --- |
| `canonical`, `category`, `brand`, `lexicon_version` | Ortak | F2, F3, F4 |
| `asr_variants`, `ambiguous_with_common_word` | F2 | F2 hotword, mapper, resolver |
| `synth_text`, `suffix_base`, `phonetic_guide`, `stress` | F4 | F4 normalizer, morfoloji, G2P |
| `review_status`, `pronunciation_source` | Sözlük onay yetkilisi | Studio, F4 kalite kapısı |
| `acoustic_status` | Laboratuvar | F4-T33 (FreyaTTS gerçekten doğru okuyor mu) |
| `recognition_status` (öneri — yeni alan) | Laboratuvar | F2 benchmark (Whisper bu terimi doğru tanıyor mu) |

**Onay akışı:** `review_status = approved` yalnızca onay yetkilisi tarafından ve mevcut `PronunciationReviewStore` kanıt kuralıyla (kayıt + transkripsiyon + lisans kapsamı) verilir. Onay kaydı `approved_lexicon_rule` şemasındaki `reviewer`, `evidence`, `source_ref` alanlarını taşır. Onay yetkilisinin kim olduğu kullanıcı kararıdır ([ADR dizini](../01-architecture/adr/README.md), soru 5).

**Sürümleme:** `lexicon_version` değiştiğinde:
- F4 `plan_id` değişir → F5 önbelleği kendiliğinden geçersizleşir (F4 T36).
- F2 hotword önbelleği ve katalog dizini yeniden kurulur (F2-T09).
- Terim doğruluğu ölçümü yeni sürümle tekrarlanır.

## 3. Ölçüm: hatanın kaynağını ayırmak

Bugünkü %48,04 TTS → STT döngüsünün birleşik sonucudur. Sözlük ölçümü üç ayrı sayı üretir:

| Ölçüm | Nasıl | Sorumlu |
| --- | --- | --- |
| **Tanıma doğruluğu** (STT tek başına) | İnsan veya referans TTS ile kaydedilmiş terim cümleleri → Whisper → resolver | F2-T01, F2-T31 |
| **Seslendirme doğruluğu** (TTS tek başına) | FreyaTTS çıktısı → uzman dinlemesi (ve yardımcı olarak Whisper geri tanıma) | F4-T33 |
| **Birleşik döngü** | Bugünkü ölçüm | F2-T01 (taban) |

Her sözlük kaydı için `acoustic_status` ve `recognition_status` ayrı tutulur. Böylece "Peugeot yanlış" bulgusunun TTS'ten mi, STT'den mi geldiği kayıt düzeyinde görülür.

## 4. Görev sırası (çakışma çözümü)

F2-T08 (katalog dizini) eski `config/freyatts_automotive_lexicon.json` dosyasını, F4-T13 ise birleşik `config/linguistics/automotive_lexicon.json` dosyasını tanımlıyor. Çakışmayı önlemek için:

1. **F4-T02** sözlük uyum raporu ve **F4-T13** birleşik dosya **önce** yapılır (AIP-12).
2. **F2-T08** katalog dizini birleşik dosyayı okur; geçiş süresince eski dosya için okuma adaptörü bulunur.
3. **F4-T15** (F2 ile paylaşım) ve **F2-T11** (ortak Türkçe sayı ayrıştırıcı) birlikte yapılır; sayı okuma ve sayı tanıma aynı tabloyu kullanır.
4. Eski kopyalar, tüm okuyucular yeni dosyaya geçtikten sonra kaldırılır (silme ayrı PR).
