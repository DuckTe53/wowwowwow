package com.silahmod.car;

import com.silahmod.SilahMod;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

/** Araba entity tipi. Hitbox 2 x 1.3 blok; gorunum CarEntity icindeki ItemDisplay ile cizilir. */
public final class CarEntities {
	private CarEntities() {}

	public static final ResourceKey<EntityType<?>> CAR_KEY =
			ResourceKey.create(Registries.ENTITY_TYPE, SilahMod.id("car"));

	public static final EntityType<CarEntity> CAR = Registry.register(BuiltInRegistries.ENTITY_TYPE, CAR_KEY,
			EntityType.Builder.of(CarEntity::new, MobCategory.MISC)
					.sized(2.4F, 1.5F)
					.clientTrackingRange(10)
					.updateInterval(1)
					.build(CAR_KEY));

	/** Siniflarin yuklenmesini tetikler (kayit statik alanda yapilir). */
	public static void init() {
	}
}
