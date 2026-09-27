# Productplan

## Uitgangspunt

De publieke bot bevat geen persoonlijke screenshots, accountgegevens of lokale
profielen. Iedere gebruiker geeft de bot toegang tot een eigen live MuMu-frame
via ADB. Frames worden alleen tijdelijk in het geheugen gebruikt.

## Fase 1 — distributiebasis

- [x] MuMu- en ADB-detectie
- [x] veilige verbinding met één instance
- [x] live framevalidatie zonder bestandsopslag
- [x] resolutiecontrole
- [x] Windows-buildworkflow
- [x] Windows-build lokaal uitvoeren
- [ ] Windows-build op een schone pc starten

## Fase 2 — observatie

- [x] Home, menu, battle en results via live Engelse UI-tekst onderscheiden
- [x] herkenning met echte MuMu-frames valideren
- [x] pop-up en onbekend scherm onderscheiden
- [x] Engelse UI en 1920×1080-resolutie controleren
- [x] bedragen, builderstatus en Town Hall-tekst parseren
- [x] OCR-tekst met positie aan builder- en Town Hall-labels koppelen
- [x] OCR-tekst aan de juiste resource- en builderpositie koppelen
- [x] confidence en harde stop bij onzekere observatie
- [x] geselecteerd Stadhuis en lopende bouwstatus alleen-lezen herkennen

## Fase 3 — progression

- [x] upgradeprioriteiten als instellingenbestand
- [x] dry-run met voorstel voor één upgrade
- [x] kosten, vrije builder en resource in een pure veiligheidsregel verifiëren
- [x] één Town Hall-upgrade starten en het resultaat bevestigen
- [x] nooit gems gebruiken

## Fase 4 — army en battle

- [x] army status parser
- [ ] training starten en resultaat bevestigen
- [x] tegenstander beoordelen op lootdrempel
- [x] één gecontroleerde aanval uitvoeren
- [x] battle-resultaat herkennen
- [ ] resultaten-terugkeer live bevestigen

### Live validatie op 27 september 2026

- [x] HOME → attack-menu → My Army → battle → Victory doorlopen
- [x] 7 Giants en 20 Barbarians geplaatst; Victory met 100% schade
- [x] battle-opbrengst en Loot Cart-verzameling in live MuMu-frame bevestigd
- [ ] Laboratoriumupgrade van 12.500 elixer starten nadat Town Hall 4 klaar is

## Fase 5 — autonome loop

- [x] read-only state-machine koppelen aan schermobservaties
- [x] pop-up en onbekend scherm stoppen de normale flow in recovery
- [x] inactiviteitspopup gecontroleerd herladen en HOME verifiëren
- [x] kort laadscherm na herladen begrensd afwachten
- [ ] andere disconnect- en restartvarianten uitvoeren
- [x] begrensde read-only statuslog met harde recovery-stop
- [ ] lange duurtest op een actieve MuMu-instance
- [ ] Windows-release en installatiehandleiding
