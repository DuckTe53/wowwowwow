package com.silahmod.client;

import com.silahmod.ModItems;
import com.silahmod.Net;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * B tusuyla acilan menu. Iki sutun silahlar, ucuncu sutun zirhlar ve medkit, dorduncu sutun arabalar.
 * Bir esyaya tiklayinca sunucu onu envantere verir.
 *
 * NOT: Arka plani (renderBackground) elle CAGIRMA. Screen.render() zaten cizer; ikinci kez cizmek
 * Minecraft 1.21.6+ surumlerinde "Can only blur once per frame" hatasiyla oyunu coker.
 */
public class WeaponMenuScreen extends Screen {
	/** Sira ModItems.byIndex ile ayni. */
	private static final String[] NAME_KEYS = {
			"item.silahmod.pistol", "item.silahmod.glock_17", "item.silahmod.m4a1_s", "item.silahmod.m4a4",
			"item.silahmod.ak_47", "item.silahmod.ak_74m", "item.silahmod.p90", "item.silahmod.kriss_vector",
			"item.silahmod.helmet_1", "item.silahmod.vest_1", "item.silahmod.helmet_2", "item.silahmod.vest_2",
			"item.silahmod.medkit", "item.silahmod.knife",
			"item.silahmod.car_black_sedan", "item.silahmod.car_armored_skoda", "item.silahmod.car_lamborghini"
	};
	/** Menu yerlesimi: her sutun icin esya indeksleri. Sutun 0-1 = Silahlar, sutun 2 = Zirhlar ve medkit. */
	private static final int[][] COLUMNS = {
			{ 0, 1, 2, 3 },
			{ 4, 5, 6, 7, 13 },
			{ 8, 9, 10, 11, 12 },
			{ 14, 15, 16 }
	};
	private static final int ROWS = 5;           // en uzun sutunda 5 esya
	private static final int BUTTON_W = 84;
	private static final int BUTTON_H = 18;
	private static final int GAP = 3;
	private static final int ICON_SPACE = 16;    // butonun solundaki ikon alani
	private static final int COLUMN_GAP = 6;

	public WeaponMenuScreen() {
		super(Component.translatable("screen.silahmod.menu"));
	}

	private int top() {
		int total = ROWS * (BUTTON_H + GAP) + BUTTON_H + 10;
		return this.height / 2 - total / 2 + 12;
	}

	/** Sutunun butonlarinin sol x konumu. */
	private int columnX(int column) {
		int blockW = COLUMNS.length * (ICON_SPACE + BUTTON_W) + (COLUMNS.length - 1) * COLUMN_GAP;
		int left = this.width / 2 - blockW / 2;
		return left + column * (ICON_SPACE + BUTTON_W + COLUMN_GAP) + ICON_SPACE;
	}

	@Override
	protected void init() {
		int y = top();
		for (int column = 0; column < COLUMNS.length; column++) {
			for (int row = 0; row < COLUMNS[column].length; row++) {
				final int index = COLUMNS[column][row];
				this.addRenderableWidget(Button.builder(Component.translatable(NAME_KEYS[index]),
								button -> ClientPlayNetworking.send(new Net.GiveWeaponPayload(index)))
						.pos(columnX(column), y + row * (BUTTON_H + GAP))
						.size(BUTTON_W, BUTTON_H)
						.build());
			}
		}
		int closeW = 130;
		this.addRenderableWidget(Button.builder(Component.translatable("gui.silahmod.close"), button -> this.onClose())
				.pos(this.width / 2 - closeW / 2, y + ROWS * (BUTTON_H + GAP) + 6)
				.size(closeW, BUTTON_H)
				.build());
	}

	@Override
	public void render(GuiGraphics graphics, int mouseX, int mouseY, float delta) {
		// Arka plan + butonlar (super.render arka plani kendisi cizer)
		super.render(graphics, mouseX, mouseY, delta);

		graphics.drawCenteredString(this.font, this.title, this.width / 2, top() - 22, 0xFFFFFFFF);
		// "Silahlar" basligi iki sutunun ortasinda
		int weaponsCenter = (columnX(0) + columnX(1) + BUTTON_W) / 2;
		graphics.drawCenteredString(this.font, Component.translatable("gui.silahmod.weapons"),
				weaponsCenter, top() - 10, 0xFFAAAAAA);
		graphics.drawCenteredString(this.font, Component.translatable("gui.silahmod.armors"),
				columnX(2) + BUTTON_W / 2, top() - 10, 0xFFAAAAAA);
		graphics.drawCenteredString(this.font, Component.translatable("gui.silahmod.cars"),
				columnX(3) + BUTTON_W / 2, top() - 10, 0xFFAAAAAA);

		// Her butonun soluna esya ikonu
		int y = top();
		for (int column = 0; column < COLUMNS.length; column++) {
			for (int row = 0; row < COLUMNS[column].length; row++) {
				Item item = ModItems.byIndex(COLUMNS[column][row]);
				if (item == null) {
					continue;
				}
				graphics.renderItem(new ItemStack(item), columnX(column) - 19, y + row * (BUTTON_H + GAP) + 3);
			}
		}
	}
}
