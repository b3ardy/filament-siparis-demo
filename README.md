# Filament Sipariş Otomasyonu (Simülasyon)

Hayali bir filament satıcısının sipariş sürecini otomatikleştirmeyi öğrenmek için hazırlanmış küçük bir proje.
**Gerçek pazaryeri veya kargo bağlantısı yoktur; müşteriler, adresler, telefonlar ve takip numaraları tamamen uydurmadır.**

Yalnızca Python 3 standart kütüphanesi kullanılır, kurulum gerekmez.

## Dosyalar

| Dosya | Açıklama |
|---|---|
| `otomasyon.py` | Ana betik (komutlar aşağıda) |
| `data/siparisler.json` | 15 sahte sipariş (durum ve zaman damgalı geçmiş burada tutulur) |
| `data/stok.json` | SKU başına stok adedi ve depo raf konumu |
| `logs/bildirimler.log` | Üretilen bildirimlerin kaydı (git'e eklenmez) |

SKU formatı: `ÜRÜN-ÇAP-RENK-AĞIRLIK`, örn. `PLA-175-SIY-1KG` (PLA, 1.75 mm, siyah, 1 kg). Ürünler: PLA, PETG, ABS, TPU.

## Çalıştırma

```bash
python otomasyon.py isle            # YENI siparişleri işle (komutsuz çalıştırmak da aynıdır)
python otomasyon.py durum           # sipariş ve stok özeti
python otomasyon.py topla SIP-1001  # depocu "topladım" onayı
python otomasyon.py paketle SIP-1001  # paketçi onayı; ardından kargo çağrılır, takip no üretilir
python otomasyon.py kargola SIP-1001  # kurye teslim aldı
```

Bildirimler hem ekrana hem `logs/bildirimler.log` dosyasına yazılır.

## Durum akışı

```
YENI → DEPOYA_BILDIRILDI → TOPLANDI → PAKETLENDI → KARGO_CAGRILDI → KARGOYA_VERILDI
  └──→ YETERSIZ_STOK   (stok yoksa)
```

- `isle`: Stok yeterliyse stok rezerve edilir (düşülür), depocuya raf/ürün/adet içeren mesaj gider ve sipariş `DEPOYA_BILDIRILDI` olur. Yetersizse `YETERSIZ_STOK` olur ve yönetime bildirim gider.
- `topla`: `DEPOYA_BILDIRILDI` → `TOPLANDI`.
- `paketle`: `TOPLANDI` → `PAKETLENDI`, ardından kargo çağrılır (`KARGO_CAGRILDI`) ve sahte takip numarası (`TRK` + 10 hane) oluşturulur.
- `kargola`: `KARGO_CAGRILDI` → `KARGOYA_VERILDI`.
- Her geçiş, siparişin `gecmis` alanına zaman damgasıyla kaydedilir. Sıra dışı geçiş denenirse (örn. toplanmamış siparişi paketlemek) hata verilir.

Örnek verilerde birkaç ürünün stoğu bilerek yetersizdir (örn. `PETG-175-MAV-1KG` stoğu 0); böylece `YETERSIZ_STOK` durumu da denenebilir.

## Sıfırlama

Betik `data/*.json` dosyalarını günceller. Başa dönmek için:

```bash
git checkout data/ && rm -f logs/bildirimler.log
```
