import os
import numpy as np


def grouped_file(fichiers_chemins):
    """Takes a list of acquisition file paths,
    sums the 'counts' channel by channel and the 'number of frames',
    then exports a new file updating the metadata line.
    """
    if not fichiers_chemins:
        print("Error: The file list is empty.")
        return

    premier_fichier = fichiers_chemins[0]
    nbr_frames_total = 0
    idx_frame_line = None
    cle_separateur = ":"
    
    # 1. Read the header of the first file
    with open(premier_fichier, 'r', encoding='utf-8') as f:
        lignes = f.readlines()
    
    # Isolate the first 15 header lines
    entete_lignes = lignes[:15]
    
    # Extract frames from the first file
    for idx, ligne in enumerate(entete_lignes):
        if "number of frame" in ligne.lower() or "number of frames" in ligne.lower():
            cle_separateur = ":" if ":" in ligne else "="
            try:
                valeur = ligne.split(cle_separateur)[-1].strip()
                nbr_frames_total += int(valeur)
                idx_frame_line = idx  
            except ValueError:
                pass

    # Load numerical data from the first file
    donnees_premiers = np.loadtxt(premier_fichier, skiprows=15)
    tof_axe = donnees_premiers[:, 0]
    counts_cumules = donnees_premiers[:, 1]

    # 2. Loop over remaining files (full header extraction)
    for chemin in fichiers_chemins[1:]:
        with open(chemin, 'r', encoding='utf-8') as f:
            lignes_courantes = f.readlines()[:15]
            for ligne in lignes_courantes:
                if "number of frame" in ligne.lower() or "number of frames" in ligne.lower():
                    sep = ":" if ":" in ligne else "="
                    try:
                        valeur = ligne.split(sep)[-1].strip()
                        nbr_frames_total += int(valeur)
                    except ValueError:
                        pass
        
        # Sum of counts channel by channel
        donnees_courantes = np.loadtxt(chemin, skiprows=15)
        counts_cumules += donnees_courantes[:, 1]

    # 3. Clean replacement on the same line (no spurious line breaks)
    if idx_frame_line is not None:
        ligne_origine = entete_lignes[idx_frame_line]
        # Extract the clean key without spaces or line breaks
        cle = ligne_origine.split(cle_separateur)[0].strip()
        # Rebuild the line uniformly
        entete_lignes[idx_frame_line] = f"{cle}{cle_separateur} {nbr_frames_total}\n"
    else:
        print("Warning: The 'Number of frames' line was not detected.")

    # 4. Export
    base_path, ext = os.path.splitext(premier_fichier)
    chemin_export = f"{base_path}_grp{ext}"

    with open(chemin_export, 'w', encoding='utf-8') as f_out:
        f_out.writelines(entete_lignes)
        for t, c in zip(tof_axe, counts_cumules):
            f_out.write(f"  {t:<13}  {int(c)}\n")

    print(f"Success: Grouped file exported -> {chemin_export}")
    print(f"Total cumulative frames rewritten: {nbr_frames_total}")
    