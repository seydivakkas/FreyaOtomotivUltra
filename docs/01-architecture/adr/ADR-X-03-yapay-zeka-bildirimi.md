# ADR-X-03 — Yapay zekâ bildirimi (karar günlüğü: ADR-002)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | H01 (H01.14), F3-A; önkoşul olduğu aşamalar: G5, PILOT_DECISION |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Arayanın bir insanla mı yoksa yapay zekâ ile mi görüştüğünü bilmesi gerekir. Gerçek kullanıcı testleri (G5) ve pilottan önce bu konunun netleşmesi gerekiyordu ([decisions.md K-06](../../execution/decisions.md#k-06--yapay-zekâ-bildirimi)).

## Seçenekler

| Seçenek | Açıklama |
| --- | --- |
| A | Karşılamada açık bildirim |
| B | Yalnız sorulursa bildirim |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı. Karşılama süresine etkisi G4/G5'te ölçülür.

## Karar

**Seçenek A.** Görüşmenin başında açık bir bildirim yapılır. Örnek metin:

> "Merhaba, Freya yapay zekâ destekli müşteri temsilcisine ulaştınız."

Gerekçe: şeffaflık sağlar, kullanıcı beklentisini doğru yönetir, pilot başlangıcı için önkoşuldur.

## Uygulama kuralları

- Bildirim **her görüşmenin** karşılamasında yer alır: gelen ve giden çağrı, telefon ve web. Önbellekteki karşılama da bu metinle yeniden üretilir (Leyla, seed 9).
- Metin M03 yapılandırmasında tek yerde tutulur; ajan metni kendiliğinden değiştirmez. Metin değişikliği ürün sahibi onayı ister.
- Arayan "insanla mı konuşuyorum?" diye sorarsa yanıt dürüsttür ve operatöre aktarım seçeneği sunulur.
- Söz kesme bildirimi atlatmaz: arayan karşılamanın ortasında konuşursa bildirim cümlesi tamamlanmış sayılmaz; ilk yanıtta kısa biçimde tekrarlanır (ör. "Ben Freya, yapay zekâ destekli asistanım.").

## Sonuçlar

- H01.14 ve HF16 artık koşulsuzdur.
- G5 ve PILOT_DECISION'daki "bildirim kararı verilmiş" giriş koşulu karşılandı; bildirimin uygulanmış ve test edilmiş olması (HF16 PASS) koşulu sürer.
- **Geri alma koşulu:** hukuki gereklilik veya kurumsal politika metni değiştirirse yalnız metin güncellenir; bildirimin kaldırılması yeni bir karar gerektirir.
