package com.silahmod;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

/** Zirh etkileri: govde/kafa hasari azaltma ve Kask 2'nin altin kalbi. Sayilar WeaponConfig'de. */
public final class Armors {
	private Armors() {}

	/** Kask 2'yi giyip altin kalbini almis oyuncular (her giyisinde bir kez verilir). */
	private static final Set<UUID> GOLD_GRANTED = new HashSet<>();

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(Armors::tick);
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> GOLD_GRANTED.remove(handler.getPlayer().getUUID()));
	}

	/** Tum silahlarin GOVDE hasari bununla carpilir (yelek yoksa 1.0). */
	public static float bodyFactor(LivingEntity entity) {
		ItemStack chest = entity.getItemBySlot(EquipmentSlot.CHEST);
		if (chest.is(ModItems.VEST_1)) {
			return 1.0F - WeaponConfig.VEST_1_BODY_REDUCTION;
		}
		if (chest.is(ModItems.VEST_2)) {
			return 1.0F - WeaponConfig.VEST_2_BODY_REDUCTION;
		}
		return 1.0F;
	}

	/** Silahlarin KAFA isabeti hasari bununla carpilir (Kask 1 yoksa 1.0). */
	public static float headFactor(LivingEntity entity) {
		ItemStack head = entity.getItemBySlot(EquipmentSlot.HEAD);
		if (head.is(ModItems.HELMET_1)) {
			return 1.0F - WeaponConfig.HELMET_1_HEAD_REDUCTION;
		}
		return 1.0F;
	}

	/** Kask 2 giyilince altin kalpleri (emilim) ver. Cikarinca ek can limiti kalkar, kalpler kendiliginden kaybolur. */
	private static void tick(MinecraftServer server) {
		float gold = WeaponConfig.hearts(WeaponConfig.HELMET_2_GOLD_HEARTS);
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			UUID id = player.getUUID();
			boolean wearing = player.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.HELMET_2);
			if (wearing) {
				// Ek can limiti kaskin ozelligiyle yukselmis olmali; ancak o zaman kalpleri ver
				if (!GOLD_GRANTED.contains(id) && player.getMaxAbsorption() >= gold) {
					player.setAbsorptionAmount(Math.max(player.getAbsorptionAmount(), gold));
					GOLD_GRANTED.add(id);
				}
			} else if (GOLD_GRANTED.remove(id)) {
				if (player.getAbsorptionAmount() > player.getMaxAbsorption()) {
					player.setAbsorptionAmount(player.getMaxAbsorption());
				}
			}
		}
	}
}
