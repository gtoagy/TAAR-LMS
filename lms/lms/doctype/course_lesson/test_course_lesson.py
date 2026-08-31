# Copyright (c) 2021, FOSS United and Contributors
# See license.txt

import unittest

import frappe

from lms.lms.test_helpers import BaseTestUtils


class TestApplyEnforcementFlags(unittest.TestCase):
	def _call(self, *, quiz_done, assignment_done, enforce_quiz, enforce_assignment):
		from lms.lms.doctype.course_lesson.course_lesson import (
			apply_enforcement_flags,
		)

		settings = {
			"enforce_quiz_completion": enforce_quiz,
			"enforce_assignment_completion": enforce_assignment,
		}
		return apply_enforcement_flags(
			quiz_done=quiz_done,
			assignment_done=assignment_done,
			settings=settings,
		)

	def test_both_enforced_passes_through(self):
		self.assertEqual(
			self._call(quiz_done=True, assignment_done=True, enforce_quiz=1, enforce_assignment=1),
			(True, True),
		)
		self.assertEqual(
			self._call(quiz_done=False, assignment_done=True, enforce_quiz=1, enforce_assignment=1),
			(False, True),
		)
		self.assertEqual(
			self._call(quiz_done=True, assignment_done=False, enforce_quiz=1, enforce_assignment=1),
			(True, False),
		)

	def test_quiz_off_returns_true_for_quiz(self):
		self.assertEqual(
			self._call(quiz_done=False, assignment_done=False, enforce_quiz=0, enforce_assignment=1),
			(True, False),
		)

	def test_assignment_off_returns_true_for_assignment(self):
		self.assertEqual(
			self._call(quiz_done=False, assignment_done=False, enforce_quiz=1, enforce_assignment=0),
			(False, True),
		)

	def test_both_off_returns_true_true(self):
		self.assertEqual(
			self._call(quiz_done=False, assignment_done=False, enforce_quiz=0, enforce_assignment=0),
			(True, True),
		)

	def test_missing_settings_keys_treated_as_enforced(self):
		from lms.lms.doctype.course_lesson.course_lesson import (
			apply_enforcement_flags,
		)

		self.assertEqual(
			apply_enforcement_flags(quiz_done=False, assignment_done=True, settings={}),
			(False, True),
		)


class TestApplyEnforcementFlagsEdgeCases(unittest.TestCase):
	def setUp(self):
		from lms.lms.doctype.course_lesson.course_lesson import (
			apply_enforcement_flags,
		)

		self.fn = apply_enforcement_flags

	def test_dict_subclass_input(self):
		"""A frappe._dict-like subclass of dict should work via duck-typing."""

		class _Dict(dict):
			pass

		settings = _Dict({"enforce_quiz_completion": 0, "enforce_assignment_completion": 1})
		self.assertEqual(self.fn(quiz_done=False, assignment_done=False, settings=settings), (True, False))

	def test_string_zero_is_truthy_treated_as_enforced(self):
		"""Frappe may return '0' as a string from raw queries. `not '0'` is False, so it's still enforced.

		Codifies current behavior — callers that hit this should pass int(value) explicitly.
		"""
		settings = {"enforce_quiz_completion": "0", "enforce_assignment_completion": "0"}
		# Both still treated as enforced because non-empty strings are truthy.
		self.assertEqual(self.fn(quiz_done=False, assignment_done=False, settings=settings), (False, False))

	def test_string_one_treated_as_enforced(self):
		settings = {"enforce_quiz_completion": "1", "enforce_assignment_completion": "1"}
		self.assertEqual(self.fn(quiz_done=True, assignment_done=True, settings=settings), (True, True))
		self.assertEqual(self.fn(quiz_done=False, assignment_done=True, settings=settings), (False, True))

	def test_none_for_flag_disables_enforcement(self):
		"""Present-but-None: helper sees `not None == True`, treats as NOT enforced.

		Distinct from missing key (which defaults to 1 / enforced via dict.get's default).
		"""
		settings = {"enforce_quiz_completion": None, "enforce_assignment_completion": 1}
		self.assertEqual(self.fn(quiz_done=False, assignment_done=False, settings=settings), (True, False))

	def test_both_int_zero_disabled(self):
		settings = {"enforce_quiz_completion": 0, "enforce_assignment_completion": 0}
		for quiz_done in (True, False):
			for assignment_done in (True, False):
				with self.subTest(quiz_done=quiz_done, assignment_done=assignment_done):
					self.assertEqual(
						self.fn(quiz_done=quiz_done, assignment_done=assignment_done, settings=settings),
						(True, True),
					)

	def test_idempotent(self):
		settings = {"enforce_quiz_completion": 1, "enforce_assignment_completion": 1}
		first = self.fn(quiz_done=True, assignment_done=False, settings=settings)
		second = self.fn(quiz_done=True, assignment_done=False, settings=settings)
		self.assertEqual(first, second)

	def test_does_not_mutate_settings(self):
		settings = {"enforce_quiz_completion": 1, "enforce_assignment_completion": 0}
		snapshot = dict(settings)
		self.fn(quiz_done=True, assignment_done=False, settings=settings)
		self.assertEqual(settings, snapshot)

	def test_keyword_argument_contract(self):
		"""save_progress invokes with keyword args; the helper must accept them in any order."""
		settings = {"enforce_quiz_completion": 1, "enforce_assignment_completion": 1}
		self.assertEqual(
			self.fn(settings=settings, quiz_done=True, assignment_done=False),
			(True, False),
		)
		self.assertEqual(
			self.fn(assignment_done=False, quiz_done=True, settings=settings),
			(True, False),
		)


