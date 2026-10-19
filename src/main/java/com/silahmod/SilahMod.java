package com.silahmod;

import com.silahmod.car.CarEntities;

import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;

public class SilahMod implements ModInitializer {
	public static final String MOD_ID = "silahmod";

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}

	@Override
	public void onInitialize() {
		ModComponents.init();
		ModItems.init();
		Net.init();
		Combat.init();
		Armors.init();
		CarEntities.init();
	}
}
