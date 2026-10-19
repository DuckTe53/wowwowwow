package com.silahmod;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/** Bir silahin icindeki (sarjor) ve yedek mermi sayisi. Esyanin uzerinde saklanir. */
public record AmmoData(int mag, int reserve) {
	public static final Codec<AmmoData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.fieldOf("mag").forGetter(AmmoData::mag),
			Codec.INT.fieldOf("reserve").forGetter(AmmoData::reserve)
	).apply(instance, AmmoData::new));

	public static final StreamCodec<io.netty.buffer.ByteBuf, AmmoData> STREAM_CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, AmmoData::mag,
			ByteBufCodecs.VAR_INT, AmmoData::reserve,
			AmmoData::new
	);
}
