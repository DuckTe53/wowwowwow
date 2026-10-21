package com.silahmod.car;

import java.util.List;

import org.joml.Quaternionf;
import org.joml.Vector3f;

import com.mojang.math.Transformation;
import com.silahmod.Sfx;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Suruculu araba. 400 can. Hasar: carpma (hiz ile orantili) ve oyuncu vuruslari.
 * Her 150 hasarda gorunum degisir (0-149 hasarsiz, 150-299 hasarli, 300+ agir hasarli).
 * Can bitince TNT gucunde (4) patlar, ama blok/mob zarar vermez; sadece yakindaki oyunculara hasar verir.
 *
 * Sunucu fizik yapar. Istemci sadece W/A/S/D bitlerini yollar (Net.CarInputPayload).
 * Gorunum: ustune binen bir ItemDisplay (item modeli custom_model_data ile hasar kademesini secer).
 */
public class CarEntity extends Entity {
	public static final int INPUT_FORWARD = 1;
	public static final int INPUT_BACK = 2;
	public static final int INPUT_LEFT = 4;
	public static final int INPUT_RIGHT = 8;

	/** Model olcegi (tools/gen_cars.py ile ayni). Model ~40 birim = 4.5 blok uzunluk. */
	public static final float SCALE = 1.8F;

	/** Gorunumu zeminin biraz ustunde tut (surtunme/titreme olmasin). */
	private static final double VISUAL_LIFT = 0.05;
	/** Bir blok yuksekligindeki basamaklari (merdiven) asabilsin. */
	private static final float STEP_HEIGHT = 1.05F;

	public static final float MAX_HP = 400.0F;
	public static final float STAGE_DAMAGE = 150.0F;

	// Fizik (blok/tick). 0.85 ~ 17 blok/sn.
	private static final double MAX_SPEED = 0.85;
	private static final double MAX_REVERSE = 0.18;
	private static final double ACCEL = 0.022;
	private static final double BRAKE = 0.06;
	private static final double FRICTION = 0.985;
	private static final double STEER_DEG = 3.0;

	// Carpma hasari
	private static final double CRASH_MIN_SPEED = 0.12;
	private static final double CRASH_DAMAGE_PER_SPEED = 120.0;

	// Patlama (TNT gucu 4 ile ayni; yaricap = 2 * guc)
	private static final double EXPLOSION_RADIUS = 8.0;
	private static final float EXPLOSION_MAX_DAMAGE = 50.0F;

	private static final EntityDataAccessor<Float> DAMAGE =
			SynchedEntityData.defineId(CarEntity.class, EntityDataSerializers.FLOAT);
	private static final EntityDataAccessor<Integer> CAR_TYPE =
			SynchedEntityData.defineId(CarEntity.class, EntityDataSerializers.INT);

	private double speed;
	private int input;
	private int shownStage = -1;
	private Display.ItemDisplay visual;

	public CarEntity(EntityType<? extends CarEntity> type, Level level) {
		super(type, level);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		builder.define(DAMAGE, 0.0F);
		builder.define(CAR_TYPE, 0);
	}

	// ------------------------------------------------------------ genel erisim

	public CarType carType() {
		return CarType.byId(entityData.get(CAR_TYPE));
	}

	public void setCarType(CarType type) {
		entityData.set(CAR_TYPE, type.ordinal());
	}

	public float damage() {
		return entityData.get(DAMAGE);
	}

	public float health() {
		return MAX_HP - damage();
	}

	/** 0 = hasarsiz, 1 = hasarli (150+), 2 = agir hasarli (300+). */
	public int stage() {
		return Math.min(2, (int) (damage() / STAGE_DAMAGE));
	}

	/** Istemciden gelen W/A/S/D bitleri. */
	public void setInput(int bits) {
		this.input = bits;
	}

	@Override
	public boolean isPickable() {
		return !isRemoved();
	}

	@Override
	public boolean isAttackable() {
		return !isRemoved();
	}

	// --------------------------------------------------------------- hasar

