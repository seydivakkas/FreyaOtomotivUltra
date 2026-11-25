# ADR-X-04 — Sözlük okunuşlarının onaylanması (karar günlüğü: ADR-005)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | M05 (inceleme ve yayın), F4-B (varyant etkinleştirme) |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Marka, model, servis ve teknik terimlerin doğru telaffuzu müşteri deneyimi açısından kritik. Hyundai gibi tartışmalı okunuşlarda kimin son sözü söyleyeceği belirsizdi ([shared-lexicon](../../cross-cutting/shared-lexicon.md)).

## Seçenekler

| Seçenek | Açıklama |
| --- | --- |
| A | Kurum içi dil/fonetik uzmanı |
| B | Ürün sahibi + ilgili iş birimi |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı.

## Karar

**Seçenek B.** Sözlükteki özel okunuşların son onayı **ürün sahibi ve ilgili iş birimi** tarafından verilir. Yeni sözlük girdileri yayımlanmadan önce iş birimi onayı alınır.

Gerekçe: teknik ekip her terimin iş bağlamını bilemeyebilir; iş tarafı müşteri beklentisini daha iyi temsil eder.

## Uygulama kuralları (M05)

- `review_manifest.json` her girdi için iki onay kaydı tutar: `product_owner` ve `business_unit` (onaylayan rol, kişi veya oturum başvurusu, tarih, revizyon). Bir okunuş varyantı ancak **iki onay da** varsa `APPROVED` olur ve yayımlanabilir.
- Kodlama ajanı hiçbir girdiyi `APPROVED` yapamaz. Ajan önerileri `STAGED` (veya F4-B'de `PROPOSED`) olarak ekler; onay ürün sahibi ve iş birimi tarafından verilir.
- Teknik doğrulama (G2P geçerliliği, korumalı atom bütünlüğü, sözcük dağarcığı kapsamı) onaydan önce otomatik testlerle yapılır; onay bu testlerin yerini almaz, testler de onayın yerini almaz.
- Onaysız girdiler canlıda etkinleşmez; eski (`LEGACY`) okunuşlar korunur.

## Sonuçlar

- Güncellenen belgeler: M05 §5.4 ve açık karar, F4-B varyant durumları, [F4 spec](../../stages/F4-linguistic-frontend/spec.md) §12.
- **Geri alma koşulu:** onay süreci sözlük güncellemelerini kabul edilemez biçimde geciktirirse rol dağılımı yeniden değerlendirilir.
