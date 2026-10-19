package com.silahmod;

import java.util.function.Function;

import com.silahmod.car.CarItem;
import com.silahmod.car.CarType;
import com.silahmod.item.GunItem;
import com.silahmod.item.KnifeItem;
import com.silahmod.item.MedkitItem;

import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.core.Holder;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.world.item.equipment.Equippable;

public final class ModItems {
	private ModItems() {}

	// ---------------- SILAHLAR (sayilar WeaponConfig'de) ----------------
	public static final GunItem PISTOL = gun("pistol", WeaponConfig.PISTOL);
	public static final GunItem GLOCK_17 = gun("glock_17", WeaponConfig.GLOCK_17);
	public static final GunItem M4A1_S = gun("m4a1_s", WeaponConfig.M4A1_S);
	public static final GunItem M4A4 = gun("m4a4", WeaponConfig.M4A4);
	public static final GunItem AK_47 = gun("ak_47", WeaponConfig.AK_47);
	public static final GunItem AK_74M = gun("ak_74m", WeaponConfig.AK_74M);
	public static final GunItem P90 = gun("p90", WeaponConfig.P90);
	public static final GunItem KRISS_VECTOR = gun("kriss_vector", WeaponConfig.KRISS_VECTOR);

	// ---------------- ARABALAR (yere koyar; gorunum items/car_*.json + models/item/car_*) ----------------
	public static final Item CAR_BLACK_SEDAN = register("car_black_sedan", p -> new CarItem(p, CarType.BLACK_SEDAN),
			new Item.Properties().stacksTo(1));
	public static final Item CAR_ARMORED_SKODA = register("car_armored_skoda", p -> new CarItem(p, CarType.ARMORED_SKODA),
			new Item.Properties().stacksTo(1));
	public static final Item CAR_LAMBORGHINI = register("car_lamborghini", p -> new CarItem(p, CarType.LAMBORGHINI),
			new Item.Properties().stacksTo(1));

	/** Bicak: hasar mantigi (arkadan / onden / kafa) Combat.onAttack icinde. Sayilar WeaponConfig'de. */
	public static final KnifeItem KNIFE = register("knife", KnifeItem::new,
			new Item.Properties().stacksTo(1));

	// ---------------- ZIRHLAR (klasik envanterdeki zirh yuvalarindan giyilir) ----------------
	/** Kask 1: demir kask gibi 2 zirh. Kafa hasari azaltmasi Armors.java'da. */
	public static final Item HELMET_1 = register("helmet_1", Item::new,
			armorProperties(EquipmentSlot.HEAD, EquipmentSlotGroup.HEAD, "helmet_1", SoundEvents.ARMOR_EQUIP_IRON,
					WeaponConfig.HELMET_1_ARMOR, WeaponConfig.HELMET_1_TOUGHNESS, 0.0));

	/** Yelek 1: govde hasarini %15 azaltir (Armors.java). */
	public static final Item VEST_1 = register("vest_1", Item::new,
			armorProperties(EquipmentSlot.CHEST, EquipmentSlotGroup.CHEST, "vest_1", SoundEvents.ARMOR_EQUIP_LEATHER,
					0.0, 0.0, 0.0));

	/** Kask 2: elmas pantolon gibi 6 zirh + 2 sertlik (+ Koruma II buyusu stack uzerinde) + altin kalp. */
	public static final Item HELMET_2 = register("helmet_2", Item::new,
			armorProperties(EquipmentSlot.HEAD, EquipmentSlotGroup.HEAD, "helmet_2", SoundEvents.ARMOR_EQUIP_DIAMOND,
					WeaponConfig.HELMET_2_ARMOR, WeaponConfig.HELMET_2_TOUGHNESS,
					WeaponConfig.hearts(WeaponConfig.HELMET_2_GOLD_HEARTS)));

	/** Yelek 2: govde hasarini %30 azaltir (Armors.java). */
	public static final Item VEST_2 = register("vest_2", Item::new,
			armorProperties(EquipmentSlot.CHEST, EquipmentSlotGroup.CHEST, "vest_2", SoundEvents.ARMOR_EQUIP_LEATHER,
					0.0, 0.0, 0.0));

	/** Medkit: sag tik basili tut, bandaj sarilir; biter bitmez can dolar ve gecici sari kalpler gelir. */
	public static final Item MEDKIT = register("medkit", MedkitItem::new, new Item.Properties().stacksTo(4));

	public static final ResourceKey<CreativeModeTab> TAB_KEY =
			ResourceKey.create(Registries.CREATIVE_MODE_TAB, SilahMod.id("silahlar"));

