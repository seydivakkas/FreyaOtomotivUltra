# ADR-F4-03 — Telefon numarası okuma standardı (karar günlüğü: ADR-004)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | F4-A (okuma); F2-B (geri ayrıştırma) |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Telefon numaralarının tek tek rakam olarak okunması, kullanıcıların numarayı tekrar etmesini zorlaştırıyor. [F4 spec](../../stages/F4-linguistic-frontend/spec.md) §12 soru 3.

## Seçenekler

| Seçenek | Açıklama |
| --- | --- |
| A | Rakam rakam |
| B | 0532 · 123 · 45 · 67 (alışılmış 3-3-2-2 gruplama) |
| C | İkişerli gruplar |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı. Anlaşılırlık ve tekrar hatası G5'te ölçülür.

## Karar

**Seçenek C.** Telefon numaraları ikişerli gruplar hâlinde okunur. Karar günlüğündeki örnek: "05 32 12 34 56 78".

Gerekçe: kullanıcı alışkanlığıyla uyumlu; duyma ve tekrar etme hatalarını azaltır.

## Uygulama kuralları (F4-A)

Türkiye'deki numaralar (cep ve sabit) baştaki 0 ile **11 hanedir**; 11 hane ikişerli bölünemez. Karar günlüğündeki örnek 12 hanedir. Bu nedenle uygulama kuralı:

1. Numara ulusal biçime getirilir: `+90` ve `0090` → `0`; boşluk, tire, parantez atılır.
2. Baştaki **0 ayrı okunur** ("sıfır"), kalan **10 hane ikişerli** okunur:
   `0532 123 45 67` → 0 · 53 · 21 · 23 · 45 · 67 → "sıfır, elli üç, yirmi bir, yirmi üç, kırk beş, altmış yedi".
3. 0 ile başlayan ikili rakam rakam okunur: `07` → "sıfır yedi"; `00` → "sıfır sıfır".
4. Gruplar arasında kısa duraklama (F6 duraklama planı); telefon numarası tek korumalı atomdur, bölünmez.
5. Ulusal biçime getirilemeyen numara (kısa numara, yurt dışı) ikişerli okunur; tek hane kalırsa son gruba eklenir. Tahminle tamamlanmaz.

> **Ürün sahibine not:** Kural 2, örnekteki "05 32 …" başlangıcından farklıdır, çünkü 11 haneli bir numarada ikili gruplama ancak baştaki 0 ayrılarak eşit bölünür. "05 32 12 34 567" gibi başka bir biçim istenirse yalnız bu kural ve F4-A fikstürü değişir.

## Sonuçlar

- **F2-B:** arayanın numarayı hangi gruplamayla söylediğinden bağımsız ayrıştırır (ikili, üçlü, rakam rakam).
- Güncellenen belgeler: F4-A §5, [F4 spec](../../stages/F4-linguistic-frontend/spec.md) `identifier_normalizer` satırı ve §12.
- **Geri alma koşulu:** G5'te tekrar etme veya yanlış duyma hatası alışılmış 3-3-2-2 gruplamadan fazla çıkarsa karar yeniden açılır.
