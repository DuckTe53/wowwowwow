package com.silahmod;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import com.silahmod.item.GunItem;
import com.silahmod.item.KnifeItem;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Sunucu tarafi savas mantigi: atis (seri ates dahil), sarjor doldurma, bicak vurusu, silah verme. */
public final class Combat {
	private Combat() {}

	/** Devam eden bir doldurma. frame = su an gosterilen animasyon karesi (1'den baslar). */
	private static final class Reload {
		final ItemStack stack;
		final long startTick;
		final long endTick;
		int frame;

		Reload(ItemStack stack, long startTick, long endTick) {
			this.stack = stack;
			this.startTick = startTick;
			this.endTick = endTick;
		}
	}

	/** Oyuncunun bir sonraki atisi yapabilecegi zaman (tick, kusuratli: 1.33 tick'lik atis hizi icin). */
	private static final Map<UUID, Double> NEXT_SHOT = new HashMap<>();
	private static final Map<UUID, Long> KNIFE_NEXT = new HashMap<>();
	private static final Map<UUID, Reload> RELOADS = new HashMap<>();

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(Combat::tick);
		AttackEntityCallback.EVENT.register(Combat::onAttack);
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			UUID id = handler.getPlayer().getUUID();
			NEXT_SHOT.remove(id);
			KNIFE_NEXT.remove(id);
			RELOADS.remove(id);
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
			ServerPlayer player = handler.getPlayer();
			for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
				ItemStack stack = player.getInventory().getItem(i);
				if (stack.getItem() instanceof GunItem gun) {
					gun.refreshIdleFrame(stack);
				}
			}
		});
	}

	private static void message(ServerPlayer player, String key, Object... args) {
		player.displayClientMessage(Component.translatable(key, args), true);
	}

	// ------------------------------------------------------------------ ATIS

	/**
	 * Istemci ates istegi gonderdi. Otomatik silahlarda sol tik basili tutulurken her tick gelir;
	 * atis hizi burada (fireDelay) sinirlanir, yani istemci ne kadar sik gonderirse gondersin hiz ayni kalir.
	 */
	public static void shoot(ServerPlayer player) {
		ItemStack stack = player.getMainHandItem();
		if (!(stack.getItem() instanceof GunItem gun) || player.isSpectator()) {
			return;
		}
		if (!(player.level() instanceof ServerLevel level)) {
			return;
		}
		UUID id = player.getUUID();
		if (RELOADS.containsKey(id)) {
			return;
		}
		long now = level.getGameTime();
		double next = NEXT_SHOT.getOrDefault(id, 0.0);
		if (now < next) {
			return;
		}

		AmmoData ammo = gun.ammo(stack);
		if (ammo.mag() <= 0) {
			Sfx.play(level, player.getX(), player.getEyeY(), player.getZ(), "block.dispenser.fail", 0.8F, 1.5F);
			NEXT_SHOT.put(id, now + 10.0);
			if (ammo.reserve() > 0) {
				reload(player);
			} else {
				message(player, "message.silahmod.no_ammo");
			}
			return;
		}

		// Bosta bekledikten sonra ilk atis tam o tick'te cikar; seri atista sure birikerek ilerler (kusurat korunur).
		double base = (now - next >= 1.0) ? now : next;
		NEXT_SHOT.put(id, base + gun.fireDelay);
		gun.setAmmo(stack, new AmmoData(ammo.mag() - 1, ammo.reserve()));
		gun.refreshIdleFrame(stack);
		gun.fire(player, level);
	}

	// --------------------------------------------------------------- RELOAD

	/** Istemci R tusuna basinca gonderdi. */
	public static void reload(ServerPlayer player) {
		ItemStack stack = player.getMainHandItem();
		if (!(stack.getItem() instanceof GunItem gun) || !(player.level() instanceof ServerLevel level)) {
			return;
		}
		UUID id = player.getUUID();
		if (RELOADS.containsKey(id)) {
			return;
		}
		AmmoData ammo = gun.ammo(stack);
		if (ammo.mag() >= gun.magSize) {
			message(player, "message.silahmod.mag_full");
			return;
		}
		if (ammo.reserve() <= 0) {
			message(player, "message.silahmod.no_ammo");
			return;
		}
		long now = level.getGameTime();
		Reload reload = new Reload(stack, now, now + gun.reloadTicks);
		RELOADS.put(id, reload);
		advanceFrame(player, level, gun, reload, 1);
		message(player, "message.silahmod.reloading");
	}

	private static void finishReload(ServerPlayer player, ItemStack stack, ServerLevel level) {
		if (!(stack.getItem() instanceof GunItem gun)) {
			return;
		}
		AmmoData ammo = gun.ammo(stack);
		int take = Math.min(gun.magSize - ammo.mag(), ammo.reserve());
		AmmoData updated = new AmmoData(ammo.mag() + take, ammo.reserve() - take);
		gun.setAmmo(stack, updated);
		gun.refreshIdleFrame(stack);
		Sfx.play(level, player.getX(), player.getEyeY(), player.getZ(), "item.crossbow.loading_end", 1.0F, 1.0F);
		message(player, "message.silahmod.reloaded", updated.mag(), updated.reserve());
	}

	private static void tick(MinecraftServer server) {
		if (RELOADS.isEmpty()) {
			return;
		}
		Iterator<Map.Entry<UUID, Reload>> it = RELOADS.entrySet().iterator();
		while (it.hasNext()) {
			Map.Entry<UUID, Reload> entry = it.next();
			ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
			Reload reload = entry.getValue();

			// Oyuncu silahi elinden biraktiysa / oldyse doldurma iptal
			if (player == null || !player.isAlive() || player.getMainHandItem() != reload.stack) {
				if (reload.stack.getItem() instanceof GunItem gun) {
					gun.refreshIdleFrame(reload.stack); // animasyon karesinde takili kalmasin
				}
				if (player != null) {
					message(player, "message.silahmod.reload_cancelled");
				}
				it.remove();
				continue;
			}
			if (!(player.level() instanceof ServerLevel level) || !(reload.stack.getItem() instanceof GunItem gun)) {
				continue;
			}
			long now = level.getGameTime();
			if (now >= reload.endTick) {
				finishReload(player, reload.stack, level);
				it.remove();
				continue;
			}
			// Gecen sureye gore animasyon karesini ilerlet (1..reloadFrames)
			int frames = gun.reloadFrames();
			long total = Math.max(1L, reload.endTick - reload.startTick);
			int target = (int) Math.min(frames, 1 + (now - reload.startTick) * frames / total);
			if (target != reload.frame) {
				advanceFrame(player, level, gun, reload, target);
			}
		}
	}

	/** Animasyonu verilen kareye getirir ve o kareye bagli sesi calar. */
	private static void advanceFrame(ServerPlayer player, ServerLevel level, GunItem gun, Reload reload, int frame) {
		reload.frame = frame;
		gun.setFrame(reload.stack, frame);
		String[] sounds = gun.reloadSounds();
		if (frame - 1 < sounds.length && sounds[frame - 1] != null) {
			Sfx.play(level, player.getX(), player.getEyeY(), player.getZ(), sounds[frame - 1], 0.9F, 1.0F);
		}
	}

	// ---------------------------------------------------------------- BICAK

	private static InteractionResult onAttack(net.minecraft.world.entity.player.Player player,
			net.minecraft.world.level.Level world, net.minecraft.world.InteractionHand hand,
			net.minecraft.world.entity.Entity entity, net.minecraft.world.phys.EntityHitResult hitResult) {
		if (!(world instanceof ServerLevel level) || !(player instanceof ServerPlayer attacker)) {
			return InteractionResult.PASS; // istemcide dokunma: vurus paketi sunucuya gitsin
		}
		if (!(attacker.getMainHandItem().getItem() instanceof KnifeItem) || !(entity instanceof LivingEntity target)) {
			return InteractionResult.PASS;
		}
		if (attacker.isSpectator()) {
			return InteractionResult.PASS;
		}

		UUID id = attacker.getUUID();
		long now = level.getGameTime();
		if (now < KNIFE_NEXT.getOrDefault(id, 0L)) {
			return InteractionResult.FAIL;
		}
		KNIFE_NEXT.put(id, now + WeaponConfig.KNIFE_COOLDOWN);

		// Vurusun hedefin neresine geldigi
		Vec3 eye = attacker.getEyePosition();
		Vec3 reach = eye.add(attacker.getLookAngle().scale(6.0));
		Optional<Vec3> hit = target.getBoundingBox().inflate(target.getPickRadius()).clip(eye, reach);
		boolean head = hit.isPresent() && Ballistics.isHeadHit(target, hit.get());

		// Arkadan mi? Saldirganin bakisi ile hedefin bakisi ayni yone gidiyorsa arkadan.
		Vec3 attackerLook = flat(attacker.getLookAngle());
		Vec3 targetLook = flat(target.getViewVector(1.0F));
		boolean backstab = attackerLook.dot(targetLook) > WeaponConfig.KNIFE_BACK_DOT;

		float damage;
		if (backstab) {
			damage = WeaponConfig.KNIFE_BACKSTAB;
			message(attacker, "message.silahmod.backstab");
		} else if (head) {
			damage = WeaponConfig.KNIFE_HEAD;
			message(attacker, "message.silahmod.headshot");
		} else {
			damage = WeaponConfig.KNIFE_FRONT * Armors.bodyFactor(target); // yelek govde hasarini azaltir
		}

		Ballistics.damage(level, attacker, target, damage);
		Sfx.play(level, target.getX(), target.getEyeY(), target.getZ(), "entity.player.attack.strong", 1.0F, 1.0F);
		return InteractionResult.SUCCESS; // vanilla vurusu iptal
	}

	private static Vec3 flat(Vec3 v) {
		Vec3 flat = new Vec3(v.x, 0.0, v.z);
		return flat.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : flat.normalize();
	}

	// ----------------------------------------------------------- ESYA VERME

	/** B menusunden istenen esyayi oyuncuya verir. Silah zaten varsa mermisini doldurur. */
	public static void giveWeapon(ServerPlayer player, int index) {
		Item item = ModItems.byIndex(index);
		if (item == null) {
			return;
		}
		if (item == ModItems.MEDKIT) {
			// Tuketilebilir: istenen adede tamamla (zaten yeterince varsa dokunma)
			// Item'in maksimum stack boyutunu asma (asarsa envanter cokebilir).
			int give = Math.min(WeaponConfig.MEDKIT_MENU_GIVE, new ItemStack(item).getMaxStackSize());
			for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
				ItemStack have = player.getInventory().getItem(i);
				if (have.getItem() == item) {
					if (have.getCount() < give) {
						have.setCount(give);
					}
					return;
				}
			}
			player.getInventory().placeItemBackInInventory(new ItemStack(item, give));
			return;
		}
		for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
			ItemStack existing = player.getInventory().getItem(i);
			if (existing.getItem() == item) {
				if (item instanceof GunItem gun) {
					gun.setAmmo(existing, new AmmoData(gun.magSize, gun.reserveMax));
					gun.refreshIdleFrame(existing);
					message(player, "message.silahmod.refilled");
				}
				return;
			}
		}
		ItemStack stack;
		if (item instanceof GunItem gun) {
			stack = gun.createFull();
		} else if (item == ModItems.HELMET_2) {
			stack = ModItems.createHelmet2(player.level().registryAccess()); // Koruma II buyulu
		} else {
			stack = new ItemStack(item);
		}
		player.getInventory().placeItemBackInInventory(stack);
	}
}
