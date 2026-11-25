# G2 — Özellik entegrasyon incelemesi

> W0–W4'teki tüm zorunlu paketler yapısal olarak kabul edildikten sonra, sistem **bir bütün olarak** incelenir: güncel CG/WG geçerliliği, etkilenen entegre testlerin yeniden çalıştırılması, M00 özellik envanterinin kapanışı (her özellik korunmuş veya gerekçeli karar almış), entegrasyon risklerinin kapanışı, bayrak kiplerinin (OFF/SHADOW/GUARDED) güvenli davranışı. G2 kabulü arayüz (G3) için ön koşuldur ama G3'ü kendiliğinden başlatmaz.

| Alan | Değer |
| --- | --- |
| Kimlik | G2 |
| Dalga | Ürün aşaması |
| Öncelik | P0 |
| Önkoşullar | F1-C, F3-C, F5-C, F6-C |
| Sonraki | G3 |
| Bayrak | Yeni bayrak yok; tüm paket bayrakları ve M03 profilleri OFF/SHADOW/GUARDED kiplerinde doğrulanır; canlı varsayılan değişmez |
| Ortam | CPU; sahte modeller ve sağlayıcılar; yalıtılmış test DB'si (MOS, gerçek SIP veya eğitim gerekmez) |
| Eski görevler | — (aşama sonu entegrasyon; eski planda her aşamanın regresyon sprinti: F0-S10, F1-S13, F2-S18, F3-S24, F4-S22, F5-S24, F6-S26) |
| Kaynak | Bundle `00_START_HERE/Freya_2_0_Master_Agent_Orchestrator.md` §J; `04_GOVERNANCE/UNIFIED_EXECUTION_POLICY.md`; [risk kaydı](../risks.md) |
| Durum | NOT_RUN |

## 1. Amaç

Her paket kendi kapısını geçmiş olabilir; ama paketler aynı dosyalara (`session.py`, `models.py`, `audio.py`, Supervisor, DB, aktarım, yapılandırma) dokunduğu için birlikte bozulabilirler. G2; mevcut hiçbir özelliğin sessizce kaybolmadığını, eski API/UI/DB davranışının korunduğunu, tek sahipli rotaların ve güvenli geri düşmelerin gerçekten çalıştığını tek bir bağımsız incelemeyle doğrular.

## 2. Başlamadan önce

- [ ] Doğrudan önkoşullar (F1-C, F3-C, F5-C, F6-C) zorunlu W0–W4 zincirinin uç noktalarıdır; zincirdeki tüm zorunlu paketlerin `decision.json` dosyası `PASS` ve bağımsız gözden geçiren onaylı.
- [ ] CORE_GATE ve W2_GATE kararları güncel soya göre hâlâ geçerli (sonradan değişen kaynaklar için etkilenen kapılar yeniden çalıştırılmış).
- [ ] İsteğe bağlı paketlerin kapsam kararı yazılı: F6-D (ertelendi veya yapısal kabul), F5-D (G2 paydasından **hariç**).
- [ ] Kullanıcı G2'yi başlattı ("G2 aşamasını başlat").

## 3. Kapsam

**Yapılacak:** soy ve kanıt uzlaştırma; tam regresyon; M00 özellik kapanışı; entegrasyon risklerinin kapanışı; kip ve geri dönüş doğrulaması; bilinen baz hataların ayrı kaydı; bağımsız inceleme.

**Yapılmayacak:** yeni özellik; bayrak varsayılanını canlıda açma; gerçek model performans iddiası (G4); insan/SIP (G5); F5-D eğitimi.

## 4. Dosyalar

```
tests/                      mevcut ve paketlerin eklediği tüm testler
evidence/G2/<run_id>/       manifest.json, test-log.txt, decision.json ve aşağıdaki raporlar
```

Kaynak kod değişikliği yalnız bulunan kusurun sahibi pakette, o paketin dalında yapılır; G2 dalı yalnız kanıt ekler.

## 5. Tasarım ve sözleşmeler

### 5.1 Zorunlu paket kümesi

W0: M00, H01 · W1: M01–M08, CORE_GATE · W2: F0-A, F1-A, F2-A, F3-A, F4-A, F5-A, F6-A, W2_GATE · W3: F1-B, F6-B, F2-B, F3-B, F4-B, F5-B · W4: F0-B, F2-C, F1-C, F3-C, F4-C, F5-C, F6-C.

