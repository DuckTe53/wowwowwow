package com.silahmod.item;

import java.util.List;

import com.silahmod.AmmoData;
import com.silahmod.Ballistics;
import com.silahmod.GunSpec;
import com.silahmod.ModComponents;
import com.silahmod.WeaponConfig;

import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;

/**
 * Tum ates eden silahlarin tek sinifi. Fark yaratan sayilar GunSpec'te (WeaponConfig).
 * Sinirsiz dayaniklilik: esyada hasar/dayaniklilik yok.
 */
public class GunItem extends Item {
	/** Reload sirasinda her animasyon karesinde calan ses (index 0 = 1. kare); null = ses yok. */
	private static final String[] RELOAD_SOUNDS = {
			"block.iron_trapdoor.open",   // 1: sarjor serbest
			null,                         // 2: sarjor dusuyor
			"item.armor.equip_iron",      // 3: yeni sarjor giriyor
			"block.lever.click",          // 4: sarjor oturdu / kurma kolu
			"item.crossbow.loading_end"   // 5: hazir
	};

	public final GunSpec spec;
	public final int magSize;
	public final int reserveMax;
	public final float fireDelay;
	public final int reloadTicks;

	public GunItem(Properties properties, GunSpec spec) {
		super(properties);
		this.spec = spec;
		this.magSize = spec.mag();
		this.reserveMax = spec.reserve();
		this.fireDelay = spec.fireDelay();
		this.reloadTicks = spec.reloadTicks();
	}

	public boolean automatic() {
		return this.spec.automatic();
	}

	/** Reload animasyonunun kare sayisi. tools/gen_models.py'deki kare sayisiyla ayni olmali. */
	public int reloadFrames() {
		return WeaponConfig.RELOAD_FRAMES;
	}

	public String[] reloadSounds() {
		return RELOAD_SOUNDS;
	}

	/**
	 * Animasyon karesi, esyanin custom_model_data bileseninde tasinir (items/*.json bunu okur).
	 * 0 = bilesen yok = normal model.
	 */
	public int frame(ItemStack stack) {
		CustomModelData data = stack.get(DataComponents.CUSTOM_MODEL_DATA);
		if (data == null || data.floats().isEmpty()) {
			return 0;
		}
		return Math.round(data.floats().get(0));
	}

	public void setFrame(ItemStack stack, int frame) {
		if (frame(stack) == frame) {
			return;
		}
		if (frame <= 0) {
			stack.remove(DataComponents.CUSTOM_MODEL_DATA);
		} else {
			stack.set(DataComponents.CUSTOM_MODEL_DATA,
					new CustomModelData(List.of((float) frame), List.of(), List.of(), List.of()));
		}
	}

	/** Animasyon yokken normal modeli goster. */
	public void refreshIdleFrame(ItemStack stack) {
		setFrame(stack, 0);
	}

	/** Sunucuda atis: mermi dusme ve bekleme suresi Combat tarafindan halledilir. */
	public void fire(ServerPlayer player, ServerLevel level) {
		Ballistics.shoot(level, player, this.spec);
	}

	public AmmoData ammo(ItemStack stack) {
		return stack.getOrDefault(ModComponents.AMMO, new AmmoData(this.magSize, this.reserveMax));
	}

	public void setAmmo(ItemStack stack, AmmoData data) {
		stack.set(ModComponents.AMMO, data);
	}

	public ItemStack createFull() {
		ItemStack stack = new ItemStack(this);
		stack.set(ModComponents.AMMO, new AmmoData(this.magSize, this.reserveMax));
		return stack;
	}
}
