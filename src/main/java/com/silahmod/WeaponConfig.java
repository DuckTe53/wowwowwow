package com.silahmod;

/**
 * Tum ayarlar burada. Sayilari degistirip tekrar derlemen yeterli.
 *
 * Hasar birimi: HP. 1 kalp = 2 HP (5 kalp = 10 HP). Oyuncunun cani 20 HP (10 kalp).
 * Sure birimi: tick. 20 tick = 1 saniye.
 *
 * NOT: Silahlarin sayilarini (hasar, mermi, atis hizi...) sen belirtmedigin icin benim varsayimimdir.
 * Hepsi asagidaki GunSpec satirlarinda; istedigin gibi degistir.
 */
public final class WeaponConfig {
	private WeaponConfig() {}

	public static float hearts(float hearts) {
		return hearts * 2.0F;
	}

	// ---------------- SILAHLAR ----------------
	/** Reload animasyonunun kare sayisi. tools/gen_models.py'deki kare sayisiyla ayni olmali. */
	public static final int RELOAD_FRAMES = 5;

	//                                          mag res  delay reload body head range spread auto   ses                              vol  pitch
	/** Pistol: agir vuran, yavas yari-otomatik. */
	public static final GunSpec PISTOL = new GunSpec(12, 48, 4.0F, 40, 5.0F, 14.0F, 100.0, 0.2F, false,
			"entity.firework_rocket.blast", 2.5F, 1.2F);

	/** Glock 17: hafif, hizli tiklanir, 17'lik sarjor. */
	public static final GunSpec GLOCK_17 = new GunSpec(17, 68, 3.0F, 36, 4.0F, 11.0F, 90.0, 0.3F, false,
			"entity.firework_rocket.blast", 2.5F, 1.5F);

	/** M4A1-S: susturuculu, isabetli, yavas atar. */
	public static final GunSpec M4A1_S = new GunSpec(20, 80, 3.0F, 50, 5.0F, 14.0F, 160.0, 0.4F, true,
			"entity.firework_rocket.shoot", 1.2F, 1.6F);

	/** M4A4: hizli ve dengeli. */
	public static final GunSpec M4A4 = new GunSpec(30, 120, 2.0F, 56, 4.5F, 13.0F, 160.0, 0.8F, true,
			"entity.firework_rocket.blast", 2.5F, 0.9F);

	/** AK-47: en sert vuran tufek, kafadan tek atista oldurur, geri tepmesi (sacilma) yuksek. */
	public static final GunSpec AK_47 = new GunSpec(30, 120, 2.0F, 60, 6.0F, 22.0F, 150.0, 1.0F, true,
			"entity.firework_rocket.blast", 3.0F, 0.7F);

	/** AK-74M: AK-47'den hafif, daha kontrollu. */
	public static final GunSpec AK_74M = new GunSpec(30, 120, 2.0F, 56, 5.0F, 15.0F, 150.0, 0.7F, true,
			"entity.firework_rocket.blast", 2.8F, 0.85F);

	/** FN P90: 50'lik sarjor, cok hizli, dusuk hasar, kisa menzil. 1.33 tick = ~900 atis/dk. */
	public static final GunSpec P90 = new GunSpec(50, 150, 1.33F, 64, 3.0F, 8.0F, 90.0, 1.1F, true,
			"entity.firework_rocket.blast", 2.0F, 1.3F);

	/** Kriss Vector: en hizli (1200 atis/dk), cok dusuk hasar, kisa menzil. */
	public static final GunSpec KRISS_VECTOR = new GunSpec(25, 100, 1.0F, 44, 2.5F, 7.0F, 80.0, 1.2F, true,
			"entity.firework_rocket.blast", 2.0F, 1.4F);

	// ---------------- ZIRHLAR ----------------
	// Kask 1 (yesil): demir kask gibi (2 zirh) + KAFA vuruslarinin hasarini azaltir. Azaltma orani benim varsayimim.
	public static final double HELMET_1_ARMOR = 2.0;
	public static final double HELMET_1_TOUGHNESS = 0.0;
	public static final float HELMET_1_HEAD_REDUCTION = 0.25F;       // silah kafa hasari %25 azalir (0 = etkisiz)

	// Yelek 1 (gri kamuflaj): tum silahlarin govde hasarini azaltir
	public static final float VEST_1_BODY_REDUCTION = 0.15F;         // %15

	// Kask 2 (koyu, siperlikli): Koruma II buyulu elmas pantolon gibi (6 zirh, 2 sertlik, Koruma II) + altin kalp
	public static final double HELMET_2_ARMOR = 6.0;
	public static final double HELMET_2_TOUGHNESS = 2.0;
	public static final int HELMET_2_PROTECTION_LEVEL = 2;           // Koruma buyusu seviyesi
	public static final int HELMET_2_GOLD_HEARTS = 2;                // giyince verilen altin kalp

	// Yelek 2 (kahverengi): tum silahlarin govde hasarini azaltir
	public static final float VEST_2_BODY_REDUCTION = 0.30F;         // %30

	// ---------------- MEDKIT ----------------
	public static final int MEDKIT_USE_TICKS = 80;          // bandaj sarma suresi (20 tick = 1 sn) -> 4 sn
	public static final int MEDKIT_ABSORB_HEARTS = 10;      // gecici sari kalp (10 kalp = 20 can)
	public static final int MEDKIT_ABSORB_TICKS = 1200;     // sari kalplerin suresi -> 60 sn
	public static final int MEDKIT_MENU_GIVE = 2;           // menuden alinca kac adet verilir

	// ---------------- BICAK ----------------
	public static final float KNIFE_BACKSTAB = 200.0F;     // arkadan
	public static final float KNIFE_FRONT = hearts(3);     // onden govde = 6 HP
	public static final float KNIFE_HEAD = hearts(6);      // onden kafa = 12 HP
	public static final int KNIFE_COOLDOWN = 10;
	/** Hedefin arkasindan sayilma acisi: 0.5 = yaklasik 60 derece koni. */
	public static final double KNIFE_BACK_DOT = 0.5;
}