	/** Oyuncu vurusu / diger hasar kaynaklari. */
	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (isRemoved()) {
			return false;
		}
		applyDamage(level, amount);
		return true;
	}

	private void applyDamage(ServerLevel level, float amount) {
		float next = Math.min(MAX_HP, damage() + amount);
		entityData.set(DAMAGE, next);
		Sfx.play(level, getX(), getY() + 0.5, getZ(), "entity.iron_golem.hurt", 1.0F, 0.6F);
		if (next >= MAX_HP) {
			explode(level);
		}
	}

	/** TNT ile ayni guc, ama sadece oyunculara hasar verir (blok ve mob yok). */
	private void explode(ServerLevel level) {
		Vec3 center = position().add(0.0, 0.5, 0.0);
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, center.x, center.y, center.z, 1, 0.0, 0.0, 0.0, 0.0);
		level.sendParticles(ParticleTypes.FLAME, center.x, center.y, center.z, 60, 1.5, 0.8, 1.5, 0.08);
		Sfx.play(level, center.x, center.y, center.z, "entity.generic.explode", 4.0F, 1.0F);

		DamageSource source = level.damageSources().explosion(this, null);
		AABB area = getBoundingBox().inflate(EXPLOSION_RADIUS);
		for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, area)) {
			double dist = player.position().distanceTo(center);
			if (dist > EXPLOSION_RADIUS) {
				continue;
			}
			float dmg = (float) (EXPLOSION_MAX_DAMAGE * (1.0 - dist / EXPLOSION_RADIUS));
			player.hurtServer(level, source, dmg);
		}

		ejectPassengers();
		discard();
	}

	// ---------------------------------------------------------- tick / fizik

	@Override
	public void tick() {
		super.tick();
		if (!(level() instanceof ServerLevel level) || isRemoved()) {
			return;
		}
		ensureVisual(level);
		drive(level);
		if (isRemoved()) {
			return;
		}
		syncVisual();

		Player driver = driver();
		if (driver != null && tickCount % 10 == 0) {
			driver.displayClientMessage(
					Component.literal("Araç: " + Math.round(health()) + " / " + Math.round(MAX_HP) + " HP"), true);
		}
	}

	private void drive(ServerLevel level) {
		int in = driver() != null ? input : 0;
		boolean fwd = (in & INPUT_FORWARD) != 0;
		boolean back = (in & INPUT_BACK) != 0;
		boolean left = (in & INPUT_LEFT) != 0;
		boolean right = (in & INPUT_RIGHT) != 0;

		// W: hizlan. S: yavasla, durunca yavasca geri git. Hic basilmazsa surtunmeyle yavaslar.
		if (fwd) {
			speed = Math.min(MAX_SPEED, speed + ACCEL);
		} else if (back) {
			if (speed > 0.02) {
				speed = Math.max(0.0, speed - BRAKE);
			} else {
				speed = Math.max(-MAX_REVERSE, speed - ACCEL * 0.5);
			}
		} else {
			speed *= FRICTION;
			if (Math.abs(speed) < 0.001) {
				speed = 0.0;
			}
		}

		// A/D: hiz varken doner (dururken donmez). Geri giderken direksiyon ters calisir.
		if (Math.abs(speed) > 0.01) {
			double steer = (right ? 1.0 : 0.0) - (left ? 1.0 : 0.0);
			double turnRate = STEER_DEG * Math.min(1.0, Math.abs(speed) / 0.3) * Math.signum(speed);
			setYRot(getYRot() + (float) (steer * turnRate));
		}

		double rad = Math.toRadians(getYRot());
		double impact = Math.abs(speed);
		// Minecraft'ta yaw 0 = +Z (guney). Bakis vektoru: (-sin, cos).
		move(MoverType.SELF, new Vec3(-Math.sin(rad) * speed, -0.08, Math.cos(rad) * speed));
		if (isRemoved()) {
			return;
		}

		// Bir yere carptiysa hiz sifirlanir ve hiza oranli hasar alir.
		if (horizontalCollision && impact > CRASH_MIN_SPEED) {
			speed = 0.0;
			applyDamage(level, (float) ((impact - CRASH_MIN_SPEED) * CRASH_DAMAGE_PER_SPEED));
		}
	}

	private Player driver() {
		for (Entity passenger : getPassengers()) {
			if (passenger instanceof Player player) {
				return player;
			}
		}
		return null;
	}

	// ----------------------------------------------------------- gorunum

	/** Yolcu olarak binmis ItemDisplay'i bulur ya da yoksa olusturur (kayittan yuklenen araba icin de gecerli). */
	private void ensureVisual(ServerLevel level) {
		if (visual != null && !visual.isRemoved()) {
			return;
		}
		// Ayni arabanin eski gorunumu varsa (kayittan yuklenmis) onu kullan; yoksa yenisini olustur.
		visual = null;
		List<Display.ItemDisplay> near = level.getEntitiesOfClass(Display.ItemDisplay.class, getBoundingBox().inflate(0.5));
		if (!near.isEmpty()) {
			visual = near.get(0);
		} else {
			visual = new Display.ItemDisplay(EntityType.ITEM_DISPLAY, level);
			level.addFreshEntity(visual);
			shownStage = -1;
		}
	}

	private void syncVisual() {
		if (visual == null) {
			return;
		}
		// Gorunum arabanin tam konumunda (binmis yolcu ofseti olmadan): alt kenar zemine oturur.
		// Zemine tam oturunca z-fighting/surtunme olmasin diye 0.05 blok yukari.
		visual.setPos(getX(), getY() + VISUAL_LIFT, getZ());
		int stage = stage();
		if (stage != shownStage) {
			shownStage = stage;
			visual.setItemStack(displayStack(stage));
		}
		// Model on (merkez) ustunde; yonu arabanin yonune dondur. Model on yonu +Z.
		visual.setTransformation(new Transformation(
				new Vector3f(0.0F, 0.5F * SCALE, 0.0F),
				new Quaternionf().rotateY((float) Math.toRadians(-getYRot())),
				new Vector3f(SCALE, SCALE, SCALE),
				new Quaternionf()));
	}

	private ItemStack displayStack(int stage) {
		ItemStack stack = new ItemStack(carType().item());
		if (stage > 0) {
			stack.set(DataComponents.CUSTOM_MODEL_DATA,
					new CustomModelData(List.of((float) stage), List.of(), List.of(), List.of()));
		}
		return stack;
	}

	// ---------------------------------------------------------- etkilesim

	/** Sag tik: bos arabaya bin. */
	@Override
	public InteractionResult interact(Player player, InteractionHand hand) {
		if (driver() != null) {
			return InteractionResult.PASS;
		}
		if (!level().isClientSide()) {
			if (player.startRiding(this)) {
				player.displayClientMessage(Component.translatable("message.silahmod.car_controls"), true);
			}
		}
		return InteractionResult.SUCCESS;
	}

	/** Merdiven ve tek bloklu basamaklari cikabilsin. */
	@Override
	public float maxUpStep() {
		return STEP_HEIGHT;
	}

	/** Gorunum (ItemDisplay) bindirilmis oldugu icin varsayilan kontrol yetmez: oyuncuya bir sofor yeri ac. */
	@Override
	protected boolean canAddPassenger(Entity passenger) {
		if (passenger instanceof Display.ItemDisplay) {
			return true;
		}
		return passenger instanceof Player && driver() == null;
	}

	@Override
	public void remove(Entity.RemovalReason reason) {
		if (visual != null) {
			visual.discard();
			visual = null;
		}
		super.remove(reason);
	}

	// ------------------------------------------------------------ kayit

	@Override
	protected void readAdditionalSaveData(ValueInput in) {
		entityData.set(DAMAGE, in.getFloatOr("Damage", 0.0F));
		setCarType(CarType.byId(in.getIntOr("CarType", 0)));
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput out) {
		out.putFloat("Damage", damage());
		out.putInt("CarType", entityData.get(CAR_TYPE));
	}
}
