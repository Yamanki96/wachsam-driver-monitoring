# Überarbeitung der gelieferten Projektdateien

- Originale Oberfläche und Messgrenzen beibehalten; alle Python-Kommentare und Docstrings auf Englisch vereinheitlicht.
- Gemeinsame Augenschluss-Zeitlogik in `main.py` extrahiert und mit 18 Tests geprüft.
- Fehler beim Anlegen von Sitzungsprotokollen werden im Worker behandelt; keine Protokollmeldung für eine nicht angelegte Datei.
- Alte Ereignismeldungen werden vor einer neuen Sitzung entfernt; bei Kameralesefehlern wird kein altes Livebild weiter angezeigt.
- `analyze.py` liest GUI- und Augenprotokolle, akzeptiert eine Dateiauswahl und kann Diagramme speichern.
- Build-Konfiguration verwendet relative Projektpfade. Analyse- und Build-Abhängigkeiten getrennt.
- Modell und 24 originale CSV-Aufzeichnungen übernommen. Alte Build-Ordner und EXE nicht in dieses Quellcodepaket kopiert.

Die EAR-Schwelle 0,20, Alarmdauer 1,0 s und experimentellen Kopfgrenzen wurden nicht geändert. Keine Erweiterung auf verdeckte Augen oder 360 Grad.
