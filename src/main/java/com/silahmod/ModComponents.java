package com.silahmod;

import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;

public final class ModComponents {
	private ModComponents() {}

	public static final DataComponentType<AmmoData> AMMO = Registry.register(
			BuiltInRegistries.DATA_COMPONENT_TYPE,
			SilahMod.id("ammo"),
			DataComponentType.<AmmoData>builder()
					.persistent(AmmoData.CODEC)
					.networkSynchronized(AmmoData.STREAM_CODEC)
					.build()
	);

	public static void init() {
		// Sinifi yuklemek icin yeterli; kayit statik alanda yapilir.
	}
}
