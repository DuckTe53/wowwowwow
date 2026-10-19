package com.silahmod;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

/** Ses calma yardimcisi. Ses adini yazi olarak alir, boylece Holder/SoundEvent farkina takilmaz. */
public final class Sfx {
	private Sfx() {}

	public static void play(ServerLevel level, double x, double y, double z, String vanillaSoundId, float volume, float pitch) {
		SoundEvent event = BuiltInRegistries.SOUND_EVENT.getValue(Identifier.withDefaultNamespace(vanillaSoundId));
		if (event == null) {
			return;
		}
		level.playSound(null, x, y, z, event, SoundSource.PLAYERS, volume, pitch);
	}
}
