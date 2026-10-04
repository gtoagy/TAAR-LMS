import dayjs from '@/utils/dayjs'

// Con dayjs y no con useTimeAgo de vueuse, que solo habla inglés.
export function timeAgo(date) {
	return dayjs(date).fromNow()
}

export const formatSeconds = (time) => {
	const minutes = Math.floor(time / 60)
	const seconds = Math.floor(time % 60)
	return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`
}

export const escapeHTML = (text) => {
	if (!text) return ''
	let escape_html_mapping = {
		'&': '&amp;',
		'<': '&lt;',
		'>': '&gt;',
		'"': '&quot;',
		"'": '&#39;',
		'`': '&#x60;',
		'=': '&#x3D;',
	}

	return String(text).replace(
		/[&<>"'`=]/g,
		(char) => escape_html_mapping[char]
	)
}

export const formatTimestamp = (seconds) => {
	const date = new Date(seconds * 1000)
	const hours = String(date.getUTCHours()).padStart(2, '0')
	const minutes = String(date.getUTCMinutes()).padStart(2, '0')
	const secs = String(date.getUTCSeconds()).padStart(2, '0')
	return hours > 0 ? `${hours}:${minutes}:${secs}` : `${minutes}:${secs}`
}
