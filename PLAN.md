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
- [ ] Windows-build uitvoeren en op een schone pc starten

## Fase 2 — observatie

- [x] Home, menu, battle en results via live Engelse UI-tekst onderscheiden
- [ ] herkenning met echte MuMu-frames valideren
- [ ] pop-up en onbekend scherm onderscheiden
- [ ] Engelse UI en ondersteunde resolutie controleren
- [x] bedragen, builderstatus en Town Hall-tekst parseren
- [x] OCR-tekst met positie aan builder- en Town Hall-labels koppelen
- [ ] OCR-tekst aan de juiste resource- en builderpositie koppelen
- [ ] confidence en harde stop bij onzekere observatie

## Fase 3 — progression

- [ ] upgradeprioriteiten als instellingenbestand
- [ ] dry-run met voorstel voor één upgrade
- [x] kosten, vrije builder en resource in een pure veiligheidsregel verifiëren
- [ ] één upgrade starten en het resultaat bevestigen
- [ ] nooit gems gebruiken

## Fase 4 — army en battle

- [ ] army status en training
- [ ] tegenstander beoordelen op lootdrempel
- [ ] één gecontroleerde aanval uitvoeren
- [ ] battle-resultaat herkennen en terugkeren

## Fase 5 — autonome loop

- [ ] state-machine koppelen aan de modules
- [ ] pop-up, disconnect en restart recovery
- [ ] stopknop, statuslog en lange duurtest
- [ ] Windows-release en installatiehandleiding