İsteğe bağlı: F6-D (dahil edilirse yapısal kapıları doğrulanır, yerel etkinleştirme G4/G5'e kadar kapalı). Araştırma: F5-D (G2 paydasında yok).

### 5.2 Bilinen baz hatalar

M00'da kaydedilmiş, nesnel olarak değişmemiş, incelenmiş ve kapsam içinde engelleyici olmayan baz hatalar ayrı listede taşınabilir. Yeni kritik regresyon veya güvensiz yol etkinleşmesi G2'yi engeller.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| G2.01 | Soy ve kanıt uzlaştırma | Zorunlu her paketin kabul edilmiş çalıştırma kimliği, commit'i ve kanıt hash'leri; sonradan değişen kaynaklar için etkilenen kapılar | `LINEAGE.json`; eksik/uyuşmaz kanıt yok |
| G2.02 | Tam regresyon | `pytest tests/ experimental/tests/ -q -m "not llm and not gpu and not pbx"` + tüm paket testleri + CI01–CI24 + WI01–WI24 + M00 bulunmuş regresyonlar | `REGRESSION.json`; yeni başarısızlık yok |
| G2.03 | M00 özellik kapanışı | Her M00 özellik kimliği: korundu (testle), taşındı (uyumluluk adaptörü + testle) veya gerekçeli karar; sessiz silme yok | `FEATURE_CLOSURE.json` |
| G2.04 | Eski arayüz uyumluluğu | Mevcut API rotaları, DB şeması/verisi, UI rotaları ve yapılandırma anahtarları eski davranışla | `COMPATIBILITY.md` |
| G2.05 | Kip ve geri dönüş doğrulaması | Her bayrak/profil için OFF = PoC davranışı, SHADOW = yan etkisiz, GUARDED = yetkili; her paketin geri dönüş yolu denenmiş | `MODES_ROLLBACK.json` |
| G2.06 | Entegrasyon risklerinin kapanışı | [risks.md](../risks.md) IR01–IR48 ve CS01–CS18: her zorunlu risk için çözüm kanıtı veya incelenmiş kabul | `RISK_CLOSURE.md` |
| G2.07 | Güvenlik değişmezleri | Tek sahipli rotalar; yetkisiz mutasyon yok; bayat çıktı yok; yinelenen işlem yok; güvenli kaynak hatası; ikinci ağır model yok; seed 9 | `INVARIANTS.json` |
| G2.08 | Bağımsız inceleme ve durma | G2-K01…K08 değerlendirilir; karar; G3'ten önce dur | `decision.json` |

## 7. Testler

G2 yeni test kimliği tanımlamaz. Çalıştırılan: mevcut PoC testleri, tüm zorunlu paketlerin testleri (CT, RT, CR, OB, LX, GPU, SEC, TH, HF, AI, VA, AS, DF, LN, NS, AR, BI, PB, AE, MI, MG, RQ, AD, PS, SC, RW, PC, OS, DC aileleri), CI01–CI24, WI01–WI24 ve M00'da bulunmuş numarasız regresyonlar. Her vaka benzersiz kimlikle bir kez sayılır; yeniden çalıştırmalar ayrı satırdır.

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| G2-K01 | Paket kabulleri | Zorunlu tüm paketler bağımsız onaylı `PASS`; isteğe bağlı kapsam kararı yazılı |
| G2-K02 | Çekirdek ve dikey dilim | CG00–CG11 ve WG00–WG11 güncel soyda geçerli |
| G2-K03 | Regresyon | Tam regresyon yeşil; yalnız incelenmiş değişmemiş baz hatalar ayrı listede |
| G2-K04 | Özellik kapanışı | Her M00 özellik kimliği karara bağlı; sessiz silme yok |
| G2-K05 | Uyumluluk | API/DB/UI/yapılandırma geri uyumlu veya incelenmiş uyumluluk adaptörlü |
| G2-K06 | Kipler ve geri dönüş | OFF/SHADOW/GUARDED davranışı ve her paketin geri dönüşü kanıtlı |
| G2-K07 | Riskler ve değişmezler | Zorunlu IR/CS riskleri kapalı; güvenlik değişmezleri ihlalsiz |
| G2-K08 | Bağımsız karar | Yazar olmayan gözden geçiren kanıtı denetledi; G3 kullanıcı tarafından ayrıca başlatılır |

## 9. Kanıt

`evidence/G2/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `LINEAGE.json`, `REGRESSION.json`, `FEATURE_CLOSURE.json`, `COMPATIBILITY.md`, `MODES_ROLLBACK.json`, `RISK_CLOSURE.md`, `INVARIANTS.json`, `KNOWN_BASELINE_FAILURES.md`.

## 10. Geri dönüş

G2 kod değiştirmez. Bulunan kusur sahibi pakete döner; o paket yeniden kabul edilince etkilenen G2 kontrolleri yeniden çalıştırılır.

## 11. Devir

- **G3:** kabul edilmiş soy, `FEATURE_CLOSURE.json` (arayüz eşlemesinin girdisi), yetenek ve yetki envanteri.

## 12. Başlatma komutu

```
G2 aşamasını uygula: docs/execution/stages/G2-entegrasyon.md.
Kuralları CLAUDE.md'den oku; zorunlu tüm paketlerin kabul kanıtını ve CG/WG güncelliğini doğrula; biri eksikse dur.
Tam regresyonu, M00 özellik kapanışını, uyumluluk, kip/geri dönüş ve risk kapanışı kontrollerini yap; kaynak kodu değiştirme.
G2-K01…K08'i değerlendir, asama/G2 dalında yalnız kanıtla PR aç ve dur (G3'ü başlatma).
```
