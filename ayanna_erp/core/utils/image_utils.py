"""
Utilitaires pour la gestion des images et des logos
"""

import os
import base64
from PIL import Image
from io import BytesIO


class ImageUtils:
    """Classe utilitaire pour la gestion des images"""
    
    @staticmethod
    def file_to_blob(file_path):
        """
        Convertir un fichier image en BLOB
        
        Args:
            file_path (str): Chemin vers le fichier image
            
        Returns:
            bytes: Données binaires de l'image ou None
        """
        try:
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'rb') as file:
                return file.read()
                
        except Exception as e:
            print(f"Erreur lors de la conversion fichier vers BLOB: {e}")
            return None
    
    @staticmethod
    def blob_to_pixmap(blob_data):
        """
        Convertir des données BLOB en QPixmap pour PyQt
        
        Args:
            blob_data (bytes): Données binaires de l'image
            
        Returns:
            QPixmap: Objet QPixmap ou None
        """
        try:
            if not blob_data:
                return None
                
            from PyQt6.QtGui import QPixmap
            
            pixmap = QPixmap()
            pixmap.loadFromData(blob_data)
            
            return pixmap if not pixmap.isNull() else None
            
        except Exception as e:
            print(f"Erreur lors de la conversion BLOB vers QPixmap: {e}")
            return None
    
    @staticmethod
    def resize_image_blob(blob_data, max_width=200, max_height=200, quality=85):
        """
        Redimensionner une image stockée en BLOB
        
        Args:
            blob_data (bytes): Données binaires de l'image
            max_width (int): Largeur maximale
            max_height (int): Hauteur maximale
            quality (int): Qualité de compression (1-100)
            
        Returns:
            bytes: Image redimensionnée en BLOB
        """
        try:
            if not blob_data:
                return None
                
            # Ouvrir l'image depuis les données binaires
            image = Image.open(BytesIO(blob_data))
            
            # Convertir en RGB si nécessaire (pour JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Calculer la nouvelle taille en gardant le ratio
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Sauvegarder en mémoire
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Erreur lors du redimensionnement: {e}")
            return blob_data  # Retourner l'original en cas d'erreur
    
    @staticmethod
    def validate_image_file(file_path):
        """
        Valider qu'un fichier est une image valide
        
        Args:
            file_path (str): Chemin vers le fichier
            
        Returns:
            bool: True si c'est une image valide
        """
        try:
            if not os.path.exists(file_path):
                return False
                
            # Extensions acceptées
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext not in valid_extensions:
                return False
            
            # Tenter d'ouvrir l'image
            with Image.open(file_path) as img:
                img.verify()  # Vérifier que c'est une image valide
                
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def get_image_info(blob_data):
        """
        Obtenir des informations sur une image BLOB
        
        Args:
            blob_data (bytes): Données binaires de l'image
            
        Returns:
            dict: Informations sur l'image (format, taille, dimensions)
        """
        try:
            if not blob_data:
                return None
                
            image = Image.open(BytesIO(blob_data))
            
            return {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'data_size': len(blob_data)
            }
            
        except Exception as e:
            print(f"Erreur lors de l'extraction d'informations: {e}")
            return None
    
    @staticmethod
    def blob_to_base64(blob_data):
        """
        Convertir un BLOB en string base64 (pour affichage web)
        
        Args:
            blob_data (bytes): Données binaires de l'image
            
        Returns:
            str: Image encodée en base64 ou None
        """
        try:
            if not blob_data:
                return None
                
            return base64.b64encode(blob_data).decode('utf-8')
            
        except Exception as e:
            print(f"Erreur lors de la conversion en base64: {e}")
            return None
    
    @staticmethod
    def create_thumbnail_blob(file_path, size=(100, 100)):
        """
        Créer une miniature d'un fichier image et la retourner en BLOB
        
        Args:
            file_path (str): Chemin vers l'image source
            size (tuple): Taille de la miniature (largeur, hauteur)
            
        Returns:
            bytes: Miniature en BLOB
        """
        try:
            if not ImageUtils.validate_image_file(file_path):
                return None
                
            with Image.open(file_path) as image:
                # Convertir en RGB si nécessaire
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # Créer la miniature
                image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Sauvegarder en mémoire
                output = BytesIO()
                image.save(output, format='JPEG', quality=90, optimize=True)
                
                return output.getvalue()
                
        except Exception as e:
            print(f"Erreur lors de la création de miniature: {e}")
            return None