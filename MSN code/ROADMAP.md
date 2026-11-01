# Roadmap — Neuromodulazione e adattamento in una SNN dei gangli della base, in closed loop con un robot

> **Domanda di ricerca:** stati neuromodulatori diversi (dopamina tonica/fasica, e altri) permettono alla *stessa* architettura SNN (MSN D1/D2, inibizione laterale, 3 canali) di cambiare strategia di action selection e di adattarsi a condizioni ambientali diverse (corridoio stretto, spazio aperto, ostacoli diversi) **senza riaddestrare da zero**, rispetto a una baseline senza neuromodulazione?

Punto di partenza: il codice in questa cartella (report *SC_Report_spiny*, Rusiecka 2022, derivato da González-Redondo et al. 2020).
Direzione di sviluppo: il report *SC_Report_BRL* (Casan Crespo 2022): actor-critic, TD error ≈ dopamina fasica, D1 attivato da TD>0 e D2 da TD<0, eligibility traces.

---

## Mappa delle fasi

```
F0 Igiene repo/env ─► F1 Studio del modello ─► F2 Riproduzione paper ─► F3 Refactoring
                                                                            │
           F7 Scrittura ◄─ F6 Esperimenti/baseline ◄─ F5 Closed loop robot ◄─ F4 Neuromodulazione
```

Ogni fase ha un **criterio di uscita**: non passare alla successiva finché non è soddisfatto.
La scrittura della tesi (F7) va avanti in parallelo: tieni un diario e scrivi i metodi via via.

---

## F0 — Igiene del repository e dell'environment (½–1 giorno)

Ambiente attuale (`env_nest`): **Python 3.11.18, NEST 3.8.0, NESTML 9.0.1**.
Il paper cita **NESTML 5.0.0-rc2** (2022) e nel repo c'è il sorgente `nestml-4.0/`: il codice è stato scritto per una versione di NESTML molto più vecchia di quella che hai.

- [x] Codice originale su GitHub (`diciottopolitico18/msn`, commit `a990187`, tag `original`).
- [x] Cartella locale collegata al repo (radice = `.../Codice/MSN code/`).
- [x] **`.gitignore`**: build NESTML, `__pycache__/`, file di sistema/editor, sorgenti di terze parti (`nest-simulator-master 2/`, `nestml-4.0/`).
- [x] **Ambiente**: `environment.yml` scritto a mano (conda-forge + NESTML via pip); versioni annotate nel README.
- [x] Porting a NEST 3.8 / NESTML 9 in un commit separato dall'originale.
- [ ] Verificare che `conda env create -f environment.yml` ricrei un ambiente funzionante (in un env di prova).

**Uscita:** repo pulito, primo commit = codice originale, `environment.yml` committato.

---

## F1 — Capire a fondo il punto di partenza (1–2 settimane)

### 1.1 Letture (in quest'ordine)
1. Izhikevich (2003), *Simple model of spiking neurons*: il modello base.
2. Humphries et al. (2009), *Capturing dopaminergic modulation… of striatal MSNs*: **la fonte delle equazioni D1/D2** e di quasi tutti i parametri.
3. González-Redondo et al. (2020), *A basal ganglia computational model… Huntington's disease*: il modello completo, l'esperimento a rampa e le metriche di selettività (transient/steady-state).
4. Moyer et al. (2007): da qui vengono gli effetti D1→NMDA e D2→AMPA.
5. Documentazione NEST 3.8 (Create/Connect, `receptor_type`, `spike_recorder`, `Prepare/Run/Cleanup`) e NESTML 9 (kernel, `convolve`, porte spike, `onCondition`).
6. Sutton & Barto, cap. 6 (TD) e 13 (actor-critic), più Gerstner et al. (2018) sulle eligibility traces a tre fattori: servono per F4.

### 1.2 Mappa equazioni del paper → codice
Fai tu questa verifica riga per riga: è il modo migliore per capire il modello.

