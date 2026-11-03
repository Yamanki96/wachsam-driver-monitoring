# Wachsam

Experimenteller Windows-Prototyp zur Erkennung eines länger anhaltenden, gemessenen Augenschlusses mit einer Kamera. Entwickelt als studentisches Portfolio-Projekt von Yaman Kisanieh.

## Funktionsumfang und Grenzen

- Gesichtspunkte mit einem vortrainierten MediaPipe Face Landmarker.
- EAR je Auge; Alarm, wenn **beide** gültigen EAR-Werte unter 0,20 liegen und dies mindestens 1,0 s ohne Messunterbrechung anhält.
- Kopfrotation (Pitch/Yaw/Roll) und Kalibrierung der neutralen Kopfhaltung.
- Experimentelle Winkelgrenzen: Pitch ±15°, Yaw ±20°, Roll ±15°. Geprüft werden sowohl rohe als auch relative Winkel.
- Bei ungeeigneter Kopfhaltung, fehlendem Gesicht oder ungültiger Augengeometrie wird der Augenschluss-Zähler zurückgesetzt. Eine fehlende Messung bedeutet nicht, dass die Augen offen sind.
- Kein eigenständiger Kopfalarm in der finalen Variante. Normales kurzes Blinzeln löst keinen Alarm aus; eine validierte Blinzelfrequenzanalyse ist nicht implementiert.
- Tkinter-Oberfläche, Livebild, Kalibrierung, Start/Stopp, Tontest, CSV-Protokolle.

**Kein eigenes Modelltraining, keine medizinische Diagnose, kein validiertes Fahrzeugsicherheitssystem. Nur im stationären Versuchsaufbau testen. Nicht während echter Fahrten auf den Prototyp verlassen.**

## Projektdateien

| Datei | Zweck |
|---|---|
| `app.py` | Oberfläche, Kamera-Worker, Auswertung, Ton und Sitzungsprotokoll |
| `main.py` | Gemeinsame Messfunktionen, Einstellungen und Ressourcenpfade |
| `face_landmarker.task` | Enthaltenes vortrainiertes Modell |
| `requirements.txt` | Direkte Python-Abhängigkeiten, ohne behauptete Versionsfixierung |
| `Wachsam_Bericht.tex` / `.pdf` | Technische Dokumentation |
| `data/` | Zwei aufbereitete historische Beispielsitzungen mit unterschiedlichem Entwicklungsstand |

Dieses vollständige Quellcodepaket enthält die überarbeiteten Originaldateien, das Modell, Dokumentation und historische Messprotokolle. Eine neu gebaute EXE ist nicht enthalten. Die vorhandene Desktop-EXE bleibt unverändert, bis auf Windows neu gebaut wird. Siehe `CHANGELOG.md` und `TESTING.md`.

## Voraussetzungen

Windows 10/11, Kamera und Audioausgabe. Im Entwicklungsversuch wurde Python 3.12 verwendet. `winsound` gehört zur Windows-Python-Standardbibliothek; Tkinter ist bei der verwendeten Python-Installation vorhanden. Kamera für Desktop-Apps in den Windows-Datenschutzeinstellungen erlauben.

## Installation und Start aus dem Quellcode

PowerShell im Projektordner öffnen:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Falls die verwendete MediaPipe-Version nicht zu den vorhandenen APIs passt: die Versionen der funktionierenden Entwicklungsumgebung übernehmen. Nicht ungeprüft beliebige Paketversionen als getestet deklarieren.

Das Modell ist enthalten. Bei einer späteren Neuerstellung aus der offiziellen MediaPipe-Dokumentation herunterladen und als `face_landmarker.task` neben `main.py` ablegen: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python

## Bedienung

1. **TON TESTEN**: Audioausgabe prüfen. Dies testet nicht den Erkennungsalgorithmus.
2. **STARTEN**: Kamera öffnen.
3. **KALIBRIEREN**: Gerade zur Kamera schauen und ruhig halten. Mindestens 2 s und 20 verwertbare Bilder; bei Bewegung oder Messausfall wird erneut gesammelt. Die Kalibrierung betrifft den Kopf, nicht die EAR-Schwelle.
4. Auf **Überwachung aktiv** warten.
5. Im stationären Test die Augen bewusst länger als 1 s schließen. Bei gültiger Messung erscheinen Alarm und Ton. Augen öffnen beendet den Alarmzustand.
6. **STOPPEN**: Kamera freigeben und Sitzung abschließen.

### Zustände

