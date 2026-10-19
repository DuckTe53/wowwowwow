package com.silahmod;

import java.util.Optional;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Anlik vurus (hitscan) hesaplari ve hasar verme yardimcilari. */
public final class Ballistics {
	private Ballistics() {}

	/** Hedefin kafa bolgesi: goz hizasindan biraz asagisindan yukarisi. */
	public static boolean isHeadHit(Entity target, Vec3 hitPos) {
		return target instanceof LivingEntity && hitPos.y >= target.getEyeY() - 0.3;
	}

	public record Result(Vec3 end, Entity entity, Vec3 entityHitPos, boolean head) {}

	/** Verilen yone isin atar; once blok, sonra en yakin varlik. */
	public static Result trace(ServerLevel level, Entity shooter, Vec3 dir, double range) {
		Vec3 eye = shooter.getEyePosition();
		Vec3 end = eye.add(dir.scale(range));

		BlockHitResult blockHit = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, shooter));
		if (blockHit.getType() != HitResult.Type.MISS) {
			end = blockHit.getLocation();
		}

		AABB searchBox = new AABB(eye, end).inflate(1.0);
		Entity best = null;
		Vec3 bestPos = null;
		double bestDist = Double.MAX_VALUE;

		for (Entity candidate : level.getEntities(shooter, searchBox, e -> e.isPickable() && !e.isSpectator())) {
			AABB box = candidate.getBoundingBox().inflate(candidate.getPickRadius());
			Optional<Vec3> hit = box.clip(eye, end);
			if (hit.isPresent()) {
				double dist = eye.distanceToSqr(hit.get());
				if (dist < bestDist) {
					bestDist = dist;
					best = candidate;
					bestPos = hit.get();
				}
			}
		}

		if (best != null) {
			return new Result(bestPos, best, bestPos, isHeadHit(best, bestPos));
		}
		return new Result(end, null, null, false);
	}

	/** Bakis yonunu 'spreadDegrees' derecelik bir koni icinde rastgele saptirir. */
	public static Vec3 spreadDirection(Vec3 look, float spreadDegrees, RandomSource random) {
		if (spreadDegrees <= 0.0F) {
			return look;
		}
		Vec3 helper = Math.abs(look.y) > 0.99 ? new Vec3(1.0, 0.0, 0.0) : new Vec3(0.0, 1.0, 0.0);
		Vec3 right = look.cross(helper).normalize();
		Vec3 up = right.cross(look).normalize();
		double radius = Math.tan(Math.toRadians(spreadDegrees)) * Math.sqrt(random.nextDouble());
		double angle = random.nextDouble() * Math.PI * 2.0;
		return look.add(right.scale(radius * Math.cos(angle))).add(up.scale(radius * Math.sin(angle))).normalize();
	}

	/** Bir ates etme: saçılma, mermi izi, ses ve hasar. */
	public static void shoot(ServerLevel level, ServerPlayer shooter, GunSpec spec) {
		Vec3 dir = spreadDirection(shooter.getLookAngle(), spec.spread(), shooter.getRandom());
		Result result = trace(level, shooter, dir, spec.range());

		// Mermi izi (parcacik). Seri atesli silahlarda sunucuyu yormamak icin seyrek tutulur.
		Vec3 eye = shooter.getEyePosition();
		Vec3 path = result.end().subtract(eye);
		double length = path.length();
		if (length > 0.001) {
			Vec3 step = path.scale(1.0 / length);
			int points = (int) Math.min(24, length / 2.5);
			for (int i = 1; i < points; i++) {
				Vec3 p = eye.add(step.scale(i * 2.5));
				level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 1, 0, 0, 0, 0);
			}
		}

		Sfx.play(level, shooter.getX(), shooter.getEyeY(), shooter.getZ(), spec.sound(), spec.volume(), spec.pitch());

		Entity hit = result.entity();
		if (hit != null) {
			LivingEntity living = hit instanceof LivingEntity l ? l : null;
			float damage;
			if (result.head()) {
				damage = spec.head() * (living != null ? Armors.headFactor(living) : 1.0F); // kask kafa hasarini azaltir
			} else {
				damage = spec.body() * (living != null ? Armors.bodyFactor(living) : 1.0F); // yelek govde hasarini azaltir
			}
			damage(level, shooter, hit, damage);
			if (result.head()) {
				shooter.displayClientMessage(Component.translatable("message.silahmod.headshot"), true);
			}
		}
	}

	/** Bekleme suresini (hasar sonrasi dokunulmazlik) sifirlayip hasar uygular. Seri atista her mermi sayilsin diye. */
	public static void damage(ServerLevel level, ServerPlayer attacker, Entity target, float amount) {
		DamageSource source = level.damageSources().playerAttack(attacker);
		if (target instanceof LivingEntity living) {
			living.invulnerableTime = 0;
		}
		target.hurtServer(level, source, amount);
	}
}
