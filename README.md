# Silah Modu (Fabric, Minecraft 1.21.11)

8 ateşli silah, bıçak, medkit, 4 zırh (2 kask, 2 yelek) ve 3 sürülebilir araba ekler.

## Kurulum

1. Minecraft 1.21.11 için Fabric Loader (0.19.5 önerilir) kur.
2. Fabric API (1.21.11) ve bu modun `.jar` dosyasını `mods` klasörüne at.

`.jar` dosyasını GitHub'dan almak için: repo > **Actions** > son çalışma > **Artifacts**.

## Kontroller

| Tuş | İşlev |
|---|---|
| Sol tık | Ateş et (otomatik silahlarda basılı tut); bıçakla vur |
| **R** | Şarjör doldur |
| **B** | Silah menüsü (Creative'de "Silahlar" sekmesi de var) |
| Sağ tık (basılı tut) | Medkit kullan |

## Silahlar (1 kalp = 2 HP, oyuncu 20 HP)

| Silah | Mod | Şarjör / Yedek | Gövde | Kafa |
|---|---|---|---|---|
| Pistol | yarı-otomatik | 12 / 48 | 2,5 kalp | 7 kalp |
| Glock 17 | yarı-otomatik | 17 / 68 | 2 kalp | 5,5 kalp |
| M4A1-S (susturuculu) | otomatik | 20 / 80 | 2,5 kalp | 7 kalp |
| M4A4 | otomatik | 30 / 120 | 2,25 kalp | 6,5 kalp |
| AK-47 | otomatik | 30 / 120 | 3 kalp | 11 kalp (tek atışta öldürür) |
| AK-74M | otomatik | 30 / 120 | 2,5 kalp | 7,5 kalp |
| FN P90 | otomatik (~900/dk) | 50 / 150 | 1,5 kalp | 4 kalp |
| Kriss Vector | otomatik (~1200/dk) | 25 / 100 | 1,25 kalp | 3,5 kalp |

Silahların dayanıklılığı yoktur. Tüm değerler benim varsayımımdır; `src/main/java/com/silahmod/WeaponConfig.java`
içindeki `GunSpec` satırlarından değiştirilir (hasar, mermi, atış hızı, doldurma süresi, menzil, saçılma).

## Bıçak

Sol tıkla vurulur (bekleme 0,5 sn). Vuruşun nereye geldiğine göre hasar değişir:

| Vuruş | Hasar |
|---|---|
| Arkadan (hedefin sırtı sana dönükse, ~60° koni) | 200 HP (anında öldürür) |
| Önden kafa | 6 kalp (kask hasarı azaltmaz) |
| Önden gövde | 3 kalp (yelek hasarı azaltır) |

Değerler `WeaponConfig.java` içindeki `KNIFE_*` satırlarındadır. Menüde (B) Silahlar bölümünün sonunda yer alır.

## Zırhlar ve medkit

- **Kask 1:** 2 zırh, silahların kafa hasarını %25 azaltır. **Kask 2:** 6 zırh + 2 sertlik + Koruma II + 2 altın kalp.
- **Yelek 1 / 2:** gövde hasarını %15 / %30 azaltır.
- **Medkit:** basılı tutunca bandaj sarılır; can dolar ve 60 sn boyunca 10 geçici kalp verir.

## Arabalar

Üç araba: **Siyah Sedan**, **Zırhlı Skoda**, **Lamborghini**. Esyayi yere sağ tıklayarak koyarsın; araca sağ tıklayıp binersin.

| Tuş (arabadayken) | İşlev |
|---|---|
| **W** | Hızlanır (basılı tutulduğu sürece) |
| **S** | Yavaşlar / durunca geri gider |
| **A / D** | Sola / sağa döner (hız varken) |

- Can: **400 HP**. Bir yere çarpınca hıza oranla hasar alır. Vuruşlar da hasar verir.
- Her **150 hasarda** görünüm değişir (150+ hasarlı, 300+ ağır hasarlı): doku kararır, çatlar, bazı parçalar (tampon, bir teker) kopar.
- Can bitince TNT ile aynı güçte (4) patlar; **sadece yakındaki oyunculara** hasar verir, blok ve mobları etkilemez.
- Değerler `src/main/java/com/silahmod/car/CarEntity.java` içindeki sabitlerdedir (`MAX_HP`, `MAX_SPEED`, `CRASH_DAMAGE_PER_SPEED` vb.).
- Görseller `tools/gen_cars.py` ile üretilir (`python3 tools/gen_cars.py`).

## Derleme (kendi bilgisayarında)

Derleme aracı için JDK 25 gerekir (oyun Java 21 hedefiyle derlenir).

```
./gradlew build
```

Çıktı: `build/libs/silah-modu-1.0.0.jar` (`-sources` olmayan dosya).

## Modelleri yeniden üretme

Silah ve bıçak modelleri `tools/gen_models.py`, zırhlar ve medkit `tools/gen_armor.py`, arabalar `tools/gen_cars.py` ile üretilir.
`tools/preview.py` modellerin önizlemesini çizer (matplotlib gerekir).
