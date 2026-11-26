# ADR-F1-01 — Silero VAD oturum yalıtımı

| Alan | Değer |
| --- | --- |
| Durum | Taslak / Ölçüm bekleniyor |
| Sahibi olan görev | H01.06 (HF07); F1-A devri |
| Tarih | 2026-11-26 |
| Karar veren | Ürün sahibi (bekliyor) |

## Bağlam

[M00 RISK-0005](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC/blob/paket/M00/evidence/M00/20261126-0133-6f5867a/RISK_REGISTER.md) paylaşılan VAD modelinin yeni oturumda sıfırlandığını statik olarak doğrular. `VoiceSession.__init__` her çağrıda `models.vad.reset_states()` çalıştırıyor; `Endpoint.feed` aynı modelle 512 örneklik 16 kHz bloklar işliyor. Bağımsız Endpoint tamponları modelin iç durumunu ayırmıyor. Aynı anda iki oturum birbirinin konuşma/sessizlik kararını etkileyebilir.

Kilitli sürüm `silero-vad==6.2.3`; mevcut yükleme `load_silero_vad()` (JIT varsayılanı). [Sürümün ONNX sarmalayıcısı](https://github.com/snakers4/silero-vad/blob/v6.2.3/src/silero_vad/utils_vad.py) durum, bağlam, son örnekleme hızı ve batch boyutu taşır; bu alanların JIT yapıtında aynı isimlerle ve yazılabilir durumda olduğu **doğrulanmış değildir**. ONNX sınıfından JIT sözleşmesi çıkarılmayacaktır.

## Seçenekler

| Seçenek | Açıklama | Artı | Eksi |
| --- | --- | --- | --- |
| A | Oturum başına bağımsız model örneği | İç durum doğal olarak ayrı | Bellek/başlatma maliyeti ölçülmeli; model kopyalama yeteneği doğrulanmalı |
| B | Bir model ağırlığı, oturum başına durum/bağlam; erişim sırasında kilitli durum değişimi | Ağırlık tekrarı yok, planın varsayılan tercihi | JIT durum API'si doğrulanmalı; değişim atomik, istisna güvenli ve kopyasız referans sızıntısından arındırılmış olmalı |

## Ölçüm ve kabul protokolü

1. Kullanıcının mevcut yerel modelini ve kilitli sürümü kullan; paket/model indirme, ses kaydı veya gerçek SIP yok.
2. JIT nesnesinin gerçek durum API'sini, cihaz/dtype/şekilleri ve reset davranışını incele. Desteklenmeyen iç alanlarla sessizce devam etme.
3. A ve B adaylarında deterministik 16 kHz PCM bloklarıyla tek oturum referansını al. İki oturumu A1,B1,A2,B2 biçiminde sırala; B açılışı A'nın durumunu/çıktısını değiştirmemeli. Farklı sırayla ve eşzamanlı iş parçacıklarıyla tekrarla. HF07 için izole ve ardışık çıktıları karşılaştır; hatada durum geri yüklenmeli.
4. Her seçenek için CPU RSS artışı, oturum başlatma gecikmesi ve blok p50/p95/p99, n ve hata sayısı; model cihazı/dtype; 1/2/8/16 oturum. Gerçek model yoksa sonuçlar null, sınıf SYNTHETIC_FIXTURE yalnız sahte testler için.
5. Çıktı: `evidence/H01/<run_id>/vad-isolation.json` ve HF07 ham günlük. Gerçek ölçüm şu an yapılmadı.

| Ölçüm | A | B |
| --- | --- | --- |
| RSS farkı | Ölçülmedi | Ölçülmedi |
| Blok p95 | Ölçülmedi | Ölçülmedi |
| HF07 gerçek Silero | NOT_RUN | NOT_RUN |

## Önerilen karar (onay bekliyor)

B, gerçek JIT durum sözleşmesi ve yalıtım kanıtı uygunsa seçilir. A ancak bellek bütçesi ve model kopyalama doğrulanırsa alternatif olabilir. Ölçüm ve onay olmadan H01-G03 PASS veya üretime hazır iddiası yok. Mevcut paylaşılan reset riskine geçici çözüm olarak oturum sayısı kısıtlaması ayrı kullanıcı kararıdır; bu ADR ile uygulanmaz.

## Sonuçlar

H01.06 ve F1-A, seçilen durum yaşam döngüsünü korur. Yeni paket dizini H01'de açılmaz; plan değişiklikleri ayrı PR. HF07 regresyonu başarısız olursa aday geri alınır ve güvenli kapasite politikası değerlendirilir.
