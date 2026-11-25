# ADR-X-05 — Belge arşivi lisans ve içerik onayı sahibi (karar günlüğü: ADR-008)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | F3-C (RAG belge kaydı); ilke olarak F5-D (eğitim verisi hakları) |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Belge arşivine (RAG bilgi tabanı) eklenecek dokümanların lisans uygunluğunu, kullanım hakkını, güncelliğini ve içerik doğruluğunu nihai olarak kimin onaylayacağı belirsizdi. F3-C lisansı veya erişim incelemesi eksik belgeyi karantinada tutar; ama inceleme yetkilisi tanımlı değildi.

## Seçenekler

| Seçenek | Açıklama |
| --- | --- |
| A | Teknik ekip onaylar |
| B | Ürün sahibi onaylar |
| C | İş sahibi / veri sahibi onaylar; teknik ekip yalnız teknik doğrulama yapar |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı.

## Karar

**Seçenek C.** Nihai sorumluluk **iş sahibi / veri sahibi** (business owner) üzerindedir.

| Rol | Sorumluluk |
| --- | --- |
| Belge sahibi | İçeriği üretir veya sisteme eklenmesini talep eder |
| Teknik ekip | İndeksleme, erişim ve teknik doğrulama |
| İş sahibi / veri sahibi | Lisans uygunluğu, kullanım hakkı, güncellik ve içerik doğruluğu için nihai onay |

Gerekçe: telif, lisans ve içerik doğruluğu teknik değil kurumsal sorumluluktur; bu risk ürün veya altyapı ekibine bırakılmamalıdır.

## Uygulama kuralları (F3-C)

- Belge kaydı (`CORPUS_MANIFEST`) her belge için şunları tutar: belge sahibi (talep eden), iş sahibi / veri sahibi onayı (onaylayan başvurusu, tarih, onaylanan revizyon), lisans ve kullanım hakkı kaydı, güncellik bilgisi (yayın/son gözden geçirme tarihi ve varsa geçerlilik sonu), teknik doğrulama sonucu.
- Bir belge ancak **iş sahibi onayı + başarılı teknik doğrulama** ile etkin aranabilir dizine girer. Biri eksikse belge karantinadadır ve aranamaz.
- Onay belgenin belirli revizyonuna bağlıdır; içerik değişirse (yeni hash) onay yenilenir.
- Geçerlilik süresi dolan veya onayı geri çekilen belge yeni dizin anlık görüntüsünden çıkarılır; çalışan görüşmeler sabitlenmiş eski anlık görüntüyü tamamlar.
- Güncellik süresini iş sahibi belge başına belirler; plan sabit bir süre dayatmaz.
- Kodlama ajanı ve teknik ekip hiçbir belgeyi iş onaylı olarak işaretleyemez; ajan yalnız teknik doğrulamayı yapar ve onay alanını boş bırakır.
- İnternetten belge çekilmez; belgeler belge sahibi tarafından yerel olarak sağlanır.
- **F5-D (ilke):** eğitim veya değerlendirme için kullanılacak veri setlerinin kullanım hakkı da veri sahibi tarafından onaylanır; kişisel ses verisi ayrıca G5 gizlilik kurallarına ve katılımcı rızasına tabidir.

## Sonuçlar

- Güncellenen belgeler: F3-C §5.1 ve F3-C.04, F5-D §12, ana plan §Verilen kararlar.
- **Geri alma koşulu:** onay süreci belge güncellemelerini kabul edilemez biçimde geciktirirse rol dağılımı yeniden değerlendirilir; nihai sorumluluğun teknik ekibe geçmesi yeni bir karar gerektirir.
