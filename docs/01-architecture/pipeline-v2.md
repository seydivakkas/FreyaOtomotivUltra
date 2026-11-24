# Freya 2.0 — Ses işleme hattı v2

Bu belge yedi katmanı ve ortak katmanı tek bir bütün olarak gösterir. Her katmanın ayrıntısı kendi `spec.md` dosyasındadır; sözleşmeler [`interfaces.md`](interfaces.md) dosyasındadır.

## 1. Ana akış

```mermaid
flowchart TD
    subgraph IN["Giriş"]
        MIC["Web mikrofonu<br/>16–48 kHz"]
        PBX["Asterisk<br/>AudioSocket / chan_websocket<br/>8 kHz PCM16"]
    end

    MIC & PBX --> F0["F0 Audio Acquisition & Enhancement<br/>AEC · HPF · NS · AGC · Limiter · Resample → 16 kHz<br/>DTMF ham yoldan"]
    F0 -->|"F0Output (enhanced 16 kHz + raw)"| F1["F1 Voice & Turn Detection<br/>VAD · Lookback · Endpointing · Semantic Turn · Barge-in"]
    F1 -->|Utterance| F2["F2 Speech Recognition<br/>Whisper · Hotwords · Normalizer · Entity Resolver · Güven kapısı"]
    F1 -.->|"endpoint adayı → spekülatif STT"| F2
    F2 -->|ASRResult| F3["F3 Dialogue Intelligence<br/>Router · State Machine · Supervisor · Ajanlar · RAG · Policy · Validator"]
    F3 -->|ResponsePlan| F4["F4 Linguistic Frontend<br/>Tek normalizasyon · Sözlük · G2P · Vurgu · Prozodi · Bölümleme"]
    F4 -->|SynthesisPlan| F5["F5 Neural Synthesis<br/>FreyaTTS DiT · Seed 9 · Önbellek · Duration/Quality Guard"]
    F5 -->|"AudioChunk (48 kHz ham)"| F6["F6 Rendering & Transport<br/>Assembly · Crossfade · Duraklama · EQ · Limiter · Resample · Pacing · Kuyruk"]

    F6 --> OUTW["Web 16 kHz"]
    F6 --> OUTP["Telefon 8 kHz slin"]

    F3 -.->|TurnContext| F1
    F3 -.->|TurnContext| F2
    F6 -.->|oynatma referansı| F0
    F6 -.->|"PlaybackEvent / PlaybackState"| F1
    F1 -.->|"barge-in: PAUSE / RESUME / FLUSH"| F6
    F1 -.->|"barge-in: CANCEL"| F5
    F1 -.->|"barge-in: CANCEL"| F3

    subgraph CC["Ortak katman"]
        GPU["GPU Resource Manager<br/>P0–P7"]
        SES["Session & State<br/>kimlikler · generation · iptal"]
        OBS["Observability<br/>EventEnvelope · gecikme T1–T6"]
        SEC["Security & Privacy<br/>KVKK · kimlik doğrulama"]
        LEX["Shared Lexicon<br/>F2 tanıma ↔ F4 seslendirme"]
        FR["Fault Recovery"]
        CFG["Configuration Registry"]
    end

    F2 & F3 & F5 -.-> GPU
    F2 & F4 -.-> LEX
```

## 2. Katmanlar arası geri besleme döngüleri

| Döngü | Kaynak → Hedef | Ne taşınır | Neden |
| --- | --- | --- | --- |
| Konuşma bağlamı | F3 → F1, F2 | `TurnContext` (`expected_slot`, `awaiting_confirmation`, `freya_utterance_kind`) | F1 sessizlik eşiğini, F2 hotword kümesini ve karar kapısını seçer |
| Yankı referansı | F6 → F0 | Transport'a yazılan son sesin zaman damgalı kopyası | F0 AEC ve F1 double-talk |
| Oynatma durumu | F6 → F1 | `PlaybackEvent`, `PlaybackState` (konum, cümlecik başlangıcı) | Barge-in kararı, resume konumu, duyulabilir kesilme ölçümü |
| Barge-in | F1 → F6, F5, F3 | SOFT_PAUSE / RESUME / FLUSH / CANCEL ve yeni `generation_id` | Eski sesin durması, eski sentezin iptali, F3'ün yarım kalan yanıtı bilmesi |
| Spekülatif tanıma | F1 → F2 → F1 | Endpoint adayında kısa tanıma isteği; sonuç F1.07'ye | Semantic turn kararı ve TTFA'nın kısalması |
| Varlık odağı | F3 → F4 | `ResponseSegment.tags` (marka, model, plaka, fiyat, tarih…) | F4 korumalı öbekler, vurgu, duraklama |
| Sözlük | F2 ↔ F4 | Tek otomotiv sözlüğü (tanıma ve seslendirme yönleri) | Aynı terimin iki yönde tutarlı olması |

## 3. Tasarım ilkeleri

1. **Tek sorumluluk, tek uygulama.** Normalizasyon F4'te, duraklama/fade F6'da, VAD durumu F1'de, GPU zamanlaması ortak katmanda.
2. **Değişmez veri akışı.** Katmanlar arası nesneler `frozen` dataclass'tır; bir katman kendinden öncekinin çıktısını değiştirmez, yenisini üretir.
3. **Generation kapısı her katmanda.** F2 sonucu, F3 planı, F4 planı, F5 parçası ve F6 çerçevesi `generation_id` taşır; eski olan atılır ve sayılır.
4. **Ham veri korunur.** F0 ham çerçeveyi, F2 ham transkripti, F4 kaynak metni, F5 ham sesi taşır. Hata ayıklama ve ablation için gereklidir.
5. **Bilinmeyen değer `null`'dır.** Ölçülmemiş güven, SNR veya gecikme uydurulmaz.
6. **Bayrak arkasında kademeli geçiş.** Her katmanın `fN_pipeline_v2` bayrağı vardır; legacy yol regresyon sprinti geçene kadar varsayılandır.

## 4. Çalışma kipleri

| Kip | Açıklama |
| --- | --- |
| Legacy | Tüm `fN_pipeline_v2` bayrakları kapalı; PoC davranışı + bayraktan bağımsız düzeltmeler |
| Karma | Bazı katmanlar v2. Sözleşme adaptörleri legacy ↔ v2 dönüşümünü yapar (ör. `models.transcribe() -> str` uyumluluğu) |
| Shadow | v2 hattı legacy ile paralel çalışır, çıktısı kaydedilir ama müşteriye gitmez (F3-S23) |
| V2 | Tüm katmanlar v2; legacy kod uyumluluk sarmalayıcısı olarak kalır |

## 5. Eşzamanlılık modeli

- Görüşme başına bir `Session`; F0 ve F1 durumu oturum başınadır (Silero VAD dahil — F1 S1).
- CPU ağırlıklı DSP (F0, F6) olay döngüsünü bloklamamalı; 20 ms çerçevede 1/2/4 eşzamanlı oturumla ölçülür (F0-T22), gerekirse oturum başına iş parçacığı.
- GPU işleri (STT, LLM, TTS) tek bir ortak yöneticiden geçer; öncelik P0–P7 ([gpu-resource-manager](../cross-cutting/gpu-resource-manager.md)).
- Ağ yazmaları zaman aşımlıdır; bir oturumun yavaş tüketicisi diğerlerini etkilemez.
