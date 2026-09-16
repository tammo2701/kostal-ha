# Kostal Piko – Home Assistant Integration (alte Serie, inkl. PIKO 10.1)

Custom-Integration für Home Assistant, die Wechselrichter der **alten**
Kostal-Piko-Serie (nicht Plenticore!) über deren lokale, unauthentifizierte
JSON-Schnittstelle `/api/dxs.json` ausliest.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tammo2701&repository=kostal-ha&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=kostal)

> **Wichtig:** Die beiden Buttons funktionieren erst, wenn `DEIN-GITHUB-NAME`
> oben durch deinen tatsächlichen GitHub-Benutzernamen ersetzt wurde **und**
> der Code unter genau diesem Namen/Repository auf GitHub veröffentlicht ist
> (siehe Abschnitt „HACS – Voraussetzungen“ unten). Ohne echtes GitHub-Repo
> zeigt HACS nichts zum Installieren an – das ist kein Fehler in Home
> Assistant, sondern fehlt schlicht die Datenquelle.

## Kompatibilität

Unterstützt werden alle Kostal-Piko-Wechselrichter mit Webserver-Version
≥ 6.00, u. a.:

- **PIKO 10.1** (Hauptzielgerät dieser Integration)
- PIKO 4.2, 5.5, 7.2, 8.3, 9.3, 10, 12, 15, 17, 20, 36
- PIKO BA-Varianten (mit Batteriewerten, sofern vom Gerät geliefert)

**Nicht unterstützt:** Kostal **Plenticore** (Hybridwechselrichter). Dafür
gibt es die offizielle, in Home Assistant Core enthaltene „Kostal
Plenticore Core“-Integration, die ein anderes Protokoll (pykoplenti)
verwendet.

Ob dein Gerät unterstützt wird, kannst du vorab im Browser testen:

```
http://<IP-DEINES-WECHSELRICHTERS>/api/dxs.json?dxsEntries=16777984
```

Kommt eine JSON-Antwort mit dem Namen deines Wechselrichters zurück
(`{"dxsEntries":[{"dxsId":16777984,"value":"..."}], ...}`), funktioniert
die Integration.

## Funktionsweise

Alle paar Sekunden fragt die Integration in einem Rutsch ca. 35 bekannte
„DXS-IDs“ des Wechselrichters ab (Momentanleistungen, Tages-/Gesamtertrag,
Spannungen/Ströme je String und Netzphase, Eigenverbrauch, Autarkiegrad,
Betriebsstatus usw.). Beim ersten Abruf wird automatisch erkannt, welche
Werte dein konkretes Gerät liefert (z. B. 2 statt 3 DC-Strings, mit/ohne
Batteriewerte) – nur dafür werden dann auch Sensoren angelegt.

Die Schnittstelle ist **reine Lesezugriff (read-only)**: Die alte Piko-Serie
bietet über diese API keine Steuerbefehle (kein Schreiben von Leistungs-
begrenzung o. ä.), daher enthält diese Integration bewusst keine
Switch-/Number-Entities.

## Enthaltene Sensoren (Auswahl, je nach Gerät)

| Bereich | Sensoren |
|---|---|
| Übersicht | AC-Ausgangsleistung, DC-Gesamtleistung, Eigenverbrauch aktuell, Betriebsstatus |
| Statistik heute | Ertrag, Hausverbrauch, Eigenverbrauch, Eigenverbrauchsquote, Autarkiegrad |
| Statistik gesamt | Ertrag, Hausverbrauch, Eigenverbrauch, Eigenverbrauchsquote, Autarkiegrad, Betriebszeit |
| DC-Strings 1–3 | Spannung, Strom, Leistung je String |
| AC-Netz | Netzfrequenz, cos(phi), Spannung/Strom/Leistung je Phase L1–L3 |
| Hausverbrauch | aus PV, aus Batterie, aus Netz, je Phase |

Ertrags-Sensoren (heute/gesamt) sind als `total_increasing` markiert und
eignen sich damit direkt für das **Energie-Dashboard** von Home Assistant.

## Installation

### Manuell

