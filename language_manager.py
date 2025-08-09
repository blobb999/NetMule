import json
import os
from typing import Dict, Any

class LanguageManager:
    def __init__(self, language_file_path: str = "languages.json", default_language: str = "de"):
        """
        Verwaltet die Mehrsprachigkeit der Anwendung
        
        Args:
            language_file_path: Pfad zur JSON-Datei mit den Sprachdefinitionen
            default_language: Standard-Sprache (z.B. 'de' oder 'en')
        """
        self.language_file_path = language_file_path
        self.current_language = default_language
        self.default_language = default_language
        self.translations = {}
        self.load_languages()
    
    def load_languages(self) -> None:
        """Lädt die Sprachdefinitionen aus der JSON-Datei"""
        try:
            if os.path.exists(self.language_file_path):
                with open(self.language_file_path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            else:
                print(f"Warnung: Sprachdatei {self.language_file_path} nicht gefunden. Verwende Standard-Übersetzungen.")
                self.translations = self._get_fallback_translations()
        except Exception as e:
            print(f"Fehler beim Laden der Sprachdatei: {e}")
            self.translations = self._get_fallback_translations()
    
    def _get_fallback_translations(self) -> Dict[str, Any]:
        """Fallback-Übersetzungen falls die Datei nicht geladen werden kann"""
        return {
            "de": {
                "app_title": "NetMule",
                "menu": {"file": "Datei", "edit": "Bearbeiten"},
                "messages": {"error": "Fehler", "success": "Erfolg"}
            },
            "en": {
                "app_title": "NetMule", 
                "menu": {"file": "File", "edit": "Edit"},
                "messages": {"error": "Error", "success": "Success"}
            }
        }
    
    def set_language(self, language_code: str) -> bool:
        """
        Setzt die aktuelle Sprache
        
        Args:
            language_code: Sprachcode (z.B. 'de', 'en')
            
        Returns:
            True wenn die Sprache erfolgreich gesetzt wurde
        """
        if language_code in self.translations:
            self.current_language = language_code
            return True
        else:
            print(f"Warnung: Sprache '{language_code}' nicht verfügbar. Verwende '{self.default_language}'.")
            return False
    
    def get_available_languages(self) -> list:
        """Gibt eine Liste der verfügbaren Sprachen zurück"""
        return list(self.translations.keys())
    
    def tr(self, key_path: str, **kwargs) -> str:
        """
        Übersetzt einen Schlüssel in die aktuelle Sprache
        
        Args:
            key_path: Pfad zum Übersetzungsschlüssel (z.B. 'menu.file' oder 'messages.error')
            **kwargs: Parameter für String-Formatierung
            
        Returns:
            Übersetzter String oder Fallback
        """
        try:
            # Versuche aktuelle Sprache
            translation = self._get_translation(key_path, self.current_language)
            if translation is not None:
                return translation.format(**kwargs) if kwargs else translation
            
            # Fallback zur Standard-Sprache
            if self.current_language != self.default_language:
                translation = self._get_translation(key_path, self.default_language)
                if translation is not None:
                    return translation.format(**kwargs) if kwargs else translation
            
            # Letzter Fallback: Schlüssel selbst
            print(f"Warnung: Übersetzung für '{key_path}' in Sprache '{self.current_language}' nicht gefunden.")
            return key_path.split('.')[-1]  # Nimm den letzten Teil des Pfads
            
        except Exception as e:
            print(f"Fehler bei der Übersetzung von '{key_path}': {e}")
            return key_path.split('.')[-1]
    
    def _get_translation(self, key_path: str, language: str) -> str:
        """
        Hilfsmethode zum Abrufen einer Übersetzung aus dem verschachtelten Dictionary
        
        Args:
            key_path: Pfad zum Schlüssel (z.B. 'menu.file')
            language: Sprachcode
            
        Returns:
            Übersetzung oder None wenn nicht gefunden
        """
        if language not in self.translations:
            return None
        
        keys = key_path.split('.')
        current = self.translations[language]
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def add_language(self, language_code: str, translations: Dict[str, Any]) -> None:
        """
        Fügt eine neue Sprache zur Laufzeit hinzu
        
        Args:
            language_code: Sprachcode
            translations: Übersetzungs-Dictionary
        """
        self.translations[language_code] = translations
    
    def save_languages(self) -> bool:
        """
        Speichert die aktuellen Übersetzungen in die JSON-Datei
        
        Returns:
            True wenn erfolgreich gespeichert
        """
        try:
            with open(self.language_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.translations, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Sprachdatei: {e}")
            return False

# Globale Instanz des LanguageManager
_lang_manager = None

def get_language_manager() -> LanguageManager:
    """Singleton-Zugriff auf den LanguageManager"""
    global _lang_manager
    if _lang_manager is None:
        _lang_manager = LanguageManager()
    return _lang_manager

def tr(key_path: str, **kwargs) -> str:
    """Shortcut-Funktion für Übersetzungen"""
    return get_language_manager().tr(key_path, **kwargs)
