package com.silahmod.client;

import com.silahmod.ModItems;
import com.silahmod.WeaponConfig;
import com.silahmod.item.MedkitItem;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.item.ItemStack;

/**
 * Medkit kullanilirken ekranin sag altinda, OYUNCUNUN KENDI SKININDEKI kolun (Steve = 4 piksel, Alex = 3 piksel
 * genislik otomatik secilir) bandajla sarilma animasyonunu cizer. Elde tutulan medkit modeli bu sirada gizlenir
 * (assets/silahmod/items/medkit.json).
 *
 * Kol, skin dokusundan (sag kol on yuzu + ust katman) kesilip buyutulerek cizilir; bandaj seritleri kolun
 * bilekten dirsege dogru ilerleyen yuzdesine gore eklenir.
 */
public final class MedkitOverlay {
	private MedkitOverlay() {}

	private static long startMs = -1L;

	private static boolean isHealing(Minecraft mc) {
		return mc.player != null
				&& mc.options.getCameraType().isFirstPerson()
				&& mc.player.isUsingItem()
				&& mc.player.getUseItem().getItem() instanceof MedkitItem;
	}

	public static void render(GuiGraphics graphics, DeltaTracker tickCounter) {
		Minecraft mc = Minecraft.getInstance();
		if (!isHealing(mc)) {
			startMs = -1L;
			return;
		}
		long now = System.currentTimeMillis();
		if (startMs < 0L) {
			startMs = now;
		}
		float total = WeaponConfig.MEDKIT_USE_TICKS * 50.0F;           // ms
		float p = Math.min(1.0F, (now - startMs) / total);             // 0..1 ilerleme
		float t = (now - startMs) / 1000.0F;

		var skin = mc.player.getSkin();
		var texture = skin.body().texturePath();
		boolean slim = skin.model() == PlayerModelType.SLIM;
		int armW = slim ? 3 : 4;                                        // skin pikseli cinsinden kol genisligi

		int w = graphics.guiWidth();
		int h = graphics.guiHeight();
		float s = h * 0.40F / 12.0F;                                    // 1 skin pikseli = s ekran pikseli (kol boyu ekranin %40'i)

		// Kol alttan yukari kayarak gelir (ilk %12'de)
		float rise = Math.min(1.0F, p / 0.12F);
		rise = 1.0F - (1.0F - rise) * (1.0F - rise);
		float baseX = w * 0.70F;
		float baseY = h + s * 3.0F - (s * 12.0F * 0.55F) * rise;
		float tilt = 0.30F + 0.035F * (float) Math.sin(t * 9.0F);       // sarma hareketi: hafif salinim

		// ---- Medkit: kolun solunda, hafifce sallanir ----
		graphics.pose().pushMatrix();
		graphics.pose().translate(baseX - s * 15.0F, baseY - s * 12.5F + 3.0F * (float) Math.sin(t * 4.0F));
		graphics.pose().scale(s * 0.55F, s * 0.55F);
		graphics.renderItem(new ItemStack(ModItems.MEDKIT), 0, 0);
		graphics.pose().popMatrix();

		// ---- Kol (skin dokusundan) ----
		graphics.pose().pushMatrix();
		graphics.pose().translate(baseX, baseY);
		graphics.pose().rotate(tilt);
		graphics.pose().rotate((float) Math.PI);                        // el yukari baksin
		graphics.pose().translate(-armW * s / 2.0F, 0.0F);
		graphics.pose().scale(s, s);
		graphics.blit(RenderPipelines.GUI_TEXTURED, texture, 0, 0, 44.0F, 20.0F, armW, 12, 64, 64);   // kol
		graphics.blit(RenderPipelines.GUI_TEXTURED, texture, 0, 0, 44.0F, 36.0F, armW, 12, 64, 64);   // kol ust katmani (kol)
		graphics.pose().popMatrix();

		// ---- Bandaj: ayni donusumde, 4 kat ince cozunurlukle (kol 12 piksel = 48 birim) ----
		graphics.pose().pushMatrix();
		graphics.pose().translate(baseX, baseY);
		graphics.pose().rotate(tilt);
		graphics.pose().rotate((float) Math.PI);
		graphics.pose().translate(-armW * s / 2.0F, 0.0F);
		graphics.pose().scale(s / 4.0F, s / 4.0F);
		int aw = armW * 4;
		int strips = (int) (p * 13.0F);                                 // en fazla 13 serit
		for (int k = 0; k < strips && k < 13; k++) {
			int y2 = 46 - k * 3;                                        // bilekten (46) dirsege dogru
			int y1 = y2 - 3;
			int shade = (k % 2 == 0) ? 0xFFF4F4F4 : 0xFFD9D9D9;
			// capraz sarilma gorunumu: sol yarisi 1 birim yukarida
			graphics.fill(-1, y1 - 1, aw / 2, y2 - 1, shade);
			graphics.fill(aw / 2, y1, aw + 1, y2, shade);
		}
		if (p >= 0.95F) {                                               // bitince kirmizi hacli yama
			int cx = aw / 2;
			int cy = 46 - 13 * 3 / 2;
			graphics.fill(cx - 5, cy - 5, cx + 5, cy + 5, 0xFFF4F4F4);
			graphics.fill(cx - 4, cy - 1, cx + 4, cy + 1, 0xFFD92A1E);
			graphics.fill(cx - 1, cy - 4, cx + 1, cy + 4, 0xFFD92A1E);
		}
		graphics.pose().popMatrix();

		// ---- Ilerleme cubugu (crosshair'in altinda) ----
		int bw = 80;
		int bx = w / 2 - bw / 2;
		int by = h / 2 + 22;
		graphics.fill(bx - 1, by - 1, bx + bw + 1, by + 4, 0xAA000000);
		graphics.fill(bx, by, bx + (int) (bw * p), by + 3, 0xFFD92A1E);
	}
}
