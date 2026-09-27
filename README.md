# CoC Autonomous Bot

Windows-basis voor een Clash of Clans-bot die met een actieve MuMu-instance
communiceert via ADB. De bot is bedoeld als generieke distributie: er zitten
geen accounts, screenshots, dorpsbeelden of lokale kalibratiebestanden in de
repository of in de Windows-build.

## Ondersteunde eerste setup

- Windows 10/11
- MuMu Player met één actieve Android-instance
- Clash of Clans in het Engels
- 1280×720, 1600×900 of 1920×1080 als emulatorresolutie

De eerste release ondersteunt bewust één afgebakende setup. De app controleert
de verbinding en resolutie voordat een toekomstige gameplaymodule acties mag
uitvoeren.

## Wat werkt nu

- MuMu automatisch vinden via MuMuManager of ADB
- één actieve instance afdwingen
- ADB-verbinding en live PNG-frame valideren
- live beeld in het geheugen analyseren zonder frame op schijf te bewaren
- ondersteunde resolutie rapporteren
- HOME, attack-menu, zoeken, battle en results herkennen uit Engelse UI-tekst
- Windows `.exe` bouwen via GitHub Actions

Screenherkenning, upgrades, training en aanvallen zijn nog niet geïmplementeerd.
De applicatie stuurt in de huidige versie geen tikken of swipes naar Clash of
Clans.

## Lokaal draaien

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m cocbot.cli --doctor
.\.venv\Scripts\python.exe -m cocbot.cli --observe 3
```

`--doctor` geeft alleen ADB-status, de gevonden instance en resolutie terug.
`--observe` geeft JSON-observaties terug; geen beeldbestand wordt opgeslagen.
Gebruik `--serial host:port` als er meer dan één emulator actief is.

## Windows-build

De workflow **Windows build** maakt `CoCBot.exe` op Windows via
**Actions → Windows build → Run workflow**. Bij een versie-tag (`v*`) draait
dezelfde build automatisch. De workflow uploadt het bestand als
`CoCBot-Windows` artifact.

## Ontwikkelcontrole

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests scripts
```