| Zustand | Bedeutung |
|---|---|
| `OPEN` | Beide Augenmessungen gültig; Bedingung für beidseitigen Schluss nicht erfüllt |
| `CLOSED` | Beide EAR-Werte unter Schwelle, Zeitgrenze noch nicht erreicht |
| `ALERT` | Gemessener Schluss erreicht die Zeitgrenze |
| `NOT_CALIBRATED` / `CALIBRATING` | Kopfkalibrierung fehlt oder läuft |
| `NO_FACE` | Gesicht nicht erkannt |
| `HEAD_UNAVAILABLE` | Kopfrotation nicht verfügbar |
| `EYE_MEASUREMENT_UNCERTAIN_HEAD_POSE` | Experimentelle Winkelgrenzen überschritten |
| `EYE_GEOMETRY_UNAVAILABLE` | Geometrische Messprüfung fehlgeschlagen |
| `CAMERA_READ_FAILED` | Kamerabild nicht gelesen |

Auch ein gültiger Messwert beweist nicht, dass eine verdeckte Augenpartie zuverlässig erkannt wurde.

## Standalone-Version erstellen

Die Quellcode-Version zuerst prüfen und schließen. In derselben funktionierenden Windows-Python-Umgebung:

```powershell
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean Wachsam.spec
```

Anschließend `dist\Wachsam\Wachsam.exe` öffnen. **Den gesamten Ordner `dist\Wachsam` weitergeben**, nicht nur die EXE. Auf einem weiteren geeigneten Windows-Rechner muss kein VS Code installiert sein; die tatsächliche Funktion dort separat prüfen. Nach Quellcodeänderungen neu bauen. Bei Buildfehlern Schreibweise prüfen: `PyInstaller`, `--add-data`, `app.py`.

## Protokolle

Entwicklung: `app_log_*.csv` neben den Python-Dateien. Paketierte Version mit angepasstem `main.py`: `%LOCALAPPDATA%\Wachsam\logs`.

Die Anwendung speichert Messwerte und Zustände, kein Video. Roh-EAR-Werte können auch in ungültigen Zuständen vorhanden sein und dürfen dann nicht als gültige Augenschlussentscheidung interpretiert werden. Zeitlücken über 0,5 s setzen den Zähler zurück.

Siehe `LOGS.md` für Datenfelder, Versionsunterschiede und die Auswertung. Die Beispielprotokolle sind Entwicklungsdaten; sie belegen keine Erkennungsgenauigkeit für echte Müdigkeit.

## Reproduzierbarkeit

Versionen der tatsächlich getesteten Umgebung festhalten:

```powershell
python --version
python -m pip freeze > requirements-lock.txt
```

Zusätzlich Windows-Version, Kamera, Position, Beleuchtung, Brille, Einstellungen, Codeversion und Testbedingungen dokumentieren. `requirements-lock.txt` vor Veröffentlichung auf lokale Pfade/private Paketquellen prüfen.

## Weiterentwicklung

Zuerst Kameraposition, Beleuchtung, Messverfügbarkeit und individuelle EAR-Kalibrierung untersuchen. Zusätzliche Kameras oder NIR-Hardware sind prüfbare Optionen, kein garantierter Ersatz für Validierung. Vier Kameras werden nicht als notwendige oder optimale Konfiguration behauptet.

## Quellen und Unterstützung

- MediaPipe: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python
- Soukupová & Čech (2016), EAR-Grundlage: https://cmp.felk.cvut.cz/ftp/articles/cech/Soukupova-CVWW-2016.pdf
- PyInstaller: https://pyinstaller.org/en/stable/usage.html

Implementierung und Fehlersuche wurden mit KI-Unterstützung entwickelt. Das Projekt verwendet einen vorhandenen Landmark-Detektor und eigene regelbasierte Auswertung; es wurde kein eigener Müdigkeitsklassifikator trainiert.

## Analyse und Tests

```powershell
python -m pip install -r requirements-analysis.txt
python analyze.py --csv data/session_gui.csv --output session_plot.png
python -m unittest discover -s tests -v
```

Ohne `--csv` wird die zuletzt geänderte GUI- oder Augenaufzeichnung gesucht. `head_tracking.py` bleibt ein separates Diagnoseprogramm. Die 24 ursprünglichen CSV-Dateien liegen unverändert in `archive/logs/`; sie werden für den Programmstart nicht benötigt. Vor einer öffentlichen Veröffentlichung persönliche Aufzeichnungen prüfen. Die synthetischen Tests prüfen Rechen- und Zeitlogik, keine Genauigkeit für Müdigkeit.
