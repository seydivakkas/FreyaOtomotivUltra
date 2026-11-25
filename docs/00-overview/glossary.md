# Sözlük

| Terim | Açıklama |
| --- | --- |
| **AEC** (Acoustic Echo Cancellation) | Freya'nın kendi sesinin mikrofondan geri dönen kısmını, F6'nın oynatma referansıyla bastırma (F0.02) |
| **AGC** | Otomatik kazanç kontrolü; düşük mikrofon seviyesini hedef seviyeye çeker (F0.06) |
| **AIP** (Agent Implementation Package) | Eski plandaki uygulama paketi (AIP-01…48); emekliye ayrıldı, yerini **paket** aldı ([legacy-mapping](../execution/legacy-mapping.md)) |
| **Paket** | Kodlama ajanının tek oturumda uyguladığı, kendi görev, test ve kabul kapılarıyla kapanan iş birimi (M00, H01, M01…M08, F0-A…F6-D); dalgalar W0–W5 ([yürütme planı](../execution/README.md)) |
| **CORE_GATE / W2_GATE** | Ortak çekirdek (W1) ve uçtan uca dikey dilim (W2) sonrası bağımsız incelenen entegrasyon kapıları |
| **G2–G5, PILOT** | Ürün aşamaları: entegrasyon incelemesi, kokpit arayüzü, sentetik kabul, gerçek insan ve SIP kabulü, pilot kararı |
| **AMI / ARI** | Asterisk Manager Interface (arama, olay, aktarım) / Asterisk REST Interface (kanal ve bridge yaşam döngüsü) |
| **AP01–AP13** | Proje açıklamasındaki geliştirme modülleri; AP13 (Dialogue Orchestration) bu planda eklendi ([roadmap](../roadmap/roadmap.md)) |
| **ASRResult** | F2'nin F3'e verdiği yapılandırılmış tanıma sonucu (ham/normalize/kanonik metin, düzeltmeler, varlıklar, karar) |
| **AudioChunk** | F5'in F6'ya verdiği ham 48 kHz float32 ses parçası ve metadata'sı |
| **AudioSocket** | Asterisk'in TCP üzerinden ham PCM aktaran basit protokolü; tür (1 B) + uzunluk (2 B) + yük |
| **Barge-in** | Freya konuşurken müşterinin söze girmesi; F1 karar verir, F5/F6 uygular |
| **Backchannel** | "Hı hı", "evet evet" gibi dinleme işaretleri; söz kesme sayılmaz |
| **chan_websocket** | Asterisk'in WebSocket medya kanalı; FLUSH_MEDIA, PAUSE_MEDIA, CONTINUE_MEDIA, MARK_MEDIA, MEDIA_XOFF/XON destekler |
| **CONFIRM / RE_DECODE / REPROMPT** | F2 karar kapısının çıktıları: teyit iste / farklı profille yeniden çöz / yeniden sor |
| **Double-talk** | Freya ve müşterinin aynı anda konuştuğu durum (F1.08) |
| **Endpointing** | Müşterinin konuşmasının bittiğine karar verme (F1.06–F1.07) |
| **Entity Resolver** | Ham transkriptteki araç marka/model/yıl ifadesini fonetik benzerlik, katalog ve bağlamla çözen F2 bileşeni |
| **Generation (generation_id)** | Freya'nın iptal edilebilir tek bir yanıt üretimi. Barge-in veya yeni tur generation'ı ilerletir; eski generation'a ait her şey atılır |
| **G2P** | Grapheme-to-Phoneme; yazıdan fonem dizisine dönüşüm (F4) |
| **Hotword** | Whisper'a önceden verilen, tanınması istenen terimler (F2.04) |
| **KNOWLEDGE yolu** | F3'te RAG ile teknik bilgi yanıtı üreten yol |
| **Leyla** | Freya'nın sabit ses kimliği (FreyaTTS, seed 9) |
| **Lookback / pre-roll** | Konuşma başlangıcı algılanmadan önceki sesin tamponda tutulup STT'ye eklenmesi |
| **MARK_MEDIA** | chan_websocket'te kuyruğa işaret koyma; işlendiğinde `MEDIA_MARK_PROCESSED` olayı gelir (oynatma konumu bilgisi) |
| **Pacing** | Çerçevelerin gerçek zamanlı aralıklarla (20 ms) gönderilmesi |
| **ResponsePlan** | F3'ün F4'e verdiği doğrulanmış yanıt (parçalar, anlamsal etiketler, `TurnContext`) |
| **RTF** | Real-Time Factor; işlem süresi / ses süresi |
| **Seed** | Sentezdeki gürültü üretecinin başlangıç değeri; Leyla için 9 |
| **SpeechFrame / SpeechEvent / Utterance** | F1 sözleşmeleri: VAD olasılıklı blok / konuşma olayı / STT'ye giden tamamlanmış söz |
| **Supervisor** | F3'teki görev planlayıcı ve ajan orkestratörü (`backend/supervisor/`) |
| **SynthesisPlan** | F4'ün F5'e verdiği değişmez (immutable) sentez planı; `plan_id` önbellek anahtarıdır |
| **TTFA** | Time To First Audio; müşterinin konuşması bittikten sonra Freya'nın ilk sesinin duyulmasına kadar geçen süre |
| **TurnContext** | F3'ün F1/F2'ye verdiği bağlam: beklenen bilgi türü, onay bekleniyor mu, Freya'nın son ifade türü |
| **VAD** | Voice Activity Detection; Silero VAD |
| **WSOLA** | Waveform Similarity Overlap-Add; perdeyi koruyarak konuşma hızını değiştirme (F6.03) |
| **XOFF / XON** | Asterisk chan_websocket'in "göndermeyi durdur / devam et" akış kontrolü olayları |
