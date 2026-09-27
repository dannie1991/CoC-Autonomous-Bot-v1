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
- HOME, attack-menu, My Army, zoeken, battle, results en het Laboratorium herkennen uit Engelse UI-tekst
- bedragen, builderstatus en Town Hall-niveau veilig uit OCR-tekst parseren
- read-only dorpsstatus met resources uit de live HOME-HUD rapporteren
- instelbare upgradeprioriteiten en een gecontroleerde dry-run voor één voorstel
- pure army- en lootbeoordeling, plus gecontroleerde live navigatie naar een battle
- één herkenbare Loot Cart of verzamelindicator veilig eenmalig innen
- de inactiviteitspopup herladen en HOME opnieuw bevestigen
- de kosten van een geselecteerde Laboratoriumupgrade uitlezen zonder die te starten
- Windows `.exe` bouwen via GitHub Actions

De koppeling tussen OCR-tekst en resources en bouwers werkt voor de standaard
HOME-HUD. Training en algemene gebouwupgrades worden nog niet geautomatiseerd.
Invoeropdrachten vereisen steeds expliciet `--execute`; de upgrademodus is
alleen uitlezen en kan geen grondstoffen uitgeven.

## Lokaal draaien

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m cocbot.cli --doctor
.\.venv\Scripts\python.exe -m cocbot.cli --status
.\.venv\Scripts\python.exe -m cocbot.cli --watch 30
.\.venv\Scripts\python.exe -m cocbot.cli --open-attack-menu
.\.venv\Scripts\python.exe -m cocbot.cli --open-attack-menu --execute
.\.venv\Scripts\python.exe -m cocbot.cli --recover --execute
.\.venv\Scripts\python.exe -m cocbot.cli --find-match --execute
.\.venv\Scripts\python.exe -m cocbot.cli --start-matchmaking --execute
.\.venv\Scripts\python.exe -m cocbot.cli --return-home --execute
.\.venv\Scripts\python.exe -m cocbot.cli --collect-once --execute
.\.venv\Scripts\python.exe -m cocbot.cli --plan-laboratory-upgrade
.\.venv\Scripts\python.exe -m cocbot.cli --town-hall-status
.\.venv\Scripts\python.exe -m cocbot.cli --plan-upgrade laboratory --currency elixir --cost 100000 --priority-file config/upgrade-priorities.yaml
.\.venv\Scripts\python.exe -m cocbot.cli --observe 3
```

`--doctor` geeft alleen ADB-status, de gevonden instance en resolutie terug.
`--status` leest één tijdelijk HOME-frame, rapporteert herkende waarden en de veilige volgende toestand.
`--watch` herhaalt die veilige controle een begrensd aantal keer en stopt bij een onbekend scherm of popup.
`--open-attack-menu` toont standaard alleen een live OCR-gebaseerd klikplan; voeg uitsluitend bij gewenste MuMu-invoer `--execute` toe.
`--recover` werkt uitsluitend voor de herkende inactiviteitspopup en verifieert daarna HOME.
`--find-match` werkt uitsluitend vanaf het herkende attack-menu en verifieert daarna My Army.
`--start-matchmaking` werkt uitsluitend vanaf het herkende My Army-scherm en verifieert daarna zoeken of battle.
`--return-home` werkt uitsluitend vanaf een herkend resultaatscherm en verifieert daarna HOME.
`--collect-once` werkt uitsluitend voor één live herkende Collect-indicator en verifieert de gewijzigde dorpsstatus.
`--plan-laboratory-upgrade` leest alleen de live geselecteerde Laboratoriumkosten en valideert de beslissing zonder iets te starten.
`--town-hall-status` leest alleen de status van een live geselecteerd Stadhuis, inclusief of er al een upgrade loopt.

## Live validatie

Op 27 september 2026 is op de actieve MuMu-instance één volledige aanval
uitgevoerd met 7 Giants en 20 Barbarians. De bot doorliep HOME, attack-menu,
My Army, battle en Victory; de aanval eindigde met 100% schade en verzamelde
2.531 goud, 1.944 elixer en de 400/400-bonus. Daarna is een Loot Cart
verzameld: goud steeg van 12.590 naar 14.090 en elixer van 22.084 naar 23.500.

Een Laboratorium-upgrade van 12.500 elixer is beschikbaar met twee vrije
bouwers, maar vereist eerst een hoger Town Hall-niveau. Op 27 september 2026
is daarom eerst de Town Hall-upgrade van niveau 3 naar 4 gestart voor 12.500
goud; één bouwer blijft vrij. De standaardprioriteit behandelt Town Hall vóór
Laboratorium.
`--plan-upgrade` beoordeelt alleen een opgegeven voorstel en start nooit een upgrade.
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
