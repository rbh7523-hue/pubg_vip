[app]
title = PUBG VIP Hub
package.name = pubgviphub
package.domain = org.murtadha
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
version = 1.0
icon.filename = %(source.dir)s/icon_v3.png
requirements = python3,kivy==2.2.1,kivymd==1.2.0,pillow,requests,urllib3,idna,charset-normalizer,certifi,openssl,arabic-reshaper==3.0.0,python-bidi==0.4.2
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
