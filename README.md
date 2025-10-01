# 🔥 Ultra-Turbo AppData Cleaner v4.0

## Descriere
Script PowerShell ultra-performant pentru curățarea AppData și optimizarea spațiului de stocare pe Windows. Utilizează tehnici hibride CMD + PowerShell pentru performanță maximă.

## 🚀 Caracteristici
- **Ultra-rapid**: Tehnici hibride CMD + PowerShell pentru viteză maximă
- **Sigur**: Verificări extensive și gestionare robustă a erorilor
- **Compatibil**: Funcționează pe PowerShell 5.1+ și Windows 10/11
- **Detaliat**: Raportare completă cu statistici performanță în timp real
- **Modular**: Arhitectură modulară pentru întreținere ușoară

## 📋 Cerințe
- Windows 10/11
- PowerShell 5.1 sau superior  
- Drepturi Administrator (rulare ca Administrator)

## 🔧 Instalare și Utilizare

### Instalare Rapidă
```powershell
# Clonare repository
git clone https://github.com/Gzeu/ultra-turbo-appdata-cleaner.git
cd ultra-turbo-appdata-cleaner

# Rulare script instalare
.\scripts\install.ps1
```

### Utilizare
```powershell
# Rulare script principal (ca Administrator)
.\src\AppDataCleaner.ps1

# Rulare în mod test (fără ștergere efectivă)
.\src\AppDataCleaner.ps1 -DryRun

# Rulare cu logging detaliat
.\src\AppDataCleaner.ps1 -Verbose -LogPath "C:\logs\cleanup.log"
```

## 📊 Performanță Demonstrată
- **2700+ fișiere** procesate în **28.6 secunde**
- **1.2+ GB** spațiu eliberat în medie
- **43 MB/sec** viteză de procesare
- **Multiple locații** procesate simultan

## 📁 Zone de Curățare

### AppData Local Cleanup
- Temp files (`%LOCALAPPDATA%\Temp`)
- Browser cache (Chrome, Edge, Opera, Firefox)
- INetCache și WebCache
- CrashDumps
- GPU Cache
- Office FileCache

### AppData Roaming Cleanup  
- Microsoft Teams (cache, logs, blob storage)
- Slack cache și logs
- Zoom logs
- Adobe Flash Player cache

### System Cleanup
- Windows Temp (`%windir%\Temp`)
- Prefetch files
- Windows Update cache
- Recycle Bin
- Registry cleanup (Recent Docs, MRU)

## 🛡️ Funcții de Siguranță
- **Verificări Path**: Test-Path înainte de orice operațiune
- **Gestionare Excepții**: Try-catch pentru toate operațiunile critice
- **Timeout Protection**: Timeout automat pentru operații lungi
- **Fallback Methods**: Metode alternative în caz de eșec
- **Dry Run Mode**: Testare fără ștergere efectivă

## 🏗️ Arhitectura Proiectului

```
ultra-turbo-appdata-cleaner/
├── src/
│   ├── AppDataCleaner.ps1          # Script principal
│   ├── modules/
│   │   ├── DiskUtils.psm1          # Utilitare disk
│   │   └── CleaningEngine.psm1     # Engine curățare
│   └── config/
│       └── cleaning-paths.json     # Configurație paths
├── docs/                           # Documentație
├── tests/                          # Teste unitare
├── scripts/                        # Scripturi instalare
└── README.md                       # Documentația aceasta
```

## 📈 Exemplu Output

```
═══════════════════════════════════════════════════════════════
🔥 ULTRA-TURBO APPDATA CLEANER v4.0 FIXED 🔥
═══════════════════════════════════════════════════════════════
💾 Spațiu inițial: 45.2 GB / 250.0 GB (18.1%)
👤 User curent: UserName
⚠️  CLEANUP AGRESIV APPDATA ACTIVAT!

⚡ 🎯 APPDATA LOCAL CLEANUP
   🎯 TOTAL: 2496 fișiere, 1201.5 MB din 10 locații

🗂️ SYSTEM TEMP CLEANUP
   🎯 TOTAL: 242 fișiere, 13.4 MB din 3 locații

═══════════════════════════════════════════════════════════════
🎉 CLEANUP FINALIZAT CU SUCCES!
═══════════════════════════════════════════════════════════════
⏱️  TIMP TOTAL: 28.6 secunde
📊 ÎNAINTE: 45.2 GB (18.1%)
📊 DUPĂ:    46.4 GB (18.6%)
🚀 SPAȚIU ELIBERAT: 1.20 GB
⚡ VITEZĂ: 43.0 MB/sec
```

## 🤝 Contribuții
Contribuțiile sunt binevenite! Pentru bug reports, feature requests sau pull requests:

1. Fork repository-ul
2. Creează branch pentru feature (`git checkout -b feature/AmazingFeature`)
3. Commit modificările (`git commit -m 'Add AmazingFeature'`)
4. Push la branch (`git push origin feature/AmazingFeature`)
5. Deschide Pull Request

## 📝 Licență
Acest proiect este licențiat sub MIT License - vezi fișierul [LICENSE](LICENSE) pentru detalii.

## ⚠️ Disclaimer
Acest script șterge fișiere din sistem. Deși include verificări de siguranță, utilizarea se face pe propria răspundere. Recomandăm backup-ul datelor importante înainte de utilizare.

## 🔄 Recomandări
- Rulează lunar pentru performanțe optime
- Verifică Downloads folder pentru fișiere mari
- Dezinstalează aplicații neutilizate
- Monitorizează spațiul rămas după curățare