[app]
title = namfetch
package.name = namfetch
package.domain = org.namfetch

source.dir = .
source.include_exts = py,png,ttf

version = 1.0.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = 1

[buildozer]
log_level = 2
warn_on_root = 0
