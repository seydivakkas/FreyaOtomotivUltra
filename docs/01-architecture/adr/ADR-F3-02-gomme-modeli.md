# ADR-F3-02 — Belge arama gömme (embedding) modeli (karar günlüğü: ADR-007)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | F3-C (RAG), M03 (model kaydı) |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Bilgi tabanı ve RAG tabanlı belge aramada Türkçe performans kritik. F3-C bu karar verilene kadar yalnız BM25 (sözcük eşleşmeli arama) kullanacaktı. RTX 4070 Laptop 8 GB'ta tepe VRAM kullanımı zaten %91,3 ölçülmüştür; [constraints](../../00-overview/constraints.md) RAG gömme modeline GPU bütçesi ayırmaz.

## Seçenekler

| Model | Parametre | Bağlam | Boyut | Lisans | Not |
| --- | --- | --- | --- | --- | --- |
| `intfloat/multilingual-e5-large` | ≈ 560M (XLM-RoBERTa-large tabanı) | 512 belirteç | 1024 | MIT | Sorgu `query: `, belge `passage: ` önekiyle kodlanmalı |
| `BAAI/bge-m3` | ≈ 568M (XLM-RoBERTa tabanı) | 8192 belirteç | 1024 | MIT | Yoğun + seyrek + çok vektörlü arama tek modelde; önek gerekmez |

Kaynak: model kartları (Hugging Face, NVIDIA NIM). Değerler üretici beyanıdır; Freya donanımında ölçülmemiştir.

## Ölçüm

Henüz yok. F3-C laboratuvarında, Freya'nın kendi Türkçe otomotiv belge kümesinde, kalibrasyon/test ayrımıyla geri çağırma (recall@k), BM25'e göre eşli fark ve CPU sorgu gecikmesi (p50/p95/p99, n) ölçülür: `data/F3/lab-report-*.json`.

## Karar

- **Varsayılan:** `multilingual-e5-large`.
- **Alternatif:** kaynak kısıtı olan ortamlarda `bge-m3` değerlendirilebilir.

Gerekçe: çok dilli içerikte güçlü performans; Türkçe sorgularda yüksek geri çağırma; RAG mimarilerinde yaygın kullanım.

> **Ürün sahibine not:** Model kartlarına göre `bge-m3` (≈ 568M) ile `multilingual-e5-large` (≈ 560M) aynı boyut sınıfındadır; `bge-m3` kaynak tasarrufu sağlamaz. Asıl farkı uzun belge desteği (8192 belirteç) ve tek modelde yoğun + seyrek arama yapabilmesidir. Gerçek bir kaynak kısıtında seçenekler daha küçük bir model (ör. `multilingual-e5-base`, 12 katman, 768 boyut) veya yalnız BM25'tir. Bu alternatif ayrı karar ister; karar verilene kadar kaynak kısıtında yalnız BM25 kullanılır.

## Uygulama kuralları

- **CPU'da çalışır.** Gömme modeli GPU'ya yüklenmez (GPU bütçesi 0 MB). Belge dizini çevrimdışı oluşturulur; canlı görüşmede yalnız sorgu kodlanır. GPU kullanımı ancak M06 ölçümü ve ayrı karar ile mümkündür.
- **İndirme yok.** Model yapıtı kullanıcı tarafından yerel olarak sağlanır; M03 model kaydına sürüm, SHA-256 ve lisans (MIT) ile girer. Ajan modeli internetten indirmez (CLAUDE.md kural 13).
- **e5 önekleri:** sorgular `query: `, belgeler `passage: ` önekiyle kodlanır; önek eksikliği test edilir.
- **Uzunluk:** e5 için 512 belirteç sınırı; belgeler bu sınıra göre parçalanır. Kesme sessiz yapılmaz, parça sayısı kaydedilir.
- **Hibrit arama:** BM25 her zaman çalışır; yoğun arama onunla birleştirilir. Gömme modeli yüklenemezse sistem yalnız BM25 ile sürer ve bu durum `HOLD` olarak kaydedilir (yoğun arama yok, uydurma sonuç yok).
- Erişim filtresi sıralamadan önce uygulanır; getirilen metin araç yetkisi taşımaz (F3-C kuralları).

## Sonuçlar

- CLAUDE.md kural 4'e istisna notu eklendi: bu model GPU'ya yüklenmeyen, CPU'da çalışan, onaylı tek gömme modelidir.
- Güncellenen belgeler: F3-C §2 ve §11, [constraints](../../00-overview/constraints.md) (değişiklik yok; CPU varsayımı korunur).
- **Geri alma koşulu:** F3-C ölçümünde e5-large BM25'e göre anlamlı kazanç sağlamazsa veya CPU sorgu gecikmesi tur bütçesini aşarsa karar yeniden açılır.
