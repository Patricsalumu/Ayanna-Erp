import sys
import os
sys.path.append('.')

try:
    from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
    from ayanna_erp.modules.boutique.view.commandes_index import CommandesIndexWidget
    from PyQt6.QtWidgets import QApplication
    import tempfile

    # Créer une application Qt temporaire
    app = QApplication([])

    # Créer un widget temporaire pour tester
    widget = CommandesIndexWidget(None, None)

    # Récupérer quelques commandes
    controller = CommandeController()
    commandes = controller.get_commandes(limit=3)

    if not commandes:
        print("❌ Aucune commande trouvée pour le test")
        sys.exit(1)

    print(f"✅ {len(commandes)} commandes récupérées pour test PDF")

    # Tester le formatage des produits
    for i, cmd in enumerate(commandes[:2]):
        produits_raw = str(cmd.get('produits', ''))
        produits_formatted = widget._format_produits_services(produits_raw)
        print(f"Commande {i+1} - Produits formatés:")
        print(f"  Original: {repr(produits_raw)}")
        print(f"  Formaté: {repr(produits_formatted)}")
        print()

    # Tester la génération PDF
    pdf_filename = widget._generate_commandes_pdf(commandes, None, None, None, None)

    if pdf_filename and os.path.exists(pdf_filename):
        file_size = os.path.getsize(pdf_filename)
        print(f"✅ PDF généré avec succès: {pdf_filename}")
        print(f"   Taille: {file_size} bytes")

        # Ouvrir le PDF avec l'explorateur
        try:
            import subprocess
            subprocess.run(['explorer', '/select,', pdf_filename], shell=True, check=True)
            print("✅ Explorateur ouvert sur le fichier PDF")
        except Exception as e:
            print(f"⚠️ Impossible d'ouvrir l'explorateur: {e}")

    else:
        print("❌ Échec de génération du PDF")

    app.quit()

except Exception as e:
    print(f"❌ Erreur test PDF: {e}")
    import traceback
    traceback.print_exc()