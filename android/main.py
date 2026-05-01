"""Kivy wrapper around namfetch so it can run as an Android APK / iOS .ipa."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import namfetch

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock


class NamFetchApp(App):
    title = "namfetch"

    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.09, 1)
        self.detected = namfetch.detect_os()

        outer = BoxLayout(orientation="vertical", padding=20, spacing=8)

        title = Label(
            text=f"[b]namfetch[/b]  [i]({self.detected})[/i]",
            markup=True,
            font_size="22sp",
            size_hint_y=None,
            height=60,
            color=(0.55, 0.85, 1, 1),
        )
        outer.add_widget(title)

        self.body = BoxLayout(
            orientation="vertical", padding=10, spacing=4, size_hint_y=None,
        )
        self.body.bind(minimum_height=self.body.setter("height"))

        sv = ScrollView()
        sv.add_widget(self.body)
        outer.add_widget(sv)

        refresh = Button(
            text="Refresh", size_hint_y=None, height=56,
            background_color=(0.4, 0.6, 1, 1),
        )
        refresh.bind(on_press=lambda *_: self.populate())
        outer.add_widget(refresh)

        Clock.schedule_once(lambda *_: self.populate(), 0)
        return outer

    def populate(self):
        self.body.clear_widgets()
        for k, v in namfetch.collect(self.detected):
            row = Label(
                text=f"[b][color=66ccff]{k}[/color][/b]   {v}",
                markup=True,
                font_size="15sp",
                size_hint_y=None,
                height=42,
                halign="left",
                valign="middle",
            )
            row.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            self.body.add_widget(row)


if __name__ == "__main__":
    NamFetchApp().run()
