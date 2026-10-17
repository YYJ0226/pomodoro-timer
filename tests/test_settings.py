"""Exercise the real settings callback without a Tk window (Windows only)."""

import unittest
from unittest.mock import Mock, patch

from pomodoro import PomodoroTimer


class SettingsTests(unittest.TestCase):
    def setUp(self):
        info_patch = patch("pomodoro.messagebox.showinfo")
        error_patch = patch("pomodoro.messagebox.showerror")
        self.info = info_patch.start()
        self.error = error_patch.start()
        self.addCleanup(info_patch.stop)
        self.addCleanup(error_patch.stop)
        self.make_timer()

    def make_timer(self):
        self.info.reset_mock()
        self.error.reset_mock()
        self.timer = PomodoroTimer.__new__(PomodoroTimer)
        self.timer.work_time = 1500
        self.timer.short_break = 300
        self.timer.time_left = 123
        self.timer.is_running = True
        self.timer.is_work_mode = True
        self.timer.pomodoros_completed = 2
        self.timer.work_spinbox = Mock()
        self.timer.break_spinbox = Mock()
        self.timer.start_button = Mock()
        self.timer.time_label = Mock()
        self.timer.progress = {}

    def apply(self, work, rest):
        self.timer.work_spinbox.get.return_value = work
        self.timer.break_spinbox.get.return_value = rest
        self.timer.apply_settings()

    def state(self):
        return (
            self.timer.work_time, self.timer.short_break,
            self.timer.time_left, self.timer.is_running,
            self.timer.is_work_mode, self.timer.pomodoros_completed,
        )

    def assert_rejected_without_changes(self, work, rest):
        before = self.state()
        self.apply(work, rest)
        self.assertEqual(self.state(), before)
        self.error.assert_called_once()
        self.info.assert_not_called()
        self.timer.start_button.config.assert_not_called()
        self.timer.time_label.config.assert_not_called()
        self.assertEqual(self.timer.progress, {})

    def test_zero_work_is_rejected_before_division(self):
        self.assert_rejected_without_changes("0", "5")

    def test_invalid_second_field_does_not_partially_apply_first(self):
        self.assert_rejected_without_changes("30", "oops")

    def test_work_range_and_integer_syntax(self):
        for value in ("-1", "61", "", " ", "2.5", "abc", "+2", "1_0", "２５"):
            with self.subTest(value=value):
                self.make_timer()
                self.assert_rejected_without_changes(value, "5")

    def test_break_range_and_integer_syntax(self):
        for value in ("0", "-1", "31", "", " ", "2.5", "abc", "+2", "1_0", "５"):
            with self.subTest(value=value):
                self.make_timer()
                self.assert_rejected_without_changes("30", value)

    def test_invalid_settings_preserve_break_mode(self):
        self.timer.is_work_mode = False
        self.assert_rejected_without_changes("30", "0")

    def test_valid_boundaries_reset_current_work_mode(self):
        for work, rest in (("1", "1"), ("60", "30")):
            with self.subTest(work=work, rest=rest):
                self.make_timer()
                self.apply(work, rest)
                self.assertEqual(self.timer.work_time, int(work) * 60)
                self.assertEqual(self.timer.short_break, int(rest) * 60)
                self.assertEqual(self.timer.time_left, int(work) * 60)
                self.assertFalse(self.timer.is_running)
                self.assertEqual(self.timer.progress["value"], 100)
                self.info.assert_called_once()
                self.error.assert_not_called()

    def test_valid_settings_reset_current_break_mode(self):
        self.timer.is_work_mode = False
        self.apply("30", "10")
        self.assertEqual(self.timer.time_left, 600)
        self.assertFalse(self.timer.is_running)
        self.assertFalse(self.timer.is_work_mode)
        self.assertEqual(self.timer.pomodoros_completed, 2)
        self.assertEqual(self.timer.progress["value"], 100)
        self.error.assert_not_called()

    def test_whitespace_and_leading_zeroes_are_accepted(self):
        self.apply(" 025 ", "05")
        self.assertEqual(self.timer.work_time, 1500)
        self.assertEqual(self.timer.short_break, 300)
        self.info.assert_called_once()
        self.error.assert_not_called()

    def test_error_identifies_invalid_field_and_allowed_range(self):
        for work, rest, field, bounds in (
            ("0", "5", "工作", "1–60"),
            ("25", "0", "休息", "1–30"),
        ):
            with self.subTest(field=field):
                self.make_timer()
                self.apply(work, rest)
                message = self.error.call_args.args[1]
                self.assertIn(field, message)
                self.assertIn(bounds, message)


if __name__ == "__main__":
    unittest.main()