class TestCompletionBlocker(unittest.TestCase):
	"""What get_completion_blocker reports back to the lesson page.

	Kept free of the database: the point is the mapping from "which requirement
	failed" to the word the UI turns into an explanation.
	"""

	def _blocker(self, *, quiz_done, assignment_done, settings):
		from unittest.mock import patch

		module = "lms.lms.doctype.course_lesson.course_lesson"
		with (
			patch(f"{module}.get_quiz_progress", return_value=quiz_done),
			patch(f"{module}.get_assignment_progress", return_value=assignment_done),
			patch(f"{module}.get_enforcement_settings", return_value=settings),
		):
			from lms.lms.doctype.course_lesson.course_lesson import get_completion_blocker

			return get_completion_blocker("some-lesson")

	def test_nothing_pending_returns_none(self):
		self.assertIsNone(
			self._blocker(
				quiz_done=True,
				assignment_done=True,
				settings={"enforce_quiz_completion": 1, "enforce_assignment_completion": 1},
			)
		)

	def test_pending_quiz_wins_over_pending_assignment(self):
		"""Only one reason is shown, and the quiz is the one to name first."""
		self.assertEqual(
			self._blocker(
				quiz_done=False,
				assignment_done=False,
				settings={"enforce_quiz_completion": 1, "enforce_assignment_completion": 1},
			),
			"quiz",
		)

	def test_pending_assignment(self):
		self.assertEqual(
			self._blocker(
				quiz_done=True,
				assignment_done=False,
				settings={"enforce_quiz_completion": 1, "enforce_assignment_completion": 1},
			),
			"assignment",
		)

	def test_enforcement_off_blocks_nothing(self):
		self.assertIsNone(
			self._blocker(
				quiz_done=False,
				assignment_done=False,
				settings={"enforce_quiz_completion": 0, "enforce_assignment_completion": 0},
			)
		)


class TestManualLessonCompletion(BaseTestUtils):
	"""Marking and unmarking a lesson by hand, end to end."""

	def setUp(self):
		super().setUp()
		self._create_user("frappe@example.com", "Frappe", "Admin", ["Moderator", "Course Creator"])
		self.student = self._create_user("student@example.com", "Test", "Student", ["LMS Student"])
		self.course = self._create_course()

		self.lessons = []
		for i in range(1, 3):
			chapter = self._create_chapter(f"Chapter {i}", self.course.name)
			self._create_chapter_reference(self.course.name, chapter.name, idx=i)
			for j in range(1, 3):
				lesson = self._create_lesson(f"Lesson {i}.{j}", chapter.name, self.course.name)
				self._create_lesson_reference(chapter.name, lesson.name)
				self.lessons.append(lesson)

		self.enrollment = self._create_enrollment(self.student.email, self.course.name)
		frappe.set_user(self.student.email)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _mark(self, lesson):
		from lms.lms.doctype.course_lesson.course_lesson import mark_lesson_complete

		return mark_lesson_complete(lesson=lesson.name, course=self.course.name)

	def _unmark(self, lesson):
		from lms.lms.doctype.course_lesson.course_lesson import unmark_lesson_complete

		return unmark_lesson_complete(lesson=lesson.name, course=self.course.name)

	def test_marking_closes_the_lesson_and_moves_the_percentage(self):
		result = self._mark(self.lessons[0])

		self.assertTrue(result["completed"])
		self.assertIsNone(result["blocked_by"])
		self.assertEqual(result["progress"], 25)

		self.enrollment.reload()
		self.assertEqual(self.enrollment.progress, 25)

	def test_marking_twice_does_not_duplicate_or_double_count(self):
		self._mark(self.lessons[0])
		result = self._mark(self.lessons[0])

		self.assertTrue(result["completed"])
		self.assertEqual(result["progress"], 25)
		self.assertEqual(
			frappe.db.count(
				"LMS Course Progress",
				{"member": self.student.email, "lesson": self.lessons[0].name},
			),
			1,
		)

	def test_unmarking_removes_the_row_and_lowers_the_percentage(self):
		self._mark(self.lessons[0])
		self._mark(self.lessons[1])

		result = self._unmark(self.lessons[1])

		self.assertFalse(result["completed"])
		self.assertEqual(result["progress"], 25)
		self.assertFalse(
			frappe.db.exists(
				"LMS Course Progress",
				{"member": self.student.email, "lesson": self.lessons[1].name},
			)
		)

		self.enrollment.reload()
		self.assertEqual(self.enrollment.progress, 25)

	def test_unmarking_something_never_marked_is_harmless(self):
		result = self._unmark(self.lessons[0])

		self.assertFalse(result["completed"])
		self.assertEqual(result["progress"], 0)

	def test_marking_without_enrollment_reports_failure(self):
		"""A moderator previewing has no enrollment: nothing is written."""
		outsider = self._create_user("outsider@example.com", "Out", "Sider", ["LMS Student"])
		frappe.set_user(outsider.email)

		result = self._mark(self.lessons[0])

		self.assertFalse(result["completed"])
		self.assertFalse(
			frappe.db.exists(
				"LMS Course Progress",
				{"member": outsider.email, "lesson": self.lessons[0].name},
			)
		)
