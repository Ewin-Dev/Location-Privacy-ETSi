# Dokumentation

##### dummy-grid.net.xml

Erstellt mittels [`netgenerate`](https://sumo.dlr.de/docs/netgenerate.html) mit Parametern `--grid --grid.number=4 --default.lanenumber=2 --grid.length=100`. <br>
Erzeugt ein rechteckiges Straßennetz mit 4×4 Straßennetz mit 2 Richtungen pro Fahrbahn und 2 Fahrstreifen je Richtung.

##### dummy-grid-tls.net.xml

Wie `dummy-grid.net.xml`, aber mit händisch per [`netedit`](https://sumo.dlr.de/docs/Netedit/index.html) eingefügten Ampeln

##### dummy-trips.xml

Handgeschrieben, erzeugt 5 Fahrzeuge auf `dummy-grid.net.xml` mit `id` 1–5, verteilten Startpunkten und -zeiten unten links im `dummy-grid` mit gleichem Endpunkt ganz oben rechts

##### dummy-rout.rou.xml

Erst erzeugt durch [`duarouter`](https://sumo.dlr.de/docs/duarouter.html) auf `dummy-trips.xml`, dann händisch die Routen korrigiert, dass die Fahrzeuge nicht dieselben Routen fahren. <br>
Version mit gleichen Routen, aber Ampeln, ist `dummy-rout-tls.rou.xml` auf `dummy-grids-tls.net.xml`

<hr>

##### dummy-detectors.add.xml

Mittels [`generateTLSE1Detectors.py`](https://sumo.dlr.de/docs/Tools/Output.html#generatetlse1detectorspy) an den Kreuzungen 96 [`induction loops`](https://sumo.dlr.de/docs/Simulation/Output/Induction_Loops_Detectors_%28E1%29.html) erzeugt. <br>
Erfordert Ampeln an den Kreuzungen, nutzt als Netz also `dummy-grid-tls.net.xml`. Ohne Ampeln scheint es nicht zu gehen. 🚦

##### dummy.sumocfg

Simuliert `dummy-rout` auf `dummy-grid`. Nutzt die `induction loops` mittels `dummy-detectors.add.xml` und schreibt [`FCDOutput`](https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html) in `dummy-grid.output.xml`

##### dummy-tls.sumocfg

Simuliert `dummy-rout-tls` auf `dummy-grid-tls`. Nutzt die `induction loops` mittels `dummy-detectors.add.xml` und schreibt keinen Output

##### dummy-grid.output.xml

Ist [`FCDOutput`](https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html) von `dummy.sumocfg`

<hr>

##### dummy.py

folgt

