# Eigen CoC-bot: uitvoering en acceptatie

## Controle op 20 september 2026

Repo: dannie1991/CoC-Autonomous-Bot-v1. De oorspronkelijke code bevatte
een passieve controller, ADB-opdrachten en een classifier die altijd UNKNOWN gaf.
De oudere m24842/CoC_Bot is een ander project en wordt niet als basis gebruikt.

## 1. MuMu en observatie

- [x] Eigen lokale checkout en Python-omgeving.
- [x] MuMu executable detecteren en adres uit MuMuManager lezen.
- [x] Expliciete apparaatselectie; meerdere apparaten niet willekeurig kiezen.
- [x] PNG valideren, bruikbare foutmeldingen en JSON-observaties bewaren.
- [x] Werkelijk beeld van 1920x1080 ontvangen.

## 2. Dorpsherkenning en verzamelen

- [x] Meerdere onafhankelijke UI-ankers voor HOME.
- [x] Andere resolutie, ontbrekende ankers en gedimde overlays afwijzen.
- [x] Lokale kalibratie van accountnaam en resourcebubbels.
- [x] Begrensde verzamelcyclus met nieuwe observatie voor elke klik.
- [x] Live verzamelcyclus en gewijzigde resources verifiëren: goud 102 -> 2789,
  elixer 394 -> 3782; twee klikken, daarna gestopt zonder resterende bubbels.

## 3. Voortgang van het dorp

Nog te implementeren: OCR voor goud/elixer/bouwers/stadhuisniveau, upgrade-menu
herkennen, kosten en beschikbare bouwers controleren, prioriteiten bepalen,
upgrade starten en resultaat bevestigen. Daarna nieuwe gebouwen plaatsen en
laboratorium/helden toevoegen wanneer het account die vrijspeelt.
Acceptatie: een beschikbare bouwer start één bedoelde upgrade zonder edelstenen,
met voor- en nabeeld en stop bij onvoldoende middelen of onzekere herkenning.

## 4. Leger en aanvallen

Nog te implementeren: legerstatus, aanvalsmenu, tegenstanderbeoordeling,
troepplaatsing, afloop en terugkeer. Eerst één complete bewaakte aanval testen;
daarna pas herhaling. Geen vaste schermcoördinaten zonder actuele herkenning.

## 5. Autonome cyclus en herstel

Controller aan de bewezen modules koppelen, time-outs/recovery begrenzen,
stopknop en statusvenster toevoegen. Builder Base krijgt afzonderlijke beelden
en regels. Acceptatie: langdurige test inclusief netwerkuitval, onbekende popup,
accountwissel en herstart. De huidige code is nog geen volledige autonome bot.

Screenshots, accountkalibratie en rapporten blijven lokaal in genegeerde mappen.
