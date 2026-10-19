package com.silahmod.client;

import org.lwjgl.glfw.GLFW;

import com.mojang.blaze3d.platform.InputConstants;
import com.silahmod.Net;
import com.silahmod.SilahMod;
import com.silahmod.car.CarEntities;
import com.silahmod.car.CarEntity;
import com.silahmod.item.GunItem;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.fabricmc.fabric.api.event.client.player.ClientPreAttackCallback;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.renderer.entity.EmptyEntityRenderer;

public class SilahModClient implements ClientModInitializer {
	public static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(SilahMod.id("silahlar"));

	public static KeyMapping reloadKey;
	public static KeyMapping menuKey;

	@Override
	public void onInitializeClient() {
		reloadKey = KeyBindingHelper.registerKeyBinding(
				new KeyMapping("key.silahmod.reload", InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, CATEGORY));
		menuKey = KeyBindingHelper.registerKeyBinding(
				new KeyMapping("key.silahmod.menu", InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_B, CATEGORY));

		// R = doldur, B = silah menusu
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			if (client.player == null || client.getConnection() == null) {
				return;
			}
			while (reloadKey.consumeClick()) {
				if (client.player.getMainHandItem().getItem() instanceof GunItem) {
					ClientPlayNetworking.send(new Net.ReloadPayload());
				}
			}
			while (menuKey.consumeClick()) {
				if (client.screen == null) {
					client.setScreen(new WeaponMenuScreen());
				}
			}

			// Araba surusu: arabadayken W/A/S/D durumunu her tick sunucuya yolla (ekran aciksa 0).
			if (client.player.getVehicle() instanceof CarEntity) {
				int bits = 0;
				if (client.screen == null) {
					if (client.options.keyUp.isDown()) bits |= CarEntity.INPUT_FORWARD;
					if (client.options.keyDown.isDown()) bits |= CarEntity.INPUT_BACK;
					if (client.options.keyLeft.isDown()) bits |= CarEntity.INPUT_LEFT;
					if (client.options.keyRight.isDown()) bits |= CarEntity.INPUT_RIGHT;
				}
				ClientPlayNetworking.send(new Net.CarInputPayload(bits));
			}
		});

		// Sol tik: elinde ates edilen silah varsa vanilla saldiri yerine ates et.
		//  - Yari-otomatik silah (pistol, Glock): her tik tek atis.
		//  - Otomatik silah (tufekler, SMG): sol tik basili tutuldukca her tick ates istegi gider;
		//    gercek atis hizini sunucu (GunSpec.fireDelay) sinirlar.
		ClientPreAttackCallback.EVENT.register((client, player, clickCount) -> {
			if (player.getMainHandItem().getItem() instanceof GunItem gun) {
				boolean pressed = clickCount > 0;
				boolean held = gun.automatic() && client.options.keyAttack.isDown();
				if ((pressed || held) && !player.isSpectator() && client.screen == null) {
					ClientPlayNetworking.send(new Net.ShootPayload());
				}
				return true; // blok kirma / vanilla saldiriyi engelle
			}
			return false;
		});

		// Mermi sayaci
		HudElementRegistry.attachElementAfter(VanillaHudElements.INFO_BAR, SilahMod.id("ammo"), AmmoOverlay::renderAmmo);
		// Araba: govde gorunmez (asil gorunum ustune binen ItemDisplay); renderer yalnizca kayit icin.
		EntityRendererRegistry.register(CarEntities.CAR, ctx -> new EmptyEntityRenderer<>(ctx));
		// Medkit bandaj sarma animasyonu (oyuncunun kendi skinindeki kol)
		HudElementRegistry.attachElementAfter(VanillaHudElements.MISC_OVERLAYS, SilahMod.id("medkit"), MedkitOverlay::render);
	}
}
