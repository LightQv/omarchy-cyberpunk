"""Check bounded mouse-wheel and high-resolution trackpad accumulation."""

from pathlib import Path
import unittest

from PySide6.QtQml import QJSEngine
from PySide6.QtWidgets import QApplication


class MenuInteractionTest(unittest.TestCase):
    def test_apps_redirect_is_scoped_and_does_not_mutate_defaults(self):
        app = QApplication.instance() or QApplication([])
        engine = QJSEngine()
        root = Path(__file__).resolve().parents[1]
        engine.evaluate((root / "menu-plugin/MenuInteraction.js").read_text())
        engine.evaluate((root / "menu-plugin/MenuModel.js").read_text())
        result = engine.evaluate("""
            var shipped = normalizeItem('apps', {label: 'Apps', provider: 'apps', action: 'omarchy-shell omarchy.dock apps'});
            var integrated = integratedApps([shipped])[0];
            var custom = normalizeItem('apps', {provider: 'apps', action: 'my-launcher'});
            var merged = mergeMenuSources([integrated], [custom]);
            [integrated.kind, integrated.action, integrated.provider,
             shipped.kind, shipped.action, integratedApps([custom])[0].action,
             merged.items.apps.action];
        """)
        self.assertFalse(result.isError(), result.toString())
        self.assertEqual(result.toVariant(), ["menu", "", "apps", "action",
            "omarchy-shell omarchy.dock apps", "my-launcher", "my-launcher"])

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
