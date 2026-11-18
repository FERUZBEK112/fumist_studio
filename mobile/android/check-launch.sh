set -eu
adb install -r FUMIST-Studio-1.3.1-build2.apk
adb shell am start -W -n uz.fumist.studio/.Studio
for attempt in $(seq 1 32); do
    adb shell uiautomator dump /sdcard/studio.xml >/dev/null || true
    tree=$(adb shell cat /sdcard/studio.xml 2>/dev/null || true)
    if [[ "$tree" == *'package="uz.fumist.studio"'* && "$tree" == *'class="android.webkit.WebView"'* && "$tree" == *'class="android.widget.Button"'* ]]; then
        exit 0
    fi
    sleep 2
done
echo "Editor controls were not visible inside FUMIST Studio." >&2
exit 1
