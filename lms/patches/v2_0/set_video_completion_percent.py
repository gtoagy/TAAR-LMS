import frappe


def execute():
	"""Backfill the video completion threshold on the existing LMS Settings singleton.

	Same trap as `set_course_progress_defaults`: Frappe applies a docfield default
	only when the doc is first created, and this singleton already exists, so the
	Settings screen would show an empty threshold instead of 90.

	Guard on row existence in `tabSingles` (i.e. the field was never stored), not
	on the value: `frappe.db.get_single_value` cint-coerces an unset Int to 0, so
	a value-based check would never match. Existence-guarding keeps the patch
	idempotent and never overwrites a threshold an admin has saved.
	"""
	stored = frappe.db.sql(
		"""select field from tabSingles
		   where doctype = 'LMS Settings' and field = 'video_completion_percent'"""
	)
	if not stored:
		frappe.db.set_single_value("LMS Settings", "video_completion_percent", 90)
