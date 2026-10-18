<p align="center">
  <img src="https://raw.githubusercontent.com/tammo2701/kostal-ha/main/assets/banner.png" alt="Kostal PIKO Solar – Home Assistant Integration" width="100%">
</p>

<p align="center">
  <a href="https://github.com/tammo2701/kostal-ha/releases"><img alt="Release" src="https://img.shields.io/github/v/release/tammo2701/kostal-ha?style=for-the-badge&color=ffb703"></a>
  <a href="https://hacs.xyz"><img alt="HACS Custom" src="https://img.shields.io/badge/HACS-Custom-41bdf5?style=for-the-badge"></a>
  <img alt="Home Assistant" src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-18bcf2?style=for-the-badge">
  <img alt="IoT class" src="https://img.shields.io/badge/lokal-ohne%20Cloud-2ea44f?style=for-the-badge">
</p>

# Kostal PIKO Solar

Home-Assistant-Integration für **ältere Kostal-PIKO-Wechselrichter mit „PV Webserver“** – getestet mit dem **PIKO 10.1**. Die Werte werden lokal und ohne Cloud direkt vom Wechselrichter gelesen.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=tammo2701&repository=kostal-ha&category=integration"><img alt="In HACS öffnen" src="https://my.home-assistant.io/badges/hacs_repository.svg"></a>
  &nbsp;
  <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=kostal_piko"><img alt="Integration hinzufügen" src="https://my.home-assistant.io/badges/config_flow_start.svg"></a>
</p>

---

## Das bekommst du

| | |
|---|---|
| **Leistung** | AC-Ausgangsleistung, DC-Gesamtleistung |
| **Ertrag** | Tagesertrag und Gesamtertrag – direkt nutzbar im **Energie-Dashboard** |
| **Status** | Betriebsstatus des Wechselrichters (z. B. „Einspeisen MPP“) |
| **DC-Strings** | Spannung, Strom und Leistung je String (bis zu 3) |
| **AC-Phasen** | Spannung und Leistung je Phase L1 bis L3 |
| **Lokal** | Reiner Lesezugriff über das Heimnetz, keine Cloud, kein Konto |

Sensoren werden nur für die Werte angelegt, die dein Gerät tatsächlich anzeigt.

## Kompatibilität

Die Integration funktioniert mit PIKO-Wechselrichtern, deren Startseite den Titel **„PV Webserver“** trägt und per Login (HTTP Basic Auth) geschützt ist.

- ✅ **PIKO 10.1** (getestet)
- ❌ **PIKO IQ / Plenticore** – dafür gibt es die offizielle Home-Assistant-Integration „Kostal Plenticore“

**Schnelltest:** Öffne `http://<IP-DES-WECHSELRICHTERS>/` im Browser und melde dich mit Benutzer `pvserver` und Passwort `pvwr` an. Siehst du eine Seite mit AC-Leistung, Energie und PV-Generator, passt die Integration.

## Installation

### Über HACS (empfohlen)

1. In HACS oben rechts auf **⋮ → Benutzerdefinierte Repositories** gehen.
2. URL `https://github.com/tammo2701/kostal-ha` einfügen, Kategorie **Integration** wählen, **Hinzufügen**.
3. **Kostal PIKO Solar** in HACS öffnen und herunterladen.
4. Home Assistant **neu starten**.

### Manuell

1. Den Ordner `custom_components/kostal_piko` nach `config/custom_components/kostal_piko` kopieren.
2. Home Assistant **neu starten**.

## Einrichtung

**Einstellungen → Geräte & Dienste → Integration hinzufügen → „Kostal PIKO Solar“**

| Feld | Bedeutung | Vorgabe |
|---|---|---|
| IP-Adresse oder Hostname | Adresse des Wechselrichters im Heimnetz | – |
| HTTPS verwenden | Nur aktivieren, wenn dein Gerät HTTPS anbietet | aus |
| Benutzername | Login des PV Webservers | `pvserver` |
| Passwort | Login des PV Webservers | `pvwr` |
| Abfrageintervall | Sekunden zwischen zwei Abfragen (mindestens 10) | 30 |

Das Abfrageintervall kann später in den Optionen der Integration geändert werden. Ein zu kurzes Intervall kann den schwachen Webserver älterer Geräte überlasten.

## Entitäten

| Sensor | Einheit | Hinweis |
|---|---|---|
| AC-Ausgangsleistung | W | |
| DC-Gesamtleistung | W | Summe der Stringleistungen |
| Ertrag heute | Wh | setzt sich täglich zurück |
| Ertrag gesamt | kWh | steigt dauerhaft |
| Betriebsstatus | Text | z. B. „Einspeisen MPP“ |
| DC String 1–3 Spannung | V | Diagnose |
| DC String 1–3 Strom | A | Diagnose |
| DC String 1–3 Leistung | W | berechnet aus Spannung × Strom |
| AC Phase 1–3 Spannung | V | Diagnose |
| AC Phase 1–3 Leistung | W | Diagnose |

> Die Statusseite des Geräts zeigt keinen Strom pro AC-Phase und keinen Hausverbrauch. Dafür gibt es deshalb keine Sensoren.

### Energie-Dashboard

Unter **Einstellungen → Dashboards → Energie → Solarmodule hinzufügen** den Sensor **Ertrag gesamt** auswählen.

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| „Verbindung zum Wechselrichter konnte nicht hergestellt werden“ | IP-Adresse prüfen, Schnelltest im Browser machen, Netzwerk/VLAN zwischen Home Assistant und Wechselrichter prüfen. |
| „Anmeldedaten wurden abgelehnt“ | Benutzername und Passwort des PV Webservers prüfen (Werksvorgabe `pvserver` / `pvwr`). |
| „Invalid handler specified“ | Home Assistant nach der Installation oder dem Update **komplett neu starten**. |
| Integration erscheint doppelt | Doppelten Eintrag unter **Geräte & Dienste** entfernen und die Integration einmal neu hinzufügen. |
| Sensoren zeitweise „nicht verfügbar“ | Der Webserver des Wechselrichters antwortet nicht immer, etwa bei Standby. Die Werte kommen von selbst zurück. Bei häufigen Aussetzern das Abfrageintervall erhöhen. |

Für Fehlermeldungen im Log hilft die Suche nach `kostal` unter **Einstellungen → System → Protokolle**. Fehler und Wünsche gern als [Issue](https://github.com/tammo2701/kostal-ha/issues) melden.

## So funktioniert es

Der PIKO 10.1 hat keine JSON-Schnittstelle. Die Integration lädt deshalb bei jeder Abfrage die Startseite des PV Webservers (eine einzige Anfrage, mit Login) und liest die Werte aus der HTML-Tabelle. Es werden keine Daten an den Wechselrichter geschrieben.

## Hinweis

Inoffizielles Community-Projekt, nicht von Kostal. Der Seitenaufbau kann je nach Firmware-Version abweichen.