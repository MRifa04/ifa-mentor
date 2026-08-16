"""Kunlik reja vazifalarini skill sahifalariga ulash."""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class DailyTaskMixin:
    """Skill widgetlariga kunlik vazifa banner va yakunlash qo'shadi."""

    def init_daily_task(self):
        self.daily_task = None
        self.mock_exam_task = None
        self._task_banner = None
        self._task_banner_label = None

    def attach_task_banner(self, parent_layout):
        self._task_banner = QFrame()
        self._task_banner.setStyleSheet("""
            QFrame {
                background: #0F2A1E;
                border-bottom: 1px solid #10B981;
            }
            QLabel {
                color: #10B981;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)

        banner_layout = QHBoxLayout(self._task_banner)
        banner_layout.setContentsMargins(20, 10, 20, 10)

        self._task_banner_label = QLabel()
        self._task_banner_label.setWordWrap(True)
        banner_layout.addWidget(self._task_banner_label)

        if isinstance(parent_layout, QVBoxLayout):
            parent_layout.insertWidget(0, self._task_banner)
        else:
            wrapper = QVBoxLayout()
            wrapper.setContentsMargins(0, 0, 0, 0)
            wrapper.setSpacing(0)
            wrapper.addWidget(self._task_banner)
            wrapper.addLayout(parent_layout)
            return wrapper

        self._task_banner.hide()
        return None

    def apply_daily_task(self, task):
        if not task:
            return

        self.daily_task = task

        if not self._task_banner_label:
            return

        skill = task.get("skill", "")
        minutes = int(task.get("duration_minutes", 0) or 0)
        task_type = (
            str(task.get("task_type", "practice"))
            .replace("_", " ")
            .title()
        )

        self._task_banner_label.setText(
            f"📋 Bugungi vazifa: {skill} — {task_type} "
            f"({minutes} min)"
        )
        self._task_banner.show()

    def apply_mock_exam_task(self, task):
        if not task:
            return
        self.mock_exam_task = task
        self.daily_task = None
        if not self._task_banner_label:
            return
        title = task.get("mock_title", "Mock")
        skill = task.get("skill", "")
        step = task.get("step", 1)
        total = task.get("total_steps", 4)
        self._task_banner_label.setText(
            f"🎓 Mock: {title} — {skill} ({step}/{total})"
        )
        self._task_banner.show()

    def finish_skill_task(self, score, max_score=75):
        """Kunlik vazifa yoki mock imtihon skillini yakunlash."""
        if self.mock_exam_task:
            task = self.mock_exam_task
            self.mock_exam_task = None
            if self._task_banner:
                self._task_banner.hide()
            callback = getattr(self, "on_mock_skill_complete", None)
            if callable(callback):
                callback(task, score, max_score)
            return

        self.complete_daily_task(score)

    def complete_daily_task(self, score):
        if not self.daily_task:
            return

        task_id = self.daily_task.get("id")
        if task_id:
            self.db.complete_plan_task(task_id, score)

        self.daily_task = None

        if self._task_banner:
            self._task_banner.hide()

        callback = getattr(
            self,
            "on_task_completed",
            None,
        )
        if callable(callback):
            callback()
