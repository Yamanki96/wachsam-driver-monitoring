# Messprotokolle und Evaluation

## Was mit den bisherigen Dateien tun?

Originale unverändert lokal archivieren. Neue Tests pro Sitzung speichern; alte und neue Programmstände nicht zusammenwerfen. Für GitHub genügt eine kleine, geprüfte Auswahl an Beispieldaten plus Beschreibung. Videos/Gesichter nicht ohne Einwilligung veröffentlichen. CSV-Messwerte sind ebenfalls personenbezogen behandelbar; Namen, private Pfade und unnötige Zeitangaben vor Veröffentlichung prüfen.

## Die zwei beigefügten Sitzungen

| ID | Ursprung | Einordnung |
|---|---|---|
| `session_gui` | Eingefügtes Markdown(1).md | GUI-Schema mit ausschließlich Augenschlussalarm; 193 Zeilen, Zeit 0,766–20,000 s |
| `session_legacy` | Eingefügter Text (2)(1).txt | Frühere Entwicklungsversion mit Kopfalarm; 1072 Zeilen, Zeit 1,344–108,609 s |

Die Markdown-Kopie enthielt `**`-Formatierung und HTML-Zeichenreferenzen. Nur diese Darstellungsreste wurden entfernt. Die andere Datei wurde als CSV neu serialisiert. Leere Messfelder bleiben leer, nicht null. Herkunft und SHA-256 der Originaldateien stehen in `data/session_manifest.json`. Die Originaldateien werden durch die Aufbereitung nicht verändert.

### Beobachtungen

GUI-Sitzung: 13 Alarmzeilen bilden **ein** zusammenhängendes Ereignis von 14,313 bis 15,484 s. Die erste Alarmzeile meldet 1,032 s Augenschluss. Die 13 Zeilen sind keine 13 unabhängigen Erfolge. 87 Zeilen sind nicht kalibriert, 20 in Kalibrierung, 47 OPEN, 11 CLOSED, 10 NO_FACE und 5 aufgrund der Kopfposition unsicher.

Legacy-Sitzung: 16 Zeilen EYE_CLOSURE bilden ein Ereignis ab 88,734 s; 71 Zeilen HEAD_ATTENTION bilden ein getrenntes Ereignis ab 99,172 s. Dort ist Augenschlusszeit 0,0 s möglich, weil der Kopfalarm unabhängig war. Insgesamt 604 Kalibrierungszeilen; eine längere Kalibrierungsphase ist sichtbar, der konkrete Grund ist aus diesem Protokoll nicht eindeutig bestimmbar. Alle Benutzerlabels sind UNLABELED. Diese Sitzung nicht zur Bewertung der final deaktivierten Kopfalarmfunktion verwenden.

## Datenfelder

- `elapsed_seconds`: Zeit seit Sitzungsstart, kein Video-Zeitstempel mit Ground Truth.
- `left_ear`, `right_ear`, `average_ear`: geometrische Rohwerte; nur mit Zustandsprüfung interpretieren.
- `closed_seconds`: Dauer der aktuellen gültigen beidseitigen Schließbedingung.
- `status`, `alert_active`: Messzustand und Alarmflag. Ein Alarmereignis besteht meist aus mehreren Zeilen.
- `pitch_deg`, `yaw_deg`, `roll_deg`: geschätzte Rotation relativ zur Kopfkalibrierung.
- `raw_*`: geschätzte Winkel vor Abzug der neutralen Haltung.
- `calibration_id`: 0 vor erfolgreicher Kalibrierung, danach Sitzungszähler.
- `eye_threshold`, `alert_seconds`, `max_eye_*`: verwendete Parameter.
- Alte Dateien: zusätzliche Kopfalarme und `user_label`; kein gleiches Schema für alle Versionen voraussetzen.

## Sinnvolle Auswertung

1. EAR-Verlauf je Auge über der Zeit mit Schwellwert darstellen.
2. Ungültige Messphasen und Kalibrierung gesondert markieren; fehlende Werte nicht als offene Augen behandeln.
3. Alarmereignisse als zusammenhängende Alarmphasen zählen.
4. Nutzbare Messdauer nach Kalibrierung getrennt von der Gesamtdauer berichten. Frame-Anteile sind bei variabler Abtastrate keine Zeitanteile.
5. Gegen unabhängig dokumentierte Testereignisse vergleichen. Ohne diese Zuordnung keine Accuracy, Precision oder Recall behaupten.

## Neuer Testplan

Je Bedingung mehrere Wiederholungen, zunächst am ruhenden Laptop:

| Bedingung | Erwartung |
|---|---|
| Frontal, Augen offen | Kein Augenschlussalarm |
| Natürliches Blinzeln | Kein Alarm bei kurzen Schlüssen |
| Frontal, absichtlich länger geschlossen | Alarm bei durchgehend gültiger Messung ab 1 s |
| Kopf nach unten, Augen offen | Kein reiner Kopfalarm; Gültigkeit prüfen |
| Kopf Richtung Schulter, Augen geschlossen | Möglicher Ausfall; als Einschränkung erfassen |
| Linke/rechte Drehung | Verfügbarkeit und Fehlalarme erfassen |
| Gesicht aus dem Bild | NO_FACE, Schließzähler zurückgesetzt |
| Stopp und Neustart | Kamera freigegeben, neue Sitzung |
| EXE-Version | Dieselben Basisfunktionen separat prüfen |

`test_results_template.csv` manuell ergänzen. `actual_eye_state` und `actual_head_action` werden durch Testperson/Beobachtung dokumentiert, nicht aus EAR oder automatischem Status übernommen. Ein kurzer Bildschirmmitschnitt kann bei Einwilligung die Zuordnung erleichtern. Ein simulierter Augenschluss ist kein Nachweis echten Schlafs.

## Kennzahlen erst nach Annotation

Erkannte/vorgegebene Schließereignisse, verpasste Ereignisse, Fehlalarme pro Testminute, Messverfügbarkeit und Warnlatenz berichten. Ereignisdefinition und Umgang mit Messausfällen vorher festlegen. Für unterschiedliche Personen und Bedingungen getrennt auswerten.