1. Ordner `custom_components/kostal_piko` in das `custom_components`-
   Verzeichnis deiner Home-Assistant-Konfiguration kopieren (Endstruktur:
   `config/custom_components/kostal_piko/...`).
2. Home Assistant neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen** →
   „Kostal Piko“ suchen.

### Über HACS (Custom Repository)

#### Voraussetzungen

HACS kann **nur echte, öffentliche GitHub-Repositories** laden. Die
Buttons/Links oben funktionieren also erst, nachdem:

1. Du ein eigenes **öffentliches** GitHub-Repository angelegt hast
   (z. B. `ha-kostal-piko`).
2. Der komplette Inhalt dieses ZIPs (inkl. `custom_components/kostal_piko/…`
   und `hacs.json` im Repo-Root) dort hochgeladen/gepusht wurde.
3. Du im Repo unter **Releases** mindestens **einen Release/Tag** erstellt
   hast (z. B. `v1.0.0`). Ohne Release zeigt HACS das Repository zwar an,
   aber es taucht nichts zum Herunterladen auf bzw. der Download-Button
   bleibt inaktiv – das ist die häufigste Ursache für „es passiert nichts“.
4. Optional: `codeowners`, `documentation` und `issue_tracker` in
   `custom_components/kostal_piko/manifest.json` sowie die Owner/Repository-
   Angaben in den Badges oben an deinen echten GitHub-Namen anpassen.

#### Installation

1. Ersten Badge-Link oben anklicken **oder** manuell: HACS → Menü (⋮
   oben rechts) → „Benutzerdefinierte Repositories“ → URL
   `https://github.com/DEIN-GITHUB-NAME/ha-kostal-piko` einfügen, Kategorie
   **„Integration“** wählen, „Hinzufügen“ klicken.
2. Das Repository in der HACS-Liste suchen/öffnen und über den
   Download-Button (unten rechts) installieren.
3. Home Assistant neu starten.
4. Zweiten Badge-Link oben anklicken **oder** manuell: **Einstellungen →
   Geräte & Dienste → Integration hinzufügen** → „Kostal Piko“ suchen.

Falls du keine eigene GitHub-Veröffentlichung möchtest, überspringe HACS
komplett und nutze die manuelle Installation oben – das Ergebnis ist
funktional identisch, nur ohne automatische Update-Benachrichtigung.

## Einrichtung

Im Einrichtungsdialog werden abgefragt:

- **IP-Adresse/Hostname** des Wechselrichters (erforderlich)
- **HTTPS verwenden** (optional, Standard: aus)
- **Benutzername/Passwort** (optional). Für einige zusätzliche Werte
  verlangt die Firmware eine Anmeldung. Kostal vergibt werkseitig
  Benutzername `pvserver` und Passwort `pvwr` – bitte in den
  Wechselrichter-Einstellungen ändern und hier entsprechend eintragen.
- **Abfrageintervall** in Sekunden (Standard: 30, Minimum: 10 – ein zu
  kurzes Intervall kann ältere Wechselrichter überlasten).

Das Abfrageintervall lässt sich später jederzeit über die
Integrations-Optionen anpassen.

## Fehlerbehebung

- „Verbindung fehlgeschlagen“: IP-Adresse prüfen, obigen Browser-Test
  durchführen, ggf. Firewall/VLAN zwischen Home Assistant und Wechselrichter
  prüfen.
- „Anmeldedaten abgelehnt“: Benutzername/Passwort leer lassen oder die
  tatsächlich am Gerät hinterlegten Zugangsdaten eintragen.
- Es fehlen einzelne Sensoren (z. B. String 3 oder Batteriewerte): Diese
  DXS-IDs liefert dein Gerät nicht – das ist normal und modellabhängig.

## Haftungsausschluss

Diese Integration nutzt eine von Kostal nicht offiziell dokumentierte
Schnittstelle, die auf Community-Recherchen (u. a. Tafkas, klausenbusk,
msxfaq.de, openWB-Forum) beruht. Funktionsumfang und Feldnamen können sich
je nach Firmware-Version unterscheiden.
