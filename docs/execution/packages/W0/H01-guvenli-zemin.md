# H01 — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri

> Bugün canlı görüşmeyi veya kişisel veriyi etkileyen hataları, yeni mimari beklenmeden ve bayrak arkasına alınmadan, **mevcut kodda en küçük değişiklikle** düzeltir. Test paketini torch, CUDA ve Ollama olmadan çalışır hale getirir; ölçülmemiş değer gösteren yerleri temizler.

| Alan | Değer |
| --- | --- |
| Kimlik | H01 |
| Dalga | W0 |
| Öncelik | P0 |
| Önkoşullar | M00 |
| Sonraki | M01, CORE_GATE |
| Bayrak | Yok — bu paketteki düzeltmeler **bayraktan bağımsızdır** (eski yolda da geçerlidir) |
| Ortam | CPU (HF11–HF13 için GPU'lu makinede bir duman testi önerilir) |
| Eski görevler | F3-T01, F3-T05, F3-T03, F1-T03, F1-T05, F0-T14, F4-T04, F4-T05, F5-T11, F5-T17 (yalnızca iptal filtresi), F6-T03, F5-T04 |
| Kaynak | Eski plan "Faz 0 — Bayraktan bağımsız düzeltmeler" + teknik rapor bulguları (UI-1, UI-2, yapay zekâ bildirimi). Bundle'da karşılığı yok; neden için [decisions.md](../../decisions.md) K-01. |
| Durum | NOT_RUN |

## 1. Amaç

Bundle planında ilk kod değişikliği M01'de başlar ve kritik hataların bir kısmı ancak F3-A, F5-B gibi çok sonraki paketlerde ele alınır. Oysa bazı hatalar bugün müşteriyi etkiliyor: kimliği doğrulanmamış bir arayana araç geçmişi okunabiliyor, ikinci araç randevusu başarısız olabiliyor, bir görüşme diğerinin VAD durumunu sıfırlayabiliyor, "Mégane" içeren bir yanıt hiç okunmuyor. H01 bu hataları yeni paketleri beklemeden kapatır. Yeni mimari (M01–F6) daha sonra bu düzeltmeleri kendi yapısına taşır; davranış korunur.

## 2. Başlamadan önce

- [ ] M00 kabul edilmiş (veya en az HOLD; ama M00-G00 ve M00-G07 PASS olmalı).
- [ ] M00 `RISK_REGISTER.md` içinde aşağıdaki bulguların durumu (`CONFIRMED` / `NOT_REPRODUCED`) okunmuş. `NOT_REPRODUCED` olan bulgu için ilgili görev yapılmaz, nedeniyle `DEFERRED` yazılır.
- [ ] ADR-F3-01 (ikinci kimlik etkeni) kararı verilmemiş olabilir: güvenli varsayılan uygulanır (aşağıda H01.03).
- [ ] K-06 kararı (karşılamada yapay zekâ bildirimi) [decisions.md](../../decisions.md)'de "Kabul" değilse H01.14 yapılmaz.

## 3. Kapsam

**Yapılacak:** Aşağıdaki düzeltmeler, her biri kendi regresyon testiyle; test paketinin hermetik hale getirilmesi; ölçülmemiş iddiaların temizlenmesi.

**Yapılmayacak:** Yeni paket dizinleri (`backend/voice_activity/` vb.), yeni sözleşme türleri, yeni mimari. Bunlar M01 ve sonrasındadır. H01'deki her değişiklik mevcut dosyalarda, en küçük biçimde yapılır.

## 4. Dosyalar

| Tür | Yol (PoC reposu) |
| --- | --- |
| Değişecek | `backend/sft_leyla.py`, `backend/routers/text_speech.py`, `tests/conftest.py`, `backend/dialogue.py`, `backend/caller_memory.py`, `backend/models.py`, `backend/session.py`, `noise_estimator.py` (kalibrasyon), `backend/text.py`, `backend/normalizer_rules.py`, `backend/batched_ode.py`, `backend/audiosocket_server.py`, `backend/websocket_adapter.py`, `backend/main.py`, `backend/ab_testing.py` (yalnız H01.14), `frontend/src/tabs/LabTab.tsx`, `frontend/src/tabs/VoiceTab.tsx`, `frontend/src/CarDenoiserPanel.tsx`, `frontend/src/CockpitHeader.tsx` |
| Yeni | `tests/fakes/fake_llm.py`, `tests/h01/test_*.py` |
| Plan reposunda | `docs/01-architecture/adr/ADR-F1-01-vad-isolation.md` (H01.06), `ADR-F3-01` taslağı (H01.03) |

## 5. Tasarım ve sözleşmeler

1. **Hermetik test minimumu (bulgu X8, P8).** `sft_leyla.py` modül düzeyinde `import torch` yaptığı için `backend.main`'i içe aktaran 43 test dosyası torch olmadan toplanamıyor. torch içe aktarması fonksiyon içine taşınır; SFT router'ı yalnızca SFT uçları çağrıldığında yükler. `pytest.ini`/`pyproject` içine `gpu`, `llm`, `pbx` işaretleri tanımlanır. Canlı Ollama gerektiren testler senaryo bazında JSON döndüren sahte LLM'e geçirilir. Tam test altyapısı (sahte saat, sahte çıkarım motoru, altın senaryolar) M08'dedir.
2. **Kimliksiz özel kayıt (P4, P5).** Garanti ve geçmiş bakım gibi özel kayıtlar, arayan numarasıyla bulunan profilden **okunmaz**. Arayan numarası yalnızca eşleştirme ipucudur. ADR-F3-01 kararı verilene kadar güvenli varsayılan: ikinci etken yoksa özel kayıt içeriği söylenmez; operatöre aktarım veya şubeye başvuru önerilir. Arama başında otomatik profil oluşturma kaldırılır.
3. **Çoklu araç idempotency (P7).** Önce mevcut test ikinci aracın onayına kadar uzatılarak hata doğrulanır. Doğrulanırsa her araç işlemine ayrı idempotency anahtarı verilir. Aynı onayın tekrarı ikinci kayıt üretmez.
4. **VAD oturum yalıtımı (S1).** Paylaşılan Silero durumu yerine oturum başına durum; `models.vad.reset_states()` çağrısı kaldırılır. İki seçenek ADR-F1-01'de tartışılır: (A) oturum başına model kopyası, (B) paylaşılan ağırlık + oturum başına durum tensörü. Bellek ölçümü yoksa B tercih edilir.
5. **Bölüm iptali (S5).** Yeni konuşma bölümü geldiğinde önceki tur henüz F3'e iletilmediyse iki bölüm **birleştirilir**; `self.task.cancel()` ile atılmaz. Tam Utterance Manager F1-B'dedir.
6. **Bloklamayan kalibrasyon (F0).** Gürültü kalibrasyonu sırasında ses VAD/STT'ye gitmeye devam eder.
7. **Tek karakter yanıtı düşürmesin (L5).** Minimal güvenli yedek tablosu: `°` → "derece", `−` → "eksi", `é` → "e", `&` → "ve", küçük `q` → "k" (sözlükte özel okunuş yoksa). Tablo dışı karakter atılır ve olay olarak kaydedilir; yanıt düşmez. Tam adaptör F4-A'dadır.
8. **Sıra sayısı (L3).** "1. / 2." → "birinci / ikinci" (sayıdan sonra nokta + boşluk + küçük harf veya sıra bağlamı). F3 seçenek şablonu sıra etiketiyle üretilir. "Bir." gibi tek sözcüklük parça oluşmaz.
9. **Seed düşürmeleri (N3).** Yedek yoldaki `seed=LEYLA_SEED`, geniş `except TypeError` blokları ve önbellek anahtarındaki `None → 9` varsayılanı kaldırılır. Seed her zaman ses profilinden gelir; değişimi yalnızca açık profil değişimiyle olur ve kaydedilir.
10. **İptal filtresi (N5).** İptal edilmiş veya eski generation'a ait sentez öğeleri yığına alınmadan çıkarılır. Yığın tekilliği ve profiller F5-B/F5-C'dedir.
11. **Ağ yazma zaman aşımı (R6).** Her `drain`/`send` çağrısına zaman aşımı (öneri: 2 × çerçeve süresi × önden gönderim sınırı, en az 200 ms); aşılınca kontrollü kapanış ve olay kaydı.
12. **Ölçülmemiş iddialar.** `batched_ode.py` docstring'indeki RTX 4090 / RTF / F0 iddiaları kaldırılır veya "ölçülmedi" etiketlenir. Arayüzde ölçüm yokken sabit sayı gösterilmez (`—`); ses laboratuvarı modeli doğru adlandırır (FreyaTTS); ses süresi WAV başlığındaki gerçek örnekleme hızından hesaplanır; "TTFB" etiketi "İstek süresi" olur; etkisiz `speed`/`speaker` kontrolleri devre dışı bırakılıp nedeni gösterilir; demo değilken "CANLI REEL MOD" yalnızca gerçek ölçüm akarken gösterilir.
13. **Arayüzde uydurma yanıt yok (UI-2).** Arka uç LLM yanıt vermediğinde arayüz kendi Leyla yanıtını üretmez; "Şu anda yanıt veremiyorum" türünde bir hata gösterir. Doğrulanmamış başarı cümlesi ("…başarıyla iletilmiştir") hiçbir yerde istemci tarafında üretilmez.

## 6. Görevler

Her düzeltme ayrı commit'tir. Önce testi yaz (hatayı gösteren), sonra düzelt.

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| H01.01 | Hermetik test minimumu | torch içe aktarmasını tembelleştir; `gpu`/`llm`/`pbx` işaretlerini tanımla; `tests/fakes/fake_llm.py` ve conftest bağlantısı; canlı Ollama isteyen testleri sahteye geçir. | HF01, HF02 geçer |
| H01.02 | Karakterizasyon notu | Değiştirilecek her davranış için bugünkü davranışı gösteren testi yaz (düzeltme sonrası beklenen davranışla güncellenecek). | Her düzeltme görevinin "önce" testi var |
| H01.03 | Kimliksiz özel kayıt kapatma | Tasarım 2. Güvenli varsayılan + otomatik profil oluşturmanın kaldırılması; ADR-F3-01 taslağı plan reposuna. | HF03, HF04 geçer |
| H01.04 | Çoklu araç idempotency | Tasarım 3. Önce doğrula, sonra düzelt. | HF05 geçer |
| H01.05 | Bölüm iptalinin kaldırılması | Tasarım 5. | HF06 geçer |
| H01.06 | VAD oturum yalıtımı | Tasarım 4; ADR-F1-01. | HF07 geçer |
| H01.07 | Bloklamayan kalibrasyon | Tasarım 6. | HF08 geçer |
| H01.08 | Tek karakter yedek tablosu | Tasarım 7. | HF09 geçer |
| H01.09 | Sıra sayısı | Tasarım 8; F3 seçenek şablonu. | HF10 geçer |
| H01.10 | Seed düşürmelerinin kaldırılması | Tasarım 9. | HF11 geçer |
| H01.11 | İptal filtresi | Tasarım 10. | HF12 geçer |
| H01.12 | Ağ yazma zaman aşımı | Tasarım 11; okumayı durduran sahte istemciyle test. | HF13 geçer |
| H01.13 | Ölçülmemiş iddiaların temizlenmesi | Tasarım 12; `test_voice_path_honesty.py` kapsamının genişletilmesi. | HF14, HF15 geçer |
| H01.14 | Karşılamada yapay zekâ bildirimi | Yalnızca K-06 kabul edildiyse: karşılama şablonlarına kısa bildirim ("Ben Freya, yapay zekâ destekli randevu asistanıyım."); önbellek ısıtma listesinin güncellenmesi. | HF16 geçer veya görev DEFERRED |
| H01.15 | Arayüzde uydurma yanıtın kaldırılması | Tasarım 13. | HF17 geçer |
| H01.16 | Kapanış | Tüm test paketini `-m "not llm and not gpu and not pbx"` ile torch/Ollama olmadan çalıştır; GPU'lu makinede kısa duman testi (bir görüşme); sonuçları kanıta yaz. | H01-G00…G05 değerlendirilmiş |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| HF01 | Torch/CUDA/Ollama olmayan ortamda test toplama | Toplama hatası 0 |
| HF02 | `pytest -m "not llm and not gpu and not pbx"` | Tamamı geçer; canlı servis çağrısı 0 |
| HF03 | Doğrulanmamış arayan garanti/bakım geçmişi sorar | Özel içerik söylenmez; aktarım/şube önerisi |
| HF04 | Yeni arayan için arama başında profil oluşturulmaz | Profil tablosunda yeni satır yok |
| HF05 | İki araçlı randevu, iki ayrı onay; aynı onayın tekrarı | İki randevu oluşur; tekrar ikinci kayıt üretmez |
| HF06 | "Benim aracım" [450 ms] "2021 model Passat" | İki bölümün sözcükleri de F3'e ulaşır |
| HF07 | İki eşzamanlı oturum; birinde yeni görüşme başlar | Diğer oturumun VAD durumu değişmez |
| HF08 | Kalibrasyon sırasında söylenen cümle | STT çıktısında görünür |
| HF09 | "−5 °C", "Mégane", "Coupé", "Town & Country" | Seslendirilebilir metin; yanıt düşmez; atılan karakter olay olarak kayıtlı |
| HF10 | "1. seçenek 25 Kasım 10:00." | "Birinci seçenek yirmi beş Kasım saat on." tek parça; "Bir." parçası yok |
| HF11 | Profil seed'i 9 dışı (deney profili) veya `None` | Seed sessizce 9'a dönmez; değişim olay olarak kaydedilir |
| HF12 | Söz kesmeden sonra kuyruktaki eski generation öğeleri | Yığına alınmaz; sentez çağrısı yapılmaz |
| HF13 | Okumayı durduran sahte AudioSocket/WebSocket istemcisi | Zaman aşımında kontrollü kapanış; süresiz bekleme yok |
| HF14 | Kaynakta doğrulanmamış performans iddiası taraması | `batched_ode.py` ve arayüzde etiketsiz ölçüm iddiası yok |
| HF15 | Ses laboratuvarı ve kokpit ölçümsüz açılış | Sabit sayı yerine `—`; model adı FreyaTTS; süre gerçek örnekleme hızından |
| HF16 | Karşılama metni (K-06 kabul edildiyse) | Yapay zekâ bildirimi içerir; önbellekten çalınır |
| HF17 | Arka uç LLM hatası sırasında metin turu | Arayüz yanıt üretmez; hata mesajı gösterir |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| H01-G00 | Kapsam | Yalnızca §4'teki dosyalar değişti; yeni mimari dizini yok; değişiklik listesi kanıtta |
| H01-G01 | Hermetiklik | HF01, HF02 PASS (torch/CUDA/Ollama olmayan ortamda kanıtla) |
| H01-G02 | Güvenlik | HF03, HF04, HF05 PASS; doğrulanmamış arayana özel kayıt içeriği hiçbir yoldan söylenmiyor |
| H01-G03 | Canlı hat | HF06–HF13 PASS (DEFERRED olanlar gerekçeli) |
| H01-G04 | Ölçüm dürüstlüğü | HF14, HF15, HF17 PASS |
| H01-G05 | Regresyon | M00 `REGRESSION_MATRIX.csv` kapsamındaki mevcut testler geçiyor; yeni başarısızlık 0 |

## 9. Kanıt

`evidence/H01/<run_id>/`: `manifest.json` (commit, değişen dosyalar, çalıştırılan komutlar), `test-log.txt`, `decision.json` (kapı kararları), GPU duman testi notu (varsa).

## 10. Geri dönüş

Her düzeltme ayrı commit olduğu için tek tek geri alınabilir (`git revert <sha>`). Güvenlik düzeltmesi (H01.03) geri alınmamalıdır; sorun çıkarsa güvenli varsayılan korunarak düzeltilir.

## 11. Devir

- **M01** H01'in davranışlarını sözleşmelere taşır (ör. sıra sayısı kuralı F4-A'ya, idempotency M07'ye).
- **M08** H01.01'in hermetik altyapısını tam test altyapısına genişletir.
- **F1-A** H01.06'nın oturum başına VAD durumunu yeni `voice_activity` paketine taşır; **F1-B** H01.05'in minimal birleştirmesini Utterance Manager ile değiştirir.
- **F4-A** H01.08/H01.09'u tek normalizasyon otoritesine taşır.
- **F5-B** H01.10/H01.11'i seed yöneticisi ve yığın zamanlayıcısına taşır.

## 12. Başlatma komutu

```
H01 paketini uygula: docs/execution/packages/W0/H01-guvenli-zemin.md.
Kuralları CLAUDE.md'den oku; M00 kanıtındaki RISK_REGISTER.md'yi kontrol et.
Her düzeltmeyi mevcut dosyalarda en küçük değişiklikle, önce testini yazarak yap.
Yeni mimari dizini açma. Her görev ayrı commit; paket/H01 dalında PR aç.
Kapıları (H01-G00…G05) değerlendir ve dur.
```
