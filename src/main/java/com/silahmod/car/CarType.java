package com.silahmod.car;

import com.silahmod.ModItems;

import net.minecraft.world.item.Item;

/** Uc araba modeli. Her biri icin esya (spawn + gorunum) ModItems'ta kayitli. */
public enum CarType {
	BLACK_SEDAN,
	ARMORED_SKODA,
	LAMBORGHINI;

	public static CarType byId(int id) {
		CarType[] all = values();
		return all[Math.floorMod(id, all.length)];
	}

	public Item item() {
		return switch (this) {
			case BLACK_SEDAN -> ModItems.CAR_BLACK_SEDAN;
			case ARMORED_SKODA -> ModItems.CAR_ARMORED_SKODA;
			case LAMBORGHINI -> ModItems.CAR_LAMBORGHINI;
		};
	}
}
