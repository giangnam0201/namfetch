"""Kivy wrapper around devfetch so it can run as an Android APK."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devfetch

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window


class DevFetchApp(App):
    title = "devfetch"

    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.09, 1)
        detected = devfetch.detect_os()

        info = [
            ("OS", devfetch.get_os(detected)),
            ("Host", devfetch.get_hostname()),
            ("User", devfetch.get_user()),
            ("Kernel", devfetch.get_kernel()),
            ("Arch", devfetch.get_arch()),
            ("Uptime", devfetch.get_uptime(detected)),
            ("Shell", devfetch.get_shell()),
            ("CPU", devfetch.get_cpu(detected)),
            ("Memory", devfetch.get_memory(detected)),
            ("Disk", devfetch.get_disk()),
            ("Python", devfetch.get_python()),
        ]

        outer = BoxLayout(orientation="vertical", padding=20, spacing=8)

        title = Label(
            text="[b]devfetch[/b]  ([i]" + detected + "[/i])",
            markup=True,
            font_size="22sp",
            size_hint_y=None,
            height=60,
            color=(0.55, 0.85, 1, 1),
        )
        outer.add_widget(title)

        body = BoxLayout(
            orientation="vertical",
            padding=10,
            spacing=4,
            size_hint_y=None,
        )
        body.bind(minimum_height=body.setter("height"))

        for k, v in info:
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
            body.add_widget(row)

        sv = ScrollView()
        sv.add_widget(body)
        outer.add_widget(sv)
        return outer


if __name__ == "__main__":
    DevFetchApp().run()
