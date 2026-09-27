# CoC-Autonomous-Bot-v1

Eigen Python-bot voor MuMu. Momenteel werken apparaatdetectie, screenshots,
gekalibreerde dorpsherkenning en begrensd verzamelen van goud en elixer.
Upgrades, aanvallen en een volledige autonome cyclus zijn nog niet geïmplementeerd.
Zie [PLAN.md](PLAN.md) voor de gecontroleerde uitgangssituatie en verdere fasen.

## Installeren (PowerShell, Python 3.11+)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

Open MuMu met Clash of Clans. MuMuManager levert het werkelijke ADB-adres,
inclusief het netwerkadres bij deze Hyper-V-configuratie. Bij meerdere instances
moet je `--serial host:port` opgeven. Een ander ADB-pad kan met `--adb`.

```powershell
.\.venv\Scripts\python.exe -m cocbot.cli --probe
.\.venv\Scripts\python.exe -m cocbot.cli --observe 5 --profile profiles/local/profile.json
.\.venv\Scripts\python.exe -m cocbot.cli --collect --profile profiles/local/profile.json
.\.venv\Scripts\python.exe -m cocbot.cli --collect --execute --profile profiles/local/profile.json
```

`--collect` toont standaard alleen een voorstel. `--execute` verzamelt maximaal
acht keer, controleert vóór elke klik opnieuw HOME en de gekalibreerde naam,
en stopt bij onbekend beeld, ander account, verkeerde resolutie of een bubble
die na een klik blijft staan. Ctrl+C stopt. Er draait geen achtergrondproces.
De accountcontrole is een vergelijking met een lokaal beeld, geen account-API.

Screenshots en JSON-rapporten staan in `artifacts/`; lokale kalibratie staat in
`profiles/local/`. Beide mappen worden niet naar Git geüpload. De huidige lokale
kalibratie is op 20 september 2026 gemaakt voor BETAAA, Engels, 1920x1080.
Zonder profiel blijven observaties UNKNOWN. Het kalibratiescript gebruikt alleen
de toen visueel gecontroleerde uitsneden: gebruik het niet blind op een ander
beeld/account. Bij gewijzigde interface moet de kalibratie opnieuw worden beoordeeld.

Instellingen via `COCBOT_ADB_PATH`, `COCBOT_ADB_SERIAL`,
`COCBOT_SCREENSHOT_TIMEOUT`, `COCBOT_POLL_INTERVAL`. `.env.example` is documentatie;
de CLI leest procesomgevingsvariabelen, geen `.env`-bestand.

## Verificatie

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests scripts
```

Live verzameling op BETAAA: goud 102 → 2789, elixer 394 → 3782. Het programma
voerde twee resourceklikken uit en observeerde daarna geen resourcebubbels meer.
Dit bewijst de verzamelstap op deze interface, niet volledige spelautonomie.

## Beelden voor de volgende stap: upgrades

`--survey-stage` maakt één screenshot en een JSON-observatie zonder te tikken of
te swipen. Zet zelf eerst het gewenste scherm in MuMu klaar en voer de opdracht
uit. Gebruik voor elk van de vijf schermen dezelfde optie `--profile`:

```powershell
.\.venv\Scripts\python.exe -m cocbot.cli --survey-stage home --profile profiles/local/profile.json
.\.venv\Scripts\python.exe -m cocbot.cli --survey-stage builders --profile profiles/local/profile.json
.\.venv\Scripts\python.exe -m cocbot.cli --survey-stage building --profile profiles/local/profile.json
.\.venv\Scripts\python.exe -m cocbot.cli --survey-stage upgrade --profile profiles/local/profile.json
.\.venv\Scripts\python.exe -m cocbot.cli --survey-stage confirmation --profile profiles/local/profile.json
```

De stages zijn: leeg hoofdscherm; open builderoverzicht; geselecteerd gebouw;
open upgradevenster met kosten; en hetzelfde venster bij onvoldoende resources of
een gem-aanbieding. Open die schermen uitsluitend zelf. De bot voert in deze
modus geen acties uit. De resultaten staan lokaal in `artifacts/` en worden
genegeerd door Git. Deze beelden zijn nodig om bouwers, valuta, kosten en
knoppen te kalibreren voordat een upgrade veilig kan worden geautomatiseerd.
