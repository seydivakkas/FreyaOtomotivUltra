# ADR-F4-03 — Telefon numarası okuma standardı (karar günlüğü: ADR-004)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi (revize) |
| Sahibi olan paket | F4-A (okuma); F2-B (geri ayrıştırma) |
| Tarih | 2026-11-26 (ilk karar: ikişerli gruplar; aynı gün revize edildi) |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Telefon numaralarının tek tek rakam olarak okunması, kullanıcıların numarayı tekrar etmesini zorlaştırıyor. [F4 spec](../../stages/F4-linguistic-frontend/spec.md) §12 soru 3.

İlk kararda ikişerli gruplama seçilmişti. Ancak Türkiye'deki numaralar baştaki 0 ile 11 hanedir ve ikişerli eşit bölünemez. Ürün sahibi kararı alışılmış yazım biçimine göre revize etti.

## Seçenekler

| Seçenek | Örnek |
| --- | --- |
| A | Rakam rakam |
| B | `05xx xxx xx xx` gruplaması (4-3-2-2) |
| C | İkişerli gruplar (11 hanede eşit bölünmez) |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı. Anlaşılırlık ve tekrar hatası G5'te ölçülür.

## Karar

**Seçenek B.** Telefon numaraları `05xx xxx xx xx` biçiminde, 4-3-2-2 gruplarla okunur:

`0532 123 45 67` → "sıfır beş yüz otuz iki, yüz yirmi üç, kırk beş, altmış yedi"

Gerekçe: Türkiye'de numaranın yazılış ve söyleniş alışkanlığıyla aynı; duyma ve tekrar etme hatalarını azaltır.

## Uygulama kuralları (F4-A)

1. Numara ulusal biçime getirilir: `+90` ve `0090` → `0`; boşluk, tire, parantez atılır. Sonuç 11 hane ve `0` ile başlıyorsa 4-3-2-2 gruplanır. Cep (`05xx`) ve sabit hat (`0212` vb.) aynı kuralla okunur.
2. **İlk grup** (`0` + 3 haneli alan/operatör kodu): "sıfır" + üç basamaklı sayı → `0532` "sıfır beş yüz otuz iki", `0212` "sıfır iki yüz on iki".
3. **İkinci grup** (3 hane) üç basamaklı sayı olarak: `123` "yüz yirmi üç", `400` "dört yüz".
4. **Üçüncü ve dördüncü grup** (2 hane) iki basamaklı sayı olarak: `45` "kırk beş".
5. **Sıfırla başlayan grup:** baştaki her sıfır "sıfır" diye okunur, kalan sayı olarak: `045` "sıfır kırk beş", `07` "sıfır yedi", `00` "sıfır sıfır", `005` "sıfır sıfır beş".
6. Gruplar arasında kısa duraklama (F6 duraklama planı); telefon numarası tek korumalı atomdur, bölünmez.
7. Ulusal biçime getirilemeyen numara (kısa numara, yurt dışı, eksik hane) rakam rakam okunur; tahminle tamamlanmaz, eksik hane uydurulmaz.

## Sonuçlar

- **F2-B:** arayanın numarayı hangi gruplamayla söylediğinden bağımsız ayrıştırır (4-3-2-2, ikili, rakam rakam).
- Güncellenen belgeler: F4-A §5 ve LN24, [F4 spec](../../stages/F4-linguistic-frontend/spec.md) `identifier_normalizer` satırı ve §12, [F4 acceptance](../../stages/F4-linguistic-frontend/acceptance.md) T10.
- **Geri alma koşulu:** G5'te tekrar etme veya yanlış duyma hatası kabul edilemez çıkarsa karar yeniden açılır.
