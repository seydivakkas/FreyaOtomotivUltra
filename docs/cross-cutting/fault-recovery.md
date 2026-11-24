# Hata yönetimi ve kurtarma

Her aşamanın kendi hata tablosu `spec.md` içindedir. Bu belge ortak ilkeleri ve aşamalar arası davranışı tanımlar.

## 1. İlkeler

1. **Görüşme düşmez.** Bir bileşen hatası mümkün olduğunca o turu etkiler, görüşmeyi değil.
2. **Sessiz başarı yok.** Hata kullanıcıya doğru biçimde söylenir ("Şu anda sistemimizde bir sorun var, sizi operatöre aktarayım") veya yeniden sorulur; başarı iddia edilmez.
3. **Kurtarma sınırlıdır.** Her kurtarma bir kez (en fazla tanımlı sayıda) denenir; sonsuz döngü yoktur.
4. **Ses kimliği korunur.** TTS kurtarmasında seed değiştirilmez (F5 N3; `experimental` modüldeki seed değiştiren kurtarma taşınmaz).
5. **Her hata olay olarak yayımlanır** ([observability](observability.md)).

## 2. Devre kesiciler

Mevcut `automotive_voice/adapters/lifecycle/breaker.CircuitBreaker` (`models.breakers`: stt, tts, llm; eşik 3, bekleme 10 s) korunur ve genişletilir:

| Kesici | Açılınca |
| --- | --- |
| `stt` | F2 `REPROMPT`; tekrarında DTMF ile seçim veya operatöre aktarım |
| `llm` | F3 yalnızca kural ve şablon yolları (FAST/STANDARD); KNOWLEDGE soruları için "bu konuda sizi uzmanımıza aktarayım" |
| `tts` | Önbellekteki sabit cümleler; önbellekte yoksa operatöre aktarım |
| `transport` (yeni) | Görüşme kontrollü kapatılır (F6 §5.14) |
| `gpu` (yeni, `gpu_health_circuit_breaker` ile) | OOM tekrarında düşük profiller (F2 FAST, F5 küçük yığın) |

## 3. Aşamalar arası hata tablosu

| Hata | Algılayan | Davranış | Ayrıntı |
| --- | --- | --- | --- |
| Bozuk/eksik giriş çerçevesi | F0 | Dolgu + `GAP_FILLED`; NaN/Inf temizleme | F0 §5 |
| VAD durumu bozulması | F1 | Oturum VAD durumunu sıfırla (yalnızca o oturum) | F1 S1 |
| CUDA OOM (STT) | F2 / GPU yöneticisi | Önbellek boşalt, `FAST` ile bir kez; sonra `REPROMPT` | F2 §5.14 |
| Whisper sahte metin | F2 | `hallucination_flags`, `REPROMPT` | F2 S8 |
| Araç çağrısı zaman aşımı | F3 | Aynı idempotency anahtarıyla uzlaştırma; sonuç bilinmeden başarı denmez | F3 P2 |
| Desteklenmeyen karakter | F4 | Yanıt düşmez; `review_required` + güvenli okuma | F4 L5, L12 |
| Bozuk/sessiz sentez | F5 | Aynı seed ile kontrollü yeniden sentez (en fazla 1); sonra önbellek/şablon | F5 §5.8–5.9 |
| Ağ yazması bloklandı | F6 | Zaman aşımı → kontrollü kapanış | F6 R6 |
| Asterisk bağlantısı koptu | F6 | Oturum kapanır, F3'e bildirilir | F6 §5.14 |
| Süreç yeniden başladı | Oturum yöneticisi | Açık görüşmeler `FAILED`/`ENDED`; sürdürülmez | [session-and-state](session-and-state.md) §5 |

## 4. Test

- Her hata satırı için en az bir hata enjeksiyonu testi (sahte motorlar ve `FakeTransport` ile).
- Uçtan uca regresyonlarda (F0-S10 … F6-S26) hata senaryoları ayrı bir grup olarak çalışır.
