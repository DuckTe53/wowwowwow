package com.silahmod.item;

import com.silahmod.WeaponConfig;

import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Medkit: sag tik basili tutulur. Sure dolunca (WeaponConfig.MEDKIT_USE_TICKS) can fullenir ve gecici sari kalpler
 * (emilim) eklenir. Tus erken birakilirsa bir sey olmaz, medkit harcanmaz.
 * Kol/bandaj animasyonu istemci tarafinda cizilir (client/MedkitOverlay.java).
 */
public class MedkitItem extends Item {
	public MedkitItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		player.startUsingItem(hand);
		return InteractionResult.CONSUME;
	}

	@Override
	public int getUseDuration(ItemStack stack, LivingEntity entity) {
		return WeaponConfig.MEDKIT_USE_TICKS;
	}

	@Override
	public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
		if (!level.isClientSide()) {
			entity.setHealth(entity.getMaxHealth());
			// Emilim efekti: seviye basina 4 can (2 kalp). 10 kalp = 20 can = seviye 5 (amplifier 4)
			int amplifier = Math.max(0, (int) Math.ceil(WeaponConfig.MEDKIT_ABSORB_HEARTS * 2 / 4.0) - 1);
			entity.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, WeaponConfig.MEDKIT_ABSORB_TICKS, amplifier));
			level.playSound(null, entity.getX(), entity.getY(), entity.getZ(),
					SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.6F, 1.4F);
		}
		stack.consume(1, entity);
		return stack;
	}
}
