# Prüfstand der überarbeiteten Quellen

18 automatisierte Tests erfolgreich (`python -m unittest discover -s tests -v`). Geprüft: synthetische offene/geschlossene Augengeometrie; degenerierte, nicht endliche und außerhalb des Bildes liegende Punkte; gültige Rotationsprojektion; Winkel und Abstände; Kopfgrenzen; Alarmgrenze von 1,0 s; Rücksetzen bei offenem Auge, ungültiger Messung und Unterbrechung.

Zusätzlich: Python-Syntaxprüfung und Diagrammexport einer enthaltenen GUI-Beispielsitzung.

Diese Prüfungen wurden in einer Linux-Umgebung durchgeführt. Die Windows-Oberfläche, Kamera, Audioausgabe und ein neuer PyInstaller-Build konnten hier nicht ausgeführt werden. Sie müssen nach dem Austausch auf Windows erneut geprüft werden. Die bisherigen Kameraversuche sind historische Entwicklungsversuche und keine Validierung dieser Änderung.

Keine Aussage über Accuracy, Precision oder Recall für tatsächliche Müdigkeit. Keine neu erstellte EXE enthalten.
