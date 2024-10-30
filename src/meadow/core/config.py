"""Configuration management for Meadow"""

import os
import json
import keyring

class Config:
    """Singleton configuration manager"""
    _instance = None
    _config = None
    _config_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def __init__(self):
        """Initialize configuration settings"""
        if not hasattr(self, 'app_dir'):  # Only initialize once
            self._initialize()

    def _initialize(self):
        """Initialize configuration settings"""
        self.app_dir = os.path.expanduser('~/Library/Application Support/Meadow')
        self.config_dir = os.path.join(self.app_dir, 'config')
        self._config_path = os.path.join(self.config_dir, 'config.json')

        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)

        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        default_config = {
            'notes_dir': os.path.join(os.path.expanduser('~/Documents'), 'Meadow Notes'),
            'interval': 60,
            'research_topics': ['civic government']
        }

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                # Ensure all default keys exist
                for key, value in default_config.items():
                    if key not in self._config:
                        self._config[key] = value
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = default_config
            self._save_config()

    def _save_config(self):
        """Save current configuration to file"""
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f)

    def get(self, key, default=None):
        """Get configuration value"""
        return self._config.get(key, default)

    def get_all(self):
        """Get full configuration dictionary"""
        return self._config.copy()

    def set(self, key, value):
        """Set configuration value"""
        self._config[key] = value
        self._save_config()

    def update(self, updates):
        """Update multiple configuration values"""
        self._config.update(updates)
        self._save_config()

    def get_api_key(self):
        """Get API key from secure storage"""
        return keyring.get_password("meadow", "anthropic_api_key")

    def set_api_key(self, key):
        """Set API key in secure storage"""
        if key:
            keyring.set_password("meadow", "anthropic_api_key", key)
