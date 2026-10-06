"""Acesso isolado às rotinas de diagnóstico e smoke test do jogo."""

import json
import os
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication


class DevAccess:
    """Mantém flags, validações e efeitos de desenvolvimento fora do jogo."""

    def __init__(self, argv=None, environ=None):
        self.argv = list(sys.argv if argv is None else argv)
        self.environ = os.environ if environ is None else environ
        self.enabled = "--smoke-test" in self.argv

    def validate_launch(self):
        if not self.enabled:
            return
        if not self.environ.get("PESCA_IDLE_SAVE_PATH"):
            raise RuntimeError("Defina PESCA_IDLE_SAVE_PATH para não tocar o progresso real.")
        if not self.environ.get("PESCA_IDLE_SMOKE_DIR"):
            raise RuntimeError("Smoke test requer save e diretório de saída isolados.")

    def prepare_window(self, game):
        if self.enabled:
            game.setAttribute(Qt.WA_DontShowOnScreen, True)

    def schedule_smoke_test(
        self, game, shop_dialog, encyclopedia_dialog, icon_factory,
        pets, flags, scene_size,
    ):
        if not self.enabled:
            return
        output = Path(self.environ["PESCA_IDLE_SMOKE_DIR"])
        output.mkdir(parents=True, exist_ok=True)
        QTimer.singleShot(
            250,
            lambda: self._capture_smoke_test(
                game, shop_dialog, encyclopedia_dialog, icon_factory,
                pets, flags, scene_size, output,
            ),
        )

    def _capture_smoke_test(
        self, game, shop_dialog, encyclopedia_dialog, icon_factory,
        pets, flags, scene_size, output,
    ):
        try:
            from datetime import datetime

            game.fase = 2.0
            game.grab().save(str(output / "executavel.png"))
            current = game._render.lighting.at()
            for hour in (0, 6, 9, 12, 18, 22):
                game._preview_clock = datetime(2026, 10, 6, hour)
                game.grab().save(str(output / f"horario-{hour:02d}-executavel.png"))
            game._preview_clock = None

            shop = shop_dialog(game)
            shop.setAttribute(Qt.WA_DontShowOnScreen, True)
            shop.show()
            shop.grab().save(str(output / "loja-executavel.png"))
            shop.accept()

            encyclopedia = encyclopedia_dialog(game)
            encyclopedia.setAttribute(Qt.WA_DontShowOnScreen, True)
            encyclopedia.show()
            encyclopedia.grab().save(str(output / "enciclopedia-executavel.png"))
            encyclopedia.accept()

            (output / "resultado.json").write_text(json.dumps({
                "assets": not game._render.background.isNull(),
                "scene": list(scene_size),
                "window": [game.W, game.H],
                "save": str(self.environ["PESCA_IDLE_SAVE_PATH"]),
                "frozen": bool(getattr(sys, "frozen", False)),
                "ui_icon": not icon_factory("livro").isNull(),
                "cosmetic_sprites": len(game._render.cosmetics),
                "physical_scale": game.physical_scale,
                "device_pixel_ratio": game.devicePixelRatioF(),
                "clock_source": "device_local",
                "clock_position": current.position,
                "clock_label": current.label,
                "light_plates": len(game._render.lighting.frames),
                "animated_pets": sum(
                    game._render.pet(item, 0) != game._render.pet(item, 1)
                    for item in pets
                ),
                "animated_flags": sum(
                    game._render.flag(item, 0) != game._render.flag(item, 1)
                    for item in flags
                ),
            }), encoding="utf-8")
            game.sair()
        except Exception:
            self.write_failure()
            QApplication.exit(1)

    def write_failure(self):
        diagnostic_dir = self.environ.get("PESCA_IDLE_SMOKE_DIR")
        if diagnostic_dir:
            path = Path(diagnostic_dir)
            path.mkdir(parents=True, exist_ok=True)
            (path / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
