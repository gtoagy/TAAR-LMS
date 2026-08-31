/**
 * Pure helpers for lesson-progress logic. Kept side-effect-free so they can
 * be unit-tested without mounting Lesson.vue or stubbing the Pinia store.
 */

export const DEFAULT_VIDEO_PERCENT = 90

export function resolveDwellSeconds(raw: unknown, fallback = 30): number | null {
	const n = Number(raw ?? fallback)
	if (!Number.isFinite(n) || n <= 0) return null
	return n
}

/**
 * Percentage of a video that counts as watched. Unlike the dwell time there is
 * no "disabled" state: a blank, zero or out-of-range setting falls back to the
 * default instead of returning null, because a lesson with no threshold at all
 * would never close for someone who does watch the video to the end.
 */
export function resolveVideoPercent(
	raw: unknown,
	fallback = DEFAULT_VIDEO_PERCENT
): number {
	const n = Number(raw ?? fallback)
	if (!Number.isFinite(n) || n <= 0 || n > 100) return fallback
	return n
}

export function isVideoComplete(
	currentTime: number,
	duration: number,
	percent: unknown = DEFAULT_VIDEO_PERCENT
): boolean {
	if (!Number.isFinite(currentTime) || !Number.isFinite(duration)) return false
	if (duration <= 0) return false
	// The last-second rule stays on as a second chance: on a very short clip the
	// percentage lands later than "one second from the end", and YouTube tends to
	// stop reporting time a frame early.
	const threshold = duration * (resolveVideoPercent(percent) / 100)
	return currentTime >= threshold || currentTime >= duration - 1
}

export function shouldStartDwellTimer(opts: {
	hasVideo: boolean
	enforceVideo: boolean | 0 | 1
}): boolean {
	return !(opts.hasVideo && !!opts.enforceVideo)
}

export function shouldAttachVideoFallback(opts: {
	hasVideo: boolean
	enforceVideo: boolean | 0 | 1
}): boolean {
	return opts.hasVideo && !!opts.enforceVideo
}
