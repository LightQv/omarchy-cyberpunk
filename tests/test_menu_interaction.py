"""Check bounded mouse-wheel and high-resolution trackpad accumulation."""

from pathlib import Path
import unittest

from PySide6.QtQml import QJSEngine
from PySide6.QtWidgets import QApplication


class MenuInteractionTest(unittest.TestCase):
    def test_deltas_accumulate_without_zero_event_or_large_event_runaway(self):
        app = QApplication.instance() or QApplication([])
        engine = QJSEngine()
        source = Path(__file__).resolve().parents[1] / "menu-plugin/MenuInteraction.js"
        engine.evaluate(source.read_text())
        result = engine.evaluate("""
            var state = {step: 0, remainder: 0, kind: ''};
            var steps = [];
            for (var i = 0; i < 8; i++) {
                state = wheelStep(15, 0, state); steps.push(state.step);
            }
            steps.push(wheelStep(0, 0, state).step);
            steps.push(wheelStep(-1200, 0, state).step);
            state = wheelStep(0, 12, state); steps.push(state.step);
            state = wheelStep(0, 12, state); steps.push(state.step);
            steps;
        """)
        self.assertFalse(result.isError(), result.toString())
        self.assertEqual(result.toVariant(), [0, 0, 0, 0, 0, 0, 0, -1, 0, 1, 0, -1])