| Paper (SC_Report_spiny) | Significato | Codice |
|---|---|---|
| Eq. 1 | dinamica di `v` | [msn.nestml:37](nest_module/msn.nestml#L37) (`V_m'`) |
| Eq. 2 | recovery `u` | `U_m'` |
| Eq. 3 | reset allo spike | blocco `onCondition` |
| Eq. 4 `v_r ← v_r(1+Kφ1)` | D1, corrente K⁺ | `inline v_r` (`c_1`=K, `y1`=φ1) |
| Eq. 5 `d ← d(1−Lφ1)` | D1, Ca²⁺ tipo L | `dop = d*(1-c_2*y1)` |
| Eq. 6 `k ← k(1−αφ2)` | D2, reobase | `inline k` (`alpha`, `y2`=φ2) |
| Eq. 7 | corrente sinaptica totale | `inline I_syn` |
| Eq. 8 | blocco Mg²⁺ NMDA (0.28 = 1/3.57) | `inline B` |
| Eq. 9 | correnti a conduttanza | `ampa`, `nmda`, `I_gaba` |
| Eq. 10 (h += S/τ) | sinapsi esponenziali | kernel + pesi divisi per τ in [msn_params.py](msn_params.py) |
| Eq. 11–12 | D1→NMDA (β1), D2→AMPA (β2) | `I_nmda`, `I_ampa` (`alpha_1`=β1, `alpha_2`=β2) |
| Tab. 1 | parametri D1/D2 | [msn_params.py](msn_params.py), `params.neuron.msn_d1/d2` |
| Tab. 2–3 | sinapsi ctx→MSN e MSN→MSN | [msn.py](msn.py) `_create_connections`, `_connect_msn_to_msn` |
| Sez. 3.3 | protocollo a rampa | [experiment.py](experiment.py) `ExperimentDAHD.run` |

Nota sui nomi: nel codice `y1, y2` sono φ1, φ2; `alpha_1, alpha_2` sono β1, β2; `c_1, c_2` sono K, L. Il "livello di dopamina" dell'esperimento imposta **φ1 = φ2 = DA** su entrambe le popolazioni.

### 1.3 Esercizi su un neurone singolo
Scrivili come script in `analysis/`: diventano figure del capitolo "Metodi".
- [ ] **Curva f–I** di un MSN D1 e di un D2 (corrente `I_e` a gradini), per DA ∈ {0, 0.3, 0.6, 1.0}. Confronta con le figure di Humphries 2009. È la prova che la modulazione D1/D2 è implementata correttamente.
- [ ] **Traccia di membrana** (`multimeter` su `V_m`, `U_m`): verifica il bistabile down-state/up-state tipico degli MSN.
- [ ] **PSP da un singolo spike** su ciascun recettore (AMPA, NMDA, GABA): verifica ampiezza, τ e segno. Serve anche alla F2 (vedi la semantica delle porte spike).

### 1.4 Capire la rete
- N = 0.3³ mm³ × 84900 ≈ **2292 MSN** (1146 D1 + 1146 D2), divisi in canali 40% / 40% / 20%.
- Ogni MSN riceve un **proprio** parrot neuron. Il Poisson del canale ha rate = f_ctx × 250 afferenze, quindi ogni MSN riceve un treno di Poisson indipendente che riassume 250 afferenze corticali.
- Inibizione laterale: `pairwise_bernoulli` con p = 728/2292 ≈ 0.318, **tra tutti** gli MSN (D1 e D2, tutti i canali), peso 0.25, GABA. Non è una topologia per canale: la competizione nasce dal fatto che il canale più attivo inibisce di più gli altri.
- Chiediti (e annota): cosa cambia tra D1 e D2 **in questa rete**? Solo i parametri neuronali (non c'è un'uscita GPe/SNr), quindi D1 e D2 differiscono solo per eccitabilità. Ti servirà quando dovrai decodificare l'output motorio.

**Uscita:** sai spiegare a voce ogni riga di `msn.nestml` e `msn.py`, e hai le figure f–I D1/D2.

---

## F2 — Riprodurre i risultati del paper (1–2 settimane)

### 2.1 Problemi già individuati nel codice (da risolvere o verificare)
Correggili uno alla volta, **un commit per ognuno**, così puoi misurare l'effetto di ciascuno.

**Compilazione / semantica NESTML (versione 9 contro 4/5)**
- [ ] Le porte di input sono dichiarate `spikes_ampa mV <- spike`. Nelle versioni recenti di NESTML la semantica delle porte spike (unità, moltiplicazione per il peso) è cambiata. Verifica con il test PSP di F1.3 che uno spike con peso *w* produca davvero un salto *w* in `I_syn_*`. Se non è così, i pesi vanno riscalati.
- [ ] `E_rev_AMPA/NMDA/GABA_A` sono dichiarati `real` ma sottratti a `V_m` (mV): rischio di errori o warning sulle unità. Dichiarali `mV`.
- [ ] Verifica la corrispondenza `receptor_type` 1/2/3 ↔ AMPA/NMDA/GABA con `nest.GetDefaults('msn_neuron')['receptor_types']`.
- [ ] Il reset scatta a `V_m >= 30 mV` (soglia scritta a mano), mentre il paper e `params` usano `V_th` = v_peak = 40 mV, che **non viene usato**. Il valore 30 mV è già nel codice originale (commit `a990187`), quindi la figura del paper è stata prodotta con 30 mV: per la riproduzione tienilo così, ma documenta la discrepanza con la Tab. 1.
- [ ] Il C++ generato dalla vecchia NESTML è nel commit originale (`git show a990187:"MSN code/nest_module/nestml_target/msn.cpp"`): confrontalo con quello generato da NESTML 9 per capire come venivano gestiti gli spike in ingresso.
- [ ] I default nel `.nestml` (τ = 2 ms, C = 100 pF…) sono diversi dalla Tab. 1. Vengono sovrascritti da `SetStatus`, ma controlla con `GetStatus` che i valori finali siano quelli del paper.

**Simulazione**
- [ ] `params.sim.step = 0.01` e `params.sim.n_threads = 6` **non vengono mai applicati** (nessun `nest.SetKernelStatus`): la simulazione gira a 0.1 ms e 1 thread. Prova entrambe le risoluzioni e documenta la differenza (Humphries usa 0.01 ms).
- [ ] Non viene impostato nessun seed: aggiungi `rng_seed` e ripeti su **≥ 10 seed**. Il paper mostra una sola run, ma tu riporterai media ± deviazione standard.
- [ ] La rampa (`fi = i/50`, i = 0…24) non raggiunge esattamente 3.6 / 2.2 Hz (si ferma a circa 98%): dettaglio minore, ma annotalo.

**Analisi / plotting**
- [ ] In [run_simulation.py](run_simulation.py) il firing rate è diviso per il numero di neuroni **che hanno sparato almeno una volta** (`np.unique(senders)`), mentre `MSN.plot_activity` divide per **tutti** i neuroni del canale (`GetConnections`). Il primo sovrastima i rate a bassa attività. Scegli una definizione (consiglio: tutti i neuroni del canale) e usala ovunque.
- [ ] `MSN._compute_signals` / `MSN.signal` sono rotti: `signal` è sia il nome del metodo sia `scipy.signal` (mai importato) e `itemgetter` non è importato. Di conseguenza le metriche `transient_selectivity` / `steadystate_selectivity` non funzionano. **Ti servono**: sono le metriche di González-Redondo.
- [ ] `ExperimentDAHD.plot` usa `_params`, che non è definito. `ExperimentSSTS` (lo sweep DA × HD) usa `restart_kernel`, `tqdm` e `s.bg`, che non esistono: va riscritto. Ti servirà in F4 come sweep su DA.
- [ ] `nest.ll_api.sli_func(...)` funziona in NEST 3.8 ma sparirà con NEST senza SLI: rimuovilo, non serve.
- [ ] Pesi e probabilità sono scritti a mano in `msn.py` (`1.0166…`, `0.0190625`, `0.3176…`) invece di essere letti da `params`. Oggi i valori coincidono, ma è fragile. Inoltre la Tab. 2 del paper riporta per NMDA "3.05", mentre il codice usa 3.05/160: annota la discrepanza.

### 2.2 Protocollo di riproduzione
1. Compila: `generate_nest_target("nest_module/msn.nestml", "nest_module/nestml_target")` (o [test_compile.py](test_compile.py)), poi `nest.Install("nestmlmodule")`.
2. Esegui `conda run -n env_nest python run_simulation.py` (1500 ms di warm-up, 50 ms di rampa, 1000 ms di regime, DA = 0.3).
3. Confronta con [general_behaviour.png](general_behaviour.png) e con la Fig. 3 del paper.

### 2.3 Criteri di accettazione (dal paper)
| Grandezza | Paper (Rusiecka) | González-Redondo |
|---|---|---|
| Prima attività misurabile | ~250 ms | — |
| Entrambi i canali a fine warm-up | ~3 Hz | > 5 Hz |
| Canale selezionato a regime | ~18.5 Hz (17.5–20) | 17.5–20 Hz |
| Canale non selezionato a regime | ~2 Hz (< 1 Hz subito dopo 1525 ms) | ~2.5 Hz |
| Convergenza del selezionato | ~250 ms dopo la rampa | più rapida |

Considera la riproduzione riuscita se media ± sd su 10 seed rientrano in questi intervalli e la dinamica qualitativa (picchi transitori, crollo del non selezionato) è la stessa.

**Uscita:** figura riprodotta, tabella numerica su 10 seed, nota scritta con tutte le discrepanze trovate e risolte. Questo è il **tuo baseline v0**.

---

## F3 — Refactoring per avere una base solida (≈1 settimana)

Prima di estendere il modello, rendilo facile da modificare e da testare.

```
msn_code/
  models/msn.nestml           # modello neurone (+ in F4: sinapsi neuromodulate)
  config/                     # parametri (YAML o dataclass), uno per esperimento
  network/msn_network.py      # costruzione rete (nessun valore scritto a mano)
  experiments/ramp.py         # esperimento del paper
  experiments/da_sweep.py     # sweep DA (ex ExperimentSSTS)
  analysis/metrics.py         # firing rate, selettività, ecc.
  analysis/plots.py
  tests/                      # pytest: PSP singolo, f-I, conteggio neuroni/connessioni
  scripts/compile_module.py
  results/<data>_<esperimento>/   # spike salvati (npz) + config usata
```

- [ ] Compila una volta sola e carica soltanto (non ricompilare a ogni run).
- [ ] Ogni run salva la propria config e il seed insieme ai risultati.
- [ ] Interfaccia pulita: `net.set_input_rates([r0, r1, r2])`, `net.step(dt)`, `net.get_rates(window)`. È esattamente ciò che servirà al closed loop.
- [ ] Usa `nest.Prepare()` / `nest.Run(dt)` / `nest.Cleanup()` per i loop a passi brevi (molto più veloce di tanti `Simulate`).

**Uscita:** `pytest` passa, e il notebook o lo script originale riproducono gli stessi numeri di F2 usando il nuovo codice.

---

## F4 — Estensione neuromodulatoria (4–6 settimane): il cuore della tesi

### 4.1 Definire cosa significa "stato neuromodulatorio"
Oggi la dopamina è un **parametro statico** (φ1 = φ2 = 0.3). L'idea è passare a un vettore di stato **N** = (DA tonica, DA fasica, eventualmente altri modulatori) che controlla parametri neuronali e sinaptici.

Livelli di intervento, dal più semplice al più ricco:

| Livello | Cosa modula | Implementazione |
|---|---|---|
| **L1 – DA tonica runtime** | φ1, φ2 per popolazione (D1/D2 separati) | sono già parametri: `nest.SetStatus(pop, {'y1':…, 'y2':…})` durante la simulazione. **Gratis.** |
| **L2 – Modulazione sinaptica** | peso/τ dell'inibizione laterale (GABA), guadagno corticale (AMPA/NMDA) | nuovi parametri nel `.nestml` (es. `g_gaba_mod`) oppure `SetStatus` sulle connessioni |
| **L3 – DA dinamica** | φ(t) come variabile di stato con dinamica propria (tonica + fasica, decadimento τ_DA) | porta di input `da_spikes <- spike` nel `.nestml` e una popolazione "SNc/VTA" che invia spike DA |
| **L4 – Plasticità a tre fattori** | pesi ctx→MSN | `stdp_dopamine_synapse` di NEST (volume transmitter) oppure sinapsi NESTML con eligibility trace; D1: Δw ∝ +δ, D2: Δw ∝ −δ (come in SC_Report_BRL, Fig. 7) |

Raccomandazione: **L1 → L2 → L3**, con L4 solo se avanza tempo o se il relatore vuole esplicitamente l'apprendimento. La tesi chiede adattamento *senza riaddestramento*, quindi la parte essenziale è L1–L3. L4 è la naturale estensione "actor-critic" del report BRL.

### 4.2 Esperimenti in open loop (prima del robot!)
- [ ] **Sweep DA** (riscrivi `ExperimentSSTS`): heatmap di selettività transitoria e di regime al variare di φ1 e φ2 (anche separatamente per D1 e D2).
- [ ] Sweep di modulazione dell'inibizione laterale e del guadagno corticale.
- [ ] **Cerca regimi qualitativamente diversi** di action selection. Ad esempio:
  - *winner-take-all forte* (molto selettivo, decisioni nette ma lente a cambiare);
  - *soft selection* (più canali attivi, risposta graduata, più "esplorativa");
  - *switching rapido* (bassa isteresi, reattivo a input che cambiano velocemente).
- [ ] Metriche per ogni regime: selettività, latenza di selezione, isteresi (quanto deve variare l'input perché la selezione cambi), robustezza al rumore, rate massimi.
- [ ] Input dinamici: invertire quale canale è più forte a metà simulazione e misurare il tempo di switch. Questo è il test chiave per il robot.

### 4.3 Chi decide lo stato neuromodulatorio? (decisione da prendere con il relatore)
- **A. Oracolo**: lo stato è impostato a mano in base all'ambiente (es. "corridoio" → regime X). Più semplice: dimostra che *esiste* uno stato adatto a ciascun ambiente.
- **B. Contesto sensoriale**: N = f(densità di ostacoli, larghezza del passaggio…), una funzione semplice e fissata, non appresa.
- **C. Reward / TD**: critic (SC_Report_BRL) che calcola δ dalle collisioni e dal progresso; δ guida la DA fasica.

Progressione consigliata: **A → B**, con C come obiettivo ambizioso. A da sola risponde già alla domanda "stati diversi → strategie diverse"; B mostra un adattamento autonomo senza riaddestramento.

**Uscita:** almeno 2–3 stati neuromodulatori con comportamento di selezione misurabilmente diverso, caratterizzati in open loop con figure e metriche.

---

## F5 — Closed loop con robot simulato (4–6 settimane)

### 5.1 Scelta del simulatore: partire semplice
Hai già ROS2 e Isaac Lab in ambienti separati: bene, ma **non iniziare da lì**.

1. **v1 – Simulatore 2D in Python puro dentro `env_nest`** (robot uniciclo, lidar a raggi, mappe a griglia: ~200 righe con numpy). Nessuna dipendenza, debug immediato, migliaia di episodi veloci. Ti permette di validare encoding, decoding e timing.
2. **v2 – ROS2 + Gazebo (es. TurtleBot3)** oppure **Isaac Lab**, per realismo e per la tesi.
   - Attenzione: `rclpy` è legato al Python di sistema di ROS2 (es. 3.10 su Humble, 3.12 su Jazzy), mentre `env_nest` usa 3.11. Non mescolare gli ambienti. Usa un **bridge** (ZeroMQ o socket) tra il processo NEST e un nodo ROS2 che pubblica `/cmd_vel` e legge `/scan`. Stesso discorso per Isaac Lab.

### 5.2 Encoding (sensori → spike)
- 3 canali = 3 azioni: **sinistra / dritto / destra**. Si adatta bene all'architettura esistente, ma oggi il canale 3 è "background" e ha il 20% dei neuroni: decidi se renderlo un canale-azione con il 40% come gli altri (consigliato: canali simmetrici).
- Lidar diviso in 3 settori → *spazio libero* per settore → rate Poisson del canale corrispondente, mappato nell'intervallo usato nel paper (2.2–3.6 Hz × 250 afferenze), così resti nel regime in cui la rete è caratterizzata.
- Alternative da confrontare: rate coding lineare o log, population coding con più settori per canale.

### 5.3 Decoding (spike → comandi motori)
- Firing rate per canale su una finestra mobile (es. 50–100 ms), che corrisponde a un ciclo di controllo.
- Opzioni: (a) winner-take-all → azione discreta; (b) media pesata → ω continuo; (c) usare **D1 − D2** per canale (Go/NoGo, coerente con direct/indirect pathway). La (c) è la più interessante dal punto di vista biologico e dà un ruolo funzionale alla differenza D1/D2.
- v lineare costante oppure proporzionale alla "confidenza" (selettività).

### 5.4 Timing del loop
- Passo di controllo Δt = 20–50 ms: `nest.Run(Δt)`, poi leggi gli spike, aggiorni il robot e imposti i nuovi rate.
- Il transitorio iniziale della rete è di ~1.5 s: fai un warm-up prima di iniziare l'episodio.
- Misura il rapporto tempo reale / tempo simulato: con ~2300 MSN e risoluzione 0.01 ms potrebbe essere lento. Valuta più thread, risoluzione 0.1 ms o una rete ridotta (documentando che il comportamento resta lo stesso).

**Uscita:** il robot in v1 evita ostacoli in spazio aperto con DA fissa = 0.3 (baseline funzionante).

---

## F6 — Esperimenti finali e confronto con la baseline (3–4 settimane)

### Ambienti
Spazio aperto · corridoio stretto · corridoio con curve · ostacoli sparsi o densi · (opz.) ostacoli dinamici · ambienti che **cambiano durante l'episodio** (test diretto di adattamento).

### Condizioni a confronto
1. **Baseline senza neuromodulazione**: stessa rete, φ fissi (0.3), nessuna modulazione sinaptica.
2. Neuromodulazione con stato fissato per ambiente (oracolo, A).
3. Neuromodulazione dipendente dal contesto (B).
4. (opz.) Neuromodulazione guidata da reward/TD (C).
5. (opz.) Controllore di riferimento non spiking (es. Braitenberg o potential field) per dare una scala ai risultati.

### Metriche
Collisioni/episodio · tasso di successo · tempo e lunghezza del percorso · distanza minima dagli ostacoli · smoothness (variazioni di ω) · frequenza di switch delle azioni e oscillazioni · selettività della rete durante il task.

### Rigore
- ≥ 20 episodi × più seed per condizione, posizioni iniziali randomizzate.
- Test statistici (es. Mann–Whitney o Kruskal–Wallis) e intervalli di confidenza.
- **Ablazioni**: modula solo D1, solo D2, solo l'inibizione laterale, ecc., per capire *quale* meccanismo produce l'adattamento.

**Uscita:** tabella e figure che rispondono alla domanda di ricerca, inclusi i casi in cui la neuromodulazione **non** aiuta.

---

## F7 — Scrittura (in parallelo, intensiva nelle ultime 3–4 settimane)

Struttura suggerita: Introduzione → Background (BG, D1/D2, action selection, neuromodulazione, SNN in robotica) → Modello MSN e riproduzione (F1–F2) → Estensione neuromodulatoria e caratterizzazione open loop (F4) → Closed loop (F5) → Risultati (F6) → Discussione e limiti → Conclusioni.

Tieni un `JOURNAL.md` con data, cosa hai provato, risultato e decisione: in fase di scrittura vale oro.

---

## Rischi principali e mitigazioni

| Rischio | Mitigazione |
|---|---|
| NESTML 9 ≠ NESTML 5 → la riproduzione non torna | test PSP del neurone singolo (F1.3) prima della rete; in ultima istanza, ambiente separato con la versione storica |
| Simulazione troppo lenta per il closed loop | `Prepare/Run`, multithread, rete scalata, v1 in Python puro senza real-time |
| I diversi stati DA non producono strategie abbastanza diverse | estendere la modulazione all'inibizione laterale e al guadagno corticale (L2), dove l'effetto sulla competizione è più diretto |
| Bridge NEST ↔ ROS2 / Isaac complicato | completare tutta la F6 in v1 2D; v2 solo come dimostrazione di trasferimento |
| Scope troppo ampio (L4 + Isaac + RL) | L1–L3 + scelta A/B + simulatore 2D sono già una tesi completa; il resto è un bonus |

## Domande da portare al relatore
1. Neuromodulazione "oracolo/contesto" (A/B) è sufficiente, o serve un meccanismo basato su reward/TD (C, L4)?
2. Solo dopamina, o anche altri modulatori (es. acetilcolina, serotonina) come dimensioni separate dello stato?
3. Robot: mobile 2D va bene come piattaforma principale? Gazebo/TurtleBot3 o Isaac Lab per la parte "realistica"? Il cobot è davvero un'opzione?
4. Il terzo canale: mantenerlo come background (come in González-Redondo) o trasformarlo in un'azione?
5. Serve mantenere la scala biologica (2292 MSN), o è accettabile una rete ridotta per il closed loop?

---

## Prossimi passi concreti (questa settimana)
1. [ ] F0: re-init git, `.gitignore`, `environment.yml`, commit "originale".
2. [ ] Compilare `msn.nestml` con NESTML 9 e annotare ogni warning o errore.
3. [ ] Test PSP del neurone singolo e curva f–I D1/D2.
4. [ ] Correggere il calcolo del firing rate e il seed, poi lanciare `run_simulation.py` su 10 seed.
5. [ ] Compilare la tabella di confronto F2.3.
