#!/usr/bin/env python3
"""
Test simple de la méthode figure_to_image
"""

import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
import io

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    print("Test de la méthode figure_to_image...")
    
    # Créer une figure simple
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title("Test Figure")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    
    # Test de la méthode de sauvegarde
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    
    print(f"✓ Figure sauvegardée en mémoire, taille: {len(img_buffer.getvalue())} bytes")
    
    # Test avec PILImage
    from PIL import Image as PILImage
    pil_img = PILImage.open(img_buffer)
    print(f"✓ Image PIL créée, dimensions: {pil_img.size}")
    
    plt.close(fig)
    print("\n🎉 Test de figure_to_image réussi !")
    
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")
    import traceback
    traceback.print_exc()