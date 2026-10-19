package com.silahmod.client;

import com.silahmod.AmmoData;
import com.silahmod.item.GunItem;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.world.item.ItemStack;

/** Ekranin sag altinda "sarjor / yedek" mermi sayaci. */
public final class AmmoOverlay {
	private AmmoOverlay() {}

	private static final int RED = 0xFFFF2020;
	private static final int WHITE = 0xFFFFFFFF;

	public static void renderAmmo(GuiGraphics graphics, DeltaTracker tickCounter) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || mc.options.hideGui) {
			return;
		}
		ItemStack stack = mc.player.getMainHandItem();
		if (!(stack.getItem() instanceof GunItem gun)) {
			return;
		}
		AmmoData ammo = gun.ammo(stack);
		String text = ammo.mag() + " / " + ammo.reserve();
		int x = graphics.guiWidth() - mc.font.width(text) - 10;
		int y = graphics.guiHeight() - 24;
		graphics.drawString(mc.font, text, x, y, ammo.mag() == 0 ? RED : WHITE);
	}
}
