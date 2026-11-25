# ADR-F3-01 — Arayan kimliğinin doğrulanması (karar günlüğü: ADR-001)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | H01 (H01.03), M07, F3-A, F3-B (eski görev F3-T05) |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

PoC'ta garanti ve bakım geçmişi gibi özel kayıtlar yalnız arayan numarasıyla bulunan profilden okunabiliyordu (bulgu P4/P5, [security-and-privacy](../../cross-cutting/security-and-privacy.md)). Telefon numarası tek başına kimlik doğrulaması için yeterli değildir: yanlış yönlendirme, ortak hat kullanımı, numara taşıma ve arayan numarasının sahte gösterilebilmesi mümkündür.

## Seçenekler

| Seçenek | Açıklama | Artı | Eksi |
| --- | --- | --- | --- |
| A | Arayan numarası + doğum yılı (yoksa plaka son 3–4 hanesi) | Sesli görüşmede kolay; ek altyapı gerekmez | Bilgi etkenidir; tahmin edilebilir değer aralığı dardır |
| B | Arayan numarası + plaka + ad soyad | Kayıtta genellikle bulunur | Plaka ve ad başkalarınca bilinebilir |
| C | Kayıtlı numaraya tek kullanımlık kod (SMS) | Daha güçlü | SMS altyapısı ve gecikme; çevrimdışı hedefle çelişir |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı. Kullanılabilirlik G5'te gerçek arayanlarla doğrulanır (doğrulama süresi, başarısız deneme oranı).

## Karar

**Seçenek A.** Arayanın kimliği, arayan numarasına ek olarak ikinci bir bilgiyle doğrulanır:

1. Tercihen **doğum yılı**.
2. Kayıtta doğum yılı yoksa **plaka bilgisinin son 3–4 hanesi**.

Gerekçe: sesli görüşmede kolay yanıtlanır, kullanıcı deneyimini bozmadan güvenliği artırır, ek maliyeti düşüktür.

## Uygulama kuralları

Bu kurallar kararı değiştirmez; güvenli uygulamanın asgari koşullarıdır.

- **Doğrulamayı deterministik kod yapar (M07).** Karşılaştırma yalnız arayan numarasıyla eşleşen kayıt üzerinde yapılır. LLM yalnız "doğrulandı / doğrulanmadı" bilgisini görür; doğum yılı veya plaka değeri LLM bağlamına, günlüğe ve telemetriye girmez.
- **Soru M07 doğrulama adımıyla sorulur.** Konuşma sırasında kendiliğinden söylenen plaka, ad veya numara doğrulama sayılmaz.
- **Deneme sınırı.** Bir görüşmede en çok 3 yanlış deneme; aşılınca o görüşmede özel kayıt kapanır ve operatöre aktarım veya şubeye başvuru önerilir. Aynı numaradan art arda başarısız görüşmeler M07 denetim kaydına yazılır. Sınır değerleri M03 yapılandırmasındadır.
- **Bilgi sızdırmama.** Yanlış yanıtta hangi parçanın yanlış olduğu, kayıtlı değerin ipucu veya böyle bir kaydın var olup olmadığı söylenmez. Freya kayıtlı doğum yılını veya plakayı hiçbir zaman sesli okumaz.
- **Kayıtta ikinci bilgi yoksa** (ne doğum yılı ne plaka): özel kayıt okunmaz; operatör önerilir. Yeni değer görüşmede toplanıp kaydedilmez; bu ayrı bir veri toplama ve aydınlatma kararı gerektirir.
- **Kapsam.** Doğrulama özel kayıt okuma (servis geçmişi, garanti, randevu durumu) ve randevu oluşturma/değiştirme/iptal için gerekir. Genel bilgi (çalışma saatleri, adres, genel fiyat bilgisi) doğrulama gerektirmez. İletişim bilgisi değişikliği gibi yüksek riskli işlemler bu karar kapsamında otomatik yapılmaz; operatöre aktarılır.
- **Doğrulama süresi.** Doğrulama yalnız o görüşme için geçerlidir; görüşmeler arası taşınmaz.

## Sonuçlar

- Güncellenen belgeler: H01 (H01.03, HF03, HF18), M07 (§5 kimlik kuralları, açık karar kapandı), F3-A §5.7, [security-and-privacy](../../cross-cutting/security-and-privacy.md), [F3 spec](../../stages/F3-dialogue-intelligence/spec.md) §12.
- M00 envanteri PoC veritabanında doğum yılı ve plaka alanlarının varlığını doğrular; alan yoksa yukarıdaki "ikinci bilgi yoksa" kuralı uygulanır.
- **Geri alma koşulu:** G5'te tahmin veya sosyal mühendislikle doğrulama aşımı gözlenirse ya da başarısız doğrulama oranı kabul edilemez çıkarsa karar yeniden açılır (seçenek C değerlendirilir).
