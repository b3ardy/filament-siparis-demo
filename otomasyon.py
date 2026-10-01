#!/usr/bin/env python3
"""Filament sipariş otomasyonu - tamamen simülasyon (gerçek pazaryeri/kargo yok)."""
import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent
SIPARIS_DOSYASI = KOK / "data" / "siparisler.json"
STOK_DOSYASI = KOK / "data" / "stok.json"
LOG_DOSYASI = KOK / "logs" / "bildirimler.log"

# Geçerli durum geçişleri: mevcut durum -> izin verilen sonraki durumlar
GECISLER = {
    "YENI": {"DEPOYA_BILDIRILDI", "YETERSIZ_STOK"},
    "DEPOYA_BILDIRILDI": {"TOPLANDI"},
    "TOPLANDI": {"PAKETLENDI"},
    "PAKETLENDI": {"KARGO_CAGRILDI"},
    "KARGO_CAGRILDI": {"KARGOYA_VERILDI"},
    "KARGOYA_VERILDI": set(),
    "YETERSIZ_STOK": set(),
}


def simdi():
    return datetime.now().isoformat(timespec="seconds")


def yukle(yol):
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def kaydet(yol, veri):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")


def bildir(alici, mesaj):
    """Bildirimi ekrana ve logs/bildirimler.log dosyasına yazar."""
    satir = f"[{simdi()}] [{alici}] {mesaj}"
    print(satir)
    LOG_DOSYASI.parent.mkdir(exist_ok=True)
    with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
        f.write(satir + "\n")


def gecis_yap(siparis, yeni_durum, not_=""):
    eski = siparis["durum"]
    if yeni_durum not in GECISLER[eski]:
        raise ValueError(
            f"{siparis['siparis_no']} şu an {eski} durumunda; {yeni_durum} durumuna geçilemez."
        )
    siparis["durum"] = yeni_durum
    siparis["gecmis"].append(
        {"zaman": simdi(), "kimden": eski, "kime": yeni_durum, "not": not_}
    )


def siparis_bul(siparisler, no):
    for s in siparisler:
        if s["siparis_no"] == no.upper():
            return s
    sys.exit(f"Hata: {no} numaralı sipariş bulunamadı.")


def komut_isle(siparisler, stok):
    yeniler = [s for s in siparisler if s["durum"] == "YENI"]
    if not yeniler:
        print("İşlenecek YENI sipariş yok.")
        return
    for s in yeniler:
        kayit = stok.get(s["sku"])
        mevcut = kayit["stok"] if kayit else 0
        if kayit and mevcut >= s["adet"]:
            kayit["stok"] -= s["adet"]  # stoğu rezerve et
            gecis_yap(s, "DEPOYA_BILDIRILDI", f"raf {kayit['raf']}")
            bildir(
                "DEPO",
                f"{s['siparis_no']}: Raf {kayit['raf']} -> {s['urun_adi']} "
                f"({s['sku']}) x {s['adet']} adet toplanacak.",
            )
        else:
            gecis_yap(s, "YETERSIZ_STOK", f"istenen {s['adet']}, mevcut {mevcut}")
            bildir(
                "YONETIM",
                f"{s['siparis_no']}: YETERSIZ STOK - {s['sku']} istenen {s['adet']}, "
                f"mevcut {mevcut}.",
            )


def komut_topla(siparisler, stok, no):
    s = siparis_bul(siparisler, no)
    gecis_yap(s, "TOPLANDI", "depocu onayı")
    bildir("PAKETCI", f"{s['siparis_no']}: Ürünler toplandı, paketlenebilir.")


def komut_paketle(siparisler, stok, no):
    s = siparis_bul(siparisler, no)
    gecis_yap(s, "PAKETLENDI", "paketçi onayı")
    # Kargo çağırma: sahte takip numarası burada üretilir
    s["takip_no"] = "TRK" + "".join(random.choices("0123456789", k=10))
    gecis_yap(s, "KARGO_CAGRILDI", f"takip no {s['takip_no']}")
    bildir(
        "KARGO",
        f"{s['siparis_no']}: Kargo çağrıldı. Takip no: {s['takip_no']} | "
        f"{s['musteri']}, {s['adres']}, {s['ilce']}/{s['il']}",
    )


def komut_kargola(siparisler, stok, no):
    s = siparis_bul(siparisler, no)
    gecis_yap(s, "KARGOYA_VERILDI", "kurye teslim aldı")
    bildir("MUSTERI", f"{s['siparis_no']}: Siparişiniz kargoya verildi. Takip no: {s['takip_no']}")


def komut_durum(siparisler, stok):
    print(f"{'SIPARIS':<10}{'DURUM':<19}{'SKU':<19}{'ADET':>4}  TAKIP")
    for s in siparisler:
        print(f"{s['siparis_no']:<10}{s['durum']:<19}{s['sku']:<19}{s['adet']:>4}  {s['takip_no'] or '-'}")
    print("\nStok:")
    for sku, k in stok.items():
        print(f"  {sku:<19}{k['stok']:>3} adet  raf {k['raf']}")


def main():
    p = argparse.ArgumentParser(description="Filament sipariş otomasyonu (simülasyon)")
    alt = p.add_subparsers(dest="komut")
    alt.add_parser("isle", help="YENI siparişleri işle (varsayılan)")
    alt.add_parser("durum", help="Sipariş ve stok özetini göster")
    for ad, yardim in (
        ("topla", "depocu toplama onayı"),
        ("paketle", "paketçi onayı + kargo çağır"),
        ("kargola", "kargoya teslim"),
    ):
        a = alt.add_parser(ad, help=yardim)
        a.add_argument("siparis_no", help="örn. SIP-1001")
    args = p.parse_args()

    siparisler, stok = yukle(SIPARIS_DOSYASI), yukle(STOK_DOSYASI)
    komut = args.komut or "isle"
    try:
        if komut == "isle":
            komut_isle(siparisler, stok)
        elif komut == "durum":
            komut_durum(siparisler, stok)
        else:
            {"topla": komut_topla, "paketle": komut_paketle, "kargola": komut_kargola}[komut](
                siparisler, stok, args.siparis_no
            )
    except ValueError as e:
        sys.exit(f"Hata: {e}")
    kaydet(SIPARIS_DOSYASI, siparisler)
    kaydet(STOK_DOSYASI, stok)


if __name__ == "__main__":
    main()
