# Veri kümeleri

Her veri kümesi PoC reposunda `data/<aşama>/` altında, bir **veri kümesi bildirimiyle** (`DATASHEET.md`) birlikte tutulur.

## 1. Envanter

| Küme | Aşama / görev | İçerik | Bölünme | Kişisel veri |
| --- | --- | --- | --- | --- |
| F0 test derlemi | F0-T03 | Temiz konuşma + kabin/rüzgâr/fan gürültüsü, SNR seviyeleri, yankı | Kalibrasyon / test | Sentetik veya rızalı |
| F0 gerçek koşul kayıtları | F0-T33 | Araç içi gerçek mikrofon | Test | **Rıza gerekli** |
| F1 etiketli derlem | F1-T02 | Konuşma başlangıç/bitiş etiketleri, backchannel, söz kesme, düşünme duraklamaları | Kalibrasyon / test | Sentetik + rızalı |
| F1 gerçek konuşma | F1-T29 | Gerçek kullanıcılar | Test | **Rıza gerekli** |
| F2 metin hattı | F2-T30 | Ham transkript → beklenen kanonik çıktı çiftleri | Kalibrasyon / test (F2-T33) | Yok |
| F2 akustik sentetik | F2-T31 | Otomotiv terim cümleleri, gürültü karışımları | Kalibrasyon / test | Yok |
| F2 insan sesi | F2-T36 | Farklı konuşmacılar, aksanlar, telefon bandı | Test | **Rıza gerekli** |
| F3 senaryo kümesi | F3-T40 | 2 000 diyalog senaryosu (niyet, slot, çoklu niyet, güvenlik) | Eğitim / kalibrasyon / test | Sentetik kişiler |
| F4 dilbilim kümesi | F4-T30 | 3 000 metin: sayı, para, tarih, saat, plaka, telefon, marka, kısaltma | Test | Sentetik |
| F5 sentez kümesi | F5-T28 | 2 000 girdi (F4 planlarından) | Kalibrasyon / test | Yok |
| Leyla referans kümesi | F5-T05 | Onaylı Leyla örnekleri (seed 9) | Referans — değiştirilmez | Yok |
| F6 sentetik görüşmeler | F6-T28 | Uçtan uca senaryolar | Test | Sentetik |
| PoC mevcut | `docs/POC_SOHBET_512.jsonl`, `data/fixtures/legacy_320_cases.json`, `FreyaTTS_Otomotiv_Turkce_Telaffuz_Sezer_ve_Test_Cumleleri.xlsx` | Sohbet örnekleri, eski test vakaları, telaffuz test cümleleri | Taban | Kontrol edilecek |

## 2. Kurallar

1. **Kalibrasyon ve test kümesi karışmaz.** Test kümesi yalnızca son ölçümde kullanılır; görüldükten sonra ayar yapılırsa yeni test kümesi gerekir.
2. **Sürüm:** Her küme `version` taşır; laboratuvar raporu küme adını, sürümünü ve bölünmesini yazar.
3. **Kişisel veri:** Gerçek müşteri veya gönüllü sesi yalnızca açık rıza ile; rıza kaydı bildirimde; saklama süresi `kvkk_compliance` kurallarıyla ([security-and-privacy](../cross-cutting/security-and-privacy.md)).
4. **Sentetik kişiler:** F3 senaryolarında gerçek ad, telefon veya plaka kullanılmaz; üreteç geçerli biçimde ama gerçek olmayan değerler üretir.
5. **Lisans:** Dış kaynaklı ses veya metin (RAG belgeleri dahil) lisansıyla kaydedilir (F3-T20).
6. **Bildirim şablonu (`DATASHEET.md`):** amaç, içerik, üretim yöntemi, etiketleme yöntemi ve kim etiketledi, bölünme, bilinen eksikler, kişisel veri ve rıza durumu, lisans, sürüm geçmişi.
