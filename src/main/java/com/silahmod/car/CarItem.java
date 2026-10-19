package com.silahmod.car;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** Arabanin esyasi: yere tiklayinca o model arabadan bir tane koyar. */
public class CarItem extends Item {
	private final CarType type;

	public CarItem(Item.Properties properties, CarType type) {
		super(properties);
		this.type = type;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		Level level = context.getLevel();
		if (!(level instanceof ServerLevel serverLevel)) {
			return InteractionResult.SUCCESS;
		}
		Vec3 pos = Vec3.atBottomCenterOf(context.getClickedPos().relative(context.getClickedFace()));
		float yaw = context.getPlayer() != null ? context.getPlayer().getYRot() : 0.0F;

		CarEntity car = new CarEntity(CarEntities.CAR, serverLevel);
		car.setCarType(type);
		car.moveTo(pos.x, pos.y, pos.z, yaw, 0.0F);
		serverLevel.addFreshEntity(car);

		if (context.getPlayer() == null || !context.getPlayer().isCreative()) {
			context.getItemInHand().shrink(1);
		}
		return InteractionResult.SUCCESS;
	}
}
