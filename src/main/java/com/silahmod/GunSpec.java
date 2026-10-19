package com.silahmod;

/**
 * Bir ateşli silahın tüm sayıları. Yeni silah eklemek = WeaponConfig'e bir GunSpec yazmak + ModItems'a kaydetmek.
 *
 * @param mag         şarjör kapasitesi
 * @param reserve     yedek mermi
 * @param fireDelay   iki atış arası süre (tick). 20 tick = 1 sn. Küsurat olabilir: 1.33 = dakikada 900 atış.
 *                    Dakikadaki atış (RPM) = 1200 / fireDelay
 * @param reloadTicks şarjör doldurma süresi (tick)
 * @param body        gövde hasarı (HP; 1 kalp = 2 HP)
 * @param head        kafa hasarı (HP)
 * @param range       menzil (blok)
 * @param spread      saçılma açısı (derece). 0 = nokta atışı
 * @param automatic   true: sol tık basılı tutulunca sürekli ateş eder; false: her tık tek atış
 * @param sound       atış sesi (vanilla ses adı)
 * @param volume      ses şiddeti
 * @param pitch       ses perdesi
 */
public record GunSpec(int mag, int reserve, float fireDelay, int reloadTicks,
		float body, float head, double range, float spread, boolean automatic,
		String sound, float volume, float pitch) {
}
