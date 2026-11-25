# ADR-F3-02 — Belge arama gömme (embedding) modeli (karar günlüğü: ADR-007)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi (revize) |
| Sahibi olan paket | F3-C (RAG), M03 (model kaydı) |
| Tarih | 2026-11-26 (ilk karar: multilingual-e5-large, alternatif bge-m3; aynı gün yalnız bge-m3 olarak revize edildi) |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Bilgi tabanı ve RAG tabanlı belge aramada Türkçe performans kritik. F3-C bu karar verilene kadar yalnız BM25 (sözcük eşleşmeli arama) kullanacaktı. RTX 4070 Laptop 8 GB'ta tepe VRAM kullanımı zaten %91,3 ölçülmüştür; [constraints](../../00-overview/constraints.md) RAG gömme modeline GPU bütçesi ayırmaz.

## Seçenekler

| Model | Parametre | Bağlam | Boyut | Lisans | Not |
| --- | --- | --- | --- | --- | --- |
| `intfloat/multilingual-e5-large` | ≈ 560M (XLM-RoBERTa-large tabanı) | 512 belirteç | 1024 | MIT | Sorgu `query: `, belge `passage: ` öneki gerekir |
| `BAAI/bge-m3` | ≈ 568M (XLM-RoBERTa tabanı) | 8192 belirteç | 1024 | MIT | Yoğun + seyrek + çok vektörlü arama tek modelde; önek gerekmez |

Kaynak: model kartları (Hugging Face, NVIDIA NIM). Değerler üretici beyanıdır; Freya donanımında ölçülmemiştir. İki model aynı boyut sınıfındadır.

## Ölçüm

Henüz yok. F3-C laboratuvarında, Freya'nın kendi Türkçe otomotiv belge kümesinde, kalibrasyon/test ayrımıyla geri çağırma (recall@k), BM25'e göre eşli fark ve CPU sorgu gecikmesi (p50/p95/p99, n) ölçülür: `data/F3/lab-report-*.json`.

## Karar

**Yalnız `BAAI/bge-m3`.** Başka gömme modeli kullanılmaz; alternatif model yoktur.

Gerekçe: Türkçe dahil çok dilli güçlü geri çağırma; uzun belgeleri (8192 belirteç) parçalamadan işleyebilmesi; yoğun ve seyrek vektörü tek modelde üretmesi; MIT lisansı.

## Uygulama kuralları

- **CPU'da çalışır.** Model GPU'ya yüklenmez (GPU bütçesi 0 MB). Belge dizini çevrimdışı oluşturulur; canlı görüşmede yalnız sorgu kodlanır. GPU kullanımı ancak M06 ölçümü ve ayrı karar ile mümkündür.
- **İndirme yok.** Model yapıtı kullanıcı tarafından yerel olarak sağlanır; M03 model kaydına sürüm, SHA-256 ve lisans (MIT) ile girer. Ajan modeli internetten indirmez (CLAUDE.md kural 13).
- **Önek yok:** bge-m3 sorgu ve belgeleri öneksiz kodlar; e5 tipi önek eklenmez.
- **Uzunluk:** azami 8192 belirteç; CPU gecikmesi için belge parça uzunluğu F3-C ölçümüyle seçilir ve kaydedilir. Kesme sessiz yapılmaz.
- **Hibrit arama:** BM25 her zaman çalışır; bge-m3 yoğun vektörü onunla birleştirilir. bge-m3'ün seyrek (sözcük ağırlığı) çıktısının kullanılması F3-C ölçümüne bağlıdır.
- **Model yoksa:** yapıt yerelde yoksa veya yüklenemezse sistem yalnız BM25 ile sürer ve yoğun arama `HOLD` kaydedilir. Başka bir modele geçilmez; uydurma sonuç üretilmez.
- Erişim filtresi sıralamadan önce uygulanır; getirilen metin araç yetkisi taşımaz (F3-C kuralları).

## Sonuçlar

- CLAUDE.md kural 4'e istisna notu: bu model GPU'ya yüklenmeyen, CPU'da çalışan, onaylı tek gömme modelidir.
- Güncellenen belgeler: F3-C §2 ve §11, ana plan §Verilen kararlar.
- **Geri alma koşulu:** F3-C ölçümünde bge-m3 BM25'e göre anlamlı kazanç sağlamazsa veya CPU sorgu gecikmesi tur bütçesini aşarsa karar yeniden açılır.