	private static <T extends Item> T register(String name, Function<Item.Properties, T> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, SilahMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}

	private static GunItem gun(String name, GunSpec spec) {
		return register(name, properties -> new GunItem(properties, spec),
				new Item.Properties().stacksTo(1).component(ModComponents.AMMO, new AmmoData(spec.mag(), spec.reserve())));
	}

	/**
	 * Zirh esyasi ozellikleri: giyilebilir (equippable), zirh / sertlik / ek can (altin kalp) ozellikleri.
	 * Dayaniklilik yok (silahlar gibi sinirsiz). Giyilince gorunen doku: assets/silahmod/equipment/<ad>.json
	 */
	private static Item.Properties armorProperties(EquipmentSlot slot, EquipmentSlotGroup group, String name,
			Holder<SoundEvent> equipSound, double armor, double toughness, double maxAbsorption) {
		ItemAttributeModifiers.Builder attrs = ItemAttributeModifiers.builder();
		if (armor > 0.0) {
			attrs.add(Attributes.ARMOR, new AttributeModifier(SilahMod.id("armor." + name), armor,
					AttributeModifier.Operation.ADD_VALUE), group);
		}
		if (toughness > 0.0) {
			attrs.add(Attributes.ARMOR_TOUGHNESS, new AttributeModifier(SilahMod.id("toughness." + name), toughness,
					AttributeModifier.Operation.ADD_VALUE), group);
		}
		if (maxAbsorption > 0.0) {
			attrs.add(Attributes.MAX_ABSORPTION, new AttributeModifier(SilahMod.id("absorption." + name), maxAbsorption,
					AttributeModifier.Operation.ADD_VALUE), group);
		}
		return new Item.Properties().stacksTo(1)
				.attributes(attrs.build())
				.component(DataComponents.EQUIPPABLE, Equippable.builder(slot)
						.setEquipSound(equipSound)
						.setAsset(ResourceKey.create(EquipmentAssets.ROOT_ID, SilahMod.id(name)))
						.build());
	}

	/** Kask 2'nin Koruma II buyulu hali (buyu kayit sistemi gerektirdigi icin dunya acikken olusturulur). */
	public static ItemStack createHelmet2(HolderLookup.Provider registries) {
		ItemStack stack = new ItemStack(HELMET_2);
		stack.enchant(registries.lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(Enchantments.PROTECTION),
				WeaponConfig.HELMET_2_PROTECTION_LEVEL);
		return stack;
	}

	/** Menudeki toplam esya sayisi. */
	public static final int COUNT = 14;

	/**
	 * Menu sirasi (Net.GiveWeaponPayload ve WeaponMenuScreen ile ayni):
	 * 0 pistol, 1 glock 17, 2 m4a1-s, 3 m4a4, 4 ak-47, 5 ak-74m, 6 p90, 7 kriss vector,
	 * 8 kask 1, 9 yelek 1, 10 kask 2, 11 yelek 2, 12 medkit, 13 bicak
	 */
	public static Item byIndex(int index) {
		return switch (index) {
			case 0 -> PISTOL;
			case 1 -> GLOCK_17;
			case 2 -> M4A1_S;
			case 3 -> M4A4;
			case 4 -> AK_47;
			case 5 -> AK_74M;
			case 6 -> P90;
			case 7 -> KRISS_VECTOR;
			case 8 -> HELMET_1;
			case 9 -> VEST_1;
			case 10 -> HELMET_2;
			case 11 -> VEST_2;
			case 12 -> MEDKIT;
			case 13 -> KNIFE;
			default -> null;
		};
	}

	public static void init() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricItemGroup.builder()
				.title(Component.translatable("itemGroup.silahmod.silahlar"))
				.icon(() -> new ItemStack(AK_47))
				.displayItems((context, entries) -> {
					// Creative'den alinan silahlar dolu mermiyle gelir
					for (GunItem gun : new GunItem[] { PISTOL, GLOCK_17, M4A1_S, M4A4, AK_47, AK_74M, P90, KRISS_VECTOR }) {
						entries.accept(gun.createFull());
					}
					entries.accept(CAR_BLACK_SEDAN);
					entries.accept(CAR_ARMORED_SKODA);
					entries.accept(CAR_LAMBORGHINI);
					entries.accept(KNIFE);
					entries.accept(new ItemStack(MEDKIT, WeaponConfig.MEDKIT_MENU_GIVE));
					entries.accept(HELMET_1);
					entries.accept(VEST_1);
					entries.accept(createHelmet2(context.holders()));
					entries.accept(VEST_2);
				})
				.build());
	}
}
